#!/usr/bin/env python3
"""
04_baselines.py -- Compare proposed selector against baseline selectors.

Evaluates three strategies against PIT mutation ground truth:
  1. Coverage (proposed): dual-granularity method+class selection
  2. Class-level baseline: all tests covering changed class (no method matching)
  3. Random(k_M): per-mutation random selection with 1000 Monte Carlo trials

Uses shared evaluation logic from analysis/evaluation_core.py.

Usage:
  python3 04_baselines.py --project-dir /path/to/spring-core
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, discover_pit_files, load_pit_mutations,
    build_base_to_keys, resolve_killing_tests,
    select_original, select_class_level,
)


def evaluate_selector(name, selector_fn, mutations, test_mappings):
    """Evaluate a selector against all mutations. Returns metrics dict."""
    safe = 0
    unsafe = 0
    selection_sizes = []

    for mut in mutations:
        t_selected = selector_fn(test_mappings, mut.mutated_class, mut.mutated_method)
        killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
        if t_selected & killing_keys:
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


def evaluate_random_per_mutation(mutations, test_mappings, seed=42, num_trials=1000):
    """
    Evaluate random selector with per-mutation budget k_M over multiple trials.

    Also computes the analytical expected safety:
      P(hit for mutation M) = 1 - C(N-d, k) / C(N, k)
    """
    all_tests = sorted(test_mappings.keys())
    total_tests = len(all_tests)

    # Compute per-mutation budgets and killing test counts
    per_mutation_info = []
    for mut in mutations:
        k_m = len(select_original(test_mappings, mut.mutated_class, mut.mutated_method))
        killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
        d_m = len(killing_keys & set(all_tests))
        per_mutation_info.append((k_m, d_m, killing_keys))

    # Analytical expected safety
    analytical_safe = 0
    for k_m, d_m, _ in per_mutation_info:
        if d_m == 0 or k_m == 0:
            continue
        k = min(k_m, total_tests)
        if total_tests - d_m < k:
            p_hit = 1.0
        else:
            p_miss = comb(total_tests - d_m, k) / comb(total_tests, k)
            p_hit = 1.0 - p_miss
        analytical_safe += p_hit
    analytical_safety_pct = round(analytical_safe / len(mutations) * 100, 2) if mutations else 0

    # Monte Carlo: num_trials repetitions
    trial_safeties = []
    for trial in range(num_trials):
        safe = 0
        for i, (k_m, d_m, killing_keys) in enumerate(per_mutation_info):
            rng = random.Random(seed + trial * len(mutations) + i)
            t_selected = set(rng.sample(all_tests, min(k_m, total_tests)))
            if t_selected & killing_keys:
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
                        help="Path to spring-core checkout")
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--coverage-map", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = args.results_dir or (script_dir.parent / "results")
    coverage_map_path = args.coverage_map or (script_dir.parent / "results" / "test-coverage-map.json")

    if not coverage_map_path.exists():
        print(f"ERROR: Coverage map not found: {coverage_map_path}")
        sys.exit(1)

    coverage_data = load_coverage_map(coverage_map_path)
    test_mappings = coverage_data["testMappings"]
    total_tests = len(test_mappings)

    base_to_keys = build_base_to_keys(test_mappings)
    pit_files = discover_pit_files(REPO_ROOT, ["spring-core/results/per-class/*/mutations.xml"])
    raw_mutations = load_pit_mutations("spring-core", REPO_ROOT, pit_files)

    if not raw_mutations:
        print("ERROR: No mutations found in results/per-class/")
        sys.exit(1)

    mutations = resolve_killing_tests(raw_mutations, test_mappings, base_to_keys)

    print(f"Data: {total_tests} tests, {len(mutations)} KILLED mutations\n")

    # 1. Proposed coverage-based selector
    res_coverage = evaluate_selector("Coverage (proposed)", select_original, mutations, test_mappings)

    # 2. Class-level baseline
    res_class = evaluate_selector("Class-level only", select_class_level, mutations, test_mappings)

    # 3. Random selector
    res_random = evaluate_random_per_mutation(mutations, test_mappings, seed=args.seed)

    # Print comparison table
    results = [res_coverage, res_class, res_random]
    print(f"{'='*78}")
    print(f"BASELINE COMPARISON -- Smart Test Picker vs Baselines")
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
