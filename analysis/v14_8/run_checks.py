#!/usr/bin/env python3
"""Generate the read-only spring-core test-outcome evidence for RAD1 v14.8."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    all_coverage_keys,
    build_base_to_keys,
    build_class_to_keys,
    discover_pit_files,
    exclude_non_leaf_oracle_records,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
)

ADOPTED_MAP = ROOT / "recollection_2e0954/spring-core/test-coverage-map.json"
FROZEN_MAP = ROOT / "spring-core/results/test-coverage-map.json"
RUN_LOG = ROOT / "recollection_2e0954/spring-core-run1-test.log"
COLLECTION = ROOT / "recollection_2e0954/spring-core/collection_v14_6.json"
ORIGINAL_DOC = ROOT / "spring-core/docs/REPRODUCE.md"
PIT_GLOB = ["spring-core/results/per-class/*/mutations.xml"]

FAILURES = (
    {
        "class": "BridgeMethodResolverTests",
        "method": "testInterfaceHierarchy",
        "failureType": "org.opentest4j.AssertionFailedError",
        "messageHead": "org.opentest4j.AssertionFailedError at BridgeMethodResolverTests.java:351",
        "logLines": [65, 66],
    },
    {
        "class": "BridgeMethodResolverTests",
        "method": "testClassHierarchy",
        "failureType": "org.opentest4j.AssertionFailedError",
        "messageHead": "org.opentest4j.AssertionFailedError at BridgeMethodResolverTests.java:351",
        "logLines": [68, 69],
    },
    {
        "class": "AnnotationMetadataTests",
        "method": "standardAnnotationMetadata",
        "failureType": "java.lang.AssertionError",
        "messageHead": "java.lang.AssertionError at AnnotationMetadataTests.java:506",
        "logLines": [71, 72],
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_name(key: str) -> str:
    return re.sub(r"_[0-9a-f]{7}$", "", key)


def generate() -> dict:
    adopted = load_coverage_map(ADOPTED_MAP)
    frozen = load_coverage_map(FROZEN_MAP)
    adopted_mappings = adopted["testMappings"]
    frozen_mappings = frozen["testMappings"]

    raw = load_pit_mutations(
        "spring-core", ROOT, discover_pit_files(ROOT, PIT_GLOB)
    )
    resolved = resolve_killing_tests(
        raw,
        adopted_mappings,
        build_base_to_keys(adopted_mappings),
        build_class_to_keys(
            adopted_mappings, adopted.get("executionIdentities", {})
        ),
    )
    eligible = exclude_non_leaf_oracle_records(resolved, ROOT, "spring-core")

    result_rows = []
    all_affected_mutations: set[str] = set()
    for failure in FAILURES:
        target_base = failure["class"] + "#" + failure["method"]
        adopted_keys = sorted(
            key for key in adopted_mappings if base_name(key) == target_base
        )
        frozen_keys = sorted(
            key for key in frozen_mappings if base_name(key) == target_base
        )
        killing_mutations = sorted(
            mutation.mutation_id
            for mutation in eligible
            if set(adopted_keys) & all_coverage_keys(mutation)
        )
        all_affected_mutations.update(killing_mutations)
        adopted_footprints = [
            {
                "coverageKey": key,
                "classEdges": len(adopted_mappings[key].get("classes") or []),
                "methodEdges": len(adopted_mappings[key].get("methods") or []),
            }
            for key in adopted_keys
        ]
        row = dict(failure)
        row.update(
            {
                "identity": target_base,
                "adoptedMap": {
                    "present": bool(adopted_keys),
                    "matchingKeys": adopted_keys,
                    "footprints": adopted_footprints,
                },
                "frozen70b398Map": {
                    "present": bool(frozen_keys),
                    "matchingKeys": frozen_keys,
                },
                "eligiblePitKiller": bool(killing_mutations),
                "eligibleMutationIds": killing_mutations,
                "originalCollectionFailure": {
                    "status": "CLASS_LEVEL_FAILURE_CATEGORY_DOCUMENTED_EXACT_METHOD_UNKNOWN",
                    "source": "spring-core/docs/REPRODUCE.md:94,182",
                    "explanation": (
                        "The retained original-collection instructions name the "
                        "BridgeMethodResolverTests and AnnotationMetadataTests failure "
                        "categories, but do not retain an exact per-method failure list."
                    ),
                },
                "adoptedFailureSource": (
                    "recollection_2e0954/spring-core-run1-test.log:"
                    + "-".join(str(n) for n in failure["logLines"])
                ),
            }
        )
        result_rows.append(row)

    collection = json.loads(COLLECTION.read_text(encoding="utf-8"))
    result = {
        "schemaVersion": 1,
        "scope": "spring-core adopted 2e0954 collection run 1",
        "adoptedMap": {
            "path": str(ADOPTED_MAP.relative_to(ROOT)),
            "sha256": sha256(ADOPTED_MAP),
            "collectionRun": "run1",
            "collectionRecord": str(COLLECTION.relative_to(ROOT)),
            "recordedSha256": collection["run1"]["mapSha256"],
        },
        "testRunSummary": {
            "executed": 4704,
            "failed": 3,
            "skipped": 28,
            "source": "recollection_2e0954/spring-core-run1-test.log:65-78",
        },
        "failures": result_rows,
        "eligibleRecordsWithFailingKiller": sorted(all_affected_mutations),
        "eligibleRecordsWithFailingKillerCount": len(all_affected_mutations),
        "allFailuresPresentInAdoptedMap": all(
            row["adoptedMap"]["present"] for row in result_rows
        ),
        "noneIsEligiblePitKiller": not all_affected_mutations,
        "originalExactMethodOutcomesEstablished": False,
        "originalEvidence": {
            "source": "spring-core/docs/REPRODUCE.md:94,182",
            "finding": (
                "Original instructions document 3-5 instrumentation-sensitive "
                "failures in the same test classes, with a varying exact count; "
                "they do not establish the exact failed methods."
            ),
        },
    }
    if result["adoptedMap"]["sha256"] != result["adoptedMap"]["recordedSha256"]:
        raise AssertionError("adopted map hash differs from collection record")
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = generate()
    path = OUT / "springcore_test_outcomes.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"PASS: {len(result['failures'])} failures; "
        f"eligible killer records={result['eligibleRecordsWithFailingKillerCount']}"
    )


if __name__ == "__main__":
    main()
