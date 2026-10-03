# NO_COVERAGE reconciliation (Part A)

## Decision

**A3 outcome: (b).** The production selector at `2e0954b5b590` contains an unconditional structural NO_COVERAGE branch; the frozen Python evaluator and its Python ‘Java semantic model’ do not. The model is not an actual Java/plugin execution and records no STP commit.

## A1 — selector source

Repository: `/Users/D061177/work/issta/hibernate-orm-stp-qualification/stp-source`. Path: `smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/selector/TestSelector.java`.

- `70b3984626eb`: no empty-footprint branch. Exact method matching is lines 138–163; class-only matching 165–183; zero-hit class escalation 186–229.
- `2e0954b5b590`: lines 142–151 select every map entry for which both `classes` and `methods` are null/empty, then `continue`. There is no status, identity, inventory, or engine qualifier. Exact method matching is 154–179; class-only matching 181–200; zero-hit escalation 202–241.
- Introducing commit: `1151bbd99faf3c172bb42e7625cf4ba828da7b94`, message `fix: preserve zero-coverage tests in JaCoCo selection`.
- Verbatim numbered excerpts and the full path diff are under `source_excerpts/`.

## A2 — canonical map representation

All requested entries are ordinary `testMappings` values with empty `classes` and `methods`; none carries an explicit NO_COVERAGE/status/reason/inventory marker. Counts: JGraphT 1, Flink 1, Spring Security 23, Quarkus 9. This exactly satisfies the structural condition at 2e0954 lines 142–145.

## A3 — evaluator and equivalence model

- `select_original` (`analysis/evaluation_core.py:412–430`) selects method hits, otherwise class hits; no empty union.
- `select_constructor_only_rule` (433–466) starts from original selection and adds only tests with the changed class and constructor methods; no empty union.
- `select_class_level` (469–480) adds only changed-class hits; no empty union.
- `analysis/verify_selector_equivalence.py:3–22,45–84` is a Python semantic model, not Java execution. It has method hits and zero-hit escalation only. `results/final-verification.json` therefore proves 4,010/4,010 equivalence only between two models that both omit NO_COVERAGE, not against production 2e0954.

## A4 — five Spring Security records

This is a source-logic trace. The production column is **inferred from code**, not measured plugin execution.

| Changed method | Empty killer(s) | Evaluator size / killer | 2e source-inferred size / killer |
|---|---:|---:|---:|
| `org.springframework.security.access.hierarchicalroles.RoleHierarchyImpl#withRolePrefix` | 1 | 9 / NO | 32 / YES |
| `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAnyAuthority` | 2 | 65 / NO | 88 / YES |
| `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAnyRole` | 1 | 63 / NO | 86 / YES |
| `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAuthority` | 1 | 14 / NO | 37 / YES |
| `org.springframework.security.authorization.AuthorityAuthorizationManager#hasRole` | 1 | 7 / NO | 30 / YES |

The size increase is 23 for each record because 2e unconditionally unions all 23 Spring Security empty entries; none can already be selected by an edge-based evaluator.

## A5 — manuscript evidence mapping

| Section | Classification | Sentence / reason |
|---|---|---|
| 3.2 | **INCONSISTENT** | Runnable tests represented with an empty footprint (NO_COVERAGE) remain conservative obligations. — True for production 2e0954, but false for the frozen evaluator and its Python Java-semantic model; the sentence does not disclose that split. |
| 3.2 | **CONSISTENT** | The extension collector (2e0954...) retains every successfully collected session with zero production coverage as such an entry; the original collector (70b398...) retained sessions whose report contained only non-production coverage but dropped sessions whose report contained no package. — The canonical maps contain structural empty entries as described, and A2 confirms they have empty classes/methods rather than a policy marker. This sentence describes collection/map retention, not selection. |
| 3.2 | **CONSISTENT** | For the four original subjects, every PIT killing-identity occurrence in the KILLED records resolves to a map key, so no eligible record lost a reported killer through this difference. — A3 resolution is fail-closed: unresolved identities raise; the frozen dataset resolves all admitted records. The claim concerns identity resolution, not selection of empty entries. |
| 3.3 | **INCONSISTENT** | The class-level baseline selects every mapped test with an edge to the mutated class and retains the same NO_COVERAGE obligations; it is a concrete same-map baseline, not a universal upper bound. — analysis/evaluation_core.py:469-480 selects class-edge hits only and never unions empty entries. Production 2e behavior does not repair the manuscript's claim about the evaluated baseline. |
| 9 | **CONSISTENT** | Between them, three commits touch collection or conversion: deterministic map ordering, retention of zero-coverage sessions (Section 3.2), and per-session execution-identity metadata. — Describes collector/conversion history; it does not claim that the evaluator selects the retained empty entries. |
| 9 | **CONSISTENT** | A later source-output ownership fix changed 110 affected identities from false NO_COVERAGE to mapped coverage. — Describes a map-classification correction, not selector handling of genuine empty entries. |

## Boundary

No manuscript, STP source, evaluator, map, PIT record, or canonical result was modified. Part C/D were not executed.
