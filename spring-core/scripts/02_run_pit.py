#!/usr/bin/env python3
"""
02_run_pit.py  --  Run PIT mutation testing per-class for Spring Framework spring-core.

Uses PIT command-line execution against the already-compiled classes and test classes
from the Gradle build. Runs PIT per sampled class with fullMutationMatrix=true.

Usage:
  python3 02_run_pit.py --project-dir /path/to/spring-framework-6
  python3 02_run_pit.py --project-dir /path/to/spring-framework-6 --class org.springframework.util.Assert
  python3 02_run_pit.py --project-dir /path/to/spring-framework-6 --results-dir /tmp/fresh-results
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_classpath(project_dir):
    """Get the test runtime classpath from Gradle, comma-separated for PIT CLI."""
    cp_file = project_dir / "spring-core" / "build" / "pit-classpath.txt"
    if cp_file.exists():
        raw = cp_file.read_text().strip()
        # Convert OS path separator to comma for PIT CLI
        return raw.replace(os.pathsep, ",")

    print("Generating classpath from Gradle...")
    task_script = '''
task pitClasspath {
    doLast {
        def cp = sourceSets.test.runtimeClasspath.asPath
        file("build/pit-classpath.txt").text = cp
    }
}
'''
    gradle_file = project_dir / "spring-core" / "spring-core.gradle"
    original = gradle_file.read_text()
    gradle_file.write_text(original + "\n" + task_script)
    try:
        result = subprocess.run(
            ["./gradlew", ":spring-core:pitClasspath"],
            cwd=project_dir, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"ERROR generating classpath: {result.stderr[-500:]}")
            sys.exit(1)
    finally:
        gradle_file.write_text(original)

    raw = cp_file.read_text().strip()
    # Convert OS path separator to comma for PIT CLI
    return raw.replace(os.pathsep, ",")


def find_pitest_jar(maven_repo=None):
    """Find PIT jars and required dependencies in local Maven repo."""
    if maven_repo is None:
        maven_repo = Path.home() / ".m2" / "repository"

    pit_version = "1.17.4"
    junit5_version = "1.2.1"

    pit_jar = maven_repo / "org/pitest/pitest-command-line" / pit_version / f"pitest-command-line-{pit_version}.jar"
    pit_core = maven_repo / "org/pitest/pitest" / pit_version / f"pitest-{pit_version}.jar"
    pit_entry = maven_repo / "org/pitest/pitest-entry" / pit_version / f"pitest-entry-{pit_version}.jar"
    pit_junit5 = maven_repo / "org/pitest/pitest-junit5-plugin" / junit5_version / f"pitest-junit5-plugin-{junit5_version}.jar"
    # PIT runtime dependencies needed for spring-core
    commons_text = maven_repo / "org/apache/commons/commons-text/1.12.0/commons-text-1.12.0.jar"
    commons_lang3 = maven_repo / "org/apache/commons/commons-lang3/3.14.0/commons-lang3-3.14.0.jar"

    jars = [pit_jar, pit_core, pit_entry, pit_junit5, commons_text, commons_lang3]
    missing = [j for j in jars if not j.exists()]

    if missing:
        print("Downloading missing jars via Maven...")
        for jar in missing:
            group_path = str(jar.relative_to(maven_repo)).split("/")
            group_id = ".".join(group_path[:-3])
            artifact_id = group_path[-3]
            version = group_path[-2]
            subprocess.run([
                "mvn", f"org.apache.maven.plugins:maven-dependency-plugin:3.6.1:get",
                f"-Dartifact={group_id}:{artifact_id}:{version}"
            ], capture_output=True)

        missing = [j for j in jars if not j.exists()]
        if missing:
            print(f"ERROR: Cannot find required jars: {[str(j) for j in missing]}")
            sys.exit(1)

    return jars


def run_pit_for_class(target_class, target_tests, project_dir, classpath, pit_jars, results_dir, timeout=600):
    """Run PIT on a single class. Returns (status, mutation_count)."""
    class_dir = results_dir / "per-class" / target_class
    if class_dir.exists():
        shutil.rmtree(class_dir)
    class_dir.mkdir(parents=True)

    pit_classpath = ":".join(str(j) for j in pit_jars)

    src_dir = project_dir / "spring-core" / "src" / "main" / "java"

    cmd = [
        "java", "-cp", pit_classpath,
        "org.pitest.mutationtest.commandline.MutationCoverageReport",
        "--reportDir", str(class_dir),
        "--targetClasses", target_class,
        "--targetTests", target_tests,
        "--sourceDirs", str(src_dir),
        "--classPath", classpath,
        "--outputFormats", "XML",
        "--fullMutationMatrix", "true",
        "--threads", "4",
        "--timeoutConst", "10000",
        "--jvmArgs", "--add-opens=java.base/java.lang=ALL-UNNAMED,--add-opens=java.base/java.util=ALL-UNNAMED",
    ]

    print(f"  Running PIT for {target_class}...")
    start = time.time()

    with open(class_dir / "stdout.log", "w") as stdout_f, \
         open(class_dir / "stderr.log", "w") as stderr_f:
        try:
            result = subprocess.run(
                cmd, stdout=stdout_f, stderr=stderr_f,
                timeout=timeout, cwd=project_dir
            )
            elapsed = time.time() - start

            if result.returncode != 0:
                print(f"    FAILED: exit code {result.returncode} ({elapsed:.0f}s)")
                # Remove any partial/invalid XML
                partial_xml = class_dir / "mutations.xml"
                if partial_xml.exists():
                    partial_xml.unlink()
                return "FAILED", 0

            # Find mutations.xml in output
            mutations_xml = class_dir / "mutations.xml"
            if not mutations_xml.exists():
                for xml_file in class_dir.rglob("mutations.xml"):
                    shutil.copy2(xml_file, mutations_xml)
                    break

            if not mutations_xml.exists():
                print(f"    FAILED: no mutations.xml produced ({elapsed:.0f}s)")
                return "FAILED", 0

            # Validate XML is parseable and targets correct class
            import xml.etree.ElementTree as ET
            try:
                tree = ET.parse(mutations_xml)
            except ET.ParseError as e:
                print(f"    FAILED: invalid mutations.xml ({e}) ({elapsed:.0f}s)")
                mutations_xml.unlink()
                return "FAILED", 0

            mutations = tree.getroot().findall("mutation")
            wrong_class = [m for m in mutations if m.findtext("mutatedClass") != target_class]
            if wrong_class:
                print(f"    FAILED: {len(wrong_class)} mutations for wrong class ({elapsed:.0f}s)")
                return "FAILED", 0

            total = len(mutations)
            killed = len([m for m in mutations if m.get("status") == "KILLED"])
            print(f"    OK: {killed}/{total} killed ({elapsed:.0f}s)")
            return "OK", total

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            print(f"    TIMEOUT after {elapsed:.0f}s")
            # Remove any partial XML from timeout
            partial_xml = class_dir / "mutations.xml"
            if partial_xml.exists():
                partial_xml.unlink()
            return "TIMEOUT", 0


def main():
    parser = argparse.ArgumentParser(description="Run PIT per-class for spring-core")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to spring-framework-6 checkout")
    parser.add_argument("--class", dest="single_class", type=str, default=None,
                        help="Run PIT for a single class only")
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="Output directory (default: ../results/)")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Timeout per class in seconds (default: 600)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "sample_classes.json"
    results_dir = args.results_dir or (script_dir.parent / "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(config_path) as f:
        config = json.load(f)

    if args.single_class:
        classes = [c for c in config["classes"] if c["fqn"] == args.single_class]
        if not classes:
            print(f"ERROR: Class {args.single_class} not in sample_classes.json")
            sys.exit(1)
    else:
        classes = config["classes"]

    # Prerequisite check
    classes_dir = args.project_dir / "spring-core" / "build" / "classes"
    if not classes_dir.exists():
        print("ERROR: Compiled classes not found. Run './gradlew :spring-core:test' first.")
        print(f"  Expected: {classes_dir}")
        sys.exit(1)

    # Get classpath (comma-separated for PIT CLI)
    classpath = get_classpath(args.project_dir)

    # Find PIT jars
    pit_jars = find_pitest_jar()

    print(f"Running PIT for {len(classes)} classes...")
    print(f"Project: {args.project_dir}")
    print(f"Results: {results_dir}")
    print()

    summary = []
    for cls_info in classes:
        fqn = cls_info["fqn"]
        if "targetTests" not in cls_info:
            print(f"ERROR: {fqn} missing required 'targetTests' field in sample_classes.json")
            sys.exit(1)
        target_tests = cls_info["targetTests"]
        status, mutations = run_pit_for_class(
            fqn, target_tests, args.project_dir, classpath, pit_jars, results_dir, args.timeout
        )
        summary.append({"fqn": fqn, "status": status, "mutations": mutations})

    ok = sum(1 for s in summary if s["status"] == "OK")
    failed = sum(1 for s in summary if s["status"] == "FAILED")
    timeout = sum(1 for s in summary if s["status"] == "TIMEOUT")
    total_mutations = sum(s["mutations"] for s in summary)

    print(f"\n{'='*60}")
    print(f"SUMMARY: OK={ok}, FAILED={failed}, TIMEOUT={timeout}")
    print(f"Total mutations: {total_mutations}")

    with open(results_dir / "progress.log", "w") as f:
        for s in summary:
            f.write(f"{s['fqn']}: {s['status']} ({s['mutations']} mutations)\n")

    if failed > 0 or timeout > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
