#!/usr/bin/env python3
"""
03_evaluate.py  --  Evaluate plugin safety against PIT mutation ground truth.

For each KILLED mutation, simulates the plugin's dual-granularity selection
and checks whether at least one killing test would have been selected.

Metrics:
  - Inclusiveness (Safety): % mutations where T_selected   &   T_killing != {}
  - Selection Rate: avg |T_selected| / |all_tests|
  - Test Reduction: 1 - Selection Rate

Usage:
  python3 03_evaluate.py --project-dir /path/to/jgrapht
"""

import argparse
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def normalize_pit_test_name(pit_test_id):
    """
    Normalize PIT's JUnit Platform unique ID to coverage map format.

    PIT formats:
      [class:FQN]/[method:name()]  --  regular test
      [class:FQN]/[nested-class:A]/[nested-class:B]/[method:name()]  --  nested class
      [class:FQN]/[test-template:name(params)]/[test-template-invocation:#N]  --  parameterized

    Coverage map format: SimpleClassName#methodName
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


def select_tests_for_change(test_mappings, changed_class, changed_method):
    """Simulate plugin's dual-granularity selection."""
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


def load_mutations(results_dir):
    """Load all KILLED mutations from per-class XML files."""
    mutations = []
    per_class = results_dir / "per-class"
    for class_dir in sorted(per_class.iterdir()):
        if not class_dir.is_dir():
            continue
        xml_path = class_dir / "mutations.xml"
        gz_path = class_dir / "mutations.xml.gz"
        if gz_path.exists():
            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                tree = ET.parse(f)
        elif xml_path.exists():
            tree = ET.parse(xml_path)
        else:
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
                "lineNumber": mut.findtext("lineNumber"),
                "mutator": mut.findtext("mutator"),
                "killingTests": killing_tests,
            })
    return mutations


def main():
    parser = argparse.ArgumentParser(description="Evaluate plugin safety vs PIT ground truth")
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

    with open(coverage_map_path) as f:
        coverage_data = json.load(f)
    test_mappings = coverage_data["testMappings"]
    total_tests = len(test_mappings)
    commit = coverage_data.get("metadata", {}).get("commitId", "unknown")

    # Build reverse lookup: base name (without hash suffix) -> set of full map keys
    base_to_keys = defaultdict(set)
    for key in test_mappings:
        if '_' in key and len(key.rsplit('_', 1)[-1]) == 7:
            last = key.rsplit('_', 1)[-1]
            if all(c in '0123456789abcdef' for c in last):
                base_to_keys[key.rsplit('_', 1)[0]].add(key)
                continue
        base_to_keys[key].add(key)

    mutations = load_mutations(results_dir)
    if not mutations:
        print("ERROR: No mutations found in results/per-class/")
        sys.exit(1)

    # Resolve killing test names to coverage map keys
    raw_killing_count = 0
    resolved_killing_count = 0
    unresolved_ids = []
    for mut in mutations:
        resolved = set()
        for kt in mut["killingTests"]:
            raw_killing_count += 1
            if kt in test_mappings:
                resolved.add(kt)
            elif kt in base_to_keys:
                resolved.update(base_to_keys[kt])
        resolved_killing_count += len(resolved)
        if not resolved and mut.get("killingTests"):
            unresolved_ids.append(f"{mut["mutatedClass"]}.{mut["mutatedMethod"]}")
        mut["killingTests"] = resolved

    if unresolved_ids:
        print(f"ERROR: {len(unresolved_ids)} mutations have no resolved killing tests:")
        for uid in unresolved_ids[:5]:
            print(f"  {uid}")
        sys.exit(1)

    # Evaluate
    safe_count = 0
    unsafe_mutations = []
    selection_sizes = []
    class_safety = defaultdict(lambda: {"safe": 0, "unsafe": 0})

    for mut in mutations:
        t_selected = select_tests_for_change(test_mappings, mut["mutatedClass"], mut["mutatedMethod"])
        intersection = t_selected & mut["killingTests"]
        is_safe = len(intersection) > 0

        selection_sizes.append(len(t_selected))
        cls = mut["mutatedClass"]

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

    # Print results
    print(f"{'='*70}")
    print(f"EVALUATION RESULTS  --  Smart Test Picker vs PIT Ground Truth")
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
            print(f"  {u['mutatedClass']}.{u['mutatedMethod']} L{u['lineNumber']}")
            print(f"    killing: {list(u['killingTests'])[:3]}")

    print(f"\n--- PER-CLASS SAFETY ---")
    for cls in sorted(class_safety.keys()):
        s = class_safety[cls]
        t = s["safe"] + s["unsafe"]
        print(f"  {cls}: {s['safe']/t*100:.0f}% ({s['safe']}/{t})")

    # Write outputs
    agg_dir = results_dir / "aggregated"
    agg_dir.mkdir(parents=True, exist_ok=True)

    csv_path = agg_dir / "evaluation_results.csv"
    with open(csv_path, "w") as f:
        f.write("mutatedClass,mutatedMethod,lineNumber,mutator,numKillingTests,numSelectedTests,safe\n")
        for i, mut in enumerate(mutations):
            t_sel = select_tests_for_change(test_mappings, mut["mutatedClass"], mut["mutatedMethod"])
            inter = t_sel & mut["killingTests"]
            f.write(f"{mut['mutatedClass']},{mut['mutatedMethod']},{mut['lineNumber']},"
                    f"{mut['mutator']},{len(mut['killingTests'])},{len(t_sel)},{len(inter)>0}\n")

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
        "unsafe_details": [{"class": u["mutatedClass"], "method": u["mutatedMethod"],
                            "line": u["lineNumber"]} for u in unsafe_mutations],
    }
    with open(agg_dir / "evaluation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nOutput: {csv_path}")
    print(f"Output: {agg_dir / 'evaluation_summary.json'}")


if __name__ == "__main__":
    main()
