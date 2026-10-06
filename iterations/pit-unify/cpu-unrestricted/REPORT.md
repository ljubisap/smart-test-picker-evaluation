# CPU-override-free PIT rerun

## Status

- execution: COMPLETED_WITH_RECORDED_JOB_OUTCOMES
- numericalVerification: PASS
- authorReview: READY_FOR_REVIEW_NOT_ADOPTED
- historicalEffectiveProcessors: UNKNOWN
- commit: NONE
- push: NONE

Starting and ending HEAD: `f9c56074a092da85938f7269221a360bde4afb86`. Canonical baseline: `3bdf61c0b7481fe6da25e4bd335b91a348a4f837`. All new material is confined to `iterations/pit-unify/cpu-unrestricted/`; A and B files are preserved. No manuscript, anonymous package, evaluator, map, scope, oracle exclusion, main or tag was changed.

## Environment and actual campaigns

The initial control JVM reports 10 processors, without ActiveProcessorCount. Additional controls use each subject's configured PIT JVM arguments; they are control JVMs, not direct measurements inside leaf tests. Actual observed coverage/minion command lines and inherited launch settings are retained in worker_environment.json and per-attempt process snapshots.
Primary PIT workers: four. Per-class jobs and subjects are sequential. CPU use is monitored, with a stop-and-retry resource fallback to one PIT worker only if needed; the JVM-visible processor count is never replaced by another explicit value. This guard is not an affinity or duty-cycle limiter. Per-attempt worker modes are reported below.

| Subject | Planned classes | Attempted classes | Attempts | Successful matrices | Failed classes | Workers by attempt | Elapsed seconds |
|---|---:|---:|---:|---:|---:|---|---:|
| jgrapht | 20 | 20 | 20 | 20 | 0 | {4: 20} | 2757.035 |
| spring-core | 22 | 22 | 22 | 18 | 4 | {4: 22} | 319.593 |

Observed peak aggregate CPU use by subject (one-second process samples): {'jgrapht': 599.0, 'spring-core': 302.3}. No claim is made about unsampled instantaneous peaks.

### Jobs without usable matrices

- spring-core: `org.springframework.core.SerializableTypeWrapper` — FAILED; attempt logs: `iterations/pit-unify/cpu-unrestricted/pit/spring-core/job-01-attempt-1`.
- spring-core: `org.springframework.core.io.AbstractResource` — FAILED; attempt logs: `iterations/pit-unify/cpu-unrestricted/pit/spring-core/job-08-attempt-1`.
- spring-core: `org.springframework.core.io.buffer.DataBufferUtils` — FAILED; attempt logs: `iterations/pit-unify/cpu-unrestricted/pit/spring-core/job-09-attempt-1`.
- spring-core: `org.springframework.core.io.support.PathMatchingResourcePatternResolver` — FAILED; attempt logs: `iterations/pit-unify/cpu-unrestricted/pit/spring-core/job-10-attempt-1`.

Every attempted job, including failures or resource interruptions, has a separate directory and effective command. Successful matrices are copied only from fresh C output; no B/current matrix fills a gap. XML/gzip identity is verified in matrix_packaging.json. JGraphT receives the same documented Maven profile; Spring reuses native pitClasspath and the proven test-free runtime-JAR preparation. The original Spring runner remains unchanged; its command adapter appends --mutators DEFAULTS. No PIT history input is configured; JGraphT starts with a clean compile and removes stale target XML, while every C attempt output directory starts empty.

## A / B / C numerical results

| State | Eligible | Base inclusive | Base % | Constructor inclusive | Class inclusive |
|---|---:|---:|---:|---:|---:|
| A | 4010 | 3991 | 99.52618454 | 3998 | 4009 |
| B | 3926 | 3907 | 99.51604687 | 3914 | 3925 |
| C | 3931 | 3912 | 99.51666243 | 3919 | 3930 |

Previously A KILLED → B SURVIVED transit-routing cases found by correspondence: 6. Their C status distribution: `{'SURVIVED': 1, 'KILLED': 5}`. Full A/B/C IDs, statuses, raw/normalized killers and eligible policy outcomes are in comparison_records.json.gz. Different mutators are never paired. Ambiguous multiplicity and missing/fresh-only records remain explicit.

C residual footprint counts: `{'C': 1, 'A': 7, 'B': 10, 'MIXED': 1}`; causal annotations: `{'EARLY_EXCEPTION_PROBE_SHADOWING': 18, 'PRE_TEST_ATTRIBUTION_GAP': 1}`. Transfer of annotations requires unique correspondence and identical normalized killers/footprints at unchanged source revisions. Unestablished causes remain UNDETERMINED.

## Comparison and verification

Java full-set comparison: 1349 unique inputs, 3931 weighted occurrences, 0 mismatches, 0 non-SELECTED results. Reuse/fresh: `{'source': 'iterations/pit-unify/java/output.json', 'sourceSha256': '788a469bde630ec3e8ac11ae87a9179cf8352b08256489a49356ad579df78f76', 'sourceInputsSha256': '4a8b761bf3b0e9bff585e7781403630032b327edc65e6da5bd1f96b2c03c658c', 'identicalInputsReused': 1349, 'additionalInvocations': 0, 'freshLoaderRuns': 8, 'reason': 'Identical map digests, class/method inputs, evaluator sets, selector runtime artifacts and harness. Occurrences recomputed from C matrices; all maps freshly loaded.'}`. All map content was freshly read through the production loader. No new selector build was performed.
Manuscript comparison, without manuscript edits: 320 claim/cell entries, 66 changed, 0 unmatched. Sources point to C results. See MANUSCRIPT_COMPARISON.md/json.
Preserved tracked files checked: 1409; changed: 0. Existing checks below were rerun in this task, not copied from B. Regression test counts from logs: `{'repository': {'tests': 68, 'source': 'iterations/pit-unify/cpu-unrestricted/verification/current/unittest.log'}, 'localHelpers': {'tests': 8, 'source': 'iterations/pit-unify/cpu-unrestricted/helper-tests.log'}, 'cpuRemovalSubset': {'tests': 5, 'source': 'iterations/pit-unify/cpu-unrestricted/environment-tests.log'}}`. The CPU-removal tests are a subset of the local helper tests, not additional independent cases.

| Check | Exit | Last line |
|---|---:|---|
| unittest | 0 | OK |
| failure_modes | 0 | VERIFY PASSED: all outputs match committed artifacts |
| selector_equivalence | 0 | VERIFY PASSED: historical evaluator/model agreement matches committed artifact |
| freeze_artifacts | 0 | verified spring-security: 25 artifacts |
| recollection | 0 | VERIFY PASSED: recollection_comparison.json (1837 mutations, 187 selected-set differences, 0 safety flips) |
| b2 | 0 | VERIFY PASSED: B2 base/constructor/class summaries and selected-set IDs match frozen inputs |
| v14_6 | 0 | VERIFY PASSED: v14.6 outcomes, summaries, random baseline, intervals, mitigation, taxonomy, and selected-set IDs match recollected maps and frozen PIT inputs |
| v14_7 | 0 | VERIFY PASSED: v14.7 spring-core sensitivity, worked example, and eight-subject test-segment scan match inputs |
| v14_8 | 0 | PASS: v14.8 evidence verified; failures=3; eligible killer records=10 |
| v14_9 | 0 | PASS: v14.9 failed-killer impact verified; k_miss=0, k_only=0, k_other=10 |
| v15 | 0 | PASS: v15 succeeding-tests audit verified; f=0, u_tests=1139, unresolved=0 |
| B-unified | 0 | VERIFY PASSED: unified raw-input re-derivation, all policies/statistics/diagnostics, Java full sets, unchanged six subjects and original-file hashes |
| helpers | 0 | OK |
| configuration | 0 | PIT command comparisons 42 unexpected 0 |
| C | 0 | PASS: C raw-input re-derivation, Java full sets, loader, six-subject invariance, lossless matrices and all preserved hashes |

C verifier: PASS: C raw-input re-derivation, Java full sets, loader, six-subject invariance, lossless matrices and all preserved hashes

## Related diagnostics

Succeeding-tests check: `{'residualMisses': 19, 'noCoverageRecovered': 5, 'f': 0, 'u_tests': 1139, 'selectedSurvived': 574, 'recoveredRecordsFullyExecutedEdgeOnlySet': 1}`.
Collection-failing killer impact: `{'affectedRecords': 10, 'k_miss': 0, 'k_only': 0, 'k_other': 10}`.
Spring repeat-map selected-set differences: `{'base': 6, 'constructor': 6, 'class': 55}`; residual-miss correspondence: `{'onlyRun1': [], 'onlyRun2': [], 'sameMutationIds': True}`. This reuses retained run-2 evidence; no coverage collection was performed.
The worked example, random baseline, Wilson/class-cluster intervals and all full per-record policy sets were regenerated under results/. Cross-run multiplicities are preserved; ambiguous records are not forcibly paired (see BLOCKERS.md for the frozen index-parser boundary).

## Interpretation and remaining unknowns

The high measured inclusiveness and the observed residual mechanism model remain supported in this sample: C has 19 base misses and 7 constructor-rule recoveries. Its footprint and causal totals equal B: True. The denominator and selection statistics change; the canonical paper numbers cannot simply be relabeled as C.
Removing the explicit override establishes a newly measured execution condition, not equivalence with unknown historical CPU/thread settings. B→C is the observed repeat after removing that override (plus any labeled resource fallback). A→C also includes the changed conditional-operator treatment and other potentially unrecorded historical conditions. A single repeat does not establish determinism or prove that every status change has a single CPU cause.
CPU exposure and executor sizing can alter test paths and mutation detection, not just elapsed time. The transit-routing source evidence is preserved in ../cpu_environment_evidence.json. Numerical verifier success is distinct from certification of historical environment equality and from author adoption.

## Reproduction

From the repository root: `PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/cpu-unrestricted/scripts/verify_c.py --verify`. Per-attempt commands reproduce execution with the recorded checkout/toolchain; do not blindly rerun the guarded campaign launcher into existing attempt directories.
The unchanged final manuscript was only read for claim comparison. No commit, merge, push, tag movement or automatic promotion was performed.
