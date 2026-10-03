#!/usr/bin/env python3
"""One-shot preservation and input hashing for the V14.4 B2 session."""

from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580"
HISTORY = ROOT / "analysis/history/pre_b2_8d4cc49"


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def frozen_files() -> list[Path]:
    config = json.loads((ROOT / "analysis/projects.json").read_text())
    paths = {ROOT / "analysis/projects.json", ROOT / "analysis/oracle_exclusions.json"}
    for project in config["projects"]:
        paths.add(ROOT / project["coverageMap"])
        for pattern in project["pitFiles"]:
            paths.update(ROOT.glob(pattern))
    return sorted(path for path in paths if path.exists())


def main() -> None:
    status = command("git", "status", "--porcelain").splitlines()
    modified = []
    for line in status:
        rel = line[3:]
        path = ROOT / rel
        if line[:2].strip() and path.is_file() and not line.startswith("??"):
            modified.append({"path": rel, "sha256": file_sha(path)})
    preflight = {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "evaluationHead": command("git", "rev-parse", "HEAD").strip(),
        "gitStatusPorcelain": status,
        "modifiedTrackedFiles": modified,
        "stpPin": "2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9",
        "stpTree": "7a61a4933a7f2b6a64aa06e4893ba61c9d26da33",
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")

    inputs = {
        "files": [{"path": str(path.relative_to(ROOT)), "sha256": file_sha(path), "size": path.stat().st_size}
                  for path in frozen_files()]
    }
    inputs["aggregateSha256"] = sha("".join(
        row["path"] + "\0" + row["sha256"] + "\n" for row in inputs["files"]
    ).encode())
    (OUT / "input_hashes_before.json").write_text(json.dumps(inputs, indent=2) + "\n")

    archive_paths = [
        "results/eight-subject-summary.json", "results/failure_taxonomy.json",
        "results/mitigation_comparison.json", "results/selector_equivalence.json",
        "results/final-verification.json", "analysis/v14_4_checks/no_coverage_sensitivity.json",
        "analysis/v14_1_checks/confidence_intervals.json",
    ]
    for project in json.loads((ROOT / "analysis/projects.json").read_text())["projects"]:
        archive_paths.extend([
            f"{project['name']}/results/aggregated/evaluation_summary.json",
            f"{project['name']}/results/aggregated/baseline_comparison.json",
        ])
    manifest = []
    for rel in dict.fromkeys(archive_paths):
        source = ROOT / rel
        if not source.exists():
            continue
        destination = HISTORY / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(source, destination)
        manifest.append({"path": rel, "sha256": file_sha(destination), "size": destination.stat().st_size})
    (HISTORY / "MANIFEST.json").write_text(json.dumps({"files": manifest}, indent=2) + "\n")

    restore = {"baseCommit": BASE, "files": []}
    for rel in ("results/selector_equivalence.json", "results/final-verification.json"):
        current = (ROOT / rel).read_bytes()
        original = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=ROOT)
        diff = "".join(difflib.unified_diff(
            original.decode().splitlines(True), current.decode().splitlines(True),
            fromfile=f"{BASE}:{rel}", tofile=f"working-tree:{rel}",
        ))
        original_json, current_json = json.loads(original), json.loads(current)
        numeric_equal = _strip_text(original_json) == _strip_text(current_json)
        (ROOT / rel).write_bytes(original)
        restore["files"].append({
            "path": rel, "baseSha256": sha(original), "preRestoreSha256": sha(current),
            "postRestoreSha256": file_sha(ROOT / rel), "fullDiff": diff,
            "onlyMetadataOrDescriptionChanged": numeric_equal,
        })
    (OUT / "results_restore.json").write_text(json.dumps(restore, indent=2) + "\n")
    notes = ROOT / "results/HISTORICAL_SCOPE_NOTES.md"
    notes.write_text(
        "# Historical result scope notes\n\n"
        "`selector_equivalence.json` records agreement between the historical Python edge-only evaluator "
        "and a second Python model. It is not Java execution and omits the NO_COVERAGE branch at "
        "STP `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`.\n\n"
        "`final-verification.json` incorporates that historical model-agreement check; its recorded bytes "
        "are preserved, and current production-selector verification is reported separately under "
        "`analysis/v14_4_rederivation/`.\n",
        encoding="utf-8",
    )


def _strip_text(value):
    if isinstance(value, dict):
        return {k: _strip_text(v) for k, v in value.items()
                if k.lower() not in {"description", "scopenote", "interpretation"}}
    if isinstance(value, list):
        return [_strip_text(v) for v in value]
    return value


if __name__ == "__main__":
    main()
