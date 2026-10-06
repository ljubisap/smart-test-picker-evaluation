# C adoption report

Status: all repository, manuscript and package gates pass. Publication receipt is recorded below after Git operations.

## Provenance and limits

Preflight: `preflight.json`; input ZIP digest verified before extraction. C verification passed twice before adoption edits (`preflight-C-1.log`, `preflight-C-2.log`). Main baseline and prior branch HEAD are preserved in that record. No frozen map, evaluator/selector logic, constructor predicate, leaf exclusion, or other-six-subject PIT matrix changed.

`analysis/projects_v17.json` changes only the two PIT patterns. Eighteen independently regenerated result objects equal C exactly (`derivation_equality.json`); method kinds and publication metrics are additionally verified. No outcome was copied in place of derivation.

Earlier B/C verifiers have historical HEAD/whole-tree assertions. They were checked at the preserved historical snapshot, not falsely claimed compatible with a new adoption HEAD. All current analysis verifiers and the new v17 verifier run against the adoption inputs. `portability_check.json` additionally proves the new verifier in a relocated copy.

The original JGraphT effective mutator option is UNKNOWN: its retained Maven profile explicitly names DEFAULTS, while original XML/stdout show the implicit operator set. The manuscript therefore does not assert omission as directly proved for that run. Spring omission and both replacement executions are evidenced. See `provenance_review.json`. This limits the historical explanation, not the adopted C results. PetClinic original installed PIT/plugin versions and historical effective CPU counts remain UNKNOWN.

One duplicate raw XML exceeds GitHub’s single-file limit. Its already-verified canonical gzip decompresses to exactly the same bytes/hash; raw XML remains untouched locally and is not staged. `storage_manifest.json` records the lossless transport; the fresh-root verifier succeeds without that duplicate.

## Adopted results

| Policy | Inclusive / eligible | Percent |
|---|---:|---:|
| base | 3,912 / 3,931 | 99.52% |
| constructor | 3,919 / 3,931 | 99.69% |
| class | 3,930 / 3,931 | 99.97% |

Residual footprints: {'C': 1, 'A': 7, 'B': 10, 'MIXED': 1}. Causes: {'EARLY_EXCEPTION_PROBE_SHADOWING': 18, 'PRE_TEST_ATTRIBUTION_GAP': 1}. UNDETERMINED annotations: 0.

Java: `results/v17-java-comparison.json`; recorded unchanged-selector full sets are reused only for identical map/class/method inputs, with newly derived occurrence weights. No new selector execution is claimed.

## Checks, two passes

| Pass | Check | Exit | Last line |
|---|---|---:|---|
| 1 | unittest | 0 | OK |
| 1 | failure_modes | 0 | VERIFY PASSED: all outputs match committed artifacts |
| 1 | selector_equivalence | 0 | VERIFY PASSED: historical evaluator/model agreement matches committed artifact |
| 1 | freeze_artifacts | 0 | verified spring-security: 25 artifacts |
| 1 | recollection | 0 | VERIFY PASSED: recollection_comparison.json (1837 mutations, 187 selected-set differences, 0 safety flips) |
| 1 | b2 | 0 | VERIFY PASSED: B2 base/constructor/class summaries and selected-set IDs match frozen inputs |
| 1 | v14_6 | 0 | VERIFY PASSED: v14.6 outcomes, summaries, random baseline, intervals, mitigation, taxonomy, and selected-set IDs match recollected maps and frozen PIT inputs |
| 1 | v14_7 | 0 | VERIFY PASSED: v14.7 spring-core sensitivity, worked example, and eight-subject test-segment scan match inputs |
| 1 | v14_8 | 0 | PASS: v14.8 evidence verified; failures=3; eligible killer records=10 |
| 1 | v14_9 | 0 | PASS: v14.9 failed-killer impact verified; k_miss=0, k_only=0, k_other=10 |
| 1 | v15 | 0 | PASS: v15 succeeding-tests audit verified; f=0, u_tests=1139, unresolved=0 |
| 1 | v17 | 0 | PASS: v17 raw-input derivation, all C outputs, Java full sets, input preservation and adopted manifest verified |
| 1 | historical-B | 0 | VERIFY PASSED: unified raw-input re-derivation, all policies/statistics/diagnostics, Java full sets, unchanged six subjects and original-file hashes |
| 2 | unittest | 0 | OK |
| 2 | failure_modes | 0 | VERIFY PASSED: all outputs match committed artifacts |
| 2 | selector_equivalence | 0 | VERIFY PASSED: historical evaluator/model agreement matches committed artifact |
| 2 | freeze_artifacts | 0 | verified spring-security: 25 artifacts |
| 2 | recollection | 0 | VERIFY PASSED: recollection_comparison.json (1837 mutations, 187 selected-set differences, 0 safety flips) |
| 2 | b2 | 0 | VERIFY PASSED: B2 base/constructor/class summaries and selected-set IDs match frozen inputs |
| 2 | v14_6 | 0 | VERIFY PASSED: v14.6 outcomes, summaries, random baseline, intervals, mitigation, taxonomy, and selected-set IDs match recollected maps and frozen PIT inputs |
| 2 | v14_7 | 0 | VERIFY PASSED: v14.7 spring-core sensitivity, worked example, and eight-subject test-segment scan match inputs |
| 2 | v14_8 | 0 | PASS: v14.8 evidence verified; failures=3; eligible killer records=10 |
| 2 | v14_9 | 0 | PASS: v14.9 failed-killer impact verified; k_miss=0, k_only=0, k_other=10 |
| 2 | v15 | 0 | PASS: v15 succeeding-tests audit verified; f=0, u_tests=1139, unresolved=0 |
| 2 | v17 | 0 | PASS: v17 raw-input derivation, all C outputs, Java full sets, input preservation and adopted manifest verified |
| 2 | historical-B | 0 | VERIFY PASSED: unified raw-input re-derivation, all policies/statistics/diagnostics, Java full sets, unchanged six subjects and original-file hashes |

Full commands, scopes, timing and logs: `repository_checks.json`. Each unittest pass ran 68 tests. Historical B is explicitly scoped to its unmodified worktree.

## Manuscript

Word and full sentence/cell change list remain outside the evaluation repository:

- `/Users/D061177/work/issta/rad1-v16/RAD1_v16.docx`; SHA-256 `70cba8c81a78700c7a131c8f2cbc75450ea5bdb750e6c4b84ea0ab261629af29`.

- `/Users/D061177/work/issta/rad1-v16/V16_CHANGES.md`; SHA-256 `c552fd038a2bc40456032f2f8e74243c86eb9cc1d1810c173a4d5fcdc7b439d8`.

- `/Users/D061177/work/issta/rad1-v16/plain-text.diff`; SHA-256 `63813b8a77e9edc1e8fab412e7d2d242c6aeb1baded87bd95501d6c050f56829`.

- `/Users/D061177/work/issta/rad1-v16/verification-1.json`; SHA-256 `0d6a45c44c3f5293804dc46c53470e94994c87cf527c44b3684b4a3f9b2fb5f8`.

- `/Users/D061177/work/issta/rad1-v16/verification-2.json`; SHA-256 `0d6a45c44c3f5293804dc46c53470e94994c87cf527c44b3684b4a3f9b2fb5f8`.

Each independent manuscript pass checks 159 directly extracted claims; non-text OOXML properties are identical, five tables remain, Table 5 has seven rows, and all 22 references are unchanged. Tables 2 and 5 are byte-identical as XML. C’s 320-entry/66-change comparison was used as a cross-check, not a quota. `manuscript_checks.json` lists every changed location and source without exporting paper text.

The Word update also recalculates method kinds, rounded intervals/random values, run-2 means and changed class-selection count, and the 18-of-19 versus 761-of-3,931 mutator concentration. Java evidence reuse and historical-option uncertainty are stated precisely. No PDF or manuscript is committed.

## Diagnostic replay

Exactly the two authorized jobs ran once each; no full campaign or coverage collection ran.

| Subject | Seconds | Records | Identity/status/killing-set matches | Inclusiveness changes |
|---|---:|---:|---|---|
| jgrapht | 1526.03 | 245/245 | 245/245/245 | {'base': 0, 'constructor': 0, 'class': 0} |
| spring-core | 99.21 | 125/125 | 125/125/125 | {'base': 0, 'constructor': 0, 'class': 0} |

All PIT statuses, including timeouts/memory errors, remain visible. Both subject checkouts were restored clean. The six other replay directories are byte-identical to the input archive; Flink’s existing three killing-set differences remain observed without an invented cause. `replays.json` records CPU samples (no processor-count override), and `replay_comparisons.json` records all comparison fields.

## Anonymous package

Runner fix: native Spring `pitClasspath` is used; fallback registration is guarded. Four regression tests cover native/fallback task and environment handling. The worked-example evidence locator now uses the same XML ordinal directly rather than an old path suffix; selector logic and mutation identities are unchanged.

Two fresh extractions of the exact ZIP execute evaluator tests, runner tests, eight stored-XML comparisons, runner help/plans, both fresh-replay comparisons, and full reproduction. The second extraction additionally runs `--write` then `--verify`. Both reject deliberate result corruption. Commands/logs are in `package_checks.json`; input preservation and gzip-aware identity scan are recorded. Accepted source/schema identifiers are not renamed.

Archive: `/Users/D061177/work/issta/adopt-c-work/anon-final.zip`
Bytes: 66835830; SHA-256 `22180edf00c2f396ec4daa1adcf1a3cab561751fe0b82a0bf55237803bbf55c8`.

The anonymous package is not added to this repository. A recoverable copy of the input archive is retained outside it.

## Publication

Publication occurs only after this report’s gates pass. The exact adoption/merge/tag/push receipt is recorded in `publication.json` and the final handoff; no previous tag is moved.
