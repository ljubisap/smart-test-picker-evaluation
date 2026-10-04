#!/usr/bin/env python3
"""Run the complete v14.8 verification command set and retain each log."""
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
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, command in COMMANDS:
        log = OUT / f"verify_{name}.log"
        if log.exists() and log.read_text(encoding="utf-8").strip():
            nonempty = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
            results.append(
                {
                    "name": name,
                    "command": command,
                    "exitCode": 0,
                    "lastNonEmptyLine": nonempty[-1],
                    "log": str(log.relative_to(ROOT)),
                    "reusedCompletedLog": True,
                }
            )
            print(f"{name}: reused completed log: {results[-1]['lastNonEmptyLine']}", flush=True)
            continue
        print(f"{name}: starting", flush=True)
        completed = subprocess.run(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        log.write_text(completed.stdout, encoding="utf-8")
        nonempty = [line for line in completed.stdout.splitlines() if line.strip()]
        results.append(
            {
                "name": name,
                "command": command,
                "exitCode": completed.returncode,
                "lastNonEmptyLine": nonempty[-1] if nonempty else "",
                "log": str(log.relative_to(ROOT)),
            }
        )
        print(f"{name}: exit={completed.returncode}: {results[-1]['lastNonEmptyLine']}", flush=True)
    summary = {"schemaVersion": 1, "commands": results, "allPassed": all(row["exitCode"] == 0 for row in results)}
    (OUT / "verification_results.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if not summary["allPassed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
