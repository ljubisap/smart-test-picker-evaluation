#!/usr/bin/env python3
"""Read-only RAD1 v14.1 checks over frozen evaluation artifacts."""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import defaultdict
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
    select_original,
)

OUT = Path(__file__).resolve().parent
SEED = 20261003
TRIALS = 10_000


def load_subject(row):
    coverage_path = ROOT / row["coverageMap"]
    coverage = load_coverage_map(coverage_path)
    mappings = coverage["testMappings"]
    pit_files = discover_pit_files(ROOT, row["pitFiles"])
    raw = load_pit_mutations(row["name"], ROOT, pit_files)
    resolved = resolve_killing_tests(
        raw,
        mappings,
        build_base_to_keys(mappings),
        build_class_to_keys(mappings, coverage.get("executionIdentities", {})),
    )
    resolved = exclude_non_leaf_oracle_records(resolved, ROOT, row["name"])
    records = []
    for mutation in resolved:
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
        selections = {
            "stp": select_original(mappings, mutation.mutated_class, mutation.mutated_method),
            "class": select_class_level(mappings, mutation.mutated_class, mutation.mutated_method),
            "constructor": select_constructor_only_rule(
                mappings, mutation.mutated_class, mutation.mutated_method
            ),
        }
        records.append(
            {
                "mutation": mutation,
                "killing": killing,
                "sizes": {name: len(value) for name, value in selections.items()},
                "safe": {name: bool(value & killing) for name, value in selections.items()},
            }
        )
    return coverage_path, pit_files, coverage, mappings, records


def selector_precision(records, population, selector):
    sizes = [record["sizes"][selector] for record in records]
    safe = sum(record["safe"][selector] for record in records)
    mean = sum(sizes) / len(sizes)
    fraction = 100 * mean / population
    return {
        "safe": safe,
        "total": len(records),
        "meanSelectedFullPrecision": mean,
        "meanSelected2dp": round(mean, 2),
        "selectedFractionPctFullPrecision": fraction,
        "selectedFractionPct2dp": round(fraction, 2),
        "reductionPctFullPrecision": 100 - fraction,
        "reductionPct2dp": round(100 - fraction, 2),
    }


def wilson(successes, total, z=1.959963984540054):
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [100 * (centre - half), 100 * (centre + half)]


def cluster_bootstrap(cluster_pairs, seed):
    rng = random.Random(seed)
    values = []
    count = len(cluster_pairs)
    for _ in range(TRIALS):
        sampled = [cluster_pairs[rng.randrange(count)] for _ in range(count)]
        safe = sum(pair[0] for pair in sampled)
        total = sum(pair[1] for pair in sampled)
        values.append(100 * safe / total)
    values.sort()
    return {
        "seed": seed,
        "trials": TRIALS,
        "clusters": count,
        "lowerPct": values[int(0.025 * TRIALS)],
        "upperPct": values[int(0.975 * TRIALS) - 1],
    }


def main():
    projects = json.loads((ROOT / "analysis/projects.json").read_text())["projects"]
    precision = {"sources": {}, "projects": {}}
    intervals = {"seed": SEED, "trials": TRIALS, "projects": {}}
    map_exposure = {"projects": {}}
    subject_records = {}
    aggregate_clusters = []

    for project_index, project in enumerate(projects):
        name = project["name"]
        coverage_path, pit_files, coverage, mappings, records = load_subject(project)
        subject_records[name] = (coverage, mappings, records)
        precision["sources"][name] = {
            "coverageMap": coverage_path.relative_to(ROOT).as_posix(),
            "pitFiles": [path.relative_to(ROOT).as_posix() for path in pit_files],
            "perRecordSelection": f"{name}/results/aggregated/evaluation_results.csv",
        }
        precision["projects"][name] = {
            "logicalTests": len(mappings),
            "stp": selector_precision(records, len(mappings), "stp"),
            "classBaseline": selector_precision(records, len(mappings), "class"),
            "constructorOnly": selector_precision(records, len(mappings), "constructor"),
        }

        safe = sum(record["safe"]["stp"] for record in records)
        grouped = defaultdict(lambda: [0, 0])
        for record in records:
            cls = record["mutation"].mutated_class
            grouped[cls][0] += int(record["safe"]["stp"])
            grouped[cls][1] += 1
        pairs = list(grouped.values())
        aggregate_clusters.extend(pairs)
        intervals["projects"][name] = {
            "safe": safe,
            "total": len(records),
            "estimatePct": 100 * safe / len(records),
            "wilson95Pct": wilson(safe, len(records)),
            "clusterBootstrap95Pct": cluster_bootstrap(pairs, SEED + project_index),
        }

        map_classes = sorted(
            {
                cls
                for value in mappings.values()
                for cls in value.get("classes", [])
                if ".test." in f".{cls}."
            }
        )
        no_coverage = sorted(
            key
            for key, value in mappings.items()
            if not value.get("classes") and not value.get("methods")
        )
        map_exposure["projects"][name] = {
            "coverageMap": coverage_path.relative_to(ROOT).as_posix(),
            "mappedProductionClassesWithTestSegment": map_classes,
            "mappedProductionClassCount": len(map_classes),
            "noCoverageLogicalTests": len(no_coverage),
            "noCoverageIdentities": no_coverage,
        }

    all_safe = sum(row["safe"] for row in intervals["projects"].values())
    all_total = sum(row["total"] for row in intervals["projects"].values())
    intervals["aggregate"] = {
        "safe": all_safe,
        "total": all_total,
        "estimatePct": 100 * all_safe / all_total,
        "wilson95Pct": wilson(all_safe, all_total),
        "clusterBootstrap95Pct": cluster_bootstrap(aggregate_clusters, SEED + 100),
        "clusterDefinition": "mutated production class, pooled with subject-qualified class identity",
    }

    spring_map = subject_records["spring-core"][1]
    prefix = "org.springframework.core.convert.support.GenericConversionService#canConvert"
    matching_keys = sorted(
        {method for value in spring_map.values() for method in value.get("methods", []) if method.startswith(prefix)}
    )
    method_identity = {
        "coverageMap": "spring-core/results/test-coverage-map.json",
        "keys": [
            {
                "key": key,
                "logicalTestCount": sum(key in value.get("methods", []) for value in spring_map.values()),
            }
            for key in matching_keys
        ],
        "descriptorPresent": any("(" in key for key in matching_keys),
    }

    taxonomy = json.loads((ROOT / "results/failure_taxonomy.json").read_text())
    target = next(
        mutation
        for mutation in taxonomy["byProject"]["spring-core"]["mutations"]
        if mutation["mutatedClass"].endswith("GenericConversionService")
        and mutation["mutatedMethod"] == "canConvert"
        and mutation["line"] == 133
        and mutation["mutator"] == "VoidMethodCallMutator"
    )
    worked = {
        "source": "results/failure_taxonomy.json",
        "mutationId": target["mutationId"],
        "footprintType": target["footprintType"],
        "recoveredByConstructorRule": target["recoveredByConstructorRule"],
        "killingTests": target["killingTests"],
        "mitigationSource": "results/mitigation_comparison.json",
    }

    for name, data in (
        ("table_precision.json", precision),
        ("confidence_intervals.json", intervals),
        ("map_test_segment_exposure.json", map_exposure),
        ("method_identity.json", method_identity),
        ("worked_example.json", worked),
    ):
        (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
