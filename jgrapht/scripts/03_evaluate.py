#!/usr/bin/env python3
"""
03_evaluate.py -- Evaluate plugin inclusiveness against PIT mutation ground truth.

Uses shared evaluation logic from analysis/evaluation_core.py.

Usage:
  python3 03_evaluate.py --project-dir /path/to/jgrapht
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, load_pit_mutations,
    build_base_to_keys, resolve_killing_tests, select_original,
)


def main():
    parser = argparse.ArgumentParser(description="Evaluate plugin inclusiveness vs PIT ground truth")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to jgrapht checkout")
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--coverage-map", type=Path, default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = args.results_dir or (script_dir.parent / "results")
    coverage_map_path = args.coverage_map or (
        args.project_dir / "jgrapht-core" / "target" / "test-coverage-map.json"
    )

    if not coverage_map_path.exists():
        print(f"ERROR: Coverage map not found: {coverage_map_path}")
        sys.exit(1)

    coverage_data = load_coverage_map(coverage_map_path)
    test_mappings = coverage_data["testMappings"]
    total_tests = len(test_mappings)
    commit = coverage_data.get("metadata", {}).get("commitId", "unknown")

    base_to_keys = build_base_to_keys(test_mappings)

    pit_base = results_dir / "per-class"
    pit_files = sorted(
        list(pit_base.glob("*/mutations.xml")) + list(pit_base.glob("*/mutations.xml.gz")),
        key=lambda p: p.as_posix()
    )
    if not pit_files:
        print(f"ERROR: No mutations found in {pit_base}/")
        sys.exit(1)
    # Use results_dir parent as root for relativization when files are outside REPO_ROOT
    pit_root = REPO_ROOT if str(pit_base).startswith(str(REPO_ROOT)) else results_dir.parent
    raw_mutations = load_pit_mutations("jgrapht", pit_root, tuple(pit_files))

    if not raw_mutations:
        print(f"ERROR: No KILLED mutations found in {pit_base}/")
        sys.exit(1)

    mutations = resolve_killing_tests(raw_mutations, test_mappings, base_to_keys)

    safe_count = 0
    unsafe_mutations = []
    selection_sizes = []
    class_safety = defaultdict(lambda: {"safe": 0, "unsafe": 0})

    for mut in mutations:
        t_selected = select_original(test_mappings, mut.mutated_class, mut.mutated_method)
        killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
        is_safe = bool(t_selected & killing_keys)
        selection_sizes.append(len(t_selected))
        cls = mut.mutated_class
        if is_safe:
            safe_count += 1
            class_safety[cls]["safe"] += 1
        else:
            unsafe_mutations.append(mut)
            class_safety[cls]["unsafe"] += 1

    total = len(mutations)
    inclusiveness = safe_count / total * 100
    avg_sel = sum(selection_sizes) / len(selection_sizes)
    sel_rate = avg_sel / total_tests * 100

    print(f"{'='*70}")
    print(f"EVALUATION RESULTS -- Smart Test Picker vs PIT Ground Truth")
    print(f"{'='*70}")
    print(f"Coverage map: {total_tests} tests")
    print(f"Mutations (KILLED): {total}")
    print(f"Classes: {len(class_safety)}")
    print(f"\n--- METRICS ---")
    print(f"Inclusiveness (Safety):  {inclusiveness:.2f}% ({safe_count}/{total})")
    print(f"Avg Selection Size:      {avg_sel:.1f} tests")
    print(f"Selection Rate:          {sel_rate:.2f}%")
    print(f"Test Reduction:          {100 - sel_rate:.2f}%")

    if unsafe_mutations:
        print(f"\n--- UNSAFE MUTATIONS ({len(unsafe_mutations)}) ---")
        for u in unsafe_mutations[:10]:
            killing_names = [kt.normalized_id for kt in u.killing_tests]
            print(f"  {u.mutated_class}.{u.mutated_method} L{u.line_number}")
            print(f"    killing: {killing_names[:3]}")

    print(f"\n--- PER-CLASS SAFETY ---")
    for cls in sorted(class_safety.keys()):
        s = class_safety[cls]
        t = s["safe"] + s["unsafe"]
        print(f"  {cls}: {s['safe']/t*100:.0f}% ({s['safe']}/{t})")

    agg_dir = results_dir / "aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)

    csv_path = agg_dir / "evaluation_results.csv"
    with open(csv_path, "w") as f:
        f.write("mutatedClass,mutatedMethod,lineNumber,mutator,numKillingTests,numSelectedTests,safe\n")
        for mut in mutations:
            t_sel = select_original(test_mappings, mut.mutated_class, mut.mutated_method)
            killing_keys = set(k for kt in mut.killing_tests for k in kt.coverage_keys)
            inter = t_sel & killing_keys
            num_killing = sum(len(kt.coverage_keys) for kt in mut.killing_tests)
            f.write(f"{mut.mutated_class},{mut.mutated_method},{mut.line_number},"
                    f"{mut.mutator},{num_killing},{len(t_sel)},{len(inter)>0}\n")

    summary = {
        "project": "JGraphT",
        "commit": commit,
        "num_classes": len(class_safety),
        "total_tests": total_tests,
        "total_mutations": total,
        "inclusiveness_pct": round(inclusiveness, 2),
        "avg_selection_size": round(avg_sel, 1),
        "selection_rate_pct": round(sel_rate, 2),
        "test_reduction_pct": round(100 - sel_rate, 2),
        "safe": safe_count,
        "unsafe": len(unsafe_mutations),
        "unsafe_details": [{"class": u.mutated_class, "method": u.mutated_method,
                            "line": str(u.line_number)} for u in unsafe_mutations],
    }
    with open(agg_dir / "evaluation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nOutput: {csv_path}")
    print(f"Output: {agg_dir / 'evaluation_summary.json'}")


if __name__ == "__main__":
    main()
