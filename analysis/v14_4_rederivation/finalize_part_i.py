#!/usr/bin/env python3
"""Validate Part I invariants and write a reproducibility checksum manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    compatibility = json.loads((OUT / "map_schema_compatibility.json").read_text())
    audit = json.loads((OUT / "method_kind_audit.json").read_text())
    dropped = json.loads((OUT / "dropped_session_estimate.json").read_text())
    fallback = json.loads((OUT / "fallback_status.json").read_text())
    verification = json.loads((OUT / "verification.json").read_text())

    assert len(compatibility["maps"]) == 8
    assert all(row["status"] == "ACCEPTED" for row in compatibility["maps"])
    assert compatibility["adapterUsed"] is False
    assert audit["totalEligible"] == 4010
    assert audit["totalResidualMissesUnder2ePolicy"] == 19
    assert audit["aggregate"]["lambda"] == {
        "eligible": 532,
        "inclusive": 532,
        "among19ResidualMisses": 0,
    }
    assert all(
        not row["identitiesMissingFromMap"]
        and not row["mapIdentitiesMissingFromInventory"]
        and row["droppedZeroPackageSessions"] == 0
        for row in dropped["subjects"].values()
    )
    assert fallback["fallbackTriggered"] is False
    assert verification["passed"] is True

    files = sorted(
        path for path in OUT.rglob("*")
        if path.is_file() and path.name != "CHECKSUMS.sha256"
    )
    lines = [f"{sha256(path)}  {path.relative_to(OUT)}" for path in files]
    (OUT / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PART_I_FINAL_VALIDATION_PASS")


if __name__ == "__main__":
    main()
