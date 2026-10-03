#!/usr/bin/env python3
"""Verify Joda-Time evaluator selection against the historical Python edge-only model.

This does not execute Java and does not cover the production NO_COVERAGE branch.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
    select_original,
)
from analysis.verify_selector_equivalence import java_semantic_select  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-map", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    args = parser.parse_args()

    coverage = load_coverage_map(args.coverage_map)
    mappings = coverage["testMappings"]
    pit_files = tuple(sorted(args.results_dir.glob("per-class/*/mutations.xml")))
    raw = load_pit_mutations("joda-time", args.results_dir.parent, pit_files)
    mutations = resolve_killing_tests(raw, mappings, build_base_to_keys(mappings))

    cases = {}
    mismatches = []
    for mutation in mutations:
        key = (mutation.mutated_class, mutation.mutated_method)
        if key not in cases:
            actual = select_original(mappings, *key)
            expected = java_semantic_select(mappings, *key)
            cases[key] = actual == expected
            if actual != expected:
                mismatches.append({
                    "class": key[0],
                    "method": key[1],
                    "evaluatorOnly": sorted(actual - expected),
                    "edgeOnlyModelOnly": sorted(expected - actual),
                })

    report = {
        "project": "Joda-Time",
        "mutationOccurrences": len(mutations),
        "uniqueSelectorCases": len(cases),
        "exactMatches": sum(cases.values()),
        "mismatches": len(mismatches),
        "differences": mismatches,
    }
    output = args.results_dir / "aggregated" / "selector_equivalence.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
