#!/usr/bin/env python3
"""
01_generate_coverage_map.py — Generate per-test coverage map using Smart Test Picker.

Runs the full test suite with JaCoCo per-test instrumentation, then generates
XML reports and a unified JSON coverage map.

Prerequisites:
  - Smart Test Picker plugin 0.1.0+ installed in local Maven repo
  - Maven 3.9+ on PATH (or set via --mvn)
  - commons-lang checked out at the correct commit

Usage:
  python3 01_generate_coverage_map.py --project-dir /path/to/commons-lang
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run(cmd, cwd, desc, timeout=1200):
    print(f"[{desc}] Running...")
    start = time.time()
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"[{desc}] FAILED ({elapsed:.0f}s)")
        print(result.stdout[-2000:])
        sys.exit(1)
    print(f"[{desc}] OK ({elapsed:.0f}s)")
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate per-test coverage map for commons-lang")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to commons-lang checkout")
    parser.add_argument("--mvn", type=str, default="mvn",
                        help="Path to Maven executable (default: mvn on PATH)")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Skip test execution (use existing .exec files)")
    args = parser.parse_args()

    project = args.project_dir
    mvn = args.mvn

    if not (project / "pom.xml").exists():
        print(f"ERROR: {project}/pom.xml not found")
        sys.exit(1)

    # Step 1: Run tests with JaCoCo per-test instrumentation
    if not args.skip_tests:
        run([mvn, "test", "-Psmart-test-picker", "-DtestFailureIgnore=true"],
            project, "Test suite with JaCoCo per-test sessions", timeout=1200)

    # Step 2: Generate XML reports from .exec files
    run([mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:generate-reports",
         "-Psmart-test-picker"],
        project, "Generate per-test XML reports", timeout=300)

    # Step 3: Generate coverage map JSON
    run([mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:generate-coverage-map",
         "-Psmart-test-picker"],
        project, "Generate coverage map JSON", timeout=120)

    # Verify
    map_file = project / "target" / "test-coverage-map.json"
    if map_file.exists():
        import json
        with open(map_file) as f:
            data = json.load(f)
        n_tests = len(data["testMappings"])
        commit = data["metadata"]["commitId"][:12]
        print(f"\nSUCCESS: Coverage map generated")
        print(f"  Tests: {n_tests}")
        print(f"  Commit: {commit}")
        print(f"  File: {map_file}")
    else:
        print("ERROR: Coverage map not generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
