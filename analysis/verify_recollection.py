#!/usr/bin/env python3
"""
verify_recollection.py -- Verify recollection_comparison.json against git history.

Loads old (pre-recollection) coverage maps from git commit 46b3cf4, computes
normalized selected-set differences against the current committed maps, and
verifies that results/recollection_comparison.json is consistent.

Usage:
  python3 analysis/verify_recollection.py --verify
"""

import argparse
import gzip
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, discover_pit_files, load_pit_mutations,
    build_base_to_keys, resolve_killing_tests,
    select_original, select_constructor_only_rule, select_class_level,
)

# The commit containing the pre-recollection maps
OLD_MAP_COMMIT = "46b3cf44affe721b1b81633cad426b17ed333710"


def strip_hash(key):
    """Strip 7-hex hash suffix from coverage key."""
    if re.match(r'.+_[0-9a-f]{7}$', key):
        return key.rsplit('_', 1)[0]
    return key


def normalize_set(s):
    """Normalize a set of coverage keys by stripping hash suffixes."""
    return {strip_hash(k) for k in s}


def load_old_map_from_git(map_path_str):
    """Load a coverage map from a specific git commit."""
    result = subprocess.run(
        ["git", "show", f"{OLD_MAP_COMMIT}:{map_path_str}"],
        capture_output=True, cwd=str(REPO_ROOT)
    )
    if result.returncode != 0:
        raise RuntimeError(f"Cannot load old map from git: {map_path_str} at {OLD_MAP_COMMIT}")

    raw = result.stdout
    if map_path_str.endswith(".gz"):
        with gzip.open(io.BytesIO(raw), "rt") as f:
            return json.load(f)
    else:
        return json.loads(raw)


def compute_comparison():
    """Recompute the recollection comparison from scratch."""
    config_path = REPO_ROOT / "analysis" / "projects.json"
    with open(config_path) as f:
        projects_config = json.load(f)

    comparison = {}

    for proj in projects_config["projects"]:
        name = proj["name"]
        map_path_str = proj["coverageMap"]

        # Load old map from git
        old_data = load_old_map_from_git(map_path_str)
        old_tm = old_data["testMappings"]
        old_base_to_keys = build_base_to_keys(old_tm)

        # Load new map from current working tree
        new_data = load_coverage_map(REPO_ROOT / map_path_str)
        new_tm = new_data["testMappings"]
        new_base_to_keys = build_base_to_keys(new_tm)

        # Load PIT mutations
        pit_files = discover_pit_files(REPO_ROOT, proj["pitFiles"])
        raw_mutations = load_pit_mutations(name, REPO_ROOT, pit_files)
        old_resolved = resolve_killing_tests(raw_mutations, old_tm, old_base_to_keys)
        new_resolved = resolve_killing_tests(raw_mutations, new_tm, new_base_to_keys)

        # Compare per-mutation normalized selected sets
        orig_diffs = 0
        constr_diffs = 0
        class_diffs = 0
        old_unsafe = 0
        new_unsafe = 0
        safety_flips = 0

        for old_mut, new_mut in zip(old_resolved, new_resolved):
            old_orig = normalize_set(select_original(old_tm, old_mut.mutated_class, old_mut.mutated_method))
            new_orig = normalize_set(select_original(new_tm, new_mut.mutated_class, new_mut.mutated_method))

            old_constr = normalize_set(select_constructor_only_rule(old_tm, old_mut.mutated_class, old_mut.mutated_method))
            new_constr = normalize_set(select_constructor_only_rule(new_tm, new_mut.mutated_class, new_mut.mutated_method))

            old_class = normalize_set(select_class_level(old_tm, old_mut.mutated_class, old_mut.mutated_method))
            new_class = normalize_set(select_class_level(new_tm, new_mut.mutated_class, new_mut.mutated_method))

            if old_orig != new_orig:
                orig_diffs += 1
            if old_constr != new_constr:
                constr_diffs += 1
            if old_class != new_class:
                class_diffs += 1

            old_killing = set()
            new_killing = set()
            for kt in old_mut.killing_tests:
                old_killing.update(kt.coverage_keys)
            for kt in new_mut.killing_tests:
                new_killing.update(kt.coverage_keys)

            old_safe = bool(select_original(old_tm, old_mut.mutated_class, old_mut.mutated_method) & old_killing)
            new_safe = bool(select_original(new_tm, new_mut.mutated_class, new_mut.mutated_method) & new_killing)

            if not old_safe:
                old_unsafe += 1
            if not new_safe:
                new_unsafe += 1
            if old_safe != new_safe:
                safety_flips += 1

        comparison[name] = {
            "mutationCount": len(old_resolved),
            "originalSelectedSetDifferences": orig_diffs,
            "constructorOnlySelectedSetDifferences": constr_diffs,
            "classLevelSelectedSetDifferences": class_diffs,
            "unsafeBefore": old_unsafe,
            "unsafeAfter": new_unsafe,
            "safetyStatusChanges": safety_flips,
        }

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Verify recollection comparison artifact")
    parser.add_argument("--verify", action="store_true", required=True,
                        help="Verify results/recollection_comparison.json")
    args = parser.parse_args()

    artifact_path = REPO_ROOT / "results" / "recollection_comparison.json"
    if not artifact_path.exists():
        print(f"VERIFY FAILED: {artifact_path} not found")
        sys.exit(1)

    with open(artifact_path) as f:
        committed = json.load(f)

    # Verify the old map commit matches
    if committed.get("oldMapCommit") != OLD_MAP_COMMIT:
        print(f"VERIFY FAILED: oldMapCommit mismatch "
              f"(committed={committed.get('oldMapCommit')}, expected={OLD_MAP_COMMIT})")
        sys.exit(1)

    # Recompute
    fresh = compute_comparison()

    # Compare per-project values
    errors = []
    for name, fresh_values in fresh.items():
        committed_values = committed.get("perProject", {}).get(name, {})
        for key in ["mutationCount", "originalSelectedSetDifferences",
                    "constructorOnlySelectedSetDifferences", "classLevelSelectedSetDifferences",
                    "unsafeBefore", "unsafeAfter", "safetyStatusChanges"]:
            fresh_v = fresh_values[key]
            committed_v = committed_values.get(key)
            if fresh_v != committed_v:
                errors.append(f"{name}.{key}: committed={committed_v}, computed={fresh_v}")

    # Verify totals
    total_orig = sum(v["originalSelectedSetDifferences"] for v in fresh.values())
    total_safety = sum(v["safetyStatusChanges"] for v in fresh.values())
    committed_totals = committed.get("totals", {})
    if total_orig != committed_totals.get("originalSelectedSetDifferences"):
        errors.append(f"totals.originalSelectedSetDifferences: "
                      f"committed={committed_totals.get('originalSelectedSetDifferences')}, computed={total_orig}")
    if total_safety != committed_totals.get("safetyStatusChanges"):
        errors.append(f"totals.safetyStatusChanges: "
                      f"committed={committed_totals.get('safetyStatusChanges')}, computed={total_safety}")

    if errors:
        print("VERIFY FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"VERIFY PASSED: recollection_comparison.json "
              f"({committed_totals.get('mutations', '?')} mutations, "
              f"{total_orig} selected-set differences, "
              f"{total_safety} safety flips)")


if __name__ == "__main__":
    main()
