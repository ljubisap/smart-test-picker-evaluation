#!/usr/bin/env python3
"""Verify the RAD1 v14.8 spring-core outcome evidence from frozen inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_checks import generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    expected_path = Path(__file__).with_name("springcore_test_outcomes.json")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = generate()
    if actual != expected:
        raise SystemExit("FAIL: springcore_test_outcomes.json differs from frozen inputs")
    print(
        "PASS: v14.8 evidence verified; "
        f"failures={len(actual['failures'])}; "
        f"eligible killer records={actual['eligibleRecordsWithFailingKillerCount']}"
    )


if __name__ == "__main__":
    main()
