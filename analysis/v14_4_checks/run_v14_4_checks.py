#!/usr/bin/env python3
"""Read-only RAD1 v14.4 NO_COVERAGE reconciliation and frozen-data sensitivity.

Writes only below analysis/v14_4_checks/. It does not mutate canonical inputs.
"""

from __future__ import annotations

import json
import random
import statistics
import subprocess
import sys
import zipfile
from math import comb
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
STP = ROOT.parent / "hibernate-orm-stp-qualification" / "stp-source"
DOCX = ROOT.parent / "rad1-v14-3" / "RAD1_v14_3.docx"
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    build_base_to_keys,
    build_class_to_keys,
    discover_pit_files,
    exclude_non_leaf_oracle_records,
    load_coverage_map,
    load_pit_mutations,
    resolve_killing_tests,
    select_class_level,
    select_constructor_only_rule,
    select_original,
)

OLD = "70b3984626eb"
NEW = "2e0954b5b590"
SELECTOR = "smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/selector/TestSelector.java"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(STP), *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def numbered(text: str) -> list[str]:
    return [f"{i:6d}\t{line}" for i, line in enumerate(text.splitlines(), 1)]


def excerpt(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start - 1:end]) + "\n"


def empty_keys(mappings: dict) -> list[str]:
    return sorted(
        key for key, value in mappings.items()
        if not value.get("classes") and not value.get("methods")
    )


def load_subject(project: dict):
    coverage = load_coverage_map(ROOT / project["coverageMap"])
    mappings = coverage["testMappings"]
    files = discover_pit_files(ROOT, project["pitFiles"])
    raw = load_pit_mutations(project["name"], ROOT, files)
    resolved = resolve_killing_tests(
        raw, mappings, build_base_to_keys(mappings),
        build_class_to_keys(mappings, coverage.get("executionIdentities", {})),
    )
    resolved = exclude_non_leaf_oracle_records(resolved, ROOT, project["name"])
    return coverage, mappings, resolved


def variant(selector, mappings, changed_class, changed_method):
    return selector(mappings, changed_class, changed_method) | set(empty_keys(mappings))


def selector_stats(selector, mappings, mutations):
    sizes, safe = [], 0
    for mutation in mutations:
        selected = variant(selector, mappings, mutation.mutated_class, mutation.mutated_method)
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
        sizes.append(len(selected))
        safe += bool(selected & killing)
    total = len(mutations)
    mean = statistics.mean(sizes) if sizes else 0.0
    pop = len(mappings)
    pct = 100.0 * safe / total if total else 0.0
    fraction = 100.0 * mean / pop if pop else 0.0
    return {
        "inclusive": safe,
        "total": total,
        "inclusivenessPctFullPrecision": pct,
        "inclusivenessPct2dp": round(pct, 2),
        "meanSelectedFullPrecision": mean,
        "meanSelected2dp": round(mean, 2),
        "selectedFractionPctFullPrecision": fraction,
        "selectedFractionPct2dp": round(fraction, 2),
        "reductionPctFullPrecision": 100.0 - fraction,
        "reductionPct2dp": round(100.0 - fraction, 2),
    }


def random_stats(mappings, mutations, trials=1000, seed=42):
    universe = sorted(mappings)
    universe_set = set(universe)
    rows, expected = [], 0.0
    for mutation in mutations:
        budget = len(variant(select_original, mappings, mutation.mutated_class, mutation.mutated_method))
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys} & universe_set
        rows.append((budget, killing))
        if budget and killing:
            k = min(budget, len(universe))
            expected += (
                1.0 if len(universe) - len(killing) < k
                else 1.0 - comb(len(universe) - len(killing), k) / comb(len(universe), k)
            )
    percentages = []
    for trial in range(trials):
        safe = 0
        for index, (budget, killing) in enumerate(rows):
            # Same per-record deterministic seeding as analysis/evaluate_subject.py.
            rng = random.Random(seed + trial * max(1, len(rows)) + index)
            chosen = set(rng.sample(universe, min(budget, len(universe))))
            safe += bool(chosen & killing)
        percentages.append(100.0 * safe / len(rows) if rows else 0.0)
    mean_budget = statistics.mean(x[0] for x in rows) if rows else 0.0
    frac = 100.0 * mean_budget / len(universe) if universe else 0.0
    mc = statistics.mean(percentages) if percentages else 0.0
    std = statistics.pstdev(percentages) if percentages else 0.0
    analytical = 100.0 * expected / len(rows) if rows else 0.0
    return {
        "trials": trials, "seed": seed,
        "seedingFormula": "seed + trial * max(1, record_count) + record_index",
        "monteCarloInclusivenessPctFullPrecision": mc,
        "monteCarloInclusivenessPct2dp": round(mc, 2),
        "monteCarloStdPctFullPrecision": std,
        "monteCarloStdPct2dp": round(std, 2),
        "analyticalInclusivenessPctFullPrecision": analytical,
        "analyticalInclusivenessPct2dp": round(analytical, 2),
        "meanSelectedFullPrecision": mean_budget,
        "meanSelected2dp": round(mean_budget, 2),
        "selectedFractionPctFullPrecision": frac,
        "selectedFractionPct2dp": round(frac, 2),
    }


def docx_paragraphs() -> list[str]:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(DOCX) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return [
        "".join(node.text or "" for node in p.findall(".//w:t", ns))
        for p in root.findall(".//w:p", ns)
    ]


def split_sentences(text: str) -> list[str]:
    # The relevant prose has ordinary sentence boundaries; preserve exact text.
    return [chunk.strip() + "." for chunk in text.split(". ") if chunk.strip()][:-1] + ([text.split(". ")[-1].strip()] if text else [])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    excerpts = OUT / "source_excerpts"
    excerpts.mkdir(exist_ok=True)

    old_source = git("show", f"{OLD}:{SELECTOR}")
    new_source = git("show", f"{NEW}:{SELECTOR}")
    old_lines, new_lines = numbered(old_source), numbered(new_source)
    eval_lines = numbered((ROOT / "analysis/evaluation_core.py").read_text())
    model_lines = numbered((ROOT / "analysis/verify_selector_equivalence.py").read_text())
    (excerpts / "TestSelector_70b398_lines_110_236.txt").write_text(excerpt(old_lines, 110, 236))
    (excerpts / "TestSelector_2e0954_lines_110_252.txt").write_text(excerpt(new_lines, 110, 252))
    (excerpts / "evaluation_core_lines_412_480.txt").write_text(excerpt(eval_lines, 412, 480))
    (excerpts / "verify_selector_equivalence_lines_1_84.txt").write_text(excerpt(model_lines, 1, 84))
    selector_log = git("log", "--oneline", f"{OLD}..{NEW}", "--", str(Path(SELECTOR).parent))
    selector_diff = git("diff", f"{OLD}..{NEW}", "--", SELECTOR)
    (excerpts / "selector_git_log.txt").write_text(selector_log)
    (excerpts / "selector_diff_70b398_to_2e0954.patch").write_text(selector_diff)

    config = json.loads((ROOT / "analysis/projects.json").read_text())
    subject_data = {}
    map_rows = []
    loaded = {}
    for project in config["projects"]:
        coverage, mappings, mutations = load_subject(project)
        loaded[project["name"]] = (coverage, mappings, mutations)
        empties = empty_keys(mappings)
        field_shapes = sorted({tuple(sorted(mappings[key].keys())) for key in empties})
        rows = []
        for key in empties:
            value = mappings[key]
            rows.append({
                "coverageKey": key,
                "entry": value,
                "isMatchedBy2eCondition": not value.get("classes") and not value.get("methods"),
            })
        row = {
            "project": project["name"], "mapPath": project["coverageMap"],
            "emptyFootprintCount": len(empties), "entryFieldShapes": [list(x) for x in field_shapes],
            "explicitNoCoverageMarker": any(
                any(name.lower() in {"status", "reason", "inventory", "nocoverage", "no_coverage"} for name in mappings[k])
                for k in empties
            ),
            "entries": rows,
        }
        subject_data[project["name"]] = row
        if project["name"] in {"jgrapht", "flink", "spring-security", "quarkus"}:
            map_rows.append(row)

    # A4: all five records are recomputed directly, including full killer identities.
    ss_cov, ss_map, ss_mutations = loaded["spring-security"]
    ss_empty = set(empty_keys(ss_map))
    traces = []
    for mutation in ss_mutations:
        killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
        empty_killers = sorted(killing & ss_empty)
        if not empty_killers:
            continue
        current = select_original(ss_map, mutation.mutated_class, mutation.mutated_method)
        production_inferred = current | ss_empty
        traces.append({
            "mutationId": mutation.mutation_id,
            "changedMethod": f"{mutation.mutated_class}#{mutation.mutated_method}",
            "emptyFootprintKillers": empty_killers,
            "mapEntries": {key: ss_map[key] for key in empty_killers},
            "evaluator": {
                "selectedCount": len(current),
                "emptyKillersSelected": sorted(current & set(empty_killers)),
                "killerSelected": bool(current & set(empty_killers)),
                "evidenceType": "computed from frozen map with analysis/evaluation_core.py:412-430",
            },
            "production2eLogic": {
                "selectedCount": len(production_inferred),
                "emptyKillersSelected": sorted(production_inferred & set(empty_killers)),
                "killerSelected": bool(production_inferred & set(empty_killers)),
                "evidenceType": "source-code-path inference only; no plugin execution",
                "basis": f"{NEW}:{SELECTOR}:142-151",
            },
        })

    relevant_paragraphs = [
        p for p in docx_paragraphs()
        if "NO_COVERAGE" in p or "empty footprint" in p or "zero production coverage" in p or "zero-coverage" in p
    ]
    statements = [
        {
            "section": "3.2", "sentence": "Runnable tests represented with an empty footprint (NO_COVERAGE) remain conservative obligations.",
            "classification": "INCONSISTENT",
            "reason": "True for production 2e0954, but false for the frozen evaluator and its Python Java-semantic model; the sentence does not disclose that split.",
        },
        {
            "section": "3.2", "sentence": "The extension collector (2e0954...) retains every successfully collected session with zero production coverage as such an entry; the original collector (70b398...) retained sessions whose report contained only non-production coverage but dropped sessions whose report contained no package.",
            "classification": "CONSISTENT",
            "reason": "The canonical maps contain structural empty entries as described, and A2 confirms they have empty classes/methods rather than a policy marker. This sentence describes collection/map retention, not selection.",
        },
        {
            "section": "3.2", "sentence": "For the four original subjects, every PIT killing-identity occurrence in the KILLED records resolves to a map key, so no eligible record lost a reported killer through this difference.",
            "classification": "CONSISTENT",
            "reason": "A3 resolution is fail-closed: unresolved identities raise; the frozen dataset resolves all admitted records. The claim concerns identity resolution, not selection of empty entries.",
        },
        {
            "section": "3.3", "sentence": "The class-level baseline selects every mapped test with an edge to the mutated class and retains the same NO_COVERAGE obligations; it is a concrete same-map baseline, not a universal upper bound.",
            "classification": "INCONSISTENT",
            "reason": "analysis/evaluation_core.py:469-480 selects class-edge hits only and never unions empty entries. Production 2e behavior does not repair the manuscript's claim about the evaluated baseline.",
        },
        {
            "section": "9", "sentence": "Between them, three commits touch collection or conversion: deterministic map ordering, retention of zero-coverage sessions (Section 3.2), and per-session execution-identity metadata.",
            "classification": "CONSISTENT",
            "reason": "Describes collector/conversion history; it does not claim that the evaluator selects the retained empty entries.",
        },
        {
            "section": "9", "sentence": "A later source-output ownership fix changed 110 affected identities from false NO_COVERAGE to mapped coverage.",
            "classification": "CONSISTENT",
            "reason": "Describes a map-classification correction, not selector handling of genuine empty entries.",
        },
    ]

    reconciliation = {
        "schemaVersion": 1,
        "scope": "Part A only; read-only source/artifact reconciliation",
        "checkpoint": "8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580",
        "a1": {
            "repository": str(STP), "selectorPath": SELECTOR,
            "oldCommit": OLD, "newCommit": NEW,
            "introducingCommit": {
                "commit": "1151bbd99faf3c172bb42e7625cf4ba828da7b94",
                "message": "fix: preserve zero-coverage tests in JaCoCo selection",
            },
            "branchAtOld": "ABSENT",
            "branchAtNew": "PRESENT",
            "conditionAtNew": "(classes == null or empty) AND (methods == null or empty), evaluated for every testMappings entry; no status, identity, inventory, or engine condition",
            "quotedRanges": {
                "old": [
                    {"purpose": "method exact", "lines": "138-163"},
                    {"purpose": "class-level changes", "lines": "165-183"},
                    {"purpose": "zero-hit escalation", "lines": "186-229"},
                ],
                "new": [
                    {"purpose": "NO_COVERAGE", "lines": "142-151"},
                    {"purpose": "method exact", "lines": "154-179"},
                    {"purpose": "class-level changes", "lines": "181-200"},
                    {"purpose": "zero-hit escalation", "lines": "202-241"},
                ],
            },
            "evidenceFiles": [
                "source_excerpts/TestSelector_70b398_lines_110_236.txt",
                "source_excerpts/TestSelector_2e0954_lines_110_252.txt",
                "source_excerpts/selector_git_log.txt",
                "source_excerpts/selector_diff_70b398_to_2e0954.patch",
            ],
        },
        "a2": map_rows,
        "a3": {
            "outcome": "(b)",
            "selectors": {
                "select_original": {"lines": "analysis/evaluation_core.py:412-430", "addsEmptyFootprints": False},
                "select_constructor_only_rule": {"lines": "analysis/evaluation_core.py:433-466", "addsEmptyFootprints": False},
                "select_class_level": {"lines": "analysis/evaluation_core.py:469-480", "addsEmptyFootprints": False},
            },
            "javaModel": {
                "path": "analysis/verify_selector_equivalence.py",
                "lines": "3-22,45-84",
                "implementationLanguage": "Python",
                "actualJavaExecution": False,
                "declaredDerivation": "Unpinned claim of production TestSelector semantics; the script records no STP commit.",
                "effectiveSourceMatch": f"Matches {OLD} method-hit/zero-hit behavior for this input shape and omits the NO_COVERAGE branch introduced by 1151bbd before {NEW}.",
                "addsEmptyFootprints": False,
            },
            "finalVerification": "results/final-verification.json records 4,010/4,010 between evaluator and this model; it is not equivalence to the actual 2e0954 binary/source including NO_COVERAGE.",
        },
        "a4": {
            "records": traces,
            "importantBoundary": "Evaluator results are frozen-data computations. Production 2e results are source-code-path inferences, not evidence of actual plugin execution.",
        },
        "a5": {"sourceDocx": str(DOCX), "matchedParagraphs": relevant_paragraphs, "statements": statements},
    }
    (OUT / "no_coverage_reconciliation.json").write_text(json.dumps(reconciliation, indent=2) + "\n")

    # Part B is allowed because A3 is conclusively outcome (b).
    taxonomy = json.loads((ROOT / "results/failure_taxonomy.json").read_text())
    taxonomy_by_id = {
        row["mutationId"]: row
        for project in taxonomy["byProject"].values()
        for row in project["mutations"]
    }
    old_table = json.loads((ROOT / "analysis/v14_1_checks/table_precision.json").read_text())
    sensitivity_projects, changed = {}, []
    for project in config["projects"]:
        name = project["name"]
        coverage, mappings, mutations = loaded[name]
        selectors = {
            "stpNc": selector_stats(select_original, mappings, mutations),
            "constructorOnlyNc": selector_stats(select_constructor_only_rule, mappings, mutations),
            "classLevelNc": selector_stats(select_class_level, mappings, mutations),
        }
        selectors["randomEqualBudgetNc"] = random_stats(mappings, mutations)
        old_project = old_table["projects"][name]
        key_map = {"stpNc": "stp", "constructorOnlyNc": "constructorOnly", "classLevelNc": "classBaseline"}
        deltas = {}
        for new_key, old_key in key_map.items():
            n, o = selectors[new_key], old_project[old_key]
            deltas[new_key] = {
                "inclusive": n["inclusive"] - o["safe"],
                "meanSelectedFullPrecision": n["meanSelectedFullPrecision"] - o["meanSelectedFullPrecision"],
                "selectedFractionPctFullPrecision": n["selectedFractionPctFullPrecision"] - o["selectedFractionPctFullPrecision"],
                "reductionPctFullPrecision": n["reductionPctFullPrecision"] - o["reductionPctFullPrecision"],
            }
        for mutation in mutations:
            killing = {key for test in mutation.killing_tests for key in test.coverage_keys}
            old_selected = select_original(mappings, mutation.mutated_class, mutation.mutated_method)
            new_selected = variant(select_original, mappings, mutation.mutated_class, mutation.mutated_method)
            if bool(old_selected & killing) != bool(new_selected & killing):
                annotation = taxonomy_by_id.get(mutation.mutation_id)
                changed.append({
                    "project": name, "mutationId": mutation.mutation_id,
                    "mutatedClass": mutation.mutated_class, "mutatedMethod": mutation.mutated_method,
                    "oldInclusive": bool(old_selected & killing), "variantInclusive": bool(new_selected & killing),
                    "oldSelectedCount": len(old_selected), "variantSelectedCount": len(new_selected),
                    "newlySelectedKillingTests": sorted((new_selected - old_selected) & killing),
                    "footprintType": annotation.get("footprintType") if annotation else None,
                    "causalMechanism": annotation.get("causalMechanism") if annotation else None,
                    "annotationFound": annotation is not None,
                })
        sensitivity_projects[name] = {
            "logicalTests": len(mappings), "emptyFootprintTests": len(empty_keys(mappings)),
            "selectors": selectors, "deltaAgainstV14_1TablePrecision": deltas,
        }

    sensitivity = {
        "schemaVersion": 1,
        "status": "NON_CANONICAL_FROZEN_DATA_SENSITIVITY",
        "a3Gate": "PASSED: outcome (b)",
        "variantCondition": "Union every map entry whose classes and methods are both null/missing/empty, matching production 2e0954 TestSelector.java:142-151.",
        "canonicalInputsUnchanged": True,
        "projects": sensitivity_projects,
        "recordsWhoseStpInclusivenessChanges": changed,
        "changedRecordCount": len(changed),
        "randomBaseline": {
            "trials": 1000, "seed": 42,
            "source": "analysis/evaluate_subject.py:53-84",
            "budget": "variant STP selected-set size per record",
        },
    }
    (OUT / "no_coverage_sensitivity.json").write_text(json.dumps(sensitivity, indent=2) + "\n")

    md = [
        "# NO_COVERAGE reconciliation (Part A)", "",
        "## Decision", "",
        "**A3 outcome: (b).** The production selector at `2e0954b5b590` contains an unconditional structural NO_COVERAGE branch; the frozen Python evaluator and its Python ‘Java semantic model’ do not. The model is not an actual Java/plugin execution and records no STP commit.", "",
        "## A1 — selector source", "",
        f"Repository: `{STP}`. Path: `{SELECTOR}`.", "",
        f"- `{OLD}`: no empty-footprint branch. Exact method matching is lines 138–163; class-only matching 165–183; zero-hit class escalation 186–229.",
        f"- `{NEW}`: lines 142–151 select every map entry for which both `classes` and `methods` are null/empty, then `continue`. There is no status, identity, inventory, or engine qualifier. Exact method matching is 154–179; class-only matching 181–200; zero-hit escalation 202–241.",
        "- Introducing commit: `1151bbd99faf3c172bb42e7625cf4ba828da7b94`, message `fix: preserve zero-coverage tests in JaCoCo selection`.",
        "- Verbatim numbered excerpts and the full path diff are under `source_excerpts/`.", "",
        "## A2 — canonical map representation", "",
        "All requested entries are ordinary `testMappings` values with empty `classes` and `methods`; none carries an explicit NO_COVERAGE/status/reason/inventory marker. Counts: JGraphT 1, Flink 1, Spring Security 23, Quarkus 9. This exactly satisfies the structural condition at 2e0954 lines 142–145.", "",
        "## A3 — evaluator and equivalence model", "",
        "- `select_original` (`analysis/evaluation_core.py:412–430`) selects method hits, otherwise class hits; no empty union.",
        "- `select_constructor_only_rule` (433–466) starts from original selection and adds only tests with the changed class and constructor methods; no empty union.",
        "- `select_class_level` (469–480) adds only changed-class hits; no empty union.",
        "- `analysis/verify_selector_equivalence.py:3–22,45–84` is a Python semantic model, not Java execution. It has method hits and zero-hit escalation only. `results/final-verification.json` therefore proves 4,010/4,010 equivalence only between two models that both omit NO_COVERAGE, not against production 2e0954.", "",
        "## A4 — five Spring Security records", "",
        "This is a source-logic trace. The production column is **inferred from code**, not measured plugin execution.", "",
        "| Changed method | Empty killer(s) | Evaluator size / killer | 2e source-inferred size / killer |",
        "|---|---:|---:|---:|",
    ]
    for row in traces:
        md.append(f"| `{row['changedMethod']}` | {len(row['emptyFootprintKillers'])} | {row['evaluator']['selectedCount']} / NO | {row['production2eLogic']['selectedCount']} / YES |")
    md += ["", "The size increase is 23 for each record because 2e unconditionally unions all 23 Spring Security empty entries; none can already be selected by an edge-based evaluator.", "", "## A5 — manuscript evidence mapping", "", "| Section | Classification | Sentence / reason |", "|---|---|---|"]
    for row in statements:
        md.append(f"| {row['section']} | **{row['classification']}** | {row['sentence']} — {row['reason']} |")
    md += ["", "## Boundary", "", "No manuscript, STP source, evaluator, map, PIT record, or canonical result was modified. Part C/D were not executed.", ""]
    (OUT / "NO_COVERAGE_RECONCILIATION.md").write_text("\n".join(md))

    smd = [
        "# NO_COVERAGE sensitivity (Part B)", "",
        "Non-canonical frozen-data analysis. Every variant unions structural empty-footprint entries matching the 2e0954 condition. It does not replace canonical results.", "",
        "| Subject | Empty | STP inclusive | Mean selected | Selected % | Constructor inclusive | Class inclusive | Random MC / analytical |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in sensitivity_projects.items():
        s, c, cl, rnd = row["selectors"]["stpNc"], row["selectors"]["constructorOnlyNc"], row["selectors"]["classLevelNc"], row["selectors"]["randomEqualBudgetNc"]
        smd.append(f"| {name} | {row['emptyFootprintTests']} | {s['inclusive']}/{s['total']} ({s['inclusivenessPct2dp']:.2f}%) | {s['meanSelected2dp']:.2f} | {s['selectedFractionPct2dp']:.2f}% | {c['inclusive']}/{c['total']} | {cl['inclusive']}/{cl['total']} | {rnd['monteCarloInclusivenessPct2dp']:.2f}% / {rnd['analyticalInclusivenessPct2dp']:.2f}% |")
    smd += ["", f"Records changing STP inclusiveness: **{len(changed)}**.", ""]
    for row in changed:
        smd.append(f"- `{row['project']}` `{row['mutatedClass']}#{row['mutatedMethod']}`: {row['oldSelectedCount']} → {row['variantSelectedCount']}; footprint `{row['footprintType']}`, cause `{row['causalMechanism']}`; newly selected killer(s): {', '.join(row['newlySelectedKillingTests'])}.")
    smd += [
        "", "## Delta against v14.1 table precision", "",
        "| Subject | Selector | Δ inclusive | Δ mean selected | Δ selected percentage points | Δ reduction percentage points |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, row in sensitivity_projects.items():
        for selector_name in ("stpNc", "constructorOnlyNc", "classLevelNc"):
            delta = row["deltaAgainstV14_1TablePrecision"][selector_name]
            smd.append(
                f"| {name} | {selector_name} | {delta['inclusive']:+d} | "
                f"{delta['meanSelectedFullPrecision']:+.15g} | "
                f"{delta['selectedFractionPctFullPrecision']:+.15g} | "
                f"{delta['reductionPctFullPrecision']:+.15g} |"
            )
    smd += ["", "Full-precision source values are in `no_coverage_sensitivity.json`. Random baseline: 1,000 trials, seed 42, same per-record seeding formula as `analysis/evaluate_subject.py:53–84`, with variant STP budgets.", ""]
    (OUT / "NO_COVERAGE_SENSITIVITY.md").write_text("\n".join(smd))

    readme = """# v14.4 checks delivery\n\nPart A establishes A3 outcome (b). Part B is a separate, non-canonical sensitivity analysis enabled by that clear outcome. No canonical artifact or manuscript was changed.\n\nFiles:\n- `REPORT.md`\n- `NO_COVERAGE_RECONCILIATION.md` / `no_coverage_reconciliation.json`\n- `NO_COVERAGE_SENSITIVITY.md` / `no_coverage_sensitivity.json`\n- `source_excerpts/`\n- `run_v14_4_checks.py`\n- `CHECKSUMS.sha256`\n"""
    (OUT / "README.md").write_text(readme)


if __name__ == "__main__":
    main()
