#!/usr/bin/env python3
"""Record hashes for every dirty-tree file after B2 promotion.

The manifest deliberately excludes itself because a file cannot contain its
own stable cryptographic digest.  All paths are relative to the repository.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).with_name("dirty_tree_hashes.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


status = subprocess.check_output(
    ["git", "status", "--porcelain=v1", "-z"], cwd=ROOT
).decode("utf-8", errors="surrogateescape")

paths: set[Path] = set()
items = status.split("\0")
index = 0
while index < len(items) and items[index]:
    item = items[index]
    code = item[:2]
    raw_path = item[3:]
    if "R" in code or "C" in code:
        index += 1
        if index < len(items):
            raw_path = items[index]
    path = ROOT / raw_path
    if path.is_dir():
        paths.update(candidate for candidate in path.rglob("*") if candidate.is_file())
    elif path.is_file():
        paths.add(path)
    index += 1

paths.discard(OUTPUT)
# Include every file changed from the frozen baseline as well as any current
# dirty file. This remains meaningful both immediately before and after commit.
baseline = "8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580"
changed = subprocess.check_output(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", baseline, "HEAD"],
    cwd=ROOT,
).decode("utf-8", errors="surrogateescape").splitlines()
paths.update(ROOT / name for name in changed if (ROOT / name).is_file())
paths.discard(OUTPUT)
records = [
    {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }
    for path in sorted(paths)
]

payload = {
    "repository": str(ROOT),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
    .decode()
    .strip(),
    "selfExcluded": str(OUTPUT.relative_to(ROOT)),
    "fileCount": len(records),
    "files": records,
}
OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
