#!/usr/bin/env python3
"""
analyze_failure_modes.py -- Reproducible failure taxonomy and mitigation analysis.

Identifies all unsafe mutations, classifies them by Type A/B/C coverage footprint,
evaluates the constructor-only mitigation rule, and produces deterministic JSON output.

Usage:
  python3 analysis/analyze_failure_modes.py --write
  python3 analysis/analyze_failure_modes.py --verify
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, discover_pit_files, load_pit_mutations,
    build_base_to_keys, resolve_killing_tests,
    select_original, select_constructor_only_rule, select_class_level,
    aggregate_sha256, file_sha256,
)


def classify_entry(test_mappings, coverage_key, mutated_class, mutated_method):
    """Classify a single resolved coverage entry for a killing test."""
    cov = test_mappings.get(coverage_key, {})
    classes = cov.get("classes", [])
    methods = cov.get("methods", [])

    method_fqn = f"{mutated_class}#{mutated_method}"

    if mutated_class not in classes:
        return "C", False, False, []

    class_methods = [m for m in methods if m.startswith(mutated_class + "#")]

    if not class_methods:
        # classPresentNoMethods -- should be impossible for unsafe entries (invariant)
        return "classPresentNoMethods", True, False, class_methods

    mutated_present = method_fqn in methods

    all_constructors = all(
        "#<init>" in m or "#<clinit>" in m
        for m in class_methods
    )

    if all_constructors:
        return "A", True, mutated_present, class_methods
    else:
        return "B", True, mutated_present, class_methods


def run_analysis(repo_root, projects_config, coverage_overrides=None):
    """Run complete analysis. Returns (taxonomy_dict, mitigation_dict)."""

    all_resolved_mutations = {}  # project -> list[ResolvedMutation]
    inputs_coverage = {}
    inputs_pit = {}

    for proj in projects_config["projects"]:
        name = proj["name"]

        # Load coverage map
        if coverage_overrides and name in coverage_overrides:
            map_path = Path(coverage_overrides[name])
        else:
            map_path = repo_root / proj["coverageMap"]

        coverage_data = load_coverage_map(map_path)
        test_mappings = coverage_data["testMappings"]
        commit = coverage_data.get("metadata", {}).get("commitId", "unknown")

        inputs_coverage[name] = {
            "commit": commit,
            "tests": len(test_mappings),
            "sha256": file_sha256(map_path),
        }

        # Load and resolve mutations
        base_to_keys = build_base_to_keys(test_mappings)
        pit_files = discover_pit_files(repo_root, proj["pitFiles"])
        raw_mutations = load_pit_mutations(name, repo_root, pit_files)
        resolved = resolve_killing_tests(raw_mutations, test_mappings, base_to_keys)

        inputs_pit[name] = {
            "files": [p.relative_to(repo_root).as_posix() for p in pit_files],
            "fileCount": len(pit_files),
            "aggregateSha256": aggregate_sha256(repo_root, pit_files),
            "killedMutations": len(resolved),
        }

        # Verify expected counts
        expected = proj["expected"]
        if len(test_mappings) != expected["totalTests"]:
            raise ValueError(f"{name}: expected {expected['totalTests']} tests, got {len(test_mappings)}")
        if len(resolved) != expected["killedMutations"]:
            raise ValueError(f"{name}: expected {expected['killedMutations']} killed, got {len(resolved)}")

        # Run original selector and verify expected safe/unsafe
        safe_count = 0
        for mut in resolved:
            selected = select_original(test_mappings, mut.mutated_class, mut.mutated_method)
            killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
            if selected & killing_keys:
                safe_count += 1

        if safe_count != expected["safeMutations"]:
            raise ValueError(
                f"{name}: expected {expected['safeMutations']} safe, got {safe_count}"
            )

        all_resolved_mutations[name] = (resolved, test_mappings)

    # === TAXONOMY ===
    unsafe_by_project = {}
    all_entry_types = []
    invariant_class_present_no_methods = 0
    invariant_mutated_method_present = 0

    # Resolution summary (over all mutations, not just unsafe)
    total_pit_occurrences = 0
    total_resolved_entries = 0
    unique_raw_ids = set()
    unique_normalized_ids = set()
    max_entries_per_id = 0
    single_entry_count = 0
    multiple_entry_count = 0

    for name, (resolved, test_mappings) in all_resolved_mutations.items():
        unsafe_muts = []

        for mut in resolved:
            selected = select_original(test_mappings, mut.mutated_class, mut.mutated_method)
            killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)

            # Resolution stats (all mutations)
            for kt in mut.killing_tests:
                total_pit_occurrences += 1
                unique_raw_ids.add(kt.raw_pit_id)
                unique_normalized_ids.add(kt.normalized_id)
                total_resolved_entries += len(kt.coverage_keys)
                if len(kt.coverage_keys) == 1:
                    single_entry_count += 1
                else:
                    multiple_entry_count += 1
                max_entries_per_id = max(max_entries_per_id, len(kt.coverage_keys))

            if selected & killing_keys:
                continue  # safe

            # Unsafe -- classify
            mutation_types = set()
            killing_test_details = []

            for kt in mut.killing_tests:
                entries = []
                for ckey in kt.coverage_keys:
                    etype, class_present, method_present, class_methods = classify_entry(
                        test_mappings, ckey, mut.mutated_class, mut.mutated_method
                    )
                    if etype == "classPresentNoMethods":
                        invariant_class_present_no_methods += 1
                    if method_present:
                        invariant_mutated_method_present += 1

                    mutation_types.add(etype)
                    all_entry_types.append(etype)
                    entries.append({
                        "coverageKey": ckey,
                        "targetClassPresent": class_present,
                        "targetClassMethods": sorted(class_methods),
                        "mutatedMethodPresent": method_present,
                        "type": etype,
                    })

                killing_test_details.append({
                    "rawPitId": kt.raw_pit_id,
                    "pitNormalized": kt.normalized_id,
                    "resolutionMode": kt.resolution_mode,
                    "resolvedEntries": entries,
                })

            # Check if constructor-only rule recovers this mutation
            constructor_selected = select_constructor_only_rule(
                test_mappings, mut.mutated_class, mut.mutated_method
            )
            recovered_by_constructor = bool(constructor_selected & killing_keys)

            unsafe_muts.append({
                "mutationId": mut.mutation_id,
                "mutatedClass": mut.mutated_class,
                "mutatedMethod": mut.mutated_method,
                "line": mut.line_number,
                "mutator": mut.mutator.split(".")[-1] if "." in mut.mutator else mut.mutator,
                "killingTests": killing_test_details,
                "mutationTypes": sorted(mutation_types),
                "recoveredByConstructorRule": recovered_by_constructor,
            })

        unsafe_by_project[name] = unsafe_muts

    # Invariant assertions
    if invariant_class_present_no_methods > 0:
        raise ValueError(
            f"INVARIANT VIOLATED: {invariant_class_present_no_methods} unsafe entries "
            f"have classPresentNoMethods (should be 0 -- Original selector would have selected them)"
        )
    if invariant_mutated_method_present > 0:
        raise ValueError(
            f"INVARIANT VIOLATED: {invariant_mutated_method_present} unsafe entries "
            f"have mutated method present in coverage (should be 0 -- Original selector would have selected them)"
        )

    # Type summary
    from collections import Counter
    entry_counter = Counter(all_entry_types)

    mutation_type_sets = []
    for project_muts in unsafe_by_project.values():
        for m in project_muts:
            mutation_type_sets.append(frozenset(m["mutationTypes"]))

    mutation_containing = Counter()
    for ts in mutation_type_sets:
        for t in ts:
            mutation_containing[t] += 1

    exclusive_counts = Counter()
    for ts in mutation_type_sets:
        if len(ts) == 1:
            exclusive_counts[f"{list(ts)[0]}_only"] += 1
        else:
            exclusive_counts["mixed"] += 1

    total_unsafe = sum(len(v) for v in unsafe_by_project.values())

    taxonomy = {
        "schemaVersion": 1,
        "inputs": {
            "coverageMaps": inputs_coverage,
            "pitResults": inputs_pit,
        },
        "totalUnsafeMutations": total_unsafe,
        "invariants": {
            "classPresentNoMethodsAmongUnsafeEntries": invariant_class_present_no_methods,
            "mutatedMethodPresentAmongUnsafeEntries": invariant_mutated_method_present,
        },
        "resolutionSummary": {
            "pitKillingIdOccurrences": total_pit_occurrences,
            "uniqueRawPitKillingIds": len(unique_raw_ids),
            "uniqueNormalizedPitKillingIds": len(unique_normalized_ids),
            "resolvedCoverageEntryOccurrences": total_resolved_entries,
            "idOccurrencesWithSingleCoverageEntry": single_entry_count,
            "idOccurrencesWithMultipleCoverageEntries": multiple_entry_count,
            "maxEntriesPerIdOccurrence": max_entries_per_id,
        },
        "typeSummary": {
            "byResolvedEntry": dict(sorted(entry_counter.items())),
            "mutationCountsContainingType": dict(sorted(mutation_containing.items())),
            "exclusiveMutationTypes": dict(sorted(exclusive_counts.items())),
        },
        "byProject": {
            name: {
                "unsafeCount": len(muts),
                "mutations": muts,
            }
            for name, muts in unsafe_by_project.items()
        },
    }

    # === MITIGATION COMPARISON ===
    per_project_mitigation = []

    for proj in projects_config["projects"]:
        name = proj["name"]
        resolved, test_mappings = all_resolved_mutations[name]
        total_tests = len(test_mappings)

        results = {}
        for selector_name, selector_fn in [
            ("original", select_original),
            ("constructorOnlyRule", select_constructor_only_rule),
            ("classLevelBaseline", select_class_level),
        ]:
            safe = 0
            sizes = []
            for mut in resolved:
                sel = selector_fn(test_mappings, mut.mutated_class, mut.mutated_method)
                killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
                if sel & killing_keys:
                    safe += 1
                sizes.append(len(sel))

            avg_sel = sum(sizes) / len(sizes) if sizes else 0
            results[selector_name] = {
                "inclusivenessPct": round(safe / len(resolved) * 100, 2),
                "safe": safe,
                "avgSelected": round(avg_sel, 1),
                "selectionRatePct": round(avg_sel / total_tests * 100, 2),
            }

        # Additional recovered by constructor rule
        orig_safe = results["original"]["safe"]
        constr_safe = results["constructorOnlyRule"]["safe"]
        results["constructorOnlyRule"]["additionalRecovered"] = constr_safe - orig_safe

        per_project_mitigation.append({
            "project": name,
            "totalTests": total_tests,
            "totalMutations": len(resolved),
            **results,
        })

    # Aggregated (micro-average)
    all_mutations_count = sum(p["totalMutations"] for p in per_project_mitigation)
    agg = {}
    for selector_name in ["original", "constructorOnlyRule", "classLevelBaseline"]:
        total_safe = sum(p[selector_name]["safe"] for p in per_project_mitigation)
        agg[selector_name] = {
            "inclusivenessPct": round(total_safe / all_mutations_count * 100, 2),
            "safe": total_safe,
        }
    agg["constructorOnlyRule"]["additionalRecovered"] = (
        agg["constructorOnlyRule"]["safe"] - agg["original"]["safe"]
    )

    mitigation = {
        "schemaVersion": 1,
        "methodology": {
            "inclusivenessPct": "100 * safe / total killed mutations",
            "selectionRatePct": "100 * mean(selected / totalTests)",
            "aggregation": "micro-average over all killed mutations across projects",
        },
        "perProject": per_project_mitigation,
        "aggregated": {
            "totalMutations": all_mutations_count,
            **agg,
        },
    }

    return taxonomy, mitigation


def main():
    parser = argparse.ArgumentParser(description="Failure taxonomy and mitigation analysis")
    parser.add_argument("--write", action="store_true", help="Generate output files")
    parser.add_argument("--verify", action="store_true", help="Verify against committed outputs")
    parser.add_argument("--commons-map", type=Path, default=None)
    parser.add_argument("--jgrapht-map", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    if not args.write and not args.verify:
        parser.error("Specify --write or --verify")

    if args.verify and (args.commons_map or args.jgrapht_map):
        parser.error("--verify does not allow coverage map overrides (uses committed inputs)")

    # Load config
    config_path = REPO_ROOT / "analysis" / "projects.json"
    with open(config_path) as f:
        projects_config = json.load(f)

    # Coverage overrides
    overrides = {}
    if args.commons_map:
        overrides["commons-lang"] = str(args.commons_map)
    if args.jgrapht_map:
        overrides["jgrapht"] = str(args.jgrapht_map)

    if overrides and not args.output_dir:
        parser.error("--output-dir required when using custom coverage maps")

    # Run analysis
    taxonomy, mitigation = run_analysis(REPO_ROOT, projects_config, overrides or None)

    # Output
    output_dir = args.output_dir or (REPO_ROOT / "results")
    output_dir.mkdir(parents=True, exist_ok=True)

    taxonomy_path = output_dir / "failure_taxonomy.json"
    mitigation_path = output_dir / "mitigation_comparison.json"

    if args.write:
        taxonomy_json = json.dumps(taxonomy, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        mitigation_json = json.dumps(mitigation, sort_keys=True, indent=2, ensure_ascii=False) + "\n"

        taxonomy_path.write_text(taxonomy_json)
        mitigation_path.write_text(mitigation_json)

        print(f"Written: {taxonomy_path}")
        print(f"Written: {mitigation_path}")
        print(f"\nTotal unsafe mutations: {taxonomy['totalUnsafeMutations']}")
        print(f"Type summary: {taxonomy['typeSummary']['exclusiveMutationTypes']}")
        print(f"\nMitigation (aggregated):")
        print(f"  Original: {mitigation['aggregated']['original']['inclusivenessPct']}%")
        print(f"  Constructor-only: {mitigation['aggregated']['constructorOnlyRule']['inclusivenessPct']}% "
              f"(+{mitigation['aggregated']['constructorOnlyRule']['additionalRecovered']} recovered)")
        print(f"  Class-level: {mitigation['aggregated']['classLevelBaseline']['inclusivenessPct']}%")

        # Check annotations
        annotations_path = REPO_ROOT / "analysis" / "failure_annotations.json"
        if annotations_path.exists():
            with open(annotations_path) as f:
                annotations = json.load(f)
            annotation_ids = {a["mutationId"] for a in annotations}
            taxonomy_ids = set()
            for proj_data in taxonomy.get("byProject", {}).values():
                for m in proj_data.get("mutations", []):
                    taxonomy_ids.add(m["mutationId"])
            missing = taxonomy_ids - annotation_ids
            extra = annotation_ids - taxonomy_ids
            if missing:
                print(f"\nWARNING: {len(missing)} unsafe mutations missing annotations")
            if extra:
                print(f"\nWARNING: {len(extra)} annotations for non-unsafe mutations")
        else:
            print(f"\nWARNING: {annotations_path} not found")

    elif args.verify:
        # Compute fresh
        taxonomy_json = json.dumps(taxonomy, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        mitigation_json = json.dumps(mitigation, sort_keys=True, indent=2, ensure_ascii=False) + "\n"

        # Compare with committed
        errors = []

        if taxonomy_path.exists():
            committed = taxonomy_path.read_text()
            if committed != taxonomy_json:
                errors.append(f"failure_taxonomy.json differs")
        else:
            errors.append(f"failure_taxonomy.json not found at {taxonomy_path}")

        if mitigation_path.exists():
            committed = mitigation_path.read_text()
            if committed != mitigation_json:
                errors.append(f"mitigation_comparison.json differs")
        else:
            errors.append(f"mitigation_comparison.json not found at {mitigation_path}")

        # Check annotations strict
        annotations_path = REPO_ROOT / "analysis" / "failure_annotations.json"
        if annotations_path.exists():
            with open(annotations_path) as f:
                annotations = json.load(f)
            # Check for duplicates
            all_ids = [a["mutationId"] for a in annotations]
            if len(all_ids) != len(set(all_ids)):
                errors.append("Duplicate annotation mutationId detected")
            # Check completeness
            annotation_ids = set(all_ids)
            taxonomy_ids = set()
            for proj_data in taxonomy.get("byProject", {}).values():
                for m in proj_data.get("mutations", []):
                    taxonomy_ids.add(m["mutationId"])
            if taxonomy_ids != annotation_ids:
                missing = taxonomy_ids - annotation_ids
                extra = annotation_ids - taxonomy_ids
                errors.append(f"Annotations mismatch: {len(missing)} missing, {len(extra)} extra")
            # Validate required fields
            for a in annotations:
                if not a.get("mutationId") or not a.get("cause") or not a.get("category"):
                    errors.append(f"Annotation missing required fields: {a.get('mutationId', 'unknown')}")
                    break
        else:
            errors.append("failure_annotations.json not found")

        if errors:
            print("VERIFY FAILED:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("VERIFY PASSED: all outputs match committed artifacts")


if __name__ == "__main__":
    main()
