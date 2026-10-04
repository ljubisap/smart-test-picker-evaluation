#!/usr/bin/env python3
"""Run and retain the complete v15 deterministic verification set."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
COMMANDS = [
    ("unittest", ["python3", "-m", "unittest", "discover", "-s", "analysis/tests"]),
    ("failure_modes", ["python3", "analysis/analyze_failure_modes.py", "--verify"]),
    ("selector_equivalence", ["python3", "analysis/verify_selector_equivalence.py", "--verify"]),
    ("freeze_artifacts", ["python3", "analysis/freeze_artifacts.py", "--verify"]),
    ("recollection", ["python3", "analysis/verify_recollection.py", "--verify"]),
    ("b2", ["python3", "analysis/v14_4_rederivation/verify_b2.py", "--verify"]),
    ("v14_6", ["python3", "analysis/v14_6/verify_v14_6.py", "--verify"]),
    ("v14_7", ["python3", "analysis/v14_7/verify_v14_7.py", "--verify"]),
    ("v14_8", ["python3", "analysis/v14_8/verify_v14_8.py", "--verify"]),
    ("v14_9", ["python3", "analysis/v14_9/verify_v14_9.py", "--verify"]),
    ("v15", ["python3", "analysis/v15/verify_v15.py", "--verify"]),
]


def main() -> None:
    results = []
    for name, command in COMMANDS:
        print(f"{name}: starting", flush=True)
        completed = subprocess.run(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        log = OUT / f"verify_{name}.log"
        log.write_text(completed.stdout, encoding="utf-8")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        row = {
            "name": name, "command": command, "exitCode": completed.returncode,
            "lastNonEmptyLine": lines[-1] if lines else "",
            "log": str(log.relative_to(ROOT)),
        }
        results.append(row)
        print(f"{name}: exit={row['exitCode']}: {row['lastNonEmptyLine']}", flush=True)
    summary = {"schemaVersion": 1, "commands": results,
               "allPassed": all(row["exitCode"] == 0 for row in results)}
    (OUT / "verification_results.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if not summary["allPassed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
