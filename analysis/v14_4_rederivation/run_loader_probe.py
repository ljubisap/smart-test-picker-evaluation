#!/usr/bin/env python3
"""Run the exact 2e0954 CoverageMapReader against all frozen maps.

Uses the already-built JAR in the detached exact-commit worktree; it does not
build STP or any subject. All generated evidence stays in this directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
RAW = OUT / "raw"
STP = Path("/Users/D061177/work/issta/joda-time-modern-study/stp")
JAR = STP / "smart-test-picker-common/build/libs/smart-test-picker-common-0.2.0.jar"
GSON = Path("/Users/D061177/.m2/repository/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar")
SCRIPT = OUT / "loader_probe.jsh"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args: str) -> str:
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    head = command("git", "-C", str(STP), "rev-parse", "HEAD")
    tree = command("git", "-C", str(STP), "rev-parse", "HEAD^{tree}")
    if head != "2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9":
        raise SystemExit(f"wrong STP worktree HEAD: {head}")
    java_version = subprocess.run(
        ["java", "-version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True
    ).stdout
    cp = os.pathsep.join((str(JAR), str(GSON)))
    jshell_command = [
        "jshell", "-J-Djava.util.prefs.userRoot=/tmp/stp-v14-4-jshell-prefs",
        "--feedback", "verbose", "--class-path", cp, str(SCRIPT),
    ]
    result = subprocess.run(
        jshell_command,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    (RAW / "loader_probe.stdout.txt").write_text(result.stdout)
    if result.returncode != 0:
        raise SystemExit(f"jshell failed with {result.returncode}; see {RAW / 'loader_probe.stdout.txt'}")
    rows = []
    code_source = None
    for line in result.stdout.splitlines():
        if line.startswith("CODE_SOURCE\t"):
            code_source = line.split("\t", 1)[1]
        if not line.startswith("MAP_RESULT\t"):
            continue
        parts = line.split("\t")
        row = {"project": parts[1], "status": parts[2]}
        if parts[2] == "ACCEPTED":
            row.update({"loadedTestMappings": int(parts[3]), "metadataNonNull": parts[4] == "true", "error": None})
        else:
            row.update({"loadedTestMappings": None, "metadataNonNull": None, "error": "\t".join(parts[3:])})
        rows.append(row)
    if len(rows) != 8:
        raise SystemExit(f"expected 8 probe results, got {len(rows)}")
    if code_source is None:
        raise SystemExit("probe did not report loaded CoverageMapReader code source")
    source_bytes = subprocess.run(
        ["git", "-C", str(STP), "show", head + ":smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapReader.java"],
        check=True, stdout=subprocess.PIPE,
    ).stdout
    with zipfile.ZipFile(JAR) as archive:
        reader_class_bytes = archive.read("com/sap/oss/smarttestpicker/mapper/CoverageMapReader.class")
    evidence = {
        "stpCommit": head,
        "stpTree": tree,
        "worktree": str(STP),
        "worktreeStatus": command("git", "-C", str(STP), "status", "--short"),
        "entryPoint": "com.sap.oss.smarttestpicker.mapper.CoverageMapReader.load(File)",
        "loadedClassCodeSource": code_source,
        "productionCallSite": "TestSelector.java:71-76,277-295 at 2e0954b5b590",
        "adapterUsed": False,
        "buildPerformed": False,
        "artifactNote": "Pre-existing common JAR in the detached exact-commit worktree; no Gradle/Maven build was run for Part I.",
        "javaVersion": java_version.strip(),
        "classpath": [str(JAR), str(GSON)],
        "hashes": {
            "stpCommonJarSha256": sha(JAR),
            "coverageMapReaderClassSha256": hashlib.sha256(reader_class_bytes).hexdigest(),
            "coverageMapReaderSourceAtPinSha256": hashlib.sha256(source_bytes).hexdigest(),
            "gsonJarSha256": sha(GSON),
            "probeSourceSha256": sha(SCRIPT),
        },
        "command": jshell_command,
        "maps": rows,
    }
    (OUT / "map_schema_compatibility.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
