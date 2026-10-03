#!/usr/bin/env python3
"""Extract the retained 21-case real-plugin result without rerunning it."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / "results/contract_test.json"
data = json.loads(source.read_text())
output = {
    "source": source.relative_to(ROOT).as_posix(),
    "status": "FOUND",
    "coverageMapCommit": data["coverageMapCommit"],
    "pluginCommit": data["pluginCommit"],
    "pluginVersion": data["pluginVersion"],
    "totalCases": data["totalCases"],
    "passed": data["passed"],
    "mismatches": data["mismatches"],
    "infraFailures": data["infraFailures"],
    "cases": [
        {
            "caseId": row["caseId"],
            "status": row["status"],
            "selectedCount": row["selectedCount"],
            "selectedSetHash": row["selectedSetHash"],
        }
        for row in data["cases"]
    ],
    "verifyCommand": data["verifyCommand"],
}
(Path(__file__).resolve().parent / "real_plugin_validation.json").write_text(
    json.dumps(output, indent=2) + "\n"
)
