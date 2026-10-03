#!/usr/bin/env python3
"""Generate the I-2 and I-3 read-only audits from frozen/retained evidence."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys, build_class_to_keys, discover_pit_files,
    exclude_non_leaf_oracle_records, load_coverage_map, load_pit_mutations,
    resolve_killing_tests, select_original,
)

SESSION_DIRS = {
    "commons-lang": Path("/Users/D061177/work/moje/commons-lang/target/jacoco-xml"),
    "jgrapht": Path("/Users/D061177/work/moje/jgrapht/jgrapht-core/target/jacoco-xml"),
    "spring-core": Path("/Users/D061177/work/moje/spring-framework-6/spring-core/build/jacoco-xml"),
    "petclinic": Path("/Users/D061177/work/moje/spring-petclinic/build/jacoco-xml"),
}


def method_kind(name: str) -> str:
    if name == "<init>":
        return "constructor"
    if name == "<clinit>":
        return "class_initializer"
    if name.startswith("lambda$"):
        return "lambda"
    if name.startswith("access$") or name.startswith("$deserializeLambda$") or name.startswith("bridge$"):
        return "other_synthetic_or_bridge_name_detectable"
    return "regular_method"


def map_method_kind(method_key: str) -> str:
    return method_kind(method_key.split("#", 1)[1] if "#" in method_key else method_key)


def unsanitize_session_identity(name: str) -> str:
    """Mirror CoverageMapperJaxb.unsanitizeSessionFileName at 70b398:227-251."""
    if "#" not in name:
        return name
    class_name, method = name.split("#", 1)
    decoded, index = [], 0
    while index < len(method):
        if method[index] == "~" and index + 1 < len(method):
            decoded.append(method[index + 1].upper())
            index += 2
        else:
            decoded.append(method[index])
            index += 1
    return class_name + "#" + "".join(decoded)


def identity_set_sha256(values) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_subject(project):
    coverage = load_coverage_map(ROOT / project["coverageMap"])
    mappings = coverage["testMappings"]
    raw = load_pit_mutations(project["name"], ROOT, discover_pit_files(ROOT, project["pitFiles"]))
    resolved = resolve_killing_tests(
        raw, mappings, build_base_to_keys(mappings),
        build_class_to_keys(mappings, coverage.get("executionIdentities", {})),
    )
    return coverage, mappings, exclude_non_leaf_oracle_records(resolved, ROOT, project["name"])


def main() -> None:
    config = json.loads((ROOT / "analysis/projects.json").read_text())
    audit = {
        "scope": "4,010 eligible leaf-oracle KILLED records",
        "classificationRule": {
            "constructor": "mutatedMethod == <init>",
            "class_initializer": "mutatedMethod == <clinit>",
            "lambda": "mutatedMethod starts lambda$",
            "other_synthetic_or_bridge_name_detectable": "name starts access$, $deserializeLambda$, or bridge$",
            "regular_method": "all remaining names",
            "limitation": "PIT XML has no JVM ACC_SYNTHETIC/ACC_BRIDGE flags; regular-named bridge methods cannot be distinguished without bytecode and remain in regular_method.",
        },
        "keyDerivationEvidence": {
            "pitParsing": "analysis/evaluation_core.py:210-225 (mutatedMethod text copied verbatim)",
            "selectorKey": "analysis/evaluation_core.py:412-423 (changed_class + '#' + changed_method)",
            "mapConverter": "STP 2e0954 CoverageMapperJaxb.java:143-157 (JaCoCo method.getName copied as classFqn#name)",
            "descriptorHandling": "No descriptor is added on either side.",
        },
        "subjects": {},
    }
    dropped = {
        "evidenceDefinition": "Retained per-test session JaCoCo XML filenames are the logical execution-session inventory consumed by CoverageMapperJaxb; compare exact extracted session identity to frozen map key.",
        "collectorDropCondition": "At 70b398 CoverageMapperJaxb.java:117-119 skips a parsed report when report.getPackages() is null.",
        "subjects": {},
    }

    for project in config["projects"]:
        name = project["name"]
        coverage, mappings, mutations = load_subject(project)
        empty = {k for k, v in mappings.items() if not v.get("classes") and not v.get("methods")}
        counts = {k: {"eligible": 0, "inclusiveUnder2ePolicy": 0, "residualMissesUnder2ePolicy": 0} for k in (
            "regular_method", "constructor", "class_initializer", "lambda", "other_synthetic_or_bridge_name_detectable"
        )}
        records = []
        for mutation in mutations:
            kind = method_kind(mutation.mutated_method)
            selected = select_original(mappings, mutation.mutated_class, mutation.mutated_method) | empty
            killers = {key for test in mutation.killing_tests for key in test.coverage_keys}
            inclusive = bool(selected & killers)
            counts[kind]["eligible"] += 1
            counts[kind]["inclusiveUnder2ePolicy"] += int(inclusive)
            counts[kind]["residualMissesUnder2ePolicy"] += int(not inclusive)
            if kind in {"lambda", "other_synthetic_or_bridge_name_detectable"}:
                records.append({
                    "mutationId": mutation.mutation_id, "kind": kind,
                    "mutatedClass": mutation.mutated_class, "mutatedMethod": mutation.mutated_method,
                    "inclusiveUnder2ePolicy": inclusive,
                })
        map_kind_counts = {k: 0 for k in counts}
        for entry in mappings.values():
            for method in entry.get("methods") or []:
                map_kind_counts[map_method_kind(method)] += 1
        audit["subjects"][name] = {
            "eligibleRecordsByKind": counts,
            "lambdaAndNameDetectableSyntheticRecords": records,
            "mapMethodKeyOccurrencesByKind": map_kind_counts,
            "mapCanContainKinds": {kind: amount > 0 for kind, amount in map_kind_counts.items()},
        }

        if name in SESSION_DIRS:
            session_dir = SESSION_DIRS[name]
            sessions = sorted(
                unsanitize_session_identity(path.name[len("session_"):-len(".xml")])
                for path in session_dir.glob("session_*.xml")
            ) if session_dir.exists() else []
            map_keys = sorted(mappings)
            missing = sorted(set(sessions) - set(map_keys))
            map_without_session = sorted(set(map_keys) - set(sessions))
            dropped["subjects"][name] = {
                "mapPath": project["coverageMap"],
                "mapSha256": file_sha256(ROOT / project["coverageMap"]),
                "mapCommitId": coverage.get("metadata", {}).get("commitId"),
                "retainedSessionInventoryPath": str(session_dir),
                "inventoryStatus": "AVAILABLE_EXACT_SESSION_IDENTITY" if session_dir.exists() else "UNKNOWN",
                "nativeLogicalTests": len(sessions) if session_dir.exists() else None,
                "retainedSessionIdentitySetSha256": identity_set_sha256(sessions) if session_dir.exists() else None,
                "mapIdentitySetSha256": identity_set_sha256(map_keys),
                "mapEntries": len(map_keys),
                "identitiesMissingFromMap": missing if session_dir.exists() else None,
                "mapIdentitiesMissingFromInventory": map_without_session if session_dir.exists() else None,
                "droppedZeroPackageSessions": 0 if session_dir.exists() and not missing else None,
                "interpretation": (
                    "Exact identity equality; no retained session was dropped by the null-package branch."
                    if session_dir.exists() and not missing and not map_without_session
                    else "Mismatch or unavailable evidence; zero-package attribution is UNKNOWN."
                ),
            }

    # Aggregate the required lambda/synthetic outcome over the adopted 2e policy.
    audit["aggregate"] = {}
    for kind in ("lambda", "other_synthetic_or_bridge_name_detectable"):
        eligible = sum(row["eligibleRecordsByKind"][kind]["eligible"] for row in audit["subjects"].values())
        inclusive = sum(row["eligibleRecordsByKind"][kind]["inclusiveUnder2ePolicy"] for row in audit["subjects"].values())
        misses = sum(row["eligibleRecordsByKind"][kind]["residualMissesUnder2ePolicy"] for row in audit["subjects"].values())
        audit["aggregate"][kind] = {"eligible": eligible, "inclusive": inclusive, "among19ResidualMisses": misses}
    audit["totalEligible"] = sum(
        value["eligible"] for row in audit["subjects"].values() for value in row["eligibleRecordsByKind"].values()
    )
    audit["totalResidualMissesUnder2ePolicy"] = sum(
        value["residualMissesUnder2ePolicy"] for row in audit["subjects"].values() for value in row["eligibleRecordsByKind"].values()
    )
    (OUT / "method_kind_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (OUT / "dropped_session_estimate.json").write_text(json.dumps(dropped, indent=2) + "\n")


if __name__ == "__main__":
    main()
