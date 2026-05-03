#!/usr/bin/env python3
"""
00_sample_classes.py — Document and validate the curated class sample.

Methodology Evolution Note
===========================

The 21 classes evaluated in this study were initially intended to be
generated via stratified random sampling:
  - Population: All production classes in commons-lang3 with matching
    test class (ClassNameTest), LOC <= 1200
  - Method: 2 classes per subpackage via rng.sample(candidates, 2)
    with seed=42
  - Excluded subpackages: concurrent (root), exception, function, time

During the verification phase, we attempted to reproduce the committed
sample from scratch using the same seed and filters. The reconstruction
yielded 24 classes (vs 21 original) with different selections in shared
subpackages — indicating that the original sample was generated in a
context (different LOC counting heuristic, different candidate
eligibility state) that we could not retroactively reconstruct.

The commons-lang script's original docstring acknowledged this:
"Re-running may produce slightly different classes if LOC counts
differ (comment counting heuristics)."

Rather than constructing post-hoc LOC heuristics to artificially
reproduce the existing selection (which would constitute a form of
p-hacking), we transparently document the sample as curated_stratified:
a fixed, criterion-validated selection of 1-2 classes per utility
subpackage.

The committed sample remains legitimate: each class meets the
stratification and quality criteria (matching test class, non-trivial
mutable code, LOC <= 1200, representative of its domain).

This script validates the integrity of the committed sample rather
than regenerating it.

Sample selection criteria:
  - 1-2 classes per major subpackage (13 subpackages represented)
  - Matching test class exists (ClassName -> ClassNameTest)
  - Non-trivial mutable code (>=80 LOC, <=1200 LOC)
  - Algorithm/utility implementation prioritized

Note: seed=42 is used in PIT mutation analysis and random baseline
construction; sample selection is curated and deterministic.

Usage:
  python3 00_sample_classes.py --project-dir /path/to/commons-lang --verify
  python3 00_sample_classes.py --project-dir /path/to/commons-lang --output /tmp/test.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_PKG = "org.apache.commons.lang3"
SRC_MAIN = "src/main/java/org/apache/commons/lang3"
SRC_TEST = "src/test/java/org/apache/commons/lang3"
MAX_LOC = 1200

# The 21 classes in the committed sample.
SAMPLED_CLASSES = [
    "org.apache.commons.lang3.arch.Processor",
    "org.apache.commons.lang3.builder.HashCodeBuilder",
    "org.apache.commons.lang3.compare.ComparableUtils",
    "org.apache.commons.lang3.concurrent.locks.LockingVisitors",
    "org.apache.commons.lang3.event.EventListenerSupport",
    "org.apache.commons.lang3.event.EventUtils",
    "org.apache.commons.lang3.math.Fraction",
    "org.apache.commons.lang3.math.IEEE754rUtils",
    "org.apache.commons.lang3.mutable.MutableFloat",
    "org.apache.commons.lang3.mutable.MutableObject",
    "org.apache.commons.lang3.reflect.MethodUtils",
    "org.apache.commons.lang3.reflect.FieldUtils",
    "org.apache.commons.lang3.stream.Streams",
    "org.apache.commons.lang3.stream.LangCollectors",
    "org.apache.commons.lang3.text.FormattableUtils",
    "org.apache.commons.lang3.text.translate.EntityArrays",
    "org.apache.commons.lang3.text.translate.NumericEntityEscaper",
    "org.apache.commons.lang3.tuple.Pair",
    "org.apache.commons.lang3.tuple.ImmutablePair",
    "org.apache.commons.lang3.util.FluentBitSet",
    "org.apache.commons.lang3.util.IterableStringTokenizer",
]


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


def verify_config(project_dir, config_path):
    """Verify that all classes in sample_classes.json exist and meet criteria."""
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

    # Check consistency with hardcoded list
    config_fqns = [c["fqn"] for c in classes]
    if config_fqns != SAMPLED_CLASSES:
        errors.append("  Class list does not match expected SAMPLED_CLASSES")

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


def generate_sample(project_dir, output_path):
    """Generate sample_classes.json from the fixed class list."""
    classes = []
    for fqn in SAMPLED_CLASSES:
        rel_path = fqn.replace(".", "/") + ".java"
        src_file = project_dir / "src/main/java" / rel_path
        if not src_file.exists():
            print(f"ERROR: Source not found: {src_file}")
            sys.exit(1)
        loc = count_loc(src_file)

        # Derive subpkg
        suffix = fqn[len(BASE_PKG) + 1:]  # e.g. "arch.Processor"
        parts = suffix.rsplit(".", 1)
        subpkg = parts[0].replace(".", "/") if len(parts) > 1 else "(root)"

        # targetTests pattern
        target_tests = f"{BASE_PKG}.{parts[0]}.*" if len(parts) > 1 else f"{BASE_PKG}.*"

        classes.append({
            "fqn": fqn,
            "subpkg": subpkg,
            "loc": loc,
            "targetTests": target_tests,
        })

    config = {
        "project": "Apache Commons Lang",
        "version": "3.21.0-SNAPSHOT",
        "repository": "https://github.com/apache/commons-lang",
        "commit": get_git_commit(project_dir),
        "sampling": {
            "strategy": "curated_stratified",
            "rationale": "21 classes selected for representativeness across utility domains in Apache Commons Lang",
            "criteria": [
                "Stratified sampling intent: 1-2 classes per major subpackage",
                "Class has matching test class (ClassName -> ClassNameTest)",
                "Non-trivial mutable code (>=80 LOC)",
                "Maximum LOC cap: 1200",
                "Excludes interfaces and abstract base classes"
            ],
            "subpackage_count": 13,
            "total_sampled": len(classes),
            "methodology_note": "Initially intended as stratified random sampling with seed=42 (max 2 per subpackage, max 1200 LOC). Verification revealed that re-running the script produces a different sample (24 vs 21 classes, different selections) due to LOC heuristic variance across filesystem state. Documented as curated_stratified for methodology transparency. See docs/METHODOLOGY.md."
        },
        "classes": classes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Generated sample: {len(classes)} classes from {len(set(c['subpkg'] for c in classes))} subpackages")
    print(f"Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate/regenerate curated class sample for PIT evaluation")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to commons-lang checkout")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: ../config/sample_classes.json)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing config/sample_classes.json is valid")
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

    generate_sample(project_dir, output_path)


if __name__ == "__main__":
    main()
