# Modern Joda-Time follow-up study

## Verdict

`NO_NEW_FAILURES`

On Joda-Time 2.15.0, the frozen modern JaCoCo/STP methodology selected at least one PIT-reported killing test for all 896 KILLED mutants in the pre-result-frozen sample. The study observed no STP false negative and therefore no new causal mechanism. This is a modern supplementary result, not a reproduction or explanation of the individual misses reported in the 2017 work.

## Frozen environment

- Repository: `https://github.com/JodaOrg/joda-time.git`
- Release: `v2.15.0`
- Commit/tree: `5ffcf3c2bce34c95207ef2746229a40a932afeee` / `f602da279eeb50175ef18c8651ad49fed417d3f3`
- Java: SapMachine 21.0.12.1+1-LTS
- Maven: 3.8.6
- Native JUnit/Surefire: 3.8.2 / 2.21.0
- STP commit/tree: `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9` / `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`
- STP JaCoCo: 0.8.13
- PIT: 1.17.4, built-in JUnit 3/4 plugin (no JUnit 5 PIT plugin)
- CPU bound: 8

## Qualification

The unmodified release POM declares Java source/target 1.5, which JDK 21 no longer accepts. External `maven.compiler.source=8` and `maven.compiler.target=8` properties restored a green native build without changing subject source or tests.

The native oracle executed 4,236 raw invocations (4,235 unique logical `(class, method)` identities) in 127 classes, with zero failures, errors, or skips. The one raw/logical difference is a repeated `MainTest#testChronology` identity in the native suite.

STP integration required normal/generic compatibility configuration:

- JUnit Vintage 5.9.3 with JUnit 4.13.2 compatibility runtime, because Vintage does not accept the project's native JUnit 3.8.2 runtime;
- Surefire 3.2.5;
- one fork, because a non-forked Surefire execution cannot load the JaCoCo javaagent;
- explicit `argLine` composition;
- the canonical `smart-test` child profile.

No production or test source was changed. The BASE executed the equivalent 4,236/4,235 population with identical outcomes. It produced 4,235 per-test identities: 4,213 with production coverage and 22 explicit `NO_COVERAGE` identities. Conversion failures were zero. The 24,878,250-byte map contains 96,209 class edges and 285,606 method edges over 221 unique covered classes and 2,954 unique methods.

The zero-change warm run consumed the map, returned `NONE`, and executed zero tests.

## Source-change smoke test

A temporary semantics-preserving edit inside `DateTimeUtils#currentTimeMillis` produced a real Git method diff. STP selected 409 logical identities (387 method-exact plus 22 `NO_COVERAGE`). The Maven execution contract conservatively promoted these JUnit 3 method identities to 59 class fallbacks because the provider cannot express the individual JUnit 3 methods in the canonical child plan. The fresh child executed 2,608 passing tests.

- `selectedButNotExecuted`: 0
- `executedButNotSelected`: 2,199
- explanation: explicit `CLASS_FALLBACK` / `STALE_METHOD_IDENTITY` promotion, not unexplained execution
- failures/errors/skips: 0/0/0

This is an execution-granularity limitation for the JUnit 3 Maven path; it does not alter the mutation evaluator's frozen method-selection semantics. The edit was reverted and the subject worktree is source-clean.

## Frozen sample and PIT oracle

The candidate population comprised 166 production Java files. Before PIT or STP outcomes were inspected, 18 implementation-heavy classes were frozen across root API, chronology, conversion, field, formatting, and time-zone strata. Functional `targetTests` policies were frozen by package at the same point. The freeze is preserved by evaluation-repository commit `ac571de5894f13c9224c6a7434ee3d81ba285f15`.

All 18 class runs completed successfully:

- PIT mutations: 1,241
- KILLED mutations in the measured denominator: 896
- failed classes: 0
- timed-out classes: 0

The evaluator initially failed closed on PIT's standard JUnit 3 identifier form, `FQN.method(FQN)`. A generic identity parser plus two regression tests added support for that representation. This changes neither PIT, STP, the selector, nor any result; it only maps PIT's raw JUnit 3 identifier to the existing logical identity model.

## Results

| Selector | Inclusive KILLED | Inclusiveness | Avg. selected | Selection rate | Reduction |
|---|---:|---:|---:|---:|---:|
| STP | 896/896 | 100.00% | 146.76 | 3.47% | 96.53% |
| Constructor-only mitigation | 896/896 | 100.00% | 157.88 | 3.73% | 96.27% |
| Class-level only | 896/896 | 100.00% | 667.49 | 15.76% | 84.24% |
| Random equal-budget (1,000 trials) | descriptive | 19.51% mean (0.90 pp SD; 19.50% analytical) | 146.76 | 3.47% | 96.53% |

Selector-equivalence verification covered all 896 mutation occurrences and 244 unique `(class, method)` cases: 244/244 exact matches, zero mismatches. The shared analysis suite passes 53 tests.

## Failure analysis

There are no STP-unsafe KILLED mutants, so Type A/B/C/MIXED footprint counts and all causal-mechanism counts are zero. The result supplies no evidence that historical individual Joda-Time misses disappeared for any particular reason; those mutants, versions, and environments were not reproduced.

## Relation to the 2017 motivation

The earlier report motivates selecting Joda-Time as a subject. This study asks a different question on the latest stable release and modern tooling. At the defensible level of comparison, misses were reported historically, while none occurred among the 896 modern KILLED observations sampled here. No mutant-level continuity is claimed, and the result does not explain the historical cases.

## Limits

- The 18-class sample is curated and stratified, not exhaustive.
- PIT mutations approximate faults; only KILLED mutants enter the denominator.
- Killing tests are complete only within each frozen functional `targetTests` scope.
- Mutation evaluation simulates a single changed method through the shared selector; it is not 896 end-to-end Maven executions.
- The JUnit 3 child execution path requires conservative class fallback, so actual execution reduction can be lower than evaluator selection reduction.
- This supplementary result is intentionally excluded from the canonical eight-subject aggregate.

## Reproducibility

Commands are in `commands.md`; frozen manifests and summaries are in `results/`; complete per-mutant selections, raw PIT XML matrices, the compressed coverage map, checksums, and verification output are under `smart-test-picker-evaluation/joda-time/`.
