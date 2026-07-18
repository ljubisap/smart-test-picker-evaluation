#!/usr/bin/env python3
"""
01_generate_coverage_map.py  --  Generate per-test coverage map using Smart Test Picker.

Runs the full test suite with JaCoCo per-test instrumentation and generates
the coverage map JSON file used for test selection evaluation.

Prerequisites:
  - Smart Test Picker Gradle plugin 0.1.0 (commit 70b3984626eb) published to mavenLocal
  - spring-petclinic with Smart Test Picker plugin configured in build.gradle

Usage:
  python3 01_generate_coverage_map.py --project-dir /path/to/spring-petclinic
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, cwd, desc):
    """Run a command and stream output."""
    print(f"\n{'-'*60}")
    print(f"> {desc}")
    print(f"  {' '.join(cmd)}")
    print(f"{'-'*60}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: {desc} failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Generate coverage map for Spring PetClinic")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to spring-petclinic checkout")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Skip running tests (use existing .exec files)")
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    gradlew = project_dir / "gradlew"

    if not gradlew.exists():
        print(f"ERROR: gradlew not found at {gradlew}")
        sys.exit(1)

    if not args.skip_tests:
        run_cmd(
            [str(gradlew), "clean", "test"],
            cwd=project_dir,
            desc="Run tests with JaCoCo per-test instrumentation"
        )

    run_cmd(
        [str(gradlew), "generateSmartReports"],
        cwd=project_dir,
        desc="Generate per-test XML reports from .exec files"
    )

    run_cmd(
        [str(gradlew), "generateTestCoverageJson"],
        cwd=project_dir,
        desc="Generate coverage map JSON from XML reports"
    )

    coverage_map = project_dir / "build" / "test-coverage-map.json"
    if coverage_map.exists():
        print(f"\nOK Coverage map generated: {coverage_map}")
        print(f"  Size: {coverage_map.stat().st_size / 1024:.1f} KB")
    else:
        print(f"\nERROR: Expected coverage map not found at {coverage_map}")
        sys.exit(1)


if __name__ == "__main__":
    main()
