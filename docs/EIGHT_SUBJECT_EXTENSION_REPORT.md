# Independent-subject evaluation extension

## Outcome

Eight subjects were evaluated under the frozen protocol. All eight produced a
defensible common PIT/STP data set. Spring Security was recovered through its
upstream-supported JDK 21 toolchain mode. Quarkus was recovered by translating
its already-frozen 684-test oracle from a broad package glob to the exact
BASE-proven runnable test classes; neither correction changes the qualified
test population.

| Subject | Status | KILLED | STP inclusive | Inclusiveness | Avg selected | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| Commons Lang | complete | 772 | 771 | 99.87% | 17.0 | 99.64% |
| JGraphT | complete | 517 | 516 | 99.81% | 87.7 | 96.20% |
| spring-core | complete | 454 | 443 | 97.58% | 80.6 | 97.78% |
| PetClinic | complete | 94 | 94 | 100.00% | 9.7 | 81.30% |
| Flink | complete | 349 | 349 | 100.00% | 36.23 | 94.55% |
| Hibernate ORM | complete | 402 | 400 | 99.50% | 296.53 | 73.02% |
| Quarkus Arc | complete | 1083 | 1083 | 100.00% | 260.65 | 61.89% |
| Spring Security | complete | 340 | 330 | 97.06% | 36.86 | 97.44% |

Across the eight completed subjects, STP includes a PIT-reported killing test
for 3,986 of 4,011 KILLED mutants (99.38%). The unchanged constructor-only
mitigation recovers seven of the twenty-five misses. Flink adds no false
negative. Quarkus adds 1,083 KILLED mutants and no false negative. Spring
Security adds ten misses, all instances of early-exception probe shadowing,
with footprint shapes two Type A, three Type B, and five Type C; the two Type A cases are recovered by
the unchanged rule. Hibernate adds two misses caused by enhancement work
performed by its custom JUnit engine outside STP's leaf-test attribution
window; this is a newly observed mechanism.

Across all misses, the map-evidence footprint totals are A=7, B=10, C=7, and
MIXED=1. These shapes are reported independently from causal mechanism:
23 misses are `EARLY_EXCEPTION_PROBE_SHADOWING`, while the two Hibernate misses
are `PRE_TEST_ATTRIBUTION_GAP`.

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

## Hibernate JDK 21 replay

The original JDK 25 attempt remains preserved: PIT 1.17.4 cannot process class
file major version 69. A JDK 21 replay kept Hibernate 7.4.11.Final, all 16
sampled classes, PIT/JUnit plugin versions, mutators, and `targetTests` scopes
unchanged. Hibernate's external `-Porm.jdk.min=21` property and its required
bytecode-enhanced-engine system property enabled a valid run: 1,061 total PIT
mutations and 402 KILLED. Details are in `hibernate/docs/JDK21_REFREEZE.md`.

## Quarkus scope-translation correction

The initial broad `io.quarkus.arc.test.*` translation admitted 6,044 compiled
test, helper, and generated classes. PIT's JUnit 5 finder attempted discovery
on a generated Arc `_Bean$0` class and failed in `Class.getEnclosingClass()`
because its `InnerClasses` metadata disagreed with the generated outer bean.
The fatal error occurred before mutation and was not caused by Arc's expected
bean-destruction error tests.

The corrected profile contains the exact 572 test classes represented by all
684 identities in the pre-frozen BASE runnable inventory. It therefore
preserves the full oracle while excluding artifacts that were never runnable
tests. All 16 pre-frozen class jobs completed: 1,639 PIT mutations, 1,083
KILLED, and 1,083 STP-inclusive.

## Scientific interpretation

Headline aggregation now covers all eight attempted subjects with a valid PIT
killing-test oracle. Quarkus's original failure and exact stack trace remain
under `quarkus/results/pre-runnable-inventory-correction/`; the correction is
recorded in `quarkus/results/pit-resolution.json`. Historical Hibernate and
Spring Security JDK 25 diagnostics remain preserved. Spring Security's JDK 25
diagnostic is historical evidence; `spring-security/docs/JDK21_REFREEZE.md`
records why the official JDK 21 mode is the canonical mutation environment.

The result answers the independent-validation questions as follows:

- Flink independently retains 100% killed-mutant inclusiveness.
- Flink exhibits no Type A/B/C or new observability failure.
- Quarkus independently retains 100% inclusiveness across 1,083 KILLED mutants
  and exhibits no new failure category.
- Spring Security independently adds two Type A, three Type B, and five Type C
  misses; the two Type A misses are recovered by the frozen constructor rule.
- Hibernate exposes a new pre-leaf custom-engine attribution boundary: its
  bytecode-enhancement dependencies execute while the custom JUnit engine
  constructs enhanced descriptors/classes, before STP opens the leaf-test
  coverage session. Both Hibernate misses follow this mechanism.

PIT mutations remain fault approximations, and killing tests are an operational
oracle only inside each predeclared `targetTests` scope.
