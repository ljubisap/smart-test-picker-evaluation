#!/usr/bin/env python3
"""
04_baselines.py  --  Compare proposed selector against baseline selectors.

Evaluates three strategies against PIT mutation ground truth:
  1. Coverage (proposed): dual-granularity method+class selection
  2. Class-level only: all tests covering changed class (no method matching)
  3. Random(k_M): per-mutation random selection where k_M equals the number
     of tests the proposed selector would pick for that mutation

Metrics per selector: Safety (inclusiveness), Selection Rate, Avg Selection Size.

Usage:
  python3 04_baselines.py --project-dir /path/to/commons-lang
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
    """
    Normalize PIT's JUnit Platform unique ID to coverage map format.
    See 03_evaluate.py for full format documentation.
    """
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


def load_mutations(results_dir):
    """Load all KILLED mutations from per-class XML files."""
    mutations = []
    per_class = results_dir / "per-class"
    for class_dir in sorted(per_class.iterdir()):
        if not class_dir.is_dir():
            continue
        xml_path = class_dir / "mutations.xml"
        if not xml_path.exists() or xml_path.stat().st_size == 0:
            continue
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue
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
                "killingTests": killing_tests,
            })
    return mutations


# ============ SELECTORS ============

def coverage_selector(test_mappings, changed_class, changed_method):
    """Proposed dual-granularity: method-level first, class-level fallback."""
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
    """Baseline: select ALL tests covering the changed class (ignore method info)."""
    selected = set()
    for test_name, coverage in test_mappings.items():
        classes = coverage.get("classes", [])
        if changed_class in classes:
            selected.add(test_name)
    return selected


# ============ EVALUATION ============

def evaluate_selector(name, selector_fn, mutations, test_mappings):
    """Evaluate a selector against all mutations. Returns metrics dict."""
    safe = 0
    unsafe = 0
    selection_sizes = []

    for mut in mutations:
        t_selected = selector_fn(test_mappings, mut["mutatedClass"], mut["mutatedMethod"])
        intersection = t_selected & mut["killingTests"]
        if len(intersection) > 0:
            safe += 1
        else:
            unsafe += 1
        selection_sizes.append(len(t_selected))

    total = safe + unsafe
    total_tests = len(test_mappings)
    avg_sel = sum(selection_sizes) / len(selection_sizes) if selection_sizes else 0

    return {
        "name": name,
        "safety_pct": round(safe / total * 100, 2) if total > 0 else 0,
        "safe": safe,
        "unsafe": unsafe,
        "total": total,
        "avg_selected": round(avg_sel, 1),
        "selection_rate_pct": round(avg_sel / total_tests * 100, 2),
        "test_reduction_pct": round((1 - avg_sel / total_tests) * 100, 2),
    }


def evaluate_random_per_mutation(mutations, test_mappings, coverage_selector_fn, seed=42, num_trials=1000):
    """
    Evaluate random selector with per-mutation budget k_M over multiple trials.

    For each mutation M, k_M = |coverage_selector(M)|. The random selector
    picks k_M tests uniformly at random. Repeated num_trials times to produce
    mean and standard deviation.

    Also computes the analytical expected safety:
      P(hit for mutation M) = 1 - C(N-d, k) / C(N, k)
    where N = total tests, d = |killing tests|, k = selection budget.
    """
    from math import comb

    all_tests = list(test_mappings.keys())
    total_tests = len(all_tests)

    # Compute per-mutation budgets and killing test counts
    per_mutation_info = []
    for mut in mutations:
        k_m = len(coverage_selector_fn(test_mappings, mut["mutatedClass"], mut["mutatedMethod"]))
        d_m = len(mut["killingTests"] & set(all_tests))  # killing tests that are in the map
        per_mutation_info.append((k_m, d_m, mut["killingTests"]))

    # Analytical expected safety
    analytical_safe = 0
    for k_m, d_m, _ in per_mutation_info:
        if d_m == 0 or k_m == 0:
            continue
        # P(miss) = C(N-d, k) / C(N, k); P(hit) = 1 - P(miss)
        k = min(k_m, total_tests)
        if total_tests - d_m < k:
            p_hit = 1.0  # must hit
        else:
            p_miss = comb(total_tests - d_m, k) / comb(total_tests, k)
            p_hit = 1.0 - p_miss
        analytical_safe += p_hit
    analytical_safety_pct = round(analytical_safe / len(mutations) * 100, 2) if mutations else 0

    # Monte Carlo: num_trials repetitions
    trial_safeties = []
    for trial in range(num_trials):
        safe = 0
        for i, (k_m, d_m, killing_tests) in enumerate(per_mutation_info):
            rng = random.Random(seed + trial * len(mutations) + i)
            t_selected = set(rng.sample(all_tests, min(k_m, total_tests)))
            if t_selected & killing_tests:
                safe += 1
        trial_safeties.append(safe / len(mutations) * 100)

    mean_safety = sum(trial_safeties) / len(trial_safeties)
    variance = sum((x - mean_safety) ** 2 for x in trial_safeties) / len(trial_safeties)
    std_safety = variance ** 0.5

    avg_sel = sum(k for k, _, _ in per_mutation_info) / len(per_mutation_info) if per_mutation_info else 0

    return {
        "name": "Random (k=per-mutation)",
        "safety_pct": round(mean_safety, 2),
        "safety_std": round(std_safety, 2),
        "safety_analytical_pct": analytical_safety_pct,
        "num_trials": num_trials,
        "safe": round(mean_safety * len(mutations) / 100),
        "unsafe": len(mutations) - round(mean_safety * len(mutations) / 100),
        "total": len(mutations),
        "avg_selected": round(avg_sel, 1),
        "selection_rate_pct": round(avg_sel / total_tests * 100, 2),
        "test_reduction_pct": round((1 - avg_sel / total_tests) * 100, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Baseline comparison vs PIT ground truth")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to commons-lang checkout")
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--coverage-map", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = args.results_dir or (script_dir.parent / "results")
    coverage_map_path = args.coverage_map or (script_dir.parent / "results" / "test-coverage-map.json")

    if not coverage_map_path.exists():
        print(f"ERROR: Coverage map not found: {coverage_map_path}")
        sys.exit(1)

    with open(coverage_map_path) as f:
        test_mappings = json.load(f)["testMappings"]
    total_tests = len(test_mappings)

    mutations = load_mutations(results_dir)
    if not mutations:
        print("ERROR: No mutations found in results/per-class/")
        sys.exit(1)

    # Build reverse lookup: base name (without hash suffix) -> set of full map keys
    base_to_keys = defaultdict(set)
    for key in test_mappings:
        if '_' in key and len(key.rsplit('_', 1)[-1]) == 7:
            last = key.rsplit('_', 1)[-1]
            if all(c in '0123456789abcdef' for c in last):
                base_to_keys[key.rsplit('_', 1)[0]].add(key)
                continue
        base_to_keys[key].add(key)

    # Resolve killing test names to coverage map keys
    for mut in mutations:
        resolved = set()
        for kt in mut["killingTests"]:
            if kt in test_mappings:
                resolved.add(kt)
            elif kt in base_to_keys:
                resolved.update(base_to_keys[kt])
        mut["killingTests"] = resolved

    print(f"Data: {total_tests} tests, {len(mutations)} KILLED mutations\n")

    # 1. Proposed coverage-based selector
    res_coverage = evaluate_selector(
        "Coverage (proposed)", coverage_selector, mutations, test_mappings
    )

    # 2. Class-level only selector
    res_class = evaluate_selector(
        "Class-level only", class_level_only_selector, mutations, test_mappings
    )

    # 3. Random selector (per-mutation k_M = coverage selection size for that mutation)
    res_random = evaluate_random_per_mutation(
        mutations, test_mappings, coverage_selector, seed=args.seed
    )

    # Print comparison table
    results = [res_coverage, res_class, res_random]
    print(f"{'='*78}")
    print(f"BASELINE COMPARISON  --  Smart Test Picker vs Baselines")
    print(f"{'='*78}")
    print(f"{'Selector':<25} {'Safety':>8} {'Sel. rate':>10} {'Reduction':>10} {'Avg sel.':>9}")
    print(f"{'-'*78}")
    for r in results:
        print(f"{r['name']:<25} {r['safety_pct']:>7.2f}% {r['selection_rate_pct']:>9.2f}%"
              f" {r['test_reduction_pct']:>9.2f}% {r['avg_selected']:>9.1f}")
    print(f"{'='*78}")
    print(f"\nTotal tests: {total_tests} | Mutations: {len(mutations)} | Seed: {args.seed}")

    # Write output
    agg_dir = results_dir / "aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_tests": total_tests,
        "total_mutations": len(mutations),
        "seed": args.seed,
        "results": results,
    }
    out_path = agg_dir / "baseline_comparison.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nOutput: {out_path}")


if __name__ == "__main__":
    main()
