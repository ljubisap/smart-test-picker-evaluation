#!/usr/bin/env python3
"""Verify the v14.9 failed-killer impact artifact from frozen inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_checks import generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    artifact = Path(__file__).with_name("failed_killer_impact.json")
    expected = json.loads(artifact.read_text(encoding="utf-8"))
    actual = generate()
    if actual != expected:
        raise SystemExit("FAIL: failed-killer impact differs from frozen inputs")
    summary = actual["summary"]
    print(
        "PASS: v14.9 failed-killer impact verified; "
        f"k_miss={summary['k_miss']}, "
        f"k_only={summary['k_only']}, "
        f"k_other={summary['k_other']}"
    )


if __name__ == "__main__":
    main()
