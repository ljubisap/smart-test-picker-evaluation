#!/usr/bin/env python3
"""Verify the v15 PIT succeeding-tests audit from frozen inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from succeeding_tests_check import generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    artifact = Path(__file__).with_name("succeeding_tests_check.json")
    expected = json.loads(artifact.read_text(encoding="utf-8"))
    actual = generate()
    if actual != expected:
        raise SystemExit("FAIL: succeeding-tests audit differs from frozen inputs")
    summary = actual["summary"]
    print(
        "PASS: v15 succeeding-tests audit verified; "
        f"f={summary['f']}, u_tests={summary['u_tests']}, "
        f"unresolved={len(actual['unresolvedSucceedingTestIds'])}"
    )


if __name__ == "__main__":
    main()
