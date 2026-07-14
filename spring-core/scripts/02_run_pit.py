#!/usr/bin/env python3
"""
02_run_pit.py — Run PIT mutation testing per-class for Spring Framework spring-core.

Uses PIT command-line execution against the already-compiled classes and test classes
from the Gradle build. Runs PIT per sampled class with fullMutationMatrix=true.

Usage:
  python3 02_run_pit.py --project-dir /path/to/spring-framework-6
  python3 02_run_pit.py --project-dir /path/to/spring-framework-6 --class org.springframework.util.Assert
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
    """Get the test runtime classpath from Gradle."""
    cp_file = project_dir / "spring-core" / "build" / "pit-classpath.txt"
    if cp_file.exists():
        return cp_file.read_text().strip()

    print("Generating classpath from Gradle...")
    result = subprocess.run(
        ["./gradlew", ":spring-core:dependencies", "--configuration", "testRuntimeClasspath"],
        cwd=project_dir, capture_output=True, text=True
    )
    # Alternative: use a task to export classpath
    task_script = '''
task pitClasspath {
    doLast {
        def cp = sourceSets.test.runtimeClasspath.asPath
        file("build/pit-classpath.txt").text = cp
    }
}
'''
    # Append task to spring-core.gradle temporarily and run it
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

    return cp_file.read_text().strip()


def find_pitest_jar(maven_repo=None):
    """Find PIT jars in local Maven repo or download them."""
    if maven_repo is None:
        maven_repo = Path.home() / ".m2" / "repository"

    pit_version = "1.17.4"
    junit5_version = "1.2.1"

    pit_jar = maven_repo / "org/pitest/pitest-command-line" / pit_version / f"pitest-command-line-{pit_version}.jar"
    pit_core = maven_repo / "org/pitest/pitest" / pit_version / f"pitest-{pit_version}.jar"
    pit_entry = maven_repo / "org/pitest/pitest-entry" / pit_version / f"pitest-entry-{pit_version}.jar"
    pit_junit5 = maven_repo / "org/pitest/pitest-junit5-plugin" / junit5_version / f"pitest-junit5-plugin-{junit5_version}.jar"

    jars = [pit_jar, pit_core, pit_entry, pit_junit5]
    missing = [j for j in jars if not j.exists()]

    if missing:
        print("Downloading PIT jars via Maven...")
        for jar in missing:
            group_path = str(jar.relative_to(maven_repo)).split("/")
            group_id = ".".join(group_path[:-3])
            artifact_id = group_path[-3]
            version = group_path[-2]
            subprocess.run([
                "mvn", "dependency:copy",
                f"-Dartifact={group_id}:{artifact_id}:{version}",
                f"-DoutputDirectory={jar.parent}",
                "-Dmdep.stripVersion=false"
            ], capture_output=True)

        missing = [j for j in jars if not j.exists()]
        if missing:
            # Try direct download
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
            print(f"ERROR: Cannot find PIT jars: {[str(j) for j in missing]}")
            sys.exit(1)

    return jars


def run_pit_for_class(target_class, project_dir, classpath, pit_jars, results_dir, timeout=600):
    """Run PIT on a single class."""
    class_dir = results_dir / "per-class" / target_class
    class_dir.mkdir(parents=True, exist_ok=True)

    # Determine targetTests — scope to subpackage
    pkg = target_class.rsplit(".", 1)[0]
    # For spring-core, test classes follow the pattern:
    # org.springframework.core.Foo -> test in same or similar package
    target_tests = f"{pkg}.*"

    pit_classpath = ":".join(str(j) for j in pit_jars)

    # Source dirs
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

            # Find mutations.xml in output
            mutations_xml = class_dir / "mutations.xml"
            if not mutations_xml.exists():
                # PIT may put it in a timestamped subdir
                for xml_file in class_dir.rglob("mutations.xml"):
                    shutil.copy2(xml_file, mutations_xml)
                    break

            if mutations_xml.exists():
                import xml.etree.ElementTree as ET
                tree = ET.parse(mutations_xml)
                total = len(tree.getroot().findall("mutation"))
                killed = len([m for m in tree.getroot().findall("mutation") if m.get("status") == "KILLED"])
                print(f"    OK: {killed}/{total} killed ({elapsed:.0f}s)")
                return "OK", total
            else:
                print(f"    WARN: No mutations.xml produced ({elapsed:.0f}s)")
                return "NO_MUTATIONS", 0

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            print(f"    TIMEOUT after {elapsed:.0f}s")
            return "TIMEOUT", 0


def main():
    parser = argparse.ArgumentParser(description="Run PIT per-class for spring-core")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to spring-framework-6 checkout")
    parser.add_argument("--class", dest="single_class", type=str, default=None,
                        help="Run PIT for a single class only")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Timeout per class in seconds (default: 600)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "sample_classes.json"
    results_dir = script_dir.parent / "results"

    with open(config_path) as f:
        config = json.load(f)

    if args.single_class:
        classes = [c for c in config["classes"] if c["fqn"] == args.single_class]
        if not classes:
            print(f"ERROR: Class {args.single_class} not in sample_classes.json")
            sys.exit(1)
    else:
        classes = config["classes"]

    # Get classpath
    classpath = get_classpath(args.project_dir)

    # Find PIT jars
    pit_jars = find_pitest_jar()

    print(f"Running PIT for {len(classes)} classes...")
    print(f"Project: {args.project_dir}")
    print()

    summary = []
    for cls_info in classes:
        fqn = cls_info["fqn"]
        status, mutations = run_pit_for_class(
            fqn, args.project_dir, classpath, pit_jars, results_dir, args.timeout
        )
        summary.append({"fqn": fqn, "status": status, "mutations": mutations})

    # Write progress
    print(f"\n{'='*60}")
    print(f"SUMMARY: {sum(1 for s in summary if s['status']=='OK')}/{len(summary)} OK")
    total_mutations = sum(s["mutations"] for s in summary)
    print(f"Total mutations: {total_mutations}")

    with open(results_dir / "progress.log", "w") as f:
        for s in summary:
            f.write(f"{s['fqn']}: {s['status']} ({s['mutations']} mutations)\n")


if __name__ == "__main__":
    main()
