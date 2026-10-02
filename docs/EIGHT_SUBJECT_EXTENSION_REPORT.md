# Independent-subject evaluation extension

## Outcome

Eight subjects were attempted under the frozen protocol. Seven produced a
defensible common PIT/STP data set; one was stopped rather than changing a
frozen tool, release, or `targetTests` policy after observing results. Spring
Security was recovered through its upstream-supported JDK 21 toolchain mode,
which preserves the qualified native test population.

| Subject | Status | KILLED | STP inclusive | Inclusiveness | Avg selected | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| Commons Lang | complete | 772 | 771 | 99.87% | 17.0 | 99.64% |
| JGraphT | complete | 517 | 516 | 99.81% | 87.7 | 96.20% |
| spring-core | complete | 454 | 443 | 97.58% | 80.6 | 97.78% |
| PetClinic | complete | 94 | 94 | 100.00% | 9.7 | 81.30% |
| Flink | complete | 349 | 349 | 100.00% | 36.23 | 94.55% |
| Hibernate ORM | complete | 402 | 400 | 99.50% | 296.53 | 73.02% |
| Quarkus Arc | PIT oracle blocked | — | — | — | — | — |
| Spring Security | complete | 340 | 330 | 97.06% | 36.86 | 97.44% |

Across the seven completed subjects, STP includes a PIT-reported killing test
for 2,903 of 2,928 KILLED mutants (99.15%). The unchanged constructor-only
mitigation recovers seven of the twenty-five misses. Flink adds no false
negative. Spring Security adds ten misses, all instances of the existing
Type A/B/C early-exception mechanism, including two Type A cases recovered by
the unchanged rule. Hibernate adds two misses caused by enhancement work
performed by its custom JUnit engine outside STP's leaf-test attribution
window; this is a newly observed mechanism.

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

## Stopped subject

### Quarkus

The split-module adapter is functional: an exact Arc test diagnostic generated
101 mutations successfully. The predeclared full Arc scope sends 6,044 test
and generated classes and fails in the PIT minion during Arc bean-destruction
lifecycle. Narrowing to the successful test after observing this result would
violate the frozen `targetTests` policy, so the subject was stopped.

## Scientific interpretation

The full eight-subject result remains unattainable because Quarkus is blocked.
Reporting it as a zero-mutation or zero-miss project would bias both denominator
and apparent inclusiveness. Therefore headline aggregation covers the seven
subjects with a valid PIT killing-test oracle. Quarkus's machine-readable
blocker is stored in `quarkus/results/blocked.json`. Historical Hibernate and
Spring Security JDK 25 diagnostics remain preserved. Spring Security's JDK 25
diagnostic is historical evidence; `spring-security/docs/JDK21_REFREEZE.md`
records why the official JDK 21 mode is the canonical mutation environment.

The result answers the independent-validation questions only partially:

- Flink independently retains 100% killed-mutant inclusiveness.
- Flink exhibits no Type A/B/C or new observability failure.
- Spring Security independently adds two Type A, three Type B, and five Type C
  misses; the two Type A misses are recovered by the frozen constructor rule.
- Hibernate exposes a new pre-leaf custom-engine attribution boundary: its
  bytecode-enhancement dependencies execute while the custom JUnit engine
  constructs enhanced descriptors/classes, before STP opens the leaf-test
  coverage session. Both Hibernate misses follow this mechanism.

PIT mutations remain fault approximations, and killing tests are an operational
oracle only inside each predeclared `targetTests` scope.
