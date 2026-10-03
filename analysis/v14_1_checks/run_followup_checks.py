#!/usr/bin/env python3
"""Read-only T10--T12 checks over the frozen evaluation artifacts."""

from __future__ import annotations

import json
import random
import statistics
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    build_class_to_keys,
    discover_pit_files,
    exclude_non_leaf_oracle_records,
    load_coverage_map,
    load_pit_mutations,
    normalize_pit_test_name,
    resolve_killing_tests,
    select_original,
)


def load_project(project):
    coverage_path = ROOT / project["coverageMap"]
    coverage = load_coverage_map(coverage_path)
    mappings = coverage["testMappings"]
    pit_files = discover_pit_files(ROOT, project["pitFiles"])
    raw = load_pit_mutations(project["name"], ROOT, pit_files)
    resolved = resolve_killing_tests(
        raw,
        mappings,
        build_base_to_keys(mappings),
        build_class_to_keys(mappings, coverage.get("executionIdentities", {})),
    )
    resolved = exclude_non_leaf_oracle_records(resolved, ROOT, project["name"])
    return coverage_path, pit_files, coverage, mappings, raw, resolved


def resolution_audit(project, mappings, raw):
    base_to_keys = build_base_to_keys(mappings)
    unresolved_occurrences = []
    all_unresolved_records = []
    for mutation in raw:
        statuses = []
        for raw_id in mutation.raw_killing_test_ids:
            normalized = normalize_pit_test_name(raw_id)
            if normalized in mappings:
                statuses.append(True)
            elif normalized in base_to_keys:
                statuses.append(True)
            else:
                statuses.append(False)
                unresolved_occurrences.append(
                    {
                        "mutationId": mutation.mutation_id,
                        "rawPitId": raw_id,
                        "normalizedId": normalized,
                    }
                )
        if statuses and not any(statuses):
            all_unresolved_records.append(mutation.mutation_id)
    return {
        "project": project["name"],
        "killedRecords": len(raw),
        "rawKillingIdentityOccurrences": sum(len(m.raw_killing_test_ids) for m in raw),
        "unresolvedOccurrenceCount": len(unresolved_occurrences),
        "unresolvedUniqueRawIdentityCount": len({x["rawPitId"] for x in unresolved_occurrences}),
        "recordsWithAllKillersUnresolved": len(all_unresolved_records),
        "unresolvedOccurrences": unresolved_occurrences,
        "allUnresolvedMutationIds": all_unresolved_records,
    }


def no_coverage_killer_audit(project, mappings, resolved):
    empty = sorted(
        key for key, value in mappings.items()
        if not value.get("classes") and not value.get("methods")
    )
    rows = []
    for key in empty:
        mutations = []
        for mutation in resolved:
            killing = {coverage_key for test in mutation.killing_tests for coverage_key in test.coverage_keys}
            if key in killing:
                mutations.append(mutation.mutation_id)
        rows.append(
            {
                "coverageKey": key,
                "appearsAsKiller": bool(mutations),
                "eligibleMutationOccurrenceCount": len(mutations),
                "mutationIds": mutations,
            }
        )
    return {
        "project": project["name"],
        "noCoverageTestCount": len(empty),
        "appearingAsKillerCount": sum(row["appearsAsKiller"] for row in rows),
        "tests": rows,
    }


def exact_random_metrics(resolved, mappings, trials=1000, seed=42):
    universe = sorted(mappings)
    universe_set = set(universe)
    rows = []
    analytical_probabilities = []
    for mutation in resolved:
        budget = len(select_original(mappings, mutation.mutated_class, mutation.mutated_method))
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys} & universe_set
        rows.append((budget, killing))
        probability = 0.0
        if budget and killing:
            k = min(budget, len(universe))
            probability = (
                1.0
                if len(universe) - len(killing) < k
                else 1 - comb(len(universe) - len(killing), k) / comb(len(universe), k)
            )
        analytical_probabilities.append(probability)

    trial_percentages = []
    total_hits = 0
    for trial in range(trials):
        safe = 0
        for index, (budget, killing) in enumerate(rows):
            rng = random.Random(seed + trial * max(1, len(rows)) + index)
            chosen = set(rng.sample(universe, min(budget, len(universe))))
            safe += bool(chosen & killing)
        total_hits += safe
        trial_percentages.append(100 * safe / len(rows) if rows else 0.0)

    monte_carlo = statistics.mean(trial_percentages) if rows else 0.0
    analytical = 100 * sum(analytical_probabilities) / len(rows) if rows else 0.0
    return {
        "trials": trials,
        "seed": seed,
        "records": len(rows),
        "successfulTrialRecordPairs": total_hits,
        "monteCarloInclusivenessPctFullPrecision": monte_carlo,
        "monteCarloInclusivenessPct2dp": round(monte_carlo, 2),
        "monteCarloStdPctFullPrecision": statistics.pstdev(trial_percentages) if rows else 0.0,
        "analyticalInclusivenessPctFullPrecision": analytical,
        "analyticalInclusivenessPct2dp": round(analytical, 2),
        "formula": "mean_m [1 - C(N-r_m,k_m)/C(N,k_m)], with probability 1 when N-r_m < k_m",
    }


def main():
    projects = json.loads((ROOT / "analysis/projects.json").read_text())["projects"]
    loaded = {}
    for project in projects:
        loaded[project["name"]] = load_project(project)

    original_names = {"commons-lang", "jgrapht", "spring-core", "petclinic"}
    extension_names = {"flink", "spring-security", "hibernate", "quarkus"}
    zero = {
        "sources": {
            "projectManifest": "analysis/projects.json",
            "resolutionCode": "analysis/evaluation_core.py:327-390",
            "oracleExclusionCode": "analysis/evaluation_core.py:90-123",
        },
        "originalSubjects": [],
        "extensionSubjects": [],
    }
    for project in projects:
        _, _, _, mappings, raw, resolved = loaded[project["name"]]
        if project["name"] in original_names:
            zero["originalSubjects"].append(resolution_audit(project, mappings, raw))
        if project["name"] in extension_names:
            zero["extensionSubjects"].append(no_coverage_killer_audit(project, mappings, resolved))
    (OUT / "zero_coverage_handling.json").write_text(json.dumps(zero, indent=2) + "\n")

    summary = json.loads((ROOT / "results/eight-subject-summary.json").read_text())
    reconciliation = {"sources": {}, "projects": {}}
    for name in ("flink", "hibernate"):
        sample_path = ROOT / name / "config/sample_classes.json"
        sample = json.loads(sample_path.read_text())
        frozen = [row["fqn"] for row in sample["classes"]]
        resolved = loaded[name][-1]
        clusters = sorted({mutation.mutated_class for mutation in resolved})
        subject_summary = next(row for row in summary["projects"] if row["project"] == name)
        reconciliation["sources"][name] = {
            "frozenSample": sample_path.relative_to(ROOT).as_posix(),
            "eligiblePIT": [p.relative_to(ROOT).as_posix() for p in loaded[name][1]],
            "tableSummary": "results/eight-subject-summary.json",
        }
        reconciliation["projects"][name] = {
            "tableSampledProductionClasses": subject_summary["sampledProductionClasses"],
            "tableUsableMutationProducingClasses": subject_summary["usableMutationProducingClasses"],
            "frozenClassCount": len(frozen),
            "frozenClasses": frozen,
            "eligibleClusterCount": len(clusters),
            "eligibleClusters": clusters,
            "frozenButNotEligibleCluster": sorted(set(frozen) - set(clusters)),
            "eligibleClusterNotFrozen": sorted(set(clusters) - set(frozen)),
        }
    (OUT / "contributing_class_reconciliation.json").write_text(
        json.dumps(reconciliation, indent=2) + "\n"
    )

    random_output = {
        "implementationSource": "analysis/evaluate_subject.py:53-84",
        "inputManifest": "analysis/projects.json",
        "projects": {},
    }
    for project in projects:
        mappings, resolved = loaded[project["name"]][3], loaded[project["name"]][-1]
        random_output["projects"][project["name"]] = {
            "coverageMap": project["coverageMap"],
            "pitFiles": project["pitFiles"],
            **exact_random_metrics(resolved, mappings),
        }
    (OUT / "random_baseline_full_precision.json").write_text(
        json.dumps(random_output, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
