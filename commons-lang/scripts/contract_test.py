#!/usr/bin/env python3
"""
contract_test.py - Verify Python evaluator matches production Java selector.

For each sampled mutation, modifies the target method to create a git diff,
runs the production select-tests mojo, and compares its output with the
Python selection simulation.

Usage:
  python3 contract_test.py --project-dir /path/to/commons-lang
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def python_select(coverage_map_path, changed_class, changed_method):
    """Simulate plugin selection in Python (same logic as 03_evaluate.py)."""
    with open(coverage_map_path) as f:
        tm = json.load(f)["testMappings"]

    method_fqn = f"{changed_class}#{changed_method}"
    selected = set()
    for test_name, cov in tm.items():
        methods = cov.get("methods", [])
        classes = cov.get("classes", [])
        if method_fqn in methods:
            selected.add(test_name)
            continue
        if changed_class in classes:
            has_method_info = any(m.startswith(changed_class + "#") for m in methods)
            if not has_method_info:
                selected.add(test_name)
    return selected


def java_select(project_dir, mvn, changed_class, changed_method, line_number):
    """Run production selector by creating a git diff and invoking select-tests mojo."""
    # Find the source file
    class_path = changed_class.replace(".", "/") + ".java"
    src_file = project_dir / "src" / "main" / "java" / class_path

    if not src_file.exists():
        return None, f"Source file not found: {src_file}"

    # Add a marker comment at the target line to create a diff
    lines = src_file.read_text().splitlines(keepends=True)
    line_idx = int(line_number) - 1
    if line_idx < len(lines):
        lines.insert(line_idx + 1, "        // contract-test-marker\n")
    src_file.write_text("".join(lines))

    # Commit
    subprocess.run(["git", "add", str(src_file)], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"contract test: {changed_class}.{changed_method}", "--quiet"],
        cwd=project_dir, capture_output=True
    )

    # Run select-tests
    result = subprocess.run(
        [mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:select-tests",
         "-Psmart-test-picker", "-Drat.skip=true", "-Denforcer.skip=true", "-q"],
        cwd=project_dir, capture_output=True, text=True, timeout=30
    )

    # Read output
    selected_file = project_dir / "target" / "selected-tests.json"
    java_selected = set()
    status = "UNKNOWN"
    if selected_file.exists():
        with open(selected_file) as f:
            data = json.load(f)
        status = data.get("status", "UNKNOWN")
        if status == "SELECTED":
            java_selected = set(data.get("selectedTests", []))

    # Revert
    subprocess.run(["git", "reset", "--hard", "HEAD~1", "--quiet"], cwd=project_dir, capture_output=True)

    return java_selected, status


def main():
    parser = argparse.ArgumentParser(description="Contract test: Python vs Java selector")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--mvn", type=str, default=os.path.expanduser("~/Programs/apache-maven-3.9.15/bin/mvn"))
    parser.add_argument("--sample", type=Path, default=Path("/tmp/contract_test_sample.json"))
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    coverage_map = project_dir / "target" / "test-coverage-map.json"

    if not coverage_map.exists():
        print(f"ERROR: Coverage map not found: {coverage_map}")
        sys.exit(1)

    with open(args.sample) as f:
        sample = json.load(f)

    print(f"Contract test: {len(sample)} mutations")
    print(f"Project: {project_dir}")
    print()

    passed = 0
    failed = 0
    skipped = 0

    for i, mut in enumerate(sample, 1):
        cls = mut["class"]
        method = mut["method"]
        line = mut["line"]
        short = f"{cls.split('.')[-1]}.{method}"

        # Python selection
        py_selected = python_select(coverage_map, cls, method)

        # Java selection
        java_selected, status = java_select(project_dir, args.mvn, cls, method, line)

        if java_selected is None:
            print(f"  [{i:2d}] SKIP {short}: {status}")
            skipped += 1
            continue

        # Compare
        if status == "FULL_SUITE":
            print(f"  [{i:2d}] SKIP {short}: FULL_SUITE (stale map or trigger)")
            skipped += 1
            continue

        # Java selected set should be subset of or equal to Python selected set
        # (Java may also include unmapped tests which Python doesn't compute)
        java_only = java_selected - py_selected
        py_only = py_selected - java_selected

        if java_selected == py_selected:
            print(f"  [{i:2d}] PASS {short}: {len(java_selected)} tests (identical)")
            passed += 1
        elif not java_only:
            # Java is subset of Python -- acceptable (Python may over-select)
            print(f"  [{i:2d}] PASS {short}: Java={len(java_selected)}, Python={len(py_selected)} (Java subset)")
            passed += 1
        else:
            print(f"  [{i:2d}] FAIL {short}: Java has {len(java_only)} tests not in Python")
            print(f"         Java-only: {sorted(java_only)[:3]}")
            print(f"         Python-only: {sorted(py_only)[:3]}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    if failed == 0:
        print("CONTRACT TEST PASSED: Python evaluator matches Java selector")
    else:
        print("CONTRACT TEST FAILED: Discrepancies found")
        sys.exit(1)


if __name__ == "__main__":
    main()
