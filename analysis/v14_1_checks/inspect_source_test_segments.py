#!/usr/bin/env python3
"""Static source-tree check for production packages containing a `test` segment."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent

SUBJECTS = {
    "commons-lang": ("8538458e7aeb1455a5942f60fe0b4930da6c5d68", "/Users/D061177/work/issta/finerts-feasibility/subjects-full/apache_commons-lang"),
    "jgrapht": ("093b0c5ea006ba5b1d8b7a0212676bf8850cac6b", "/Users/D061177/work/issta/finerts-feasibility/subjects-corpus/jgrapht"),
    "spring-core": ("25838a334c037b68e614f6b571af03a1f6bfec19", None),
    "petclinic": ("cbb884f01f7fef663fcff256e303d967494a4f8b", "/Users/D061177/work/issta/finerts-feasibility/subjects-corpus/spring-petclinic"),
    "flink": ("c0f8d1a1e09f209885a88f9c19ceb9d9e9870283", "/Users/D061177/work/issta/flink-stp-qualification/subject"),
    "spring-security": ("a825937b8175ee85872c49d9c7fc25eea8cff991", "/Users/D061177/work/issta/spring-security-stp-qualification/subject"),
    "hibernate": ("a95dd44cf654131e984682687cf1b2ec5d3e34cd", "/Users/D061177/work/issta/hibernate-orm-stp-qualification/subject"),
    "quarkus": ("6ce99878508d792f3c2a2a7f9520b086a1c32cab", "/Users/D061177/work/issta/quarkus-stp-qualification/subject"),
}

SCOPE_PREFIXES = {
    "commons-lang": ("src/main/java/",),
    "jgrapht": ("jgrapht-core/src/main/java/",),
    "spring-core": ("spring-core/src/main/java/",),
    "petclinic": ("src/main/java/",),
    "flink": ("flink-runtime/src/main/java/",),
    "spring-security": ("spring-security-core/src/main/java/",),
    "hibernate": ("hibernate-core/src/main/java/",),
    "quarkus": ("independent-projects/arc/processor/src/main/java/",),
}


def inspect(commit: str, checkout: str | None):
    if checkout is None:
        return {"status": "UNKNOWN", "reason": "recorded revision not present in any retained local source checkout", "classes": []}
    root = Path(checkout)
    verify = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", commit + "^{commit}"],
        capture_output=True,
    )
    if verify.returncode:
        return {"status": "UNKNOWN", "reason": "recorded revision absent from configured retained checkout", "classes": []}
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "--name-only", commit],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    java = [path for path in listing if "/src/main/java/" in f"/{path}" and path.endswith(".java")]
    grep = subprocess.run(
        [
            "git", "-C", str(root), "grep", "-n", "-E",
            r"^[[:space:]]*package[[:space:]]+([A-Za-z0-9_]+\.)*test(\.|[[:space:]]*;)",
            commit, "--", ":(glob)**/src/main/java/**/*.java",
        ],
        text=True,
        errors="replace",
        capture_output=True,
    )
    if grep.returncode not in (0, 1):
        raise RuntimeError(grep.stderr)
    classes = []
    for line in grep.stdout.splitlines():
        match = re.match(r"[^:]+:(.*?):\d+:\s*package\s+([\w.]+)\s*;", line)
        if not match:
            continue
        path, package = match.groups()
        if Path(path).name in {"package-info.java", "module-info.java"}:
            continue
        classes.append({"fqn": package + "." + Path(path).stem, "sourcePath": path})
    return {
        "status": "INSPECTED",
        "checkout": str(root),
        "revision": commit,
        "productionJavaFiles": len(java),
        "classes": classes,
        "count": len(classes),
    }


projects = {}
for name, (commit, checkout) in SUBJECTS.items():
    result = inspect(commit, checkout)
    scoped = [
        row for row in result["classes"]
        if any(row["sourcePath"].startswith(prefix) for prefix in SCOPE_PREFIXES[name])
    ]
    result["qualifiedScopePrefixes"] = list(SCOPE_PREFIXES[name])
    result["qualifiedScopeClasses"] = scoped
    result["qualifiedScopeCount"] = len(scoped) if result["status"] == "INSPECTED" else None
    projects[name] = result

output = {
    "provenanceSource": "/Users/D061177/work/issta/rad1-v14-review-ready/RAD1_v14_REVIEW_READY_PROVENANCE.csv",
    "projects": projects,
}
(OUT / "source_test_segment_exposure.json").write_text(json.dumps(output, indent=2) + "\n")
