#!/usr/bin/env python3
"""Evaluate one frozen subject with the repository's shared RTS semantics."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import sys
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    build_class_to_keys,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
    select_class_level,
    select_constructor_only_rule,
    select_original,
)


def selector_metrics(name, selector, mutations, mappings):
    sizes, safe = [], 0
    for mutation in mutations:
        selected = selector(mappings, mutation.mutated_class, mutation.mutated_method)
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
        sizes.append(len(selected))
        safe += bool(selected & killing)
    total = len(mutations)
    average = statistics.mean(sizes) if sizes else 0.0
    population = len(mappings)
    return {
        "name": name,
        "safe": safe,
        "unsafe": total - safe,
        "total": total,
        "inclusivenessPct": round(100 * safe / total, 2) if total else 0,
        "avgSelected": round(average, 2),
        "selectionRatePct": round(100 * average / population, 2) if population else 0,
        "reductionPct": round(100 * (1 - average / population), 2) if population else 0,
    }


def random_metrics(mutations, mappings, trials=1000, seed=42):
    universe = sorted(mappings)
    universe_set = set(universe)
    rows = []
    expected = 0.0
    for mutation in mutations:
        budget = len(select_original(mappings, mutation.mutated_class, mutation.mutated_method))
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys} & universe_set
        rows.append((budget, killing))
        if budget and killing:
            k = min(budget, len(universe))
            expected += 1.0 if len(universe) - len(killing) < k else 1 - comb(len(universe)-len(killing), k) / comb(len(universe), k)
    percentages = []
    for trial in range(trials):
        safe = 0
        for index, (budget, killing) in enumerate(rows):
            rng = random.Random(seed + trial * max(1, len(rows)) + index)
            chosen = set(rng.sample(universe, min(budget, len(universe))))
            safe += bool(chosen & killing)
        percentages.append(100 * safe / len(rows) if rows else 0)
    average_budget = statistics.mean(x[0] for x in rows) if rows else 0
    return {
        "name": "Random equal-budget",
        "trials": trials,
        "seed": seed,
        "inclusivenessPct": round(statistics.mean(percentages), 2),
        "inclusivenessStdPct": round(statistics.pstdev(percentages), 2),
        "analyticalInclusivenessPct": round(100 * expected / len(rows), 2) if rows else 0,
        "avgSelected": round(average_budget, 2),
        "selectionRatePct": round(100 * average_budget / len(universe), 2) if universe else 0,
        "reductionPct": round(100 * (1-average_budget/len(universe)), 2) if universe else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--coverage-map", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    args = parser.parse_args()

    coverage_map = load_coverage_map(args.coverage_map)
    mappings = coverage_map["testMappings"]
    pit_files = tuple(sorted(args.results_dir.glob("per-class/*/mutations.xml")))
    if not pit_files:
        raise SystemExit("No PIT mutations.xml files found")
    raw = load_pit_mutations(args.subject, args.results_dir.parent, pit_files)
    mutations = resolve_killing_tests(
        raw,
        mappings,
        build_base_to_keys(mappings),
        build_class_to_keys(mappings, coverage_map.get("executionIdentities", {})),
    )
    rows = []
    for mutation in mutations:
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
        original = select_original(mappings, mutation.mutated_class, mutation.mutated_method)
        class_only = select_class_level(mappings, mutation.mutated_class, mutation.mutated_method)
        mitigated = select_constructor_only_rule(mappings, mutation.mutated_class, mutation.mutated_method)
        rows.append({
            "mutationId": mutation.mutation_id,
            "mutatedClass": mutation.mutated_class,
            "mutatedMethod": mutation.mutated_method,
            "line": mutation.line_number,
            "mutator": mutation.mutator,
            "rawKillingTests": [test.raw_pit_id for test in mutation.killing_tests],
            "resolvedKillingTests": sorted(killing),
            "selectedTests": sorted(original),
            "selectedCount": len(original),
            "safe": bool(original & killing),
            "mitigatedSelectedCount": len(mitigated),
            "mitigatedSafe": bool(mitigated & killing),
            "classSelectedCount": len(class_only),
            "classSafe": bool(class_only & killing),
        })

    aggregate = args.results_dir / "aggregated"
    aggregate.mkdir(parents=True, exist_ok=True)
    (aggregate / "mutation_results.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (aggregate / "evaluation_results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["mutationId", "mutatedClass", "mutatedMethod", "line", "mutator", "selectedCount", "safe", "mitigatedSelectedCount", "mitigatedSafe", "classSelectedCount", "classSafe"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    summary = {
        "project": args.subject,
        "logicalTests": len(mappings),
        "killedMutations": len(mutations),
        "selectors": {
            "stp": selector_metrics("STP", select_original, mutations, mappings),
            "constructorOnlyMitigation": selector_metrics("Constructor-only mitigation", select_constructor_only_rule, mutations, mappings),
            "classLevel": selector_metrics("Class-level only", select_class_level, mutations, mappings),
            "randomEqualBudget": random_metrics(mutations, mappings),
        },
    }
    (aggregate / "evaluation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
