# Sampling Chronology

Factual reconstruction of target-class list history from git evidence, supplemented
by the author's study-process record.

## Summary

For Commons Lang, JGraphT, and spring-core, the target-class lists
(`config/sample_classes.json`) and their corresponding PIT results and evaluation
summaries were introduced in the **same commit**. For PetClinic, the configured
mutation scope covered all 17 production classes, while `sample_classes.json` records
the 14 classes that yielded at least one killed mutation. No subsequent commit altered
any of these class-list or scope artifacts; only metadata and methodological
documentation were updated later.

## Per-Project Timeline

### Apache Commons Lang

| Event | Commit | Date | Notes |
|-------|--------|------|-------|
| sample_classes.json introduced | `56bfd69` | 2026-05-02 | 21 classes, strategy="stratified_random", PIT results + evaluation in same commit |
| Strategy label → curated_stratified | `f7b5324` | 2026-05-03 | Metadata-only change; class list unchanged |
| First failure taxonomy (cross-project) | `cf0f7df` | 2026-07-15 | 1 unsafe mutation identified and classified |

**Class list changes after introduction: NONE**

### JGraphT

| Event | Commit | Date | Notes |
|-------|--------|------|-------|
| sample_classes.json introduced | `73629d6` | 2026-05-03 | 20 classes, strategy="stratified_random", PIT results + evaluation in same commit |
| Strategy label → curated_stratified | `ecf189b` | 2026-05-03 | Metadata-only change; class list unchanged |
| First failure taxonomy (cross-project) | `cf0f7df` | 2026-07-15 | 1 unsafe mutation identified and classified |

**Class list changes after introduction: NONE**

### Spring Core

| Event | Commit | Date | Notes |
|-------|--------|------|-------|
| sample_classes.json introduced | `bf42058` | 2026-07-14 | 22 classes, PIT results + evaluation in same commit |
| First failure taxonomy (cross-project) | `cf0f7df` | 2026-07-15 | 11 unsafe mutations identified and classified |

**Class list changes after introduction: NONE**

The 22-class list includes four classes that yielded no usable killed-mutation
observations in the final evaluation:
- `SerializableTypeWrapper` — baseline tests do not pass without mutation
- `AbstractResource` — baseline tests do not pass without mutation
- `DataBufferUtils` — PIT execution timed out
- `PathMatchingResourcePatternResolver` — baseline tests do not pass without mutation

These classes remain in `sample_classes.json` but do not contribute killed mutations
to the inclusiveness analysis. Their non-contribution reflects PIT execution feasibility
(baseline test failures or timeout), not selection based on measured RTS outcomes.
This is classified as **TECHNICAL_SETUP** — PIT feasibility, not result-informed.

### Spring PetClinic

| Event | Commit | Date | Notes |
|-------|--------|------|-------|
| sample_classes.json introduced | `d60e7f5` | 2026-05-02 | 14 classes listed (those with killed mutations) |
| First failure taxonomy (cross-project) | `cf0f7df` | 2026-07-15 | 0 unsafe mutations |

**Class list changes after introduction: NONE**

PetClinic was evaluated as a whole-project pilot (not a sampled subset):
- **Configured mutation scope:** all 17 production classes in the project
- **Classes contributing killed mutations:** 14 of 17 (3 classes produced only
  SURVIVED or NO_COVERAGE mutations and therefore do not appear in inclusiveness analysis)

The `sample_classes.json` lists only the 14 classes that contributed at least one killed
mutation. The evaluation scope was defined by the project's production class set, not by
a sampling decision. The 14-class list is a **result of PIT execution** (which classes
yielded killed mutants), not an independent sampling choice.

## Consolidated Table

| Project | Class-list/scope artifact introduced | First result in same commit? | Later class-list changes? | First failure taxonomy | List committed before first taxonomy commit? | Evidence for repository ordering |
|---------|--------------------------------------|------------------------------|--------------------------|----------------------|---------------------------------------------|----------------------------------|
| Commons Lang | `56bfd69` (2026-05-02) | YES | NO | `cf0f7df` (2026-07-15) | YES (74 days earlier) | Strong for repository ordering; insufficient to establish pre-commit selection process |
| JGraphT | `73629d6` (2026-05-03) | YES | NO | `cf0f7df` (2026-07-15) | YES (73 days earlier) | Strong for repository ordering; insufficient to establish pre-commit selection process |
| spring-core | `bf42058` (2026-07-14) | YES | NO | `cf0f7df` (2026-07-15) | YES (1 day earlier) | Strong for repository ordering; insufficient to establish pre-commit selection process |
| PetClinic | `d60e7f5` (2026-05-02) — result-derived list; whole-project scope | YES | NO | `cf0f7df` (2026-07-15) | YES (74 days earlier) | Strong for repository ordering; insufficient to establish pre-commit selection process |

## Change Classification

| Project | Change | Commit | Category | Evidence |
|---------|--------|--------|----------|----------|
| Commons Lang | strategy label to curated_stratified | `f7b5324` | SAMPLING_DESIGN | Commit message: methodology transparency |
| JGraphT | strategy label to curated_stratified | `ecf189b` | SAMPLING_DESIGN | Commit message: methodology transparency |
| spring-core | 4 classes yielded no usable killed-mutation observations | `bf42058` | TECHNICAL_SETUP | 3 baseline-test failures + 1 timeout |
| Commons Lang | Exclusion of `concurrent`, `exception`, `function`, and `time` | `56bfd69` | SAMPLING_DESIGN | Author confirmation: bounded mutation-analysis workload |
| spring-core | Exclusion of `aot`, `asm`, and `cglib` | `bf42058` | SAMPLING_DESIGN | Author confirmation: bounded mutation-analysis workload |

No **RESULT_INFORMED** changes were found **after the initial repository commit**. No
class was ever added or removed from any list after its introduction. The pre-commit
selection process cannot be established from repository evidence alone.

These exclusions were made for computational scope control and were not informed by
mutation inclusiveness or false-negative results.

## What Cannot Be Established From Git Alone

The fundamental limitation: **each project's class list and results were committed
together in a single commit**. Git cannot tell us whether:

1. The class list was definitively fixed before running PIT/evaluation (and the commit
   simply bundles the final list with its first results), OR

2. The class list was iteratively adjusted during the same working session that produced
   the results (with only the final version committed).

**The git history shows no post-result modifications**, but it cannot prove pre-result
freezing for the initial commit.

## Author Confirmation and Final Interpretation

The author confirms that target classes were not selected, added, removed, or
retained based on measured RTS inclusiveness, mutation safety status, or an
observed failure mechanism.

For Commons Lang and JGraphT, the class sets were initially produced under a
stratified-selection design intended to use a fixed random seed. However, the
committed lists cannot be reproduced exactly with the currently preserved
sampling scripts and metadata. Replaying the documented procedure produces a
different 24-class Commons Lang set and matches only 2 of the 20 committed
JGraphT classes. The difference most likely reflects an unpreserved version of
the LOC eligibility heuristic or candidate ordering.

The final committed sets are therefore described as curated stratified samples,
not as reproducible statistical random samples. The committed lists, rather
than the current validation scripts, define the evaluation inputs.

Spring-core used one representative class per eligible subpackage, excluding
infrastructure-oriented packages. PetClinic was evaluated as a whole-project
pilot and did not use target-class sampling.

Once established, the class sets were recorded in the PIT configuration and
remained fixed throughout all subsequent mutation evaluation, RTS
inclusiveness analysis, and failure-taxonomy work.

In particular:

- Commons Lang `FieldUtils` was already included before its Type C false
  negative was identified.
- Spring Core `Assert` and `GenericConversionService` were already included
  before their Type A and Type B cases were identified.
- The Type A, Type B, and Type C taxonomy was defined only during the later
  cross-project failure analysis.
- No class was subsequently added, removed, or retained because of its
  measured result.
- Subpackages and test scopes were restricted solely to keep mutation-analysis
  cost and execution time tractable.

Git history confirms that no committed class list changed after its initial
introduction. Because the lists and their first result artifacts were committed
together, the exact pre-commit execution order cannot be independently
reconstructed and is reported here as part of the study protocol.

## Evaluation Scope Layers

The study uses three distinct scopes that must not be conflated:

1. **Coverage-map scope:** the complete project test suite was executed with the
   Smart Test Picker collector.
   - Commons Lang: 4,692 tests
   - JGraphT: 2,308 tests
   - spring-core: 3,624 tests
   - PetClinic: 52 tests

2. **Mutation-target scope:** PIT mutated only the committed sampled target classes,
   except for PetClinic, where all production classes were targeted.
   - Commons Lang: 21 classes
   - JGraphT: 20 classes
   - spring-core: 22 attempted, 18 with usable results
   - PetClinic: all 17 production classes

3. **PIT test scope:** for Commons Lang, JGraphT, and spring-core, PIT killing tests
   were restricted to tests in the relevant subpackage (`targetTests`). PetClinic
   used its full test suite.

Only mutations reported as KILLED within the configured PIT test scope enter
the inclusiveness evaluation. Killing tests outside the configured scope are
not observed.
