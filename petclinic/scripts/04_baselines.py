#!/usr/bin/env python3
"""
04_baselines.py — Compare plugin selection against baseline selectors.

Baselines:
  1. Class-level only — select all tests touching the mutated class (no method info)
  2. Random(k_M) — per-mutation random selection where k_M equals the number
     of tests the proposed selector would pick for that mutation

Usage:
  python3 04_baselines.py --project-dir /path/to/spring-petclinic
"""

import argparse
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def normalize_pit_test_name(pit_test_id):
    """Normalize PIT's JUnit Platform unique ID to coverage map format."""
    class_match = re.search(r'\[class:([^\]]+)\]', pit_test_id)
    method_match = re.search(r'\[method:([^\]]+)\]', pit_test_id)
    if not method_match:
        method_match = re.search(r'\[test-template:([^\]]+)\]', pit_test_id)
    if not class_match or not method_match:
        return None

    fqn = class_match.group(1)
    method = re.sub(r'\(.*\)', '', method_match.group(1))
    simple_class = fqn.split('.')[-1]

    nested_matches = re.findall(r'\[nested-class:([^\]]+)\]', pit_test_id)
    if nested_matches:
        simple_class = nested_matches[-1]

    return f"{simple_class}#{method}"


def coverage_selector(test_mappings, changed_class, changed_method):
    """Plugin's dual-granularity selection."""
    selected = set()
    method_fqn = f"{changed_class}#{changed_method}"

    for test_name, coverage in test_mappings.items():
        methods = coverage.get("methods", [])
        classes = coverage.get("classes", [])

        if method_fqn in methods:
            selected.add(test_name)
            continue

        if changed_class in classes:
            has_method_info = any(m.startswith(changed_class + "#") for m in methods)
            if not has_method_info:
                selected.add(test_name)

    return selected


def class_level_only_selector(test_mappings, changed_class, changed_method):
    """Select ALL tests touching the mutated class (ignoring method info)."""
    selected = set()
    for test_name, coverage in test_mappings.items():
        classes = coverage.get("classes", [])
        if changed_class in classes:
            selected.add(test_name)
    return selected


def load_mutations(mutations_xml_path):
    """Load all KILLED mutations from mutations.xml."""
    mutations = []
    tree = ET.parse(mutations_xml_path)
    for mut in tree.getroot().findall("mutation"):
        if mut.get("status") != "KILLED":
            continue
        killing_raw = mut.findtext("killingTests") or ""
        killing_tests = set()
        for pit_id in (t.strip() for t in killing_raw.split("|") if t.strip()):
            n = normalize_pit_test_name(pit_id)
            if n:
                killing_tests.add(n)
        mutations.append({
            "mutatedClass": mut.findtext("mutatedClass"),
            "mutatedMethod": mut.findtext("mutatedMethod"),
            "lineNumber": mut.findtext("lineNumber"),
            "mutator": mut.findtext("mutator"),
            "killingTests": killing_tests,
        })
    return mutations


def evaluate_selector(selector_fn, test_mappings, mutations, total_tests):
    """Evaluate a selector function against all mutations."""
    safe = 0
    selection_sizes = []

    for mut in mutations:
        t_sel = selector_fn(test_mappings, mut["mutatedClass"], mut["mutatedMethod"])
        selection_sizes.append(len(t_sel))
        if t_sel & mut["killingTests"]:
            safe += 1

    total = len(mutations)
    avg_sel = sum(selection_sizes) / len(selection_sizes)
    return {
        "inclusiveness_pct": round(safe / total * 100, 2),
        "selection_rate_pct": round(avg_sel / total_tests * 100, 2),
        "avg_selection_size": round(avg_sel, 1),
        "safe": safe,
        "unsafe": total - safe,
        "total": total,
    }


def evaluate_random_per_mutation(mutations, test_mappings, coverage_selector_fn, total_tests, seed=42):
    """
    Evaluate random selector with per-mutation budget k_M.

    For each mutation M, k_M = |coverage_selector(M)|. The random selector
    picks k_M tests uniformly at random, ensuring the same selection budget
    as the proposed approach for each individual mutation.
    """
    all_tests = list(test_mappings.keys())
    safe = 0
    selection_sizes = []

    for i, mut in enumerate(mutations):
        k_m = len(coverage_selector_fn(test_mappings, mut["mutatedClass"], mut["mutatedMethod"]))
        rng = random.Random(seed + i)
        t_sel = set(rng.sample(all_tests, min(k_m, total_tests)))
        selection_sizes.append(len(t_sel))
        if t_sel & mut["killingTests"]:
            safe += 1

    total = len(mutations)
    avg_sel = sum(selection_sizes) / len(selection_sizes)
    return {
        "inclusiveness_pct": round(safe / total * 100, 2),
        "selection_rate_pct": round(avg_sel / total_tests * 100, 2),
        "avg_selection_size": round(avg_sel, 1),
        "safe": safe,
        "unsafe": total - safe,
        "total": total,
    }


def main():
    parser = argparse.ArgumentParser(description="Baseline comparison for PetClinic")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--coverage-map", type=Path, default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = args.results_dir or (script_dir.parent / "results")
    coverage_map_path = args.coverage_map or (results_dir / "test-coverage-map.json")

    if not coverage_map_path.exists():
        print(f"ERROR: Coverage map not found: {coverage_map_path}")
        sys.exit(1)

    with open(coverage_map_path) as f:
        coverage_data = json.load(f)
    test_mappings = coverage_data["testMappings"]
    total_tests = len(test_mappings)

    mutations_xml = results_dir / "mutations.xml"
    if not mutations_xml.exists():
        print(f"ERROR: mutations.xml not found: {mutations_xml}")
        sys.exit(1)

    mutations = load_mutations(mutations_xml)
    if not mutations:
        print("ERROR: No KILLED mutations found")
        sys.exit(1)

    # Run all selectors
    plugin_results = evaluate_selector(coverage_selector, test_mappings, mutations, total_tests)
    class_results = evaluate_selector(class_level_only_selector, test_mappings, mutations, total_tests)
    random_results = evaluate_random_per_mutation(mutations, test_mappings, coverage_selector, total_tests, seed=42)

    # Print
    print(f"{'='*70}")
    print(f"BASELINE COMPARISON — Spring PetClinic")
    print(f"{'='*70}")
    print(f"Mutations: {len(mutations)} KILLED | Tests: {total_tests}")
    print(f"\n{'Selector':<25} {'Safety%':>8} {'SelRate%':>9} {'AvgSel':>7}")
    print(f"{'-'*50}")
    for name, r in [("Coverage (plugin)", plugin_results),
                    ("Class-level only", class_results),
                    ("Random(k=per-mut)", random_results)]:
        print(f"{name:<25} {r['inclusiveness_pct']:>7.2f}% {r['selection_rate_pct']:>8.2f}% {r['avg_selection_size']:>6.1f}")

    # Write output
    agg_dir = results_dir / "aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)

    comparison = {
        "project": "Spring PetClinic",
        "total_tests": total_tests,
        "total_mutations": len(mutations),
        "seed": 42,
        "selectors": {
            "coverage_plugin": plugin_results,
            "class_level_only": class_results,
            "random_per_mutation": random_results,
        }
    }
    out_path = agg_dir / "baseline_comparison.json"
    with open(out_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"\nOutput: {out_path}")


if __name__ == "__main__":
    main()
