# RAD1 v14.1 read-only checks

Evaluation checkpoint: `8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580`.
Manuscript inspected: `/Users/D061177/Downloads/RAD1_v14_2_MERGED.docx`.

No PIT, coverage collection, subject build, selector campaign, or canonical-artifact rewrite was performed. All calculations below read the frozen maps and mutation records through `analysis/evaluation_core.py`. Machine-readable values and exact input paths are preserved beside this report.

## T1. Table 3/4 precision

Each cell below is `mean selected / selected fraction % / reduction %`, recomputed before rounding. Full binary floating-point values and every map/PIT source path are in `table_precision.json`.

| Subject | STP (2 dp) | Class baseline (2 dp) | Constructor rule (2 dp) |
|---|---:|---:|---:|
| Commons Lang | 17.01 / 0.36 / 99.64 | 50.12 / 1.07 / 98.93 | 19.81 / 0.42 / 99.58 |
| JGraphT | 87.70 / 3.80 / 96.20 | 207.80 / 9.00 / 91.00 | 96.94 / 4.20 / 95.80 |
| spring-core | 80.63 / 2.22 / 97.78 | 529.18 / 14.60 / 85.40 | 84.93 / 2.34 / 97.66 |
| PetClinic | 9.72 / 18.70 / 81.30 | 18.35 / 35.29 / 64.71 | 11.71 / 22.52 / 77.48 |
| Flink | 36.23 / 5.45 / 94.55 | 64.93 / 9.76 / 90.24 | 38.37 / 5.77 / 94.23 |
| Spring Security | 36.86 / 2.56 / 97.44 | 72.20 / 5.01 / 94.99 | 37.34 / 2.59 / 97.41 |
| Hibernate | 297.25 / 27.05 / 72.95 | 488.77 / 44.47 / 55.53 | 303.16 / 27.58 / 72.42 |
| Quarkus | 260.65 / 38.11 / 61.89 | 539.93 / 78.94 / 21.06 | 383.60 / 56.08 / 43.92 |

PetClinic's raw STP mean is `9.72340425531915`; the correct two-decimal display is `9.72`. Its selected fraction is `18.69885433715221%`, correctly displayed as `18.70%`. Thus `9.70` in the manuscript is a premature/one-decimal value rendered with two digits, not the value from unrounded aggregation.

For the four original subjects, the historical pipeline explicitly rounded mean selected to one decimal in each `scripts/04_baselines.py` and stored the rounded value in `results/aggregated/baseline_comparison.json`; their `evaluation_summary.json` files also store one-decimal means. Per-record STP selection counts remain in `evaluation_results.csv`, while the frozen maps and PIT XML permit all three selectors to be recomputed without using the rounded summaries.

## T2. Method identity in the coverage map

At both collection commits, `CoverageMapperJaxb.java` builds a production method edge as:

```text
classFqn + "#" + method.getName()
```

Evidence:

- STP repository `/Users/D061177/work/issta/hibernate-orm-stp-qualification/stp-source`
- commit `70b3984626ebed16db015c7c261eda132e999f10`, `smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapperJaxb.java:144`
- commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, same file at line 156

No descriptor is included. `spring-core/results/test-coverage-map.json` contains exactly one matching key:

```text
org.springframework.core.convert.support.GenericConversionService#canConvert — 100 logical tests
```

Therefore the worked example's 100 “exact hits” are name-level hits across any `canConvert` overload. The map cannot establish that all 100 hit the `(Class, Class)` overload. See `method_identity.json`.

## T3. Worked-example taxonomy and mitigation

For PIT ordinal 17 (`GenericConversionService#canConvert`, line 133, `VoidMethodCallMutator`):

- mutant-level footprint type: **A**;
- first killer footprint: only `GenericConversionService#<init>` for the target class;
- second killer, `canConvertFromClassSourceTypeToNullTargetType`, has the same Type-A footprint: target class present, only `#<init>`, mutated method absent;
- constructor-only rule recovery: **YES**.

Sources: `results/failure_taxonomy.json` and `results/mitigation_comparison.json`; the exact resolved identities are copied to `worked_example.json`.

## T4. `.test.` package-segment exposure

Static source inspection used the revisions from `RAD1_v14_REVIEW_READY_PROVENANCE.csv`. “Map count” is the union of production class identities present in each canonical map with a literal package segment `test`. `NO_COVERAGE` means an existing logical mapping with both class and method lists empty.

| Subject | Source checkout repository-wide | Qualified production scope | Canonical map | NO_COVERAGE tests |
|---|---:|---:|---:|---:|
| Commons Lang | 0 | 0 | 0 | 0 |
| JGraphT | 0 | 0 | 0 | 1 |
| spring-core | UNKNOWN | UNKNOWN | 0 | 0 |
| PetClinic | 0 | 0 | 0 | 0 |
| Flink | 50 | 0 | 0 | 1 |
| Spring Security | 27 | 0 | 0 | 23 |
| Hibernate | 0 | 0 | 0 | 0 |
| Quarkus | 324 | 0 | 0 | 9 |

The repository-wide Flink, Spring Security, and Quarkus matches reside in other main-source modules, including test-support products, but none lies in the qualified production module/scope. No canonical map contains such a production identity. Consequently the frozen eight-subject scopes show no direct `.test.`-segment exposure; the listed empty mappings have other causes and cannot be attributed to that filter from these artifacts. The recorded spring-core revision was not found in any retained local checkout, so its source-tree result is `UNKNOWN`, while its map result is established.

Full class/path lists: `source_test_segment_exposure.json`. Map classes and every empty logical identity: `map_test_segment_exposure.json`.

## T5. Collector differences

The restricted log contains three relevant commits:

- `0039cd7e7ca7838086ae506b0709e9356b0bca2c`: deterministic `TreeMap` ordering only;
- `1151bbd99faf3c172bb42e7625cf4ba828da7b94`: preserves successfully collected zero-coverage `session_*.xml` tests as empty mappings;
- `7c69ec0785b0d66e9a83780bb967783a9d5b1919`: records per-session execution-identity/engine/shape metadata and passes module identity into map generation.

The first affects serialization order. The second changes which logical tests survive conversion. The third changes retained attribution/execution metadata but not JaCoCo probe edges. Neither endpoint includes method descriptors. Exact restricted paths, commands, diff stat, and interpretation are in `collector_diff.md`.

## T6. Real-plugin end-to-end validation

**FOUND** at `results/contract_test.json`.

- Coverage map commit: `8538458e7aeb1455a5942f60fe0b4930da6c5d68`
- STP plugin commit: `70b3984626ebed16db015c7c261eda132e999f10`
- plugin version: `0.1.0`
- 21/21 cases: `EXACT`
- mismatches: 0
- infrastructure failures: 0

`real_plugin_validation.json` reports every case ID, status, selected count, and selected-set hash. This is actual Maven-plugin execution evidence for the 21 Commons Lang cases, not a dataset-wide plugin run.

## T7. Confidence intervals

Wilson intervals treat eligible records as Bernoulli observations. The cluster bootstrap resamples mutated production classes with replacement, keeping all mutation occurrences in each sampled class; it uses 10,000 trials and deterministic seeds beginning with `20261003`. The aggregate pools subject-qualified class clusters. This is new analysis over frozen records only.

| Subject | Estimate | Wilson 95% | Class-cluster bootstrap 95% | Clusters |
|---|---:|---:|---:|---:|
| Commons Lang | 99.87% | [99.27, 99.98] | [99.53, 100.00] | 21 |
| JGraphT | 99.81% | [98.91, 99.97] | [99.20, 100.00] | 20 |
| spring-core | 97.58% | [95.71, 98.64] | [95.50, 99.45] | 18 |
| PetClinic | 100.00% | [96.07, 100.00] | [100.00, 100.00] | 14 |
| Flink | 100.00% | [98.91, 100.00] | [100.00, 100.00] | 15 |
| Spring Security | 97.06% | [94.67, 98.39] | [94.08, 99.19] | 18 |
| Hibernate | 99.75% | [98.60, 99.96] | [99.24, 100.00] | 15 |
| Quarkus | 100.00% | [99.65, 100.00] | [100.00, 100.00] | 16 |
| Micro aggregate | 99.40% | [99.11, 99.60] | [98.98, 99.74] | 137 |

The zero-width bootstrap intervals for subjects with no observed class cluster containing a miss are an empirical property of this resampling scheme, not proof of certainty. Script: `run_frozen_checks.py`; unrounded output and per-subject seeds: `confidence_intervals.json`.

## T8. Cost evidence

No exact observed wall-clock log for STP coverage collection or map conversion is retained in the evaluation repository. Four documentation estimates exist:

- Commons Lang coverage-map generation: approximately 15–25 minutes (`commons-lang/docs/REPRODUCE.md:31`, `commons-lang/docs/REQUIREMENTS.md:81`);
- JGraphT: approximately 7 minutes (`jgrapht/docs/REPRODUCE.md:28`, `jgrapht/docs/REQUIREMENTS.md:86`);
- spring-core: approximately 5–10 minutes (`spring-core/docs/REQUIREMENTS.md:50`);
- PetClinic: approximately 1 minute (`petclinic/docs/REQUIREMENTS.md:56`).

There is no retained map-conversion-only timing and no extension-subject STP collection timing in this repository. PIT `elapsedSeconds` and PIT coverage-scan logs were deliberately excluded because they are not STP collection/conversion timings. See `cost_evidence.json`.

## T9. JUnit Platform versions

| Subject | Version | Evidence status and source |
|---|---:|---|
| Commons Lang | UNKNOWN | Parent-managed; no retained resolved dependency report |
| JGraphT | 6.0.3 | `DECLARED_ONLY`, root POM at recorded revision, line 81 |
| spring-core | UNKNOWN | Recorded checkout unavailable; artifacts do not retain version |
| PetClinic | UNKNOWN | Boot 3.5.0 parent retained, but resolved Platform version is not |
| Flink | 5.11.4 | `RUN_EVIDENCE`, `flink/config/subject.json` |
| Spring Security | 6.1.3 | `RUN_EVIDENCE`, `spring-security/config/subject.json` |
| Hibernate | 6.0.1 | `RUN_EVIDENCE`, `hibernate/config/subject.json` |
| Quarkus | 6.1.3 | `RUN_EVIDENCE`, `quarkus/config/subject.json` |

Because the task asks for versions actually used in collection, declared-only and unresolved values are not promoted to observed runtime facts. Details are in `junit_versions.json`.

## Bottom line for the merged manuscript

The local evidence requires three substantive cautions/corrections before numerical regeneration of the merged manuscript:

1. PetClinic mean selected should be `9.72`, not `9.70`; `18.70%` remains correct.
2. The worked example's “100 exact hits” are exact only under STP's name-only method identity, not specifically proven hits on the `(Class, Class)` overload.
3. Version-specific JUnit listener citation can be supported directly for the four extension subjects, only declaratively for JGraphT, and remains `UNKNOWN` for Commons Lang, spring-core, and PetClinic.

## T10. Zero-coverage handling at collector `70b398`

### Original four subjects

The count below is over PIT killing-identity occurrences in every KILLED record, not distinct test names. A resolved coverage key may itself have empty `classes` and `methods`; that is still a resolved identity.

| Subject | KILLED records | PIT killer occurrences | Occurrences resolving to no coverage key | Records whose killers are all unresolved |
|---|---:|---:|---:|---:|
| Commons Lang | 772 | 3,055 | 0 | 0 |
| JGraphT | 517 | 158,802 | 0 | 0 |
| spring-core | 454 | 10,307 | 0 | 0 |
| PetClinic | 94 | 422 | 0 | 0 |

Sources: the coverage maps and PIT patterns in `analysis/projects.json`; exact per-project paths and the empty unresolved lists are in `zero_coverage_handling.json`.

The evaluator does **not** silently turn unresolved killers into an empty killing set `K_m`, nor does it exclude the record from `E_p`:

- `normalize_pit_test_name` constructs the logical base identity at `analysis/evaluation_core.py:266-298`;
- direct and base-name resolution occur at `analysis/evaluation_core.py:365-371`;
- any unresolved normalized identity raises `ValueError` at `analysis/evaluation_core.py:372-377`;
- a KILLED mutation with no resolved test also raises at `analysis/evaluation_core.py:386-389`;
- only separately audited container-only mutation IDs are removed by `exclude_non_leaf_oracle_records` at `analysis/evaluation_core.py:90-123`;
- resolution precedes that exclusion in the actual evaluator at `analysis/evaluate_subject.py:99-106`.

Thus an all-unresolved record would fail evaluation before membership in the leaf-level eligible set was computed. It would not be counted with empty `K_m` and would not be automatically excluded.

### Origin of the empty JGraphT mapping

`GraphTestsTest#failRequireIsWeightedOnNull_761695b` is present in `jgrapht/results/test-coverage-map.json.gz` with empty `classes` and `methods`. It is not a missing or unresolved test identity. Under the subject revision recorded in the map (`093b0c5ea006ba5b1d8b7a0212676bf8850cac6b`):

- `GraphTestsTest.java:536-543` invokes `GraphTests.requireWeighted(null)` and expects `NullPointerException`;
- `GraphTests.java:863-866` enters `requireWeighted` and immediately throws when the graph is null;
- the converter at STP `70b3984626ebed16db015c7c261eda132e999f10`, `CoverageMapperJaxb.java:110-168`, accepts the non-empty XML, creates the test entry, and includes production methods only when `method.getCoveredCount() > 0` (`:137-150`).

The exceptional path records no covered production method/class before the throw. Test-side catch/assertion code is filtered from production coverage, so the resulting valid mapping is empty. The test does not appear as a killing identity in any of the 517 eligible JGraphT KILLED records. This is zero production coverage, not failed PIT-to-map identity resolution.

### Extension-subject `NO_COVERAGE` tests as PIT killers

| Subject | Empty mappings | Empty mappings appearing as a killer | Result |
|---|---:|---:|---|
| Flink | 1 | 0 | `ExceptionHistoryEntryTest#testNullExecution_3ace619`: NO |
| Spring Security | 23 | 6 | Six identities below: YES; remaining 17: NO |
| Hibernate | 0 | 0 | none |
| Quarkus | 9 | 0 | all nine `ReproducibilityCheckTest` identities: NO |

The six Spring Security identities that occur as killers are:

1. `AuthorityAuthorizationManagerTests#hasAnyAuthorityWhenEmptyThenException_4acbb6d`
2. `AuthorityAuthorizationManagerTests#hasAnyAuthorityWhenNullThenException_666eb63`
3. `AuthorityAuthorizationManagerTests#hasAnyRoleWhenCustomRolePrefixNullThenException_224748b`
4. `AuthorityAuthorizationManagerTests#hasAuthorityWhenNullThenException_5281bf4`
5. `AuthorityAuthorizationManagerTests#hasRoleWhenNullThenException_85c3cde`
6. `RoleHierarchyImplTests#testBuilderThrowIllegalArgumentExceptionWhenPrefixRoleNull_5894d6c`

Each occurs in exactly one eligible mutation record. `zero_coverage_handling.json` lists all 33 extension-subject empty identities, the YES/NO result, occurrence count, and mutation IDs.

## T11. Contributing-class reconciliation

Table 1's `16` is the number of sampled classes whose per-class PIT run completed with status `OK`, sourced through `pit-run-summary.json` by `analysis/build_eight_subject_summary.py:58-69`. T7's cluster count is instead the number of distinct `mutated_class` values among eligible **KILLED** records. Therefore an `OK` PIT run with no KILLED mutant contributes to Table 1 but not to a killed-record bootstrap cluster.

### Flink

The 16 Table-1 classes from `flink/config/sample_classes.json` are:

1. `org.apache.flink.runtime.scheduler.DefaultScheduler`
2. `org.apache.flink.runtime.scheduler.ExecutionGraphHandler`
3. `org.apache.flink.runtime.scheduler.SlotSharingExecutionSlotAllocator`
4. `org.apache.flink.runtime.scheduler.adaptive.DefaultStateTransitionManager`
5. `org.apache.flink.runtime.scheduler.adaptive.Executing`
6. `org.apache.flink.runtime.scheduler.adaptive.CreatingExecutionGraph`
7. `org.apache.flink.runtime.scheduler.adaptive.StopWithSavepoint`
8. `org.apache.flink.runtime.scheduler.adaptive.allocator.SlotSharingSlotAllocator`
9. `org.apache.flink.runtime.scheduler.adaptivebatch.DefaultVertexParallelismAndInputInfosDecider`
10. `org.apache.flink.runtime.scheduler.adaptivebatch.DefaultSpeculativeExecutionHandler`
11. `org.apache.flink.runtime.scheduler.adaptivebatch.util.AllToAllVertexInputInfoComputer`
12. `org.apache.flink.runtime.scheduler.adapter.DefaultExecutionTopology`
13. `org.apache.flink.runtime.scheduler.exceptionhistory.ExceptionHistoryEntry`
14. `org.apache.flink.runtime.scheduler.slowtaskdetector.ExecutionTimeBasedSlowTaskDetector`
15. `org.apache.flink.runtime.scheduler.stopwithsavepoint.StopWithSavepointTerminationHandlerImpl`
16. `org.apache.flink.runtime.scheduler.strategy.PipelinedRegionSchedulingStrategy`

The 15 T7 clusters are the same list without `ExecutionGraphHandler`. Its source artifact, `flink/results/per-class/org.apache.flink.runtime.scheduler.ExecutionGraphHandler/mutations.xml`, contains 26 mutations: 18 `NO_COVERAGE`, 4 `SURVIVED`, 4 `TIMED_OUT`, and 0 `KILLED`. Its run is nevertheless `OK` in `flink/results/pit-run-summary.json`.

### Hibernate

The 16 Table-1 classes from `hibernate/config/sample_classes.json` are:

1. `org.hibernate.bytecode.internal.BytecodeEnhancementMetadataPojoImpl`
2. `org.hibernate.bytecode.enhance.internal.bytebuddy.PersistentAttributeTransformer`
3. `org.hibernate.bytecode.enhance.internal.bytebuddy.BiDirectionalAssociationHandler`
4. `org.hibernate.bytecode.enhance.spi.interceptor.LazyAttributeLoadingInterceptor`
5. `org.hibernate.bytecode.enhance.spi.interceptor.EnhancementAsProxyLazinessInterceptor`
6. `org.hibernate.bytecode.internal.bytebuddy.ByteBuddyState`
7. `org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl`
8. `org.hibernate.proxy.AbstractLazyInitializer`
9. `org.hibernate.proxy.pojo.bytebuddy.ByteBuddyProxyFactory`
10. `org.hibernate.event.internal.AbstractFlushingEventListener`
11. `org.hibernate.event.internal.DefaultPersistEventListener`
12. `org.hibernate.event.internal.DefaultDeleteEventListener`
13. `org.hibernate.event.internal.DefaultLoadEventListener`
14. `org.hibernate.event.internal.DefaultRefreshEventListener`
15. `org.hibernate.jpa.event.internal.CallbackRegistryImpl`
16. `org.hibernate.jpa.event.internal.CallbackDefinitionResolver`

The 15 T7 clusters are the same list without `DefaultRefreshEventListener`. Its source artifact, `hibernate/results/per-class/org.hibernate.event.internal.DefaultRefreshEventListener/mutations.xml`, contains 67 mutations, all `NO_COVERAGE`, and no KILLED record. Its run is `OK` in `hibernate/results/pit-run-summary.json`.

The exact ordered frozen lists, sorted eligible-cluster lists, PIT paths, and set differences are in `contributing_class_reconciliation.json`.

## T12. Random-baseline column

The recomputation exactly follows `analysis/evaluate_subject.py:53-84`: 1,000 trials, seed `42`, per-record budget equal to STP's selected count, and per-record RNG seed `42 + trial * number_of_records + record_index`. The analytical probability is `1 - C(N-r_m,k_m)/C(N,k_m)` (or 1 when fewer than `k_m` non-killers exist). Inputs are the frozen maps and PIT patterns in `analysis/projects.json` after the audited leaf-oracle exclusion.

| Subject | Monte Carlo full precision | MC 2 dp | Analytical full precision | Analytical 2 dp |
|---|---:|---:|---:|---:|
| Commons Lang | 2.030699481865285% | 2.03% | 2.0249214128211848% | 2.02% |
| JGraphT | 33.586460348162475% | 33.59% | 33.62501962758073% | 33.63% |
| spring-core | 17.372026431718062% | 17.37% | 17.364902633258875% | 17.36% |
| PetClinic | 35.967021276595744% | 35.97% | 35.875574408630825% | 35.88% |
| Flink | 19.331518624641834% | 19.33% | 19.378562190147086% | 19.38% |
| Spring Security | 17.420882352941177% | 17.42% | 17.464735493933787% | 17.46% |
| Hibernate | 71.33067331670823% | 71.33% | 71.30474983204753% | 71.30% |
| Quarkus | 71.25327793167129% | 71.25% | 71.27926540032158% | 71.28% |

`random_baseline_full_precision.json` additionally records the number of eligible records, successful trial-record pairs, full-precision Monte Carlo standard deviation, seed, trials, input paths, and formula. Script: `run_followup_checks.py`.
