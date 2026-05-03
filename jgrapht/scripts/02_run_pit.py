#!/usr/bin/env python3
"""
02_run_pit.py — Run PIT mutation testing per-class with subpackage-scoped tests.

For each class in sample_classes.json, runs PIT with:
  - targetClasses = single class FQN
  - targetTests = subpackage of that class (scoped, not full suite)
  - fullMutationMatrix = true
  - 10 minute timeout per class

Output: results/per-class/<FQN>/mutations.xml for each class.

Usage:
  python3 02_run_pit.py --project-dir /path/to/jgrapht
  python3 02_run_pit.py --project-dir /path/to/jgrapht --class org.jgrapht.alg.color.GreedyColoring
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TIMEOUT_SECONDS = 600  # 10 minutes per class


def log(msg, log_file=None):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if log_file:
        with open(log_file, "a") as f:
            f.write(line + "\n")


def run_pit_for_class(mvn, project_dir, results_dir, fqn, target_tests, loc, index, total, log_file):
    class_dir = results_dir / "per-class" / fqn
    class_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        mvn,
        "org.pitest:pitest-maven:1.17.4:mutationCoverage",
        "-Ppitest",
        "-pl", "jgrapht-core",
        f"-DtargetClasses={fqn}",
        f"-DtargetTests={target_tests}",
        "-DfullMutationMatrix=true",
        "-Dthreads=4",
        "-DtimestampedReports=false",
        "-DskipFailingTests=true",
        "-DoutputFormats=XML",
    ]

    log(f"[{index}/{total}] Starting: {fqn} (LOC={loc}, tests={target_tests})", log_file)
    start = time.time()

    try:
        result = subprocess.run(
            cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=TIMEOUT_SECONDS
        )
        elapsed = time.time() - start

        (class_dir / "stdout.log").write_text(result.stdout)
        (class_dir / "stderr.log").write_text(result.stderr)

        if result.returncode != 0:
            if "did not pass without mutation" in result.stdout:
                reason = "test failures without mutation"
            elif "No mutations found" in result.stdout:
                reason = "no mutations generated"
            else:
                reason = f"exit code {result.returncode}"
            log(f"[{index}/{total}] FAILED: {fqn} ({elapsed:.0f}s) — {reason}", log_file)
            return {"fqn": fqn, "status": "FAILED", "reason": reason, "elapsed_s": elapsed}

        pit_xml = project_dir / "jgrapht-core" / "target" / "pit-reports" / "mutations.xml"
        if pit_xml.exists():
            shutil.copy2(pit_xml, class_dir / "mutations.xml")
            mutations_count = sum(1 for line in open(pit_xml) if "<mutation " in line)
        else:
            mutations_count = 0

        log(f"[{index}/{total}] DONE: {fqn} ({elapsed:.0f}s, {mutations_count} mutations)", log_file)
        return {"fqn": fqn, "status": "OK", "mutations": mutations_count, "elapsed_s": elapsed}

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        os.system("pkill -f 'pitest.*CoverageMinion' 2>/dev/null")
        os.system("pkill -f 'pitest.*MutationTestMinion' 2>/dev/null")
        log(f"[{index}/{total}] TIMEOUT: {fqn} ({elapsed:.0f}s)", log_file)
        return {"fqn": fqn, "status": "TIMEOUT", "elapsed_s": elapsed}


def main():
    parser = argparse.ArgumentParser(description="Run PIT per-class on sampled classes")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to jgrapht checkout")
    parser.add_argument("--mvn", type=str, default="mvn")
    parser.add_argument("--config", type=Path, default=None,
                        help="Path to sample_classes.json (default: ../config/sample_classes.json)")
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="Output directory (default: ../results/)")
    parser.add_argument("--class", type=str, dest="single_class", default=None,
                        help="Run only this single class FQN")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = args.config or (script_dir.parent / "config" / "sample_classes.json")
    results_dir = args.results_dir or (script_dir.parent / "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(config_path) as f:
        config = json.load(f)

    classes = config["classes"]
    if args.single_class:
        classes = [c for c in classes if c["fqn"] == args.single_class]
        if not classes:
            print(f"ERROR: Class {args.single_class} not found in config")
            sys.exit(1)

    log_file = results_dir / "progress.log"
    log(f"=== PIT Evaluation Run — {len(classes)} classes ===", log_file)

    results = []
    for i, cfg in enumerate(classes):
        r = run_pit_for_class(
            args.mvn, args.project_dir, results_dir,
            cfg["fqn"], cfg["targetTests"], cfg["loc"],
            i + 1, len(classes), log_file
        )
        results.append(r)

        if (i + 1) % 5 == 0:
            ok = sum(1 for r in results if r["status"] == "OK")
            failed = sum(1 for r in results if r["status"] == "FAILED")
            timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
            log(f"--- CHECKPOINT {i+1}/{len(classes)}: OK={ok}, FAILED={failed}, TIMEOUT={timeout} ---", log_file)

    # Write summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "project": config["project"],
        "commit": config["commit"],
        "total_classes": len(classes),
        "ok": sum(1 for r in results if r["status"] == "OK"),
        "failed": sum(1 for r in results if r["status"] == "FAILED"),
        "timeout": sum(1 for r in results if r["status"] == "TIMEOUT"),
        "total_mutations": sum(r.get("mutations", 0) for r in results),
        "total_elapsed_s": sum(r["elapsed_s"] for r in results),
        "results": results,
    }

    summary_path = results_dir / "aggregated" / "pit_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    log(f"=== DONE: OK={summary['ok']}, FAILED={summary['failed']}, "
        f"TIMEOUT={summary['timeout']}, mutations={summary['total_mutations']} ===", log_file)


if __name__ == "__main__":
    main()
