#!/usr/bin/env python3
"""
00_sample_classes.py — Generate stratified random sample of classes for PIT evaluation.

Documents the sampling algorithm used to produce config/sample_classes.json:
  - Strata: Java subpackages under org.jgrapht (in jgrapht-core module)
  - 1 class per subpackage (stratified random), 20 subpackages selected
  - Only classes with at least 1 test covering them (via coverage map)
  - Seed: 42 for reproducibility

NOTE: The authoritative sample is config/sample_classes.json (committed to repo).
This script documents the methodology. Re-running requires the coverage map
(jgrapht-core/target/test-coverage-map.json) to determine which classes are
covered by tests. Use --verify to check the existing config is valid.

Usage:
  python3 00_sample_classes.py --project-dir /path/to/jgrapht
  python3 00_sample_classes.py --project-dir /path/to/jgrapht --verify
  python3 00_sample_classes.py --project-dir /path/to/jgrapht --output ../config/sample_classes.json
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

SEED = 42
NUM_SUBPACKAGES = 20
MAX_PER_PACKAGE = 3
BASE_PKG = "org.jgrapht"
MODULE = "jgrapht-core"
SRC_MAIN = f"{MODULE}/src/main/java/org/jgrapht"

# Subpackages excluded from sampling:
# - alg.interfaces: pure interfaces, no meaningful method bodies to mutate
# - alg: root alg package contains only legacy classes (StoerWagnerMinimumCut, TransitiveClosure)
EXCLUDED_SUBPKGS = {"alg/interfaces", "alg"}

INCLUDE_ROOT = True


def count_loc(path):
    """Count non-blank, non-comment lines."""
    count = 0
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("//") and not stripped.startswith("/*") and not stripped.startswith("*"):
                    count += 1
    except (OSError, UnicodeDecodeError):
        return 0
    return count


def get_git_commit(project_dir):
    """Get current HEAD commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(project_dir),
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_project_version(project_dir):
    """Extract version from pom.xml."""
    pom = project_dir / "pom.xml"
    if pom.exists():
        import xml.etree.ElementTree as ET
        tree = ET.parse(pom)
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        ver = tree.getroot().find("m:version", ns)
        if ver is not None:
            return ver.text
    return "unknown"


def load_covered_classes(project_dir):
    """Load set of classes that have at least one test covering them (from coverage map)."""
    map_path = project_dir / MODULE / "target" / "test-coverage-map.json"
    if not map_path.exists():
        print(f"ERROR: Coverage map not found: {map_path}")
        print("Run scripts/01_generate_coverage_map.py first.")
        sys.exit(1)

    with open(map_path) as f:
        data = json.load(f)

    covered = set()
    for test_name, cov in data["testMappings"].items():
        for cls in cov.get("classes", []):
            covered.add(cls)
    return covered


def find_subpackages(project_dir):
    """Find all subpackage directories under org.jgrapht in jgrapht-core."""
    base = project_dir / SRC_MAIN
    subpkgs = {}

    for java_file in base.rglob("*.java"):
        if java_file.name in ("package-info.java", "module-info.java"):
            continue
        rel = java_file.parent.relative_to(base)
        if str(rel) == ".":
            if INCLUDE_ROOT:
                subpkgs.setdefault(".", base)
            continue
        subpkgs[str(rel)] = java_file.parent

    return subpkgs


def find_candidates(project_dir, subpkg_path, subpkg_name, covered_classes):
    """Find eligible classes in a subpackage (covered by at least one test)."""
    candidates = []

    for java_file in sorted(subpkg_path.iterdir()):
        if not java_file.is_file() or not java_file.suffix == ".java":
            continue
        if java_file.name in ("package-info.java", "module-info.java"):
            continue

        class_name = java_file.stem
        loc = count_loc(java_file)

        if loc < 20:
            continue

        # Build FQN
        if subpkg_name == ".":
            pkg_parts = ""
            fqn = f"{BASE_PKG}.{class_name}"
        else:
            pkg_parts = subpkg_name.replace("/", ".")
            fqn = f"{BASE_PKG}.{pkg_parts}.{class_name}"

        # Check if class is covered by at least one test
        if fqn not in covered_classes:
            continue

        # Build targetTests pattern (subpackage wildcard)
        if subpkg_name == ".":
            target_tests = f"{BASE_PKG}.*"
        else:
            target_tests = f"{BASE_PKG}.{pkg_parts}.*"

        # Subpkg label for JSON
        subpkg_label = "(root)" if subpkg_name == "." else pkg_parts

        candidates.append({
            "fqn": fqn,
            "subpkg": subpkg_label,
            "loc": loc,
            "targetTests": target_tests,
        })

    return candidates


def verify_config(project_dir, config_path):
    """Verify that all classes in sample_classes.json exist."""
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    classes = config["classes"]
    errors = []

    for c in classes:
        fqn = c["fqn"]
        # Check source exists
        rel_path = fqn.replace(".", "/") + ".java"
        src_file = project_dir / MODULE / "src/main/java" / rel_path
        if not src_file.exists():
            errors.append(f"  MISSING source: {fqn}")
            continue

    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} issues):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print(f"VERIFICATION PASSED: {len(classes)} classes")
        print(f"  All sources exist in {MODULE}")
        print(f"  Subpackages: {len(set(c['subpkg'] for c in classes))}")
        print(f"  Commit: {config.get('commit', 'unknown')[:12]}")


def main():
    parser = argparse.ArgumentParser(description="Generate stratified sample of classes for PIT evaluation")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to jgrapht checkout")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: ../config/sample_classes.json)")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--num-subpackages", type=int, default=NUM_SUBPACKAGES)
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing config/sample_classes.json is valid (classes exist)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_path = args.output or (script_dir.parent / "config" / "sample_classes.json")

    project_dir = args.project_dir
    if not (project_dir / "pom.xml").exists():
        print(f"ERROR: {project_dir}/pom.xml not found")
        sys.exit(1)

    if args.verify:
        verify_config(project_dir, script_dir.parent / "config" / "sample_classes.json")
        return

    # Load coverage map to determine which classes have tests
    covered_classes = load_covered_classes(project_dir)
    print(f"Coverage map: {len(covered_classes)} covered classes")

    rng = random.Random(args.seed)

    # Find all subpackages
    subpkgs = find_subpackages(project_dir)
    print(f"Found {len(subpkgs)} subpackages")

    # Gather candidates per subpackage
    subpkg_candidates = {}
    for subpkg_name in sorted(subpkgs.keys()):
        if subpkg_name in EXCLUDED_SUBPKGS:
            continue
        subpkg_path = subpkgs[subpkg_name]
        candidates = find_candidates(project_dir, subpkg_path, subpkg_name, covered_classes)
        if candidates:
            subpkg_candidates[subpkg_name] = candidates

    print(f"Eligible subpackages: {len(subpkg_candidates)}")

    # Select N subpackages randomly
    eligible_subpkgs = sorted(subpkg_candidates.keys())
    n_select = min(args.num_subpackages, len(eligible_subpkgs))
    selected_subpkgs = rng.sample(eligible_subpkgs, n_select)

    # Sample 1 class per selected subpackage
    sampled = []
    for subpkg_name in sorted(selected_subpkgs):
        candidates = subpkg_candidates[subpkg_name]
        selected = rng.choice(candidates)
        sampled.append(selected)
        pkg_label = selected["subpkg"]
        print(f"  {pkg_label}: {len(candidates)} candidates → {selected['fqn'].split('.')[-1]}")

    # Build output
    config = {
        "project": "JGraphT",
        "version": get_project_version(project_dir),
        "repository": "https://github.com/jgrapht/jgrapht",
        "commit": get_git_commit(project_dir),
        "module": MODULE,
        "sampling": {
            "strategy": "stratified_random",
            "seed": args.seed,
            "max_per_package": MAX_PER_PACKAGE,
            "total_sampled": len(sampled),
        },
        "classes": sampled,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"\nSampled {len(sampled)} classes from {n_select} subpackages")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
