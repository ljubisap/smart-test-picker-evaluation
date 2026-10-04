#!/usr/bin/env python3
"""Derive failed-killer policy impact from committed v14.6 outcomes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUTCOMES = ROOT / "results/v14_6-per-record-outcomes.json"
FAILED = ROOT / "analysis/v14_8/springcore_test_outcomes.json"
TAXONOMY = ROOT / "results/v14_6-residual-taxonomy.json"


def generate() -> dict:
    outcomes = json.loads(OUTCOMES.read_text(encoding="utf-8"))
    failed = json.loads(FAILED.read_text(encoding="utf-8"))
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    selected_sets = outcomes["selectedSets"]
    records_by_id = {row["mutationId"]: row for row in outcomes["records"]}
    affected_ids = failed["eligibleRecordsWithFailingKiller"]
    residual_ids = {
        row["mutationId"]
        for row in taxonomy["residualMisses"]
        if row.get("project") == "spring-core"
    }
    failed_key = next(
        key
        for row in failed["failures"]
        if row["method"] == "standardAnnotationMetadata"
        for key in row["adoptedMap"]["matchingKeys"]
    )

    rows = []
    for mutation_id in affected_ids:
        record = records_by_id[mutation_id]
        killers = sorted(record["killingTests"])
        if failed_key not in killers:
            raise AssertionError(f"failed identity absent from killers: {mutation_id}")
        policies = {}
        for policy in ("base", "constructor", "class"):
            selected = set(selected_sets[record[policy]["selectedSetId"]])
            selected_killers = sorted(selected.intersection(killers))
            policies[policy] = {
                "inclusive": bool(selected_killers),
                "selectedKillingIdentities": selected_killers,
                "failedTestSelected": failed_key in selected,
                "anotherKillerSelected": any(key != failed_key for key in selected_killers),
            }
        rows.append(
            {
                "mutationId": mutation_id,
                "mutatedClass": record["mutatedClass"],
                "mutatedMethod": record["mutatedMethod"],
                "killingIdentityCount": len(killers),
                "killingIdentities": killers,
                "baseInclusive": policies["base"]["inclusive"],
                "amongSpringCoreResidualMisses": mutation_id in residual_ids,
                "policies": policies,
            }
        )

    k_miss = sum(row["amongSpringCoreResidualMisses"] for row in rows)
    k_only = sum(
        row["policies"]["base"]["inclusive"]
        and row["policies"]["base"]["failedTestSelected"]
        and not row["policies"]["base"]["anotherKillerSelected"]
        for row in rows
    )
    k_other = sum(
        row["policies"]["base"]["inclusive"]
        and row["policies"]["base"]["anotherKillerSelected"]
        for row in rows
    )
    if k_miss + k_only + k_other != len(rows):
        raise AssertionError("summary categories do not partition affected records")
    return {
        "schemaVersion": 1,
        "inputs": {
            "failedKillerEvidence": str(FAILED.relative_to(ROOT)),
            "perRecordOutcomes": str(OUTCOMES.relative_to(ROOT)),
            "residualTaxonomy": str(TAXONOMY.relative_to(ROOT)),
        },
        "failedTestCoverageKey": failed_key,
        "records": rows,
        "summary": {
            "affectedRecords": len(rows),
            "springCoreResidualMisses": len(residual_ids),
            "k_miss": k_miss,
            "k_only": k_only,
            "k_other": k_other,
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = generate()
    (OUT / "failed_killer_impact.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    summary = result["summary"]
    print(
        "PASS: "
        f"k_miss={summary['k_miss']}, "
        f"k_only={summary['k_only']}, "
        f"k_other={summary['k_other']}"
    )


if __name__ == "__main__":
    main()
