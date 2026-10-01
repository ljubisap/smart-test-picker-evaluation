# Independent-subject evaluation extension

## Outcome

Eight subjects were attempted under the frozen protocol. Five produced a
defensible common PIT/STP data set; three were stopped rather than changing a
frozen tool, JDK, release, or `targetTests` policy after observing results.

| Subject | Status | KILLED | STP inclusive | Inclusiveness | Avg selected | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| Commons Lang | complete | 772 | 771 | 99.87% | 17.0 | 99.64% |
| JGraphT | complete | 517 | 516 | 99.81% | 87.7 | 96.20% |
| spring-core | complete | 454 | 443 | 97.58% | 80.6 | 97.78% |
| PetClinic | complete | 94 | 94 | 100.00% | 9.7 | 81.30% |
| Flink | complete | 349 | 349 | 100.00% | 36.23 | 94.55% |
| Hibernate ORM | PIT oracle blocked | — | — | — | — | — |
| Quarkus Arc | PIT oracle blocked | — | — | — | — | — |
| Spring Security | PIT oracle blocked | — | — | — | — | — |

Across the five completed subjects, STP includes a PIT-reported killing test
for 2,173 of 2,186 KILLED mutants (99.41%). The unchanged constructor-only
mitigation recovers five of the thirteen misses. Flink adds no false negative,
so it adds no new failure type and provides no positive recovery opportunity
for the mitigation.

## Flink

The frozen scheduler scope contains 665 logical tests and 16 structurally
sampled production classes. All 16 classes produced usable PIT output: 681
mutations in total, including 349 KILLED mutations. STP includes at least one
killing test for all 349.

The first PIT execution admitted `*ITCase` tests that are outside the
pre-frozen qualified Surefire unit-test scope. That run was preserved under
`flink/results/pre-scope-correction/`. The canonical run excludes `*ITCase`
and `*ITCaseBase` solely to implement the already-frozen `**/*Test` scope; the
adjudication predates evaluation of STP outcomes and is documented in
`flink/docs/SCOPE_ADJUDICATION.md`.

## Stopped subjects

### Hibernate ORM

The native JDK 25 control passes. PIT 1.17.4 fails in its coverage-generation
minion for both the frozen 932-test-class scope and a single-test diagnostic.
Spring Security exposes the same PIT generation's concrete incompatibility
with JDK 25 class files. The subject was stopped without changing PIT, JDK,
release, or test scope.

### Spring Security

PIT 1.17.4 discovers tests and generates mutations, but its relocated ASM
throws `IllegalArgumentException: Unsupported class file major version 69`
while transforming JDK 25 bytecode. All 22 diagnostic mutants consequently
have `NO_COVERAGE`. This cannot form a killing-test oracle.

### Quarkus

The split-module adapter is functional: an exact Arc test diagnostic generated
101 mutations successfully. The predeclared full Arc scope sends 6,044 test
and generated classes and fails in the PIT minion during Arc bean-destruction
lifecycle. Narrowing to the successful test after observing this result would
violate the frozen `targetTests` policy, so the subject was stopped.

## Scientific interpretation

The requested directly comparable eight-subject result was not attainable
under the frozen versions. Reporting blocked subjects as zero-mutation or
zero-miss projects would bias both denominator and apparent inclusiveness.
Therefore headline aggregation covers only the five subjects with a valid PIT
killing-test oracle. Detailed machine-readable blockers are stored in each
subject's `results/blocked.json`.

The result answers the independent-validation questions only partially:

- Flink independently retains 100% killed-mutant inclusiveness.
- Flink exhibits no Type A/B/C or new observability failure.
- The constructor rule is applied unchanged, but Flink contains no miss to
  recover; this is consistent evidence, not a recovery demonstration.
- No genuinely new JaCoCo failure type appears in the completed new subject.

PIT mutations remain fault approximations, and killing tests are an operational
oracle only inside each predeclared `targetTests` scope.
