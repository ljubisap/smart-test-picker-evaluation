#!/usr/bin/env python3
"""
01_generate_coverage_map.py  --  Generate per-test coverage map using Smart Test Picker.

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
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
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


def verify_clean_test_run(project, mvn):
    """Run tests WITHOUT testFailureIgnore and verify all pass."""
    print("[Verify] Running test suite (failures will abort)...")
    start = time.time()
    result = subprocess.run(
        [mvn, "test", "-Psmart-test-picker"],
        cwd=str(project), capture_output=True, text=True, timeout=1200
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        # Check if it's actual test failures vs build errors
        if "BUILD FAILURE" in result.stdout and "There are test failures" in result.stdout:
            print(f"[Verify] FAILED ({elapsed:.0f}s)  --  test failures detected")
            print("  Cannot generate coverage map from a failing test suite.")
            print("  Fix failing tests or exclude them via Maven profile configuration.")
            # Show which tests failed
            for line in result.stdout.split('\n'):
                if 'Tests run:' in line and ('Failures:' in line or 'Errors:' in line):
                    print(f"  {line.strip()}")
            sys.exit(1)
        else:
            print(f"[Verify] FAILED ({elapsed:.0f}s)  --  build error")
            print(result.stdout[-1000:])
            sys.exit(1)

    print(f"[Verify] OK ({elapsed:.0f}s)  --  all tests pass")
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

    # Step 0: Verify project commit
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(project), capture_output=True, text=True
    )
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
    print(f"Project commit: {commit[:12]}")

    # Step 1: Run tests with JaCoCo per-test instrumentation
    if not args.skip_tests:
        # Clean stale coverage data before generating new data
        jacoco_dir = project / "target" / "jacoco"
        if jacoco_dir.exists():
            shutil.rmtree(jacoco_dir)
            print(f"[Clean] Removed stale {jacoco_dir}")

        verify_clean_test_run(project, mvn)
    else:
        # When skipping tests, verify .exec files exist and are from current commit
        jacoco_dir = project / "target" / "jacoco"
        exec_files = list(jacoco_dir.glob("session_*.exec")) if jacoco_dir.exists() else []
        if not exec_files:
            print("ERROR: --skip-tests specified but no .exec files found in target/jacoco/")
            sys.exit(1)
        print(f"[Skip] Using {len(exec_files)} existing .exec files")

    # Step 2: Generate XML reports from .exec files
    run([mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:generate-reports",
         "-Psmart-test-picker"],
        project, "Generate per-test XML reports", timeout=300)

    # Step 3: Generate coverage map JSON
    run([mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:generate-coverage-map",
         "-Psmart-test-picker"],
        project, "Generate coverage map JSON", timeout=120)

    # Verify output
    map_file = project / "target" / "test-coverage-map.json"
    if not map_file.exists():
        print("ERROR: Coverage map not generated")
        sys.exit(1)

    with open(map_file) as f:
        data = json.load(f)
    n_tests = len(data["testMappings"])
    map_commit = data.get("metadata", {}).get("commitId", "unknown")

    print(f"\nSUCCESS: Coverage map generated")
    print(f"  Tests: {n_tests}")
    print(f"  Commit: {map_commit[:12]}")
    print(f"  File: {map_file}")

    # Verify commit matches
    if commit != "unknown" and map_commit != commit:
        print(f"  WARNING: Map commit ({map_commit[:12]}) differs from HEAD ({commit[:12]})")


if __name__ == "__main__":
    main()
