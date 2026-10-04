#!/usr/bin/env python3
"""Audit PIT succeedingTests for v14.6 residual and NO_COVERAGE cohorts."""
from __future__ import annotations

import gzip
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    build_class_to_keys,
    discover_pit_files,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
)


def read_tree(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return ET.parse(stream)
    return ET.parse(path)


def load_succeeding_by_source(project: dict) -> tuple[dict[tuple[str, int], list[str]], dict]:
    files = discover_pit_files(ROOT, project["pitFiles"])
    values: dict[tuple[str, int], list[str]] = {}
    total = available = 0
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        for ordinal, element in enumerate(read_tree(path).getroot().findall("mutation")):
            total += 1
            node = element.find("succeedingTests")
            if node is not None:
                available += 1
            text = (node.text or "").strip() if node is not None else ""
            values[(relative, ordinal)] = [item for item in text.split("|") if item]
    return values, {
        "status": "AVAILABLE" if available else "NOT_AVAILABLE",
        "pitFiles": len(files),
        "mutationRecords": total,
        "recordsWithElement": available,
    }


def generate() -> dict:
    projects = json.loads((ROOT / "analysis/projects_v14_6.json").read_text())["projects"]
    outcomes = json.loads((ROOT / "results/v14_6-per-record-outcomes.json").read_text())
    taxonomy = json.loads((ROOT / "results/v14_6-residual-taxonomy.json").read_text())
    selected_sets = outcomes["selectedSets"]
    outcome_by_id = {row["mutationId"]: row for row in outcomes["records"]}
    residual_ids = {row["mutationId"] for row in taxonomy["residualMisses"]}
    recovered_ids = {row["mutationId"] for row in taxonomy["recoveredByNoCoverage"]}
    cohort_ids = residual_ids | recovered_ids

    availability = {}
    resolved_succeeding: dict[str, set[str]] = {}
    unresolved = []
    empty_by_project: dict[str, set[str]] = {}

    for project in projects:
        name = project["name"]
        succeeding, status = load_succeeding_by_source(project)
        availability[name] = status
        coverage = load_coverage_map(ROOT / project["coverageMap"])
        mappings = coverage["testMappings"]
        empty_by_project[name] = {
            key for key, value in mappings.items()
            if not (value.get("classes") or []) and not (value.get("methods") or [])
        }
        raw_mutations = load_pit_mutations(
            name, ROOT, discover_pit_files(ROOT, project["pitFiles"])
        )
        base_to_keys = build_base_to_keys(mappings)
        class_to_keys = build_class_to_keys(
            mappings, coverage.get("executionIdentities", {})
        )
        for raw in raw_mutations:
            if raw.mutation_id not in cohort_ids:
                continue
            ids = succeeding.get((raw.source_xml, raw.xml_ordinal), [])
            keys: set[str] = set()
            for succeeding_id in ids:
                probe = replace(raw, raw_killing_test_ids=(succeeding_id,))
                try:
                    resolved = resolve_killing_tests(
                        [probe], mappings, base_to_keys, class_to_keys
                    )[0]
                    keys.update(resolved.killing_tests[0].coverage_keys)
                except ValueError as error:
                    unresolved.append(
                        {
                            "project": name,
                            "mutationId": raw.mutation_id,
                            "rawSucceedingTestId": succeeding_id,
                            "error": str(error),
                        }
                    )
            resolved_succeeding[raw.mutation_id] = keys

    records = []
    for mutation_id in sorted(cohort_ids):
        outcome = outcome_by_id[mutation_id]
        project = outcome["project"]
        cohort = "RESIDUAL_MISS" if mutation_id in residual_ids else "NO_COVERAGE_RECOVERED"
        base_selected = set(selected_sets[outcome["base"]["selectedSetId"]])
        if cohort == "NO_COVERAGE_RECOVERED":
            selected = base_selected - empty_by_project[project]
        else:
            selected = base_selected
        killers = set(outcome["killingTests"])
        succeeding = resolved_succeeding.get(mutation_id, set())
        selected_survived = sorted(selected & succeeding)
        selected_killed = sorted(selected & killers)
        selected_unexecuted = sorted(selected - killers - succeeding)
        records.append(
            {
                "project": project,
                "mutationId": mutation_id,
                "cohort": cohort,
                "selectedSetDefinition": (
                    "base" if cohort == "RESIDUAL_MISS" else "base-minus-U"
                ),
                "selectedCount": len(selected),
                "killingTests": sorted(killers),
                "resolvedSucceedingTestsCount": len(succeeding),
                "selectedSurvivingTests": selected_survived,
                "selectedKillingTests": selected_killed,
                "selectedNotExecutedByPit": selected_unexecuted,
                "fullyExecutedAndSurvived": not selected_killed and not selected_unexecuted,
            }
        )

    misses = [row for row in records if row["cohort"] == "RESIDUAL_MISS"]
    recovered = [row for row in records if row["cohort"] == "NO_COVERAGE_RECOVERED"]
    unexpected_kill_intersections = [
        row["mutationId"] for row in records if row["selectedKillingTests"]
    ]
    result = {
        "schemaVersion": 1,
        "availability": availability,
        "allSubjectsAvailable": all(
            row["status"] == "AVAILABLE" for row in availability.values()
        ),
        "cohort": {
            "residualMisses": len(residual_ids),
            "noCoverageRecovered": len(recovered_ids),
        },
        "unresolvedSucceedingTestIds": unresolved,
        "records": records,
        "summary": {
            "f": sum(row["fullyExecutedAndSurvived"] for row in misses),
            "u_tests": sum(len(row["selectedNotExecutedByPit"]) for row in misses),
            "residualMissesWithUnexpectedKillerIntersection": unexpected_kill_intersections,
            "recoveredRecordsFullyExecutedEdgeOnlySet": sum(
                row["fullyExecutedAndSurvived"] for row in recovered
            ),
            "allFiveRecoveredFullyExecutedEdgeOnlySet": bool(recovered)
            and all(row["fullyExecutedAndSurvived"] for row in recovered),
        },
    }
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = generate()
    (OUT / "succeeding_tests_check.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
