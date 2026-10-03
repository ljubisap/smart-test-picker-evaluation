# TASK_B2_ADDENDUM — Part I report

## Scope

Only Part I was executed. No manuscript work from Part II was performed. No PIT, coverage collection, subject build/test, selector campaign, canonical re-derivation, promotion, commit, or push was performed.

## I-1 — map-schema compatibility

The real public loader used by `TestSelector` at the policy pin was exercised:

- STP commit: `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`
- tree: `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`
- entry point: `CoverageMapReader.load(File)`
- loaded code source: the pre-existing common JAR in the clean detached exact-commit worktree
- adapter: none
- build performed for Part I: no

| Frozen map | Result | Loaded mappings | Metadata |
|---|---|---:|---|
| Commons Lang | ACCEPTED | 4,692 | present |
| JGraphT | ACCEPTED | 2,308 | present |
| spring-core | ACCEPTED | 3,624 | present |
| PetClinic | ACCEPTED | 52 | present |
| Flink | ACCEPTED | 665 | present |
| Spring Security | ACCEPTED | 1,440 | present |
| Hibernate | ACCEPTED | 1,099 | present |
| Quarkus | ACCEPTED | 684 | present |

Because every map is accepted unchanged, no harness adapter or field mapping is needed. Commands, classpath, Java version, source/JAR/class hashes, actual code-source location, stdout, and per-map outcomes are preserved in `map_schema_compatibility.json`, `loader_probe.jsh`, `run_loader_probe.py`, and `raw/loader_probe.stdout.txt`.

## I-2 — mutated-method kind and key derivation

The evaluator reads PIT's `<mutatedMethod>` text verbatim (`analysis/evaluation_core.py:210–225`) and forms `C#M` as `changed_class + "#" + changed_method` (`analysis/evaluation_core.py:412–423`). It adds no descriptor. The converter likewise stores JaCoCo's method name verbatim as `classFqn + "#" + method.getName()` (`CoverageMapperJaxb.java` at `2e0954`, lines 143–157).

| Kind | Eligible | Inclusive under 2e policy | Among 19 residual misses |
|---|---:|---:|---:|
| Regular method | 3,408 | 3,389 | 19 |
| `<init>` | 70 | 70 | 0 |
| `<clinit>` | 0 | 0 | 0 |
| `lambda$...` | 532 | 532 | 0 |
| Other name-detectable synthetic/bridge | 0 | 0 | 0 |

The frozen maps contain regular, constructor, class-initializer, and `lambda$...` keys, proving that the converter can emit those names. PIT XML does not preserve JVM `ACC_SYNTHETIC`/`ACC_BRIDGE` flags, so a bridge method with an ordinary method name cannot be distinguished by this artifact-only audit; this limitation is explicit in `method_kind_audit.json`.

Per-subject counts, all 532 lambda records, map-key occurrence counts, inclusion outcomes, and exact derivation citations are in `method_kind_audit.json`.

## I-3 — sessions dropped by collector 70b398

The retained `session_*.xml` inventories are the exact per-test JaCoCo session reports consumed by `CoverageMapperJaxb`. Their filename identities were decoded with the collector's `~X → X` rule (`CoverageMapperJaxb.java` at `70b398`, lines 209–251) and compared exactly with frozen map keys.

| Subject | Retained session identities | Map entries | Missing from map | Dropped zero-package session established |
|---|---:|---:|---:|---|
| Commons Lang | 4,692 | 4,692 | 0 | no |
| JGraphT | 2,308 | 2,308 | 0 | no |
| spring-core | 3,624 | 3,624 | 0 | no |
| PetClinic | 52 | 52 | 0 | no |

The identity sets match exactly in both directions. Therefore retained evidence establishes zero dropped sessions in these four collections; there is no missing identity requiring a speculative zero-package classification. Map and identity-set hashes and local evidence paths are in `dropped_session_estimate.json`.

## I-4 — fallback rule

Checked on 3 October 2026. The 20 October 2026 deadline has not been reached, so the fallback is not triggered. This Part I audit does not assert a final main-task B2 verdict and does not promote results or edit the manuscript. See `fallback_status.json`.

## I-5 — replication-package documentation scrub

Misleading descriptions of the historical Python `java_semantic_select` check were corrected or qualified in repository README files, analysis documentation/code, result metadata, and the two supplementary-subject scripts/reports. The corrected language now states that:

- the check compares two Python implementations;
- it does not execute Java;
- it omits the production NO_COVERAGE branch at `2e0954`;
- 4,010/4,010 is evaluator/model agreement, not full production-selector equivalence.

The complete occurrence/action list is `replication_documentation_scrub.json`. No claims-ledger file exists in this evaluation repository. The distinct 21-case historical Maven-plugin contract statement was retained because it refers to actual plugin execution at `70b398`, not to `java_semantic_select`.

## Part I status

`PART_I_COMPLETE`

This status is not `B2_VERIFIED_AND_D_FINALIZED`: the main B2 evaluator correction, full Java selector comparison, canonical re-derivation/promotion, and manuscript Part D were intentionally not executed in this task.
