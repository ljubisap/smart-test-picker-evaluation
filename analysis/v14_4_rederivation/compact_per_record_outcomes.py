#!/usr/bin/env python3
"""Losslessly deduplicate selected sets in an existing B2 per-record artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "per_record_outcomes.json"
PROMOTED = HERE.parents[1] / "results" / "b2-per-record-outcomes.json"
PROMOTION_STATUS = HERE / "promotion_status.json"


payload = json.loads(SOURCE.read_text(encoding="utf-8"))
if payload.get("schemaVersion") == "b2-deduplicated-selected-sets-v1":
    compact_payload = payload
else:
    selected_sets: dict[str, list[str]] = {}
    records = []
    for row in payload["records"]:
        compact = {
            key: value
            for key, value in row.items()
            if key not in {"legacy", "base", "constructor", "class"}
        }
        for policy in ("legacy", "base", "constructor", "class"):
            outcome = dict(row[policy])
            selected = outcome.pop("selectedTests")
            canonical = json.dumps(
                selected, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            selected_id = hashlib.sha256(canonical).hexdigest()
            existing = selected_sets.setdefault(selected_id, selected)
            if existing != selected:
                raise RuntimeError(f"SHA-256 collision for {selected_id}")
            outcome["selectedSetId"] = selected_id
            compact[policy] = outcome
        records.append(compact)
    compact_payload = {
        "schemaVersion": "b2-deduplicated-selected-sets-v1",
        "selectedSets": selected_sets,
        "records": records,
    }

rendered = json.dumps(compact_payload, indent=2, ensure_ascii=False) + "\n"
SOURCE.write_text(rendered, encoding="utf-8")
PROMOTED.write_text(rendered, encoding="utf-8")
digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
promotion = json.loads(PROMOTION_STATUS.read_text(encoding="utf-8"))
promotion["promoted"]["results/b2-per-record-outcomes.json"] = digest
PROMOTION_STATUS.write_text(
    json.dumps(promotion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            "records": len(compact_payload["records"]),
            "uniqueSelectedSets": len(compact_payload["selectedSets"]),
            "bytes": len(rendered.encode("utf-8")),
            "sha256": digest,
        }
    )
)
