#!/usr/bin/env python3
"""Run the read-only Part I regression checks and preserve their output."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "exitCode": completed.returncode,
        "output": completed.stdout,
    }


def main() -> None:
    checks = [
        run(["python3", "-m", "unittest", "discover", "-s", "analysis/tests"]),
        run(["python3", "analysis/verify_selector_equivalence.py", "--verify"]),
    ]
    result = {
        "scope": "Part I regression verification only; no builds, PIT, or collection",
        "checks": checks,
        "passed": all(check["exitCode"] == 0 for check in checks),
    }
    (OUT / "verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
