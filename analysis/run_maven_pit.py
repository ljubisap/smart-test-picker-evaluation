#!/usr/bin/env python3
"""Run frozen per-class PIT jobs for a Maven subject, sequentially and CPU-bounded."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--module", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--mvn", default="mvn")
    p.add_argument("--maven-repo", type=Path, required=True)
    p.add_argument("--settings", type=Path, default=Path(__file__).resolve().parents[1] / "config/maven-settings.xml")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--class", dest="single")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--cpus", type=int, default=3)
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    classes = [c for c in config["classes"] if not args.single or c["fqn"] == args.single]
    args.results.mkdir(parents=True, exist_ok=True)
    records = []
    for index, item in enumerate(classes, 1):
        out = args.results / "per-class" / item["fqn"]
        if args.resume and (out / "mutations.xml").exists():
            mutations = ET.parse(out / "mutations.xml").getroot().findall("mutation")
            record = {"fqn":item["fqn"], "targetTests":item["targetTests"], "status":"OK",
                      "reason":"reused validated per-class output", "mutations":len(mutations), "elapsedSeconds":0}
            records.append(record); print(f"[{index}/{len(classes)}] {item['fqn']}: REUSED ({len(mutations)})", flush=True)
            continue
        if out.exists(): shutil.rmtree(out)
        out.mkdir(parents=True)
        report = args.module / "target/pit-reports/mutations.xml"
        report.unlink(missing_ok=True)
        cmd = [args.mvn, "-B", "-ntp", "-s", str(args.settings.resolve()), f"-Dmaven.repo.local={args.maven_repo}",
               "org.pitest:pitest-maven:1.17.4:mutationCoverage", "-Pstp-evaluation-pit",
               f"-Dpitest.targetClasses={item['fqn']}", f"-Dpitest.targetTests={item['targetTests']}",
               f"-Dstp.eval.cpus={args.cpus}", "-DfullMutationMatrix=true", f"-Dthreads={args.cpus}", "-DtimestampedReports=false",
               "-DskipTests=false", "-DskipITs", "-Dcheckstyle.skip", "-Drat.skip", "-Denforcer.skip"]
        started = time.time()
        try:
            run = subprocess.run(cmd, cwd=args.module, text=True, capture_output=True, timeout=args.timeout,
                                 env={**__import__('os').environ, 'MAVEN_OPTS':f'-XX:ActiveProcessorCount={args.cpus} -Xmx4g'})
            (out/"stdout.log").write_text(run.stdout); (out/"stderr.log").write_text(run.stderr)
            status, reason, count = "FAILED", f"exit {run.returncode}", 0
            if run.returncode == 0 and report.exists():
                mutations = ET.parse(report).getroot().findall("mutation")
                wrong = [m for m in mutations if m.findtext("mutatedClass") != item["fqn"]]
                if wrong: reason = f"{len(wrong)} wrong-class mutations"
                else:
                    shutil.copy2(report, out/"mutations.xml")
                    status, reason, count = "OK", None, len(mutations)
        except subprocess.TimeoutExpired as exc:
            (out/"stdout.log").write_text(exc.stdout or ""); (out/"stderr.log").write_text(exc.stderr or "")
            status, reason, count = "TIMEOUT", f"{args.timeout}s", 0
        record = {"fqn":item["fqn"], "targetTests":item["targetTests"], "status":status,
                  "reason":reason, "mutations":count, "elapsedSeconds":round(time.time()-started, 2)}
        records.append(record); print(f"[{index}/{len(classes)}] {item['fqn']}: {status} ({count})", flush=True)
    summary={"project":config["project"], "classes":records, "ok":sum(r["status"]=="OK" for r in records),
             "failed":sum(r["status"]=="FAILED" for r in records), "timeout":sum(r["status"]=="TIMEOUT" for r in records),
             "totalMutations":sum(r["mutations"] for r in records)}
    (args.results/"pit-run-summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
