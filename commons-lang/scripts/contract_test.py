#!/usr/bin/env python3
"""
contract_test.py -- Verify Python evaluation selector matches production Java selector.

For each of 21 sampled classes, creates a minimal source change (comment insertion),
commits it, runs the production select-tests Maven mojo, and compares its output with
evaluation_core.select_original().

Requires:
  - commons-lang checked out at smart-test-picker-eval branch
  - coverage map in target/test-coverage-map.json (from prior collection)
  - Smart Test Picker 0.1.0 installed in mavenLocal (commit 70b3984626eb)

Usage:
  python3 contract_test.py --project-dir /path/to/commons-lang --mvn /path/to/mvn
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import (
    load_coverage_map, select_original, build_base_to_keys,
    discover_pit_files, load_pit_mutations, resolve_killing_tests,
)


def get_first_killed_mutation(project_name, repo_root, pit_patterns, test_mappings, base_to_keys, target_class):
    """Get the first KILLED mutation for a target class from PIT results."""
    pit_files = discover_pit_files(repo_root, pit_patterns)
    raw_mutations = load_pit_mutations(project_name, repo_root, pit_files)
    resolved = resolve_killing_tests(raw_mutations, test_mappings, base_to_keys)

    for mut in resolved:
        if mut.mutated_class == target_class:
            return mut
    return None


def find_source_file(project_dir, fqn):
    """Find Java source file for a fully qualified class name."""
    rel_path = fqn.replace(".", "/") + ".java"
    src_file = project_dir / "src" / "main" / "java" / rel_path
    if src_file.exists():
        return src_file
    return None


def run_cmd(cmd, cwd, desc, timeout=60):
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"TIMEOUT after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Contract test: Python evaluation selector vs Java production selector"
    )
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to commons-lang checkout (smart-test-picker-eval branch)")
    parser.add_argument("--mvn", type=str, required=True,
                        help="Path to Maven executable")
    parser.add_argument("--coverage-map", type=Path, default=None,
                        help="Coverage map path (default: <project-dir>/target/test-coverage-map.json)")
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    mvn = args.mvn
    coverage_map_path = args.coverage_map or (project_dir / "target" / "test-coverage-map.json")

    # Validate prerequisites
    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}")
        sys.exit(1)
    if not coverage_map_path.exists():
        print(f"ERROR: Coverage map not found: {coverage_map_path}")
        sys.exit(1)

    # Verify clean working tree
    ok, stdout, _ = run_cmd(["git", "status", "--porcelain"], project_dir, "git status")
    if not ok:
        print(f"ERROR: git status failed")
        sys.exit(1)
    if stdout.strip():
        print(f"ERROR: Working tree is dirty:\n{stdout}")
        sys.exit(1)

    # Record original HEAD
    ok, stdout, _ = run_cmd(["git", "rev-parse", "HEAD"], project_dir, "git HEAD")
    if not ok or not stdout.strip():
        print("ERROR: Cannot determine HEAD")
        sys.exit(1)
    original_head = stdout.strip()

    # Load coverage map
    coverage_data = load_coverage_map(coverage_map_path)
    test_mappings = coverage_data["testMappings"]
    base_to_keys = build_base_to_keys(test_mappings)
    map_commit = coverage_data.get("metadata", {}).get("commitId", "unknown")

    # Load sample classes
    sample_path = REPO_ROOT / "commons-lang" / "config" / "sample_classes.json"
    with open(sample_path) as f:
        sample_config = json.load(f)
    target_classes = [c["fqn"] for c in sample_config["classes"]]

    print("Python-Java Contract Test")
    print(f"Project: {project_dir}")
    print(f"Coverage map: {coverage_map_path.name} ({len(test_mappings)} tests, commit={map_commit[:12]})")
    print(f"STP collector: 70b3984626eb")
    print(f"Test cases: {len(target_classes)} (from config/sample_classes.json)")
    print()

    passed = 0
    failed = 0
    infra_failures = 0

    for i, target_class in enumerate(target_classes, 1):
        # Get first killed mutation for this class
        mut = get_first_killed_mutation(
            "commons-lang", REPO_ROOT,
            ["commons-lang/results/per-class/*/mutations.xml"],
            test_mappings, base_to_keys, target_class
        )
        if mut is None:
            short = target_class.split(".")[-1]
            print(f"  [{i:2d}] INFRA_FAILURE {short}: no KILLED mutation found")
            infra_failures += 1
            continue

        short = f"{target_class.split('.')[-1]}#{mut.mutated_method}"
        source_file = find_source_file(project_dir, target_class)
        if source_file is None:
            print(f"  [{i:2d}] INFRA_FAILURE {short}: source file not found")
            infra_failures += 1
            continue

        # Read original content
        original_content = source_file.read_text()

        committed = False
        try:
            # Insert a marker comment at the mutation line
            lines = original_content.splitlines(keepends=True)
            insert_idx = min(mut.line_number, len(lines))
            marker = "        // contract-test-marker: verify selection\n"
            lines.insert(insert_idx, marker)
            source_file.write_text("".join(lines))

            # Stage and commit
            ok, _, stderr = run_cmd(["git", "add", str(source_file)], project_dir, "git add")
            if not ok:
                print(f"  [{i:2d}] INFRA_FAILURE {short}: git add failed")
                infra_failures += 1
                continue

            ok, _, stderr = run_cmd(
                ["git", "commit", "-m", f"contract test: {short}", "--quiet"],
                project_dir, "git commit"
            )
            if not ok:
                print(f"  [{i:2d}] INFRA_FAILURE {short}: git commit failed")
                infra_failures += 1
                continue
            committed = True

            # Delete stale output
            selected_file = project_dir / "target" / "selected-tests.json"
            if selected_file.exists():
                selected_file.unlink()

            # Run select-tests mojo
            ok, _, stderr_mvn = run_cmd(
                [mvn, "com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0:select-tests",
                 "-Psmart-test-picker", "-Drat.skip=true", "-Denforcer.skip=true", "-q"],
                project_dir, "select-tests", timeout=30
            )
            if not ok:
                print(f"  [{i:2d}] INFRA_FAILURE {short}: Maven failed")
                infra_failures += 1
                continue

            # Read Java output
            if not selected_file.exists():
                print(f"  [{i:2d}] INFRA_FAILURE {short}: selected-tests.json not created")
                infra_failures += 1
                continue

            with open(selected_file) as f:
                java_output = json.load(f)

            status = java_output.get("status", "UNKNOWN")
            if status == "FULL_SUITE":
                reason = java_output.get("reason", "unknown")
                print(f"  [{i:2d}] INFRA_FAILURE {short}: FULL_SUITE ({reason})")
                infra_failures += 1
                continue

            if status == "NONE":
                print(f"  [{i:2d}] INFRA_FAILURE {short}: NONE (no changes detected)")
                infra_failures += 1
                continue

            java_selected = set(java_output.get("selectedTests", []))

            # Python selection
            python_selected = select_original(test_mappings, mut.mutated_class, mut.mutated_method)

            # Compare: exact equality on selectedTests
            if java_selected == python_selected:
                print(f"  [{i:2d}] EXACT  {short}: {len(java_selected)} tests")
                passed += 1
            else:
                java_only = sorted(java_selected - python_selected)
                python_only = sorted(python_selected - java_selected)
                print(f"  [{i:2d}] MISMATCH {short}:")
                print(f"         Java-only ({len(java_only)}): {java_only[:3]}")
                print(f"         Python-only ({len(python_only)}): {python_only[:3]}")
                failed += 1

        finally:
            # ALWAYS restore to the exact recorded original HEAD unconditionally.
            # This handles all cases: committed, staged-but-not-committed, or modified.
            run_cmd(["git", "reset", "--hard", original_head], project_dir, "restore original HEAD")

            # Verify clean state (HEAD, index, and working tree)
            ok, current_head, _ = run_cmd(["git", "rev-parse", "HEAD"], project_dir, "check HEAD")
            if current_head.strip() != original_head:
                print(f"  CRITICAL: HEAD is {current_head.strip()}, expected {original_head}")
                infra_failures += 1

            ok, porcelain, _ = run_cmd(["git", "status", "--porcelain"], project_dir, "check clean")
            if porcelain.strip():
                print(f"  CRITICAL: Working tree not clean after restore: {porcelain.strip()}")
                run_cmd(["git", "reset", "--hard", original_head], project_dir, "force clean")
                run_cmd(["git", "clean", "-fd"], project_dir, "remove untracked")

    # Final report
    print()
    print("═" * 60)
    print(f"RESULT: {passed} exact, {failed} mismatch, {infra_failures} infra-failure")
    print()

    if failed == 0 and infra_failures == 0 and passed == len(target_classes):
        print("CONTRACT PASSED: Java production selector ≡ Python evaluation selector")
        print(f"for all {passed} sampled single-method changes.")
    elif failed == 0 and infra_failures > 0:
        print(f"INCOMPLETE: {infra_failures} cases could not be executed.")
        print("Fix infrastructure issues and rerun.")
        sys.exit(1)
    else:
        print(f"CONTRACT FAILED: {failed} semantic mismatches detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
