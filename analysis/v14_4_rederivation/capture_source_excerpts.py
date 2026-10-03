#!/usr/bin/env python3
"""Capture line-numbered source excerpts cited by the Part I report."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "source_excerpts"
STP = Path("/Users/D061177/work/issta/hibernate-orm-stp-qualification/stp-source")


def git_show(commit: str, path: str) -> list[str]:
    text = subprocess.run(
        ["git", "-C", str(STP), "show", f"{commit}:{path}"],
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    return text.splitlines()


def write_excerpt(name: str, lines: list[str], ranges: list[tuple[int, int]]) -> None:
    chunks = []
    for start, end in ranges:
        chunks.extend(f"{number:6d}\t{lines[number - 1]}" for number in range(start, end + 1))
        chunks.append("")
    (OUT / name).write_text("\n".join(chunks))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_excerpt(
        "TestSelector_2e0954_loader_path.txt",
        git_show("2e0954b5b590", "smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/selector/TestSelector.java"),
        [(62, 100), (277, 295)],
    )
    write_excerpt(
        "CoverageMapReader_2e0954.txt",
        git_show("2e0954b5b590", "smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapReader.java"),
        [(44, 80), (88, 155)],
    )
    write_excerpt(
        "CoverageMapper_2e0954_method_keys.txt",
        git_show("2e0954b5b590", "smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapperJaxb.java"),
        [(141, 159)],
    )
    write_excerpt(
        "CoverageMapper_70b398_sessions.txt",
        git_show("70b3984626eb", "smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapperJaxb.java"),
        [(108, 168), (209, 251)],
    )
    evaluation = (ROOT / "analysis/evaluation_core.py").read_text().splitlines()
    write_excerpt("evaluation_core_method_derivation.txt", evaluation, [(210, 225), (412, 423)])
    schema = subprocess.run(
        ["git", "-C", str(STP), "show", "--stat", "--oneline", "0039cd7"],
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    (OUT / "schema_commit_0039cd7.txt").write_text(schema)


if __name__ == "__main__":
    main()
