#!/usr/bin/env python3
"""Verify promoted B2 policy results from the frozen coverage/PIT inputs.

This verifier recomputes only the base, constructor, and class policy outcomes.
It does not rewrite artifacts, run PIT, or recompute random/interval results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    build_class_to_keys,
    discover_pit_files,
    exclude_non_leaf_oracle_records,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
    select_class_level,
    select_constructor_only_rule,
    select_policy,
)


POLICIES = {
    "base": select_policy,
    "constructor": select_constructor_only_rule,
    "class": select_class_level,
}


def selected_set_id(selected: list[str]) -> str:
    canonical = json.dumps(
        selected, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify() -> list[str]:
    config = json.loads((ROOT / "analysis" / "projects.json").read_text())
    summary = json.loads((ROOT / "results" / "b2-summary-tables.json").read_text())
    outcomes = json.loads((ROOT / "results" / "b2-per-record-outcomes.json").read_text())
    selected_sets = outcomes["selectedSets"]
    committed = {
        (row["project"], row["mutationId"]): row for row in outcomes["records"]
    }
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    aggregate = {
        policy: {"eligible": 0, "inclusive": 0, "sizes": []}
        for policy in POLICIES
    }

    for project in config["projects"]:
        name = project["name"]
        coverage = load_coverage_map(ROOT / project["coverageMap"])
        mappings = coverage["testMappings"]
        raw = load_pit_mutations(
            name,
            ROOT,
            discover_pit_files(ROOT, project["pitFiles"]),
        )
        mutations = resolve_killing_tests(
            raw,
            mappings,
            build_base_to_keys(mappings),
            build_class_to_keys(mappings, coverage.get("executionIdentities", {})),
        )
        mutations = exclude_non_leaf_oracle_records(mutations, ROOT, name)
        project_stats = {
            policy: {"eligible": 0, "inclusive": 0, "sizes": []}
            for policy in POLICIES
        }

        for mutation in mutations:
            key = (name, mutation.mutation_id)
            row = committed.get(key)
            if row is None:
                errors.append(f"missing committed record: {name} {mutation.mutation_id}")
                continue
            seen.add(key)
            killing = {
                coverage_key
                for killing_test in mutation.killing_tests
                for coverage_key in killing_test.coverage_keys
            }
            for policy, selector in POLICIES.items():
                selected = sorted(
                    selector(mappings, mutation.mutated_class, mutation.mutated_method)
                )
                selected_id = selected_set_id(selected)
                inclusive = bool(set(selected) & killing)
                recorded = row[policy]
                if recorded["selectedSetId"] != selected_id:
                    errors.append(f"{name} {mutation.mutation_id} {policy}: selectedSetId")
                if recorded["selectedCount"] != len(selected):
                    errors.append(f"{name} {mutation.mutation_id} {policy}: selectedCount")
                if recorded["inclusive"] != inclusive:
                    errors.append(f"{name} {mutation.mutation_id} {policy}: inclusive")
                if selected_sets.get(selected_id) != selected:
                    errors.append(f"{name} {mutation.mutation_id} {policy}: selected-set payload")
                for stats in (project_stats[policy], aggregate[policy]):
                    stats["eligible"] += 1
                    stats["inclusive"] += int(inclusive)
                    stats["sizes"].append(len(selected))

        for policy, stats in project_stats.items():
            expected = summary["projects"][name]["policies"][policy]
            mean = sum(stats["sizes"]) / stats["eligible"] if stats["eligible"] else 0.0
            for field in ("eligible", "inclusive"):
                if stats[field] != expected[field]:
                    errors.append(
                        f"{name} {policy} {field}: {stats[field]} != {expected[field]}"
                    )
            if not math.isclose(
                mean, expected["meanSelectedFullPrecision"], rel_tol=0.0, abs_tol=1e-12
            ):
                errors.append(
                    f"{name} {policy} mean: {mean} != "
                    f"{expected['meanSelectedFullPrecision']}"
                )

    extra = set(committed) - seen
    if extra:
        errors.append(f"{len(extra)} extra committed per-record outcomes")

    for policy, stats in aggregate.items():
        expected = summary["aggregate"][policy]
        if stats["eligible"] != expected["eligible"]:
            errors.append(f"aggregate {policy} eligible")
        if stats["inclusive"] != expected["inclusive"]:
            errors.append(f"aggregate {policy} inclusive")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    errors = verify()
    if errors:
        print("VERIFY FAILED:")
        for error in errors[:50]:
            print(f"  - {error}")
        if len(errors) > 50:
            print(f"  - ... and {len(errors) - 50} more")
        raise SystemExit(1)
    print("VERIFY PASSED: B2 base/constructor/class summaries and selected-set IDs match frozen inputs")


if __name__ == "__main__":
    main()
