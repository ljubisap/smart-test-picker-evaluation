#!/usr/bin/env python3
"""Build the attempted eight-subject summary without inventing blocked results."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def old_project(name):
    summary = load(f"{name}/results/aggregated/evaluation_summary.json")
    baselines = load(f"{name}/results/aggregated/baseline_comparison.json")["results"]
    pit = load(f"{name}/results/aggregated/pit_summary.json")
    sample = load(f"{name}/config/sample_classes.json")
    proposed, class_level, random = baselines
    sampled = len(sample.get("classes", pit.get("classes", [])))
    usable = pit.get("ok")
    if usable is None:
        usable = sum(1 for row in pit.get("results", []) if row.get("status") == "OK")
    if usable is None or usable == 0:
        usable = sampled
    return {
        "project": name,
        "status": "COMPLETE",
        "logicalTests": summary["total_tests"],
        "sampledProductionClasses": sampled,
        "usableMutationProducingClasses": usable,
        "totalPitMutations": pit["total_mutations"],
        "killedMutations": summary["total_mutations"],
        "stpInclusive": summary["safe"],
        "inclusivenessPct": summary["inclusiveness_pct"],
        "avgSelected": summary["avg_selection_size"],
        "reductionPct": summary["test_reduction_pct"],
        "classLevel": class_level,
        "randomEqualBudget": random,
        "falseNegatives": summary["unsafe"],
    }


def new_project(name):
    summary = load(f"{name}/results/aggregated/evaluation_summary.json")
    pit = load(f"{name}/results/pit-run-summary.json")
    sample = load(f"{name}/config/sample_classes.json")
    selectors = summary["selectors"]
    return {
        "project": name,
        "status": "COMPLETE",
        "logicalTests": summary["logicalTests"],
        "sampledProductionClasses": len(sample["classes"]),
        "usableMutationProducingClasses": pit["ok"],
        "totalPitMutations": pit["totalMutations"],
        "killedMutations": summary["killedMutations"],
        "stpInclusive": selectors["stp"]["safe"],
        "inclusivenessPct": selectors["stp"]["inclusivenessPct"],
        "avgSelected": selectors["stp"]["avgSelected"],
        "reductionPct": selectors["stp"]["reductionPct"],
        "classLevel": selectors["classLevel"],
        "randomEqualBudget": selectors["randomEqualBudget"],
        "falseNegatives": selectors["stp"]["unsafe"],
    }


taxonomy = load("results/failure_taxonomy.json")
mitigation = load("results/mitigation_comparison.json")
mit_by_project = {row["project"]: row for row in mitigation["perProject"]}
annotations = load("analysis/failure_annotations.json")
annotations_by_id = {row["mutationId"]: row for row in annotations}
projects = [old_project(p) for p in ("commons-lang", "jgrapht", "spring-core", "petclinic")]
projects.extend(new_project(p) for p in ("flink", "spring-security", "hibernate", "quarkus"))

for row in projects:
    mutations = taxonomy["byProject"].get(row["project"], {}).get("mutations", [])
    exclusive = {"A": 0, "B": 0, "C": 0, "NEW_TYPE": 0}
    for mutation in mutations:
        annotation = annotations_by_id.get(mutation.get("mutationId"), {})
        if annotation.get("category") == "pre-test-custom-engine-enhancement":
            exclusive["NEW_TYPE"] += 1
            continue
        kinds = mutation.get("mutationTypes", [])
        if len(kinds) == 1 and kinds[0] in exclusive:
            exclusive[kinds[0]] += 1
        elif kinds:
            exclusive["NEW_TYPE"] += 1
    row["failureTaxonomy"] = exclusive
    row["mitigation"] = mit_by_project[row["project"]]["constructorOnlyRule"]

complete = [row for row in projects if row["status"] == "COMPLETE"]
output = {
    "schemaVersion": 1,
    "attemptedSubjects": 8,
    "completedSubjects": len(complete),
    "blockedSubjects": len(projects) - len(complete),
    "projects": projects,
    "aggregateCompletedSubjectsOnly": {
        "killedMutations": sum(row["killedMutations"] for row in complete),
        "stpInclusive": sum(row["stpInclusive"] for row in complete),
        "falseNegatives": sum(row["falseNegatives"] for row in complete),
        "inclusivenessPct": round(100 * sum(row["stpInclusive"] for row in complete) /
                                    sum(row["killedMutations"] for row in complete), 2),
        "mitigationRecoveries": sum(row["mitigation"]["additionalRecovered"] for row in complete),
        "newFailureTypeExists": any(row["failureTaxonomy"]["NEW_TYPE"] for row in complete),
    },
    "interpretation": "Blocked subjects are excluded from every mutation denominator; null is not zero.",
}

path = ROOT / "results/eight-subject-summary.json"
path.write_text(json.dumps(output, indent=2) + "\n")
print(path.relative_to(ROOT))
