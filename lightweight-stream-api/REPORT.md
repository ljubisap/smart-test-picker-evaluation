# Modern Lightweight-Stream-API follow-up study

## Verdict

`STP_IMPLEMENTATION_DEFECT`

The frozen `stream` mutation study observed no modern RTS miss: STP included at least one PIT-reported killing test for all 419 KILLED mutants. However, complete-project qualification independently exposed a generic STP production-edge filtering defect in the separately published `streamTest` helper module: legitimate production classes under `com.annimon.stream.test` are discarded solely because their FQN contains `.test.`. The frozen STP treatment was not changed. Thus the mutation answer is “no misses in the qualified `stream` scope,” while the complete qualification verdict must record the implementation defect.

## Subject and environment

- Repository: `https://github.com/aNNiMON/Lightweight-Stream-API.git`
- Latest stable release: `v1.2.2`
- Commit/tree: `c781b32690649993ae0dd7c48fca5591974d094c` / `bf32f4d94b2e1374c1fa284a02f16562b16af6ac`
- Java: SapMachine 21.0.12.1+1-LTS
- Native wrapper / evaluation Gradle: 6.7.1 / 8.14
- Native test framework: JUnit 4.13.1
- Mapping execution: JUnit Vintage 5.9.3
- STP commit/tree: `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9` / `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`
- JaCoCo: 0.8.13
- PIT: 1.17.4, built-in JUnit 4 support
- CPU bound: 8

## Native qualification

The 2021 build uses Gradle 6.7.1, Java 6 bytecode targets, removed Gradle JaCoCo APIs, and JaCoCo 0.8.5. Gradle 6.7.1 cannot run cleanly on JDK 21 and Java 6 output is unsupported by the current compiler. An external compatibility setup used Gradle 8.14, source/target 8, disabled native JaCoCo for the uninstrumented oracle, and translated only removed Gradle report/merge configuration APIs. Production and test source were not edited.

The complete native target (`:stream:test` plus `:streamTest:test`) passed:

- raw invocations: 1,428
- normalized logical identities: 1,428
- test classes: 307
- failures/errors/skips: 0/0/0
- framework: annotation-based JUnit 4; no JUnit 3 `TestCase`, parameterized runner, or suite class was found

## STP qualification

JUnit Vintage was required because STP's per-test listener is a JUnit Platform launcher listener. The Vintage run preserved the exact 1,428 native identities and outcomes. Collection produced 1,428 per-test exec artifacts without conversion failure.

For the mutation-study `stream` module:

- runnable identities: 1,318
- mapped identities: 1,235
- explicit `NO_COVERAGE`: 83
- class/method edges: 6,135 / 15,422
- unique covered classes/methods: 357 / 1,291
- map size: 1,830,533 bytes

The same-code warm run consumed both module maps, returned `NONE` for each, selected zero tests, and executed zero tests.

A temporary semantics-preserving change inside `Stream#filter` selected 117 logical tests: 34 method hits plus 83 `NO_COVERAGE`. Actual execution was exactly the same 117 identities, with zero `selectedButNotExecuted`, zero `executedButNotSelected`, and no failures. No legacy class fallback was needed. The edit was reverted.

## Generic implementation defect

`streamTest` is a separately published helper library whose production package is `com.annimon.stream.test`. Its raw JaCoCo XML contains coverage for those production classes, and report generation counted all 110 runnable tests as covered. During coverage-map conversion, `TestClassFilter.isTestClass` removes every class whose FQN contains `.test.`. Consequently all 110 `streamTest` identities are persisted as `NO_COVERAGE`.

The first broken stage is map conversion, not JaCoCo collection or per-test attribution. This is a generic name-based production/test classification defect. It is outside the pre-frozen `stream` mutation scope and therefore does not create or conceal a mutation result reported below. Per task policy, STP was not patched and the treatment identity remained frozen.

## Frozen mutation inputs

The candidate population was 204 production Java files in `stream/src/main/java`. Before PIT or mutation-selection outcomes, 18 concrete implementation classes were frozen across object and primitive streams, collectors, optional/exception helpers, internal buffer/terminal logic, iterator machinery, and object/int/long/double operators. The complete `stream` test namespace (`com.annimon.stream.*`) was frozen as `targetTests` for every class.

All frozen classes remain visible. Seventeen produced valid mutation matrices; abstract `PrimitiveExtIterator` produced no PIT mutations and is explicitly classified `EMPTY`, not dropped.

## PIT oracle and RTS result

- total PIT mutations: 496
- KILLED: 419
- SURVIVED: 61
- TIMED_OUT mutation statuses: 10
- MEMORY_ERROR mutation statuses: 5
- NO_COVERAGE mutation statuses: 1
- failed/timeout class runs: 0/0

Only the 419 KILLED mutants enter the unchanged denominator.

| Selector | Inclusive KILLED | Inclusiveness | Avg. selected | Selection rate | Reduction |
|---|---:|---:|---:|---:|---:|
| STP | 419/419 | 100.00% | 19.19 | 1.46% | 98.54% |
| Constructor-only mitigation | 419/419 | 100.00% | 20.75 | 1.57% | 98.43% |
| Class-level only | 419/419 | 100.00% | 180.00 | 13.66% | 86.34% |
| Random equal-budget, 1,000 trials | descriptive | 18.12% mean (1.22 pp SD; 18.18% analytical) | 19.19 | 1.46% | 98.54% |

Selector-equivalence validation covered all 419 mutation occurrences and 159 unique changed-method cases: 159/159 exact matches and zero mismatches. The shared analysis suite passes 54 tests.

PIT emitted one legitimate whole-class killing identity (`RatingsTest`) alongside ordinary `FQN.method(FQN)` identities. Resolution uses exact BASE `testClassFqn` metadata; it neither guesses a leaf nor changes the oracle.

## Failure analysis

There are zero STP-unsafe KILLED mutants. Accordingly, footprint types A/B/C/MIXED and all requested causal mechanisms have count zero. No modern evidence of early-exception shadowing, pre-test attribution gaps, legacy-test attribution gaps, or a new mechanism appeared in this frozen `stream` sample.

## Historical motivation

The 2017 report only motivates selecting this project. The present study uses release 1.2.2, JDK 21, current STP/JaCoCo, and newly generated PIT mutants. It does not reproduce the historical environment or mutants. The defensible comparison is limited to this: historical unexplained misses were reported, whereas no miss occurred among the 419 modern KILLED observations. We do not claim to have fixed or explained the historical misses.

## Scientific interpretation and limits

The `stream` result independently supports the existing failure model by adding 419 inclusive KILLED observations without a new mutation-level mechanism. It is useful supplemental evidence, but remains outside the canonical eight-subject denominator.

The separate filter defect is also scientifically useful: dependency reliability can fail before selection when build-role inference removes legitimate production edges. It is an implementation classification problem, not a JaCoCo probe-observability mechanism.

Limitations remain: curated rather than exhaustive sampling; PIT faults as proxies; the frozen `targetTests` operational oracle; KILLED-only denominator; evaluator-based single-method simulation rather than 419 Gradle executions; and the unresolved `streamTest` production-package filter defect.

## Reproducibility

Commands are in `commands.md`. The evaluation repository preserves the frozen inputs, compressed map, every per-class matrix and log, every per-mutant selection, baselines, mitigation, equivalence report, and checksums. Canonical eight-subject summaries were not modified.
