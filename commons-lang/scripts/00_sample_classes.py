#!/usr/bin/env python3
"""
00_sample_classes.py — Generate stratified random sample of classes for PIT evaluation.

Documents the sampling algorithm used to produce config/sample_classes.json:
  - Strata: Java subpackages under org.apache.commons.lang3
  - 2 classes per subpackage (stratified random)
  - Max LOC: 1200
  - Only classes with a matching test class (ClassName → ClassNameTest)
  - Seed: 42 for reproducibility

NOTE: The authoritative sample is config/sample_classes.json (committed to repo).
This script documents the methodology. Re-running may produce slightly different
classes if LOC counts differ (comment counting heuristics), but the sampling
STRATEGY is identical. Use --verify to check the existing config is valid.

Usage:
  python3 00_sample_classes.py --project-dir /path/to/commons-lang
  python3 00_sample_classes.py --project-dir /path/to/commons-lang --verify
  python3 00_sample_classes.py --project-dir /path/to/commons-lang --output ../config/sample_classes.json
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

SEED = 42
CLASSES_PER_SUBPACKAGE = 2
MAX_LOC = 1200
BASE_PKG = "org.apache.commons.lang3"
SRC_MAIN = "src/main/java/org/apache/commons/lang3"
SRC_TEST = "src/test/java/org/apache/commons/lang3"

# Subpackages to exclude from sampling:
# - doc-files: not code
# - concurrent: root has complex multi-threaded tests (only concurrent/locks included)
# - exception: thin wrapper classes with trivial mutations
# - function: functional interfaces, no meaningful method bodies to mutate
# - time: DateUtils etc. depend on system time, tests are flaky under mutation
EXCLUDED_SUBPKGS = {"doc-files", "concurrent", "exception", "function", "time"}

# Root package excluded — too many utility classes with complex test relationships
INCLUDE_ROOT = False


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


def find_subpackages(project_dir):
    """Find all subpackage directories (including nested like concurrent/locks)."""
    base = project_dir / SRC_MAIN
    subpkgs = {}

    for java_file in base.rglob("*.java"):
        if java_file.name == "package-info.java":
            continue
        rel = java_file.parent.relative_to(base)
        if str(rel) == ".":
            if INCLUDE_ROOT:
                subpkgs.setdefault("root", base)
            continue
        subpkgs[str(rel)] = java_file.parent

    return subpkgs


def find_candidates(project_dir, subpkg_path, subpkg_name):
    """Find eligible classes in a subpackage (has test class, within LOC limit)."""
    test_base = project_dir / SRC_TEST
    candidates = []

    for java_file in sorted(subpkg_path.iterdir()):
        if not java_file.is_file() or not java_file.suffix == ".java":
            continue
        if java_file.name == "package-info.java":
            continue

        class_name = java_file.stem
        loc = count_loc(java_file)

        if loc > MAX_LOC or loc < 20:
            continue

        # Check for matching test class
        test_rel = subpkg_path.relative_to(project_dir / SRC_MAIN)
        test_file = test_base / test_rel / f"{class_name}Test.java"
        if not test_file.exists():
            continue

        # Build FQN
        pkg_parts = str(test_rel).replace("/", ".")
        fqn = f"{BASE_PKG}.{pkg_parts}.{class_name}"

        # Build targetTests pattern (subpackage wildcard)
        target_tests = f"{BASE_PKG}.{pkg_parts}.*"

        candidates.append({
            "fqn": fqn,
            "subpkg": subpkg_name,
            "loc": loc,
            "targetTests": target_tests,
        })

    return candidates


def verify_config(project_dir, config_path):
    """Verify that all classes in sample_classes.json exist and have matching tests."""
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
        src_file = project_dir / "src/main/java" / rel_path
        if not src_file.exists():
            errors.append(f"  MISSING source: {fqn}")
            continue

        # Check test exists
        parts = fqn.rsplit(".", 1)
        test_fqn = parts[0] + "." + parts[1] + "Test"
        test_path = project_dir / "src/test/java" / (test_fqn.replace(".", "/") + ".java")
        if not test_path.exists():
            errors.append(f"  MISSING test: {test_fqn}")

        # Check LOC within limit
        loc = count_loc(src_file)
        if loc > MAX_LOC:
            errors.append(f"  LOC exceeds {MAX_LOC}: {fqn} ({loc})")

    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} issues):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print(f"VERIFICATION PASSED: {len(classes)} classes")
        print(f"  All sources exist, all test classes exist, all LOC <= {MAX_LOC}")
        print(f"  Subpackages: {len(set(c['subpkg'] for c in classes))}")
        print(f"  Commit: {config.get('commit', 'unknown')[:12]}")


def main():
    parser = argparse.ArgumentParser(description="Generate stratified sample of classes for PIT evaluation")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to commons-lang checkout")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: ../config/sample_classes.json)")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--per-subpackage", type=int, default=CLASSES_PER_SUBPACKAGE)
    parser.add_argument("--max-loc", type=int, default=MAX_LOC)
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing config/sample_classes.json is valid (classes exist, have tests)")
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

    rng = random.Random(args.seed)

    # Find all subpackages
    subpkgs = find_subpackages(project_dir)
    print(f"Found {len(subpkgs)} subpackages")

    # Sample from each
    sampled = []
    for subpkg_name in sorted(subpkgs.keys()):
        if subpkg_name in EXCLUDED_SUBPKGS:
            continue

        subpkg_path = subpkgs[subpkg_name]
        candidates = find_candidates(project_dir, subpkg_path, subpkg_name)

        if not candidates:
            print(f"  {subpkg_name}: 0 candidates (skipped)")
            continue

        n = min(args.per_subpackage, len(candidates))
        selected = rng.sample(candidates, n)
        sampled.extend(selected)
        print(f"  {subpkg_name}: {len(candidates)} candidates → {n} sampled")

    # Build output
    config = {
        "project": "Apache Commons Lang",
        "version": get_project_version(project_dir),
        "repository": "https://github.com/apache/commons-lang",
        "commit": get_git_commit(project_dir),
        "sampling": {
            "strategy": "stratified_random",
            "seed": args.seed,
            "classes_per_subpackage": args.per_subpackage,
            "max_loc": args.max_loc,
            "total_sampled": len(sampled),
        },
        "classes": sampled,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"\nSampled {len(sampled)} classes from {len([s for s in subpkgs if s not in EXCLUDED_SUBPKGS])} subpackages")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
