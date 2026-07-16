#!/usr/bin/env python3
"""
verify_selector_equivalence.py -- Dataset-wide Python/Java selector equivalence.

For every unique (project, changedClass, changedMethod) case represented by the
killed-mutation dataset, compares:
  - Python: evaluation_core.select_original(coverage_map, C, M)
  - Java semantic model: exact TestSelector.selectTests() semantics for
    changedClasses={C}, changedMethods={C#M} (single-method scenario)

The Java semantic model for this specific experimental scenario:
  classesWithMethodInfo = {C}     (extracted from changedMethods)
  classLevelOnlyClasses = {}      (changedClasses - classesWithMethodInfo)

  method_hits = {T : C#M in T.methods}
  if method_hits is non-empty:
      java_selected = method_hits
  else:
      java_selected = {T : C in T.classes}   # escalation

This is NOT running the actual Java binary; it is a faithful Python model of the
production TestSelector.selectTests() for the exact experimental input shape.

Usage:
  python3 analysis/verify_selector_equivalence.py
  python3 analysis/verify_selector_equivalence.py --verify
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, discover_pit_files, load_pit_mutations,
    build_base_to_keys, resolve_killing_tests,
    select_original,
)


def java_semantic_select(test_mappings: dict, changed_class: str, changed_method: str) -> set[str]:
    """
    Model the production Java TestSelector.selectTests() semantics for:
        changedClasses = {changed_class}
        changedMethods = {changed_class#changed_method}

    This means:
        classesWithMethodInfo = {changed_class}
        classLevelOnlyClasses = {} (empty)

    Step 1: method-level matching
        For each test, if changed_class#changed_method is in the test's covered methods,
        select the test and count a method-hit for changed_class.

    Step 2: escalation check
        If zero tests were selected via method-level for changed_class,
        escalate: select ALL tests that cover changed_class at class level.

    No class-level-only fallback applies because classLevelOnlyClasses is empty.
    """
    method_fqn = f"{changed_class}#{changed_method}"

    # Step 1: method-level matching
    method_hits = set()
    for test_name, coverage in test_mappings.items():
        methods = coverage.get("methods", [])
        if method_fqn in methods:
            method_hits.add(test_name)

    # Step 2: escalation
    if method_hits:
        return method_hits
    else:
        # Zero method-level hits for the class -> escalate to class-level
        class_selected = set()
        for test_name, coverage in test_mappings.items():
            classes = coverage.get("classes", [])
            if changed_class in classes:
                class_selected.add(test_name)
        return class_selected


def run_verification(repo_root: Path):
    """Run dataset-wide comparison. Returns the report dict."""
    config_path = repo_root / "analysis" / "projects.json"
    with open(config_path) as f:
        projects_config = json.load(f)

    total_mutations = 0
    unique_cases = set()
    exact_matches = 0
    mismatches = 0
    cases_with_method_hits = 0
    cases_with_zero_method_hits = 0
    cases_with_python_only_fallback = 0
    differences = []
    by_project = {}

    for proj in projects_config["projects"]:
        name = proj["name"]
        map_path = repo_root / proj["coverageMap"]

        coverage_data = load_coverage_map(map_path)
        test_mappings = coverage_data["testMappings"]
        base_to_keys = build_base_to_keys(test_mappings)

        pit_files = discover_pit_files(repo_root, proj["pitFiles"])
        raw_mutations = load_pit_mutations(name, repo_root, pit_files)
        resolved = resolve_killing_tests(raw_mutations, test_mappings, base_to_keys)

        proj_exact = 0
        proj_mismatch = 0
        proj_method_hits = 0
        proj_zero_hits = 0
        proj_python_fallback = 0

        for mut in resolved:
            total_mutations += 1
            case_key = (name, mut.mutated_class, mut.mutated_method)
            unique_cases.add(case_key)

            # Python selector
            python_selected = select_original(test_mappings, mut.mutated_class, mut.mutated_method)

            # Java semantic model
            java_selected = java_semantic_select(test_mappings, mut.mutated_class, mut.mutated_method)

            # Check method hits (for reporting)
            method_fqn = f"{mut.mutated_class}#{mut.mutated_method}"
            has_method_hit = any(
                method_fqn in test_mappings[t].get("methods", [])
                for t in test_mappings
            )
            if has_method_hit:
                cases_with_method_hits += 1
                proj_method_hits += 1
            else:
                cases_with_zero_method_hits += 1
                proj_zero_hits += 1

            # Check for Python-only per-test fallback candidates
            # These are tests where: C in T.classes AND T has no C# methods
            # Python selects them; Java (when method_hits > 0) does not.
            python_only_fallback = set()
            if has_method_hit:
                for test_name, coverage in test_mappings.items():
                    if test_name in python_selected and test_name not in java_selected:
                        python_only_fallback.add(test_name)
            if python_only_fallback:
                cases_with_python_only_fallback += 1
                proj_python_fallback += 1

            # Compare
            if python_selected == java_selected:
                exact_matches += 1
                proj_exact += 1
            else:
                mismatches += 1
                proj_mismatch += 1
                java_only = sorted(java_selected - python_selected)
                python_only = sorted(python_selected - java_selected)
                differences.append({
                    "project": name,
                    "mutationId": mut.mutation_id,
                    "mutatedClass": mut.mutated_class,
                    "mutatedMethod": mut.mutated_method,
                    "hasMethodHit": has_method_hit,
                    "javaOnlyCount": len(java_only),
                    "pythonOnlyCount": len(python_only),
                    "javaOnlyTests": java_only[:5],
                    "pythonOnlyTests": python_only[:5],
                })

        by_project[name] = {
            "mutations": len(resolved),
            "exactMatches": proj_exact,
            "mismatches": proj_mismatch,
            "casesWithMethodHits": proj_method_hits,
            "casesWithZeroMethodHits": proj_zero_hits,
            "casesWithPythonOnlyFallbackCandidates": proj_python_fallback,
        }

    report = {
        "schemaVersion": 1,
        "description": (
            "Dataset-wide comparison of Python evaluation_core.select_original() "
            "vs modeled Java TestSelector.selectTests() semantics for single-method "
            "changes. The Java model is faithful to the production code for the exact "
            "experimental input shape: changedClasses={C}, changedMethods={C#M}."
        ),
        "experimentalInputShape": {
            "changedClasses": "{C}",
            "changedMethods": "{C#M}",
            "classesWithMethodInfo": "{C}",
            "classLevelOnlyClasses": "{}  (empty)",
        },
        "mutationOccurrences": total_mutations,
        "uniqueSelectorCases": len(unique_cases),
        "exactMatches": exact_matches,
        "mismatches": mismatches,
        "casesWithMethodHits": cases_with_method_hits,
        "casesWithZeroMethodHits": cases_with_zero_method_hits,
        "casesWithPythonOnlyFallbackCandidates": cases_with_python_only_fallback,
        "byProject": by_project,
        "differences": differences,
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Verify Python/Java selector equivalence")
    parser.add_argument("--verify", action="store_true",
                        help="Verify against committed results/selector_equivalence.json")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: results/selector_equivalence.json)")
    args = parser.parse_args()

    report = run_verification(REPO_ROOT)

    output_path = args.output or (REPO_ROOT / "results" / "selector_equivalence.json")

    if args.verify:
        if not output_path.exists():
            print(f"VERIFY FAILED: {output_path} not found")
            sys.exit(1)
        committed = json.loads(output_path.read_text())
        fresh_json = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False)
        committed_json = json.dumps(committed, sort_keys=True, indent=2, ensure_ascii=False)
        if fresh_json != committed_json:
            print("VERIFY FAILED: selector_equivalence.json differs from fresh computation")
            sys.exit(1)
        print("VERIFY PASSED: selector equivalence results match committed artifact")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Written: {output_path}")
        print()
        print(f"Mutation occurrences: {report['mutationOccurrences']}")
        print(f"Unique selector cases: {report['uniqueSelectorCases']}")
        print(f"Exact matches: {report['exactMatches']}")
        print(f"Mismatches: {report['mismatches']}")
        print(f"Cases with method hits: {report['casesWithMethodHits']}")
        print(f"Cases with zero method hits: {report['casesWithZeroMethodHits']}")
        print(f"Cases with Python-only fallback candidates: {report['casesWithPythonOnlyFallbackCandidates']}")

        if report["mismatches"] == 0:
            print()
            print("EQUIVALENCE CONFIRMED: Python select_original() == Java TestSelector")
            print("for all evaluated single-method mutation cases.")
        else:
            print()
            print(f"EQUIVALENCE FAILED: {report['mismatches']} mismatches found")
            for d in report["differences"][:5]:
                print(f"  {d['project']}: {d['mutatedClass'].split('.')[-1]}#{d['mutatedMethod']}")
                print(f"    Java-only: {d['javaOnlyCount']}, Python-only: {d['pythonOnlyCount']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
