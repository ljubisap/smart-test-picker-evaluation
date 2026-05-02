#!/usr/bin/env python3
"""
02_run_pit.py — Run PIT mutation testing on Spring PetClinic.

Runs PIT on all production classes at once (small project, ~52 tests, tractable).
Generates mutations.xml with fullMutationMatrix=true.

Prerequisites:
  - spring-petclinic with PIT Gradle plugin configured in build.gradle
  - PIT config: fullMutationMatrix=true, timestampedReports=false

Usage:
  python3 02_run_pit.py --project-dir /path/to/spring-petclinic
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run PIT on Spring PetClinic")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to spring-petclinic checkout")
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="Where to copy results (default: ../results/)")
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    script_dir = Path(__file__).parent
    results_dir = (args.results_dir or (script_dir.parent / "results")).resolve()

    gradlew = project_dir / "gradlew"
    if not gradlew.exists():
        print(f"ERROR: gradlew not found at {gradlew}")
        sys.exit(1)

    # Run PIT
    print(f"\n{'─'*60}")
    print(f"▶ Running PIT mutation testing")
    print(f"  {gradlew} pitest")
    print(f"{'─'*60}")
    result = subprocess.run(
        [str(gradlew), "pitest"],
        cwd=project_dir,
        capture_output=False
    )
    if result.returncode != 0:
        print(f"ERROR: PIT failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    # Locate output
    pit_report_dir = project_dir / "build" / "reports" / "pitest"
    mutations_xml = pit_report_dir / "mutations.xml"

    if not mutations_xml.exists():
        print(f"ERROR: mutations.xml not found at {mutations_xml}")
        sys.exit(1)

    # Copy to results dir
    results_dir.mkdir(parents=True, exist_ok=True)
    dest = results_dir / "mutations.xml"
    shutil.copy2(mutations_xml, dest)
    print(f"\n✓ Copied mutations.xml → {dest}")
    print(f"  Size: {dest.stat().st_size / 1024:.1f} KB")

    # Count mutations
    import xml.etree.ElementTree as ET
    tree = ET.parse(dest)
    total = len(tree.getroot().findall("mutation"))
    killed = len([m for m in tree.getroot().findall("mutation") if m.get("status") == "KILLED"])
    print(f"  Total mutations: {total}")
    print(f"  KILLED: {killed}")


if __name__ == "__main__":
    main()
