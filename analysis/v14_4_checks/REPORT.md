# RAD1 v14.4 NO_COVERAGE audit — delivery report

## Scope and stop point

Part A and the gated Part B are complete. Part C and Part D were not executed. No manuscript, STP source, evaluator, coverage map, PIT record, canonical result, or pre-existing analysis output was changed. No PIT, coverage collection, build, plugin execution, or selector campaign was run.

## Part A result

The unambiguous A3 classification is **outcome (b)**:

- `TestSelector.java` at `70b3984626eb` has no NO_COVERAGE branch.
- Commit `1151bbd99faf3c172bb42e7625cf4ba828da7b94` (`fix: preserve zero-coverage tests in JaCoCo selection`) introduces it.
- At `2e0954b5b590`, every map entry whose `classes` and `methods` are both null/empty is selected unconditionally. There is no status, engine, identity-type, or inventory qualifier.
- The frozen Python evaluator omits this union in all three selectors.
- The 4,010/4,010 “Java” equivalence check uses a Python semantic model that also omits the branch. It is not actual Java/plugin execution and does not pin the STP commit from which it claims derivation.

The canonical maps represent the requested empty-footprint tests structurally, with empty `classes` and `methods` only: JGraphT 1, Flink 1, Spring Security 23, Quarkus 9. They therefore satisfy the 2e branch exactly.

For the five Spring Security records, the evaluator selects none of the six empty-footprint killing identities. Direct application of the 2e source logic would union all 23 empty entries and would select those killers. This latter statement is a source-code-path inference, not runtime evidence.

The detailed evidence-mapping table is in [NO_COVERAGE_RECONCILIATION.md](NO_COVERAGE_RECONCILIATION.md); structured evidence and exact map entries are in `no_coverage_reconciliation.json`.

## Part B result (non-canonical sensitivity)

The variant adds the exact 2e structural empty-entry condition to the three frozen selectors. Only five records change inclusiveness, all in Spring Security and all currently annotated footprint Type C / `EARLY_EXCEPTION_PROBE_SHADOWING`:

- STP: 330/340 → 335/340.
- Constructor-only: 332/340 → 337/340.
- Class-level: 335/340 → 340/340.
- Mean selected increases by the number of empty entries in each affected subject: JGraphT +1, Flink +1, Spring Security +23, Quarkus +9.
- No inclusiveness count changes outside Spring Security.

Random equal-budget results were recomputed with variant STP budgets, 1,000 trials, seed 42, and the same per-record seed formula as `analysis/evaluate_subject.py:53–84`.

Full precision, 2-decimal renderings, record-level changes, random results, and deltas against `analysis/v14_1_checks/table_precision.json` are in `no_coverage_sensitivity.json` and [NO_COVERAGE_SENSITIVITY.md](NO_COVERAGE_SENSITIVITY.md).

## Deliverable inventory

- `REPORT.md` — this main report
- `NO_COVERAGE_RECONCILIATION.md`
- `no_coverage_reconciliation.json`
- `NO_COVERAGE_SENSITIVITY.md`
- `no_coverage_sensitivity.json`
- `run_v14_4_checks.py`
- `source_excerpts/` — numbered code excerpts, selector history, and exact diff
- `README.md`

## Author decision required

The audit stops before Part C. The author must choose whether the manuscript defines the evaluated policy as the frozen evaluator plus a disclosed production-branch sensitivity, or authorizes a separate re-derivation adopting production 2e behavior.
