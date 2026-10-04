# V14.6 recollection retry report

## Decision

`ADOPT`

All four original subjects pass the corrected gates: every frozen normalized identity is present (G-ID), and every added identity has empty `classes` and `methods` lists (G-ADD). Collector and selector are both pinned to `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9` for all eight analyzed maps.

## Collection and gates

| Subject | Recollected identities | Added empty | G-ID | G-ADD | Map SHA-256 |
|---|---:|---:|---|---|---|
| Commons Lang | 4,697 | 5 | PASS | PASS | `3411f99e...` |
| JGraphT | 2,309 | 1 | PASS | PASS | `0f38d66f...` |
| spring-core run 1 | 3,638 | 14 | PASS | PASS | `bfeafc4b...` |
| PetClinic | 56 | 4 | PASS | PASS | `d157cae0...` |

Sources: `gate_results_v14_6.json`, `map_comparison.json`, and each subject's `collection_v14_6.json`. The published common, core, Maven-plugin and Gradle-plugin artifacts were present in the local Maven repository; no republish was needed (`publication_verification_v14_6.json`).

Commons Lang required only test-JVM configuration in the temporary subject checkout: `-Djdk.attach.allowAttachSelf=true -XX:+EnableDynamicAgentLoading`, matching the Mockito-inline/Byte-Buddy attachment requirement on JDK 21. The exact configuration-only diff is `commons-lang/configuration.diff`; production and test sources were not changed.

Every reported PIT killing identity in the frozen eligible records for these four subjects resolves to the corresponding recollected map (`killer_resolution_v14_6.json`: zero unresolved occurrences for every subject).

## spring-core repeat collection

Run 1 is the adopted map; run 2 is retained as a nondeterminism measurement. Both contain 3,638 identities and 14 empty footprints, but 262 identities have a class or method footprint difference (`spring-core/run_to_run.json`). Relative to the frozen 70b398 map, 450 run-1 identities differ: 14 added empty identities, 139 footprint differences that also differ between the two 2e0954 runs, and 297 footprint differences stable across both 2e0954 runs (`spring-core/difference_classes.json`).

## Re-derived evaluation

The leaf oracle remains 4,010 records. Base, constructor and class policies remain inclusive for 3,991, 3,998 and 4,009 records. The recollected empty sessions change logical populations and selection sizes, not inclusiveness or the residual taxonomy. Logical populations are Commons Lang 4,697, JGraphT 2,309, spring-core 3,638, PetClinic 56, Flink 665, Spring Security 1,440, Hibernate 1,099 and Quarkus 684. Complete results, random baselines, intervals, mitigation and taxonomy are in `results/v14_6-*`.

The pinned Java selector was replayed on 1,351 unique inputs covering all 4,010 occurrences: zero full-set mismatches and zero non-SELECTED modes. Production-reader comparison reports zero content differences and equal raw/loaded U sets with 58 total empty entries (`analysis/v14_6/java_comparison.json`, `loader_content_equality.json`).

## Verification

- unit tests: 68, PASS (`v14_6-unittest.log`);
- historical failure analysis: PASS;
- historical selector equivalence: PASS;
- artifact freeze verification: PASS;
- historical recollection verification: PASS;
- B2 verification: PASS;
- v14.6 full deterministic re-derivation: PASS.

No PIT run, mutation change, subject source/test change, selector change, constructor-rule change, Hibernate exclusion change, or extension-map change was performed.

## Manuscript

RAD1 version 14.6 uses the recollected logical populations and `results/v14_6-*` values. The DOCX was rendered to an 11-page PDF; all pages were inspected, and Table 5 was kept together across the page boundary. Twenty-two references and five tables are present; the required process-term grep is empty.

## Repository finish

Evidence commit: `75ec63c24bc003aefac58613a232a8c7f566cb78`.

Final tag: `rad1-v14.6` (created locally; not pushed). Manual publication command after review: `git push origin main rad1-v14.6`.
