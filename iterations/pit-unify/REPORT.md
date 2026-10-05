# PIT 1.17.4 unification iteration

## Scope and status

This branch is a separate experiment, not a promotion of current results. Only JGraphT and spring-core PIT matrices were regenerated. Adopted maps, evaluator and policy, sampled classes, targetTests, constructor rule and Hibernate exclusion are unchanged. No coverage was collected; no manuscript or anonymous package was edited.

Baseline: `3bdf61c0b7481fe6da25e4bd335b91a348a4f837`. Branch: `iteration-pit-unify`. Original tracked files checked: 1046; changed: 0.

**Interpretation status: unified-operator observations, NOT a certified PIT-version-only comparison.** The shared-machine CPU control `ActiveProcessorCount=1` is visible to subject code. JGraphT transit-routing tests derive executor parallelism from it. This extra control was an execution deviation, not a consequence of the requested eight-CPU utilization limit. The historical effective processor count remains UNKNOWN after searching retained original logs/configuration. See `BLOCKERS.md`, `cpu_evidence_search.json`, `cpu_environment_evidence.json` and `results/status_comparison.json.gz`. Numerical verification does not resolve this experimental limitation. Nothing is promoted to current results.

Both documented runner scripts already requested PIT 1.17.4/JUnit plugin 1.2.1 despite their stored negate-conditional operators. Original JGraphT stdout also reports pitest-maven:1.17.4. Operator names alone therefore do not establish an older PIT version. Runner source files were unchanged, but Spring required a command adapter adding exactly --mutators DEFAULTS: the PIT 1.17.4 CLI implicit fallback differs from that named group. Its first, implicit-defaults campaign and preliminary derivations are preserved in attempts/implicit-defaults.tar.gz and pit/spring-core-implicit-defaults/. JGraphT received the documented PIT Maven profile in a disposable POM. No Gradle PIT plugin was needed. See PROTOCOL.md, pit-default-resolution/, preflight.json, pit_tool_artifacts.json and the retained command logs.

## Campaigns

| Subject | Targeted | Complete matrices | Failed/timed out | Campaign elapsed seconds |
|---|---:|---:|---:|---:|
| jgrapht | 20 | 20 | 0 | 3020.579 |
| spring-core | 22 | 18 | 4 | 315.668 |

Per-class mutation/KILLED counts, all PIT statuses, exact scopes, operator distributions, failures and command durations are in `campaign_inventory.json`. Mutant-level TIMEOUT/MEMORY_ERROR statuses remain visible and never enter the KILLED-only denominator. Missing or failed class jobs are not silently replaced by stored matrices.

## Unified outcomes

| Policy | Eligible | Inclusive | Inclusiveness |
|---|---:|---:|---:|
| base | 3926 | 3907 | 99.51604687% |
| constructor | 3926 | 3914 | 99.69434539% |
| class | 3926 | 3925 | 99.97452878% |

Residual footprint counts: `{"A": 7, "B": 10, "C": 1, "MIXED": 1}`.
Residual causal annotations: `{"EARLY_EXCEPTION_PROBE_SHADOWING": 18, "PRE_TEST_ATTRIBUTION_GAP": 1}`.
Constructor recoveries: 7; NO_COVERAGE recoveries: 5.

Unchanged six-subject comparison errors: 0. Full selected sets and killers are compared, not only headlines.

The Spring prerequisite correction built only missing runtime project JARs, without a Test task or source change. The initial failed/interrupted attempt is preserved in `pit/spring-core-initial-interrupted/`. The final four unusable jobs are SerializableTypeWrapper, AbstractResource, DataBufferUtils and PathMatchingResourcePatternResolver: each reports 19 unmutated test failures in PIT coverage setup. These same four jobs had no usable stored matrix; DataBufferUtils formerly timed out. This is not an STP failure and no outcome-driven retry was made.

New XML matrices are compressed losslessly for GitHub file limits. `matrix_packaging.json` records raw and gzip hashes and proves identical decompressed bytes. Original raw files are retained outside the repository. Frozen input matrices were not compressed or edited.

## Causal review and comparison

Exact mutation IDs remain those produced by the unchanged loader. New XML paths/ordinals can change IDs even for a corresponding class/method/descriptor/line/operator. `comparison.json` separates exact-ID persistence from semantic correspondence. `causal_source_evidence.json` records source revisions, hashes and line-numbered excerpts; `causal_review.json` records review conclusions. An annotation is not inferred merely from footprint shape. Unsupported causes remain UNDETERMINED. This is source/control-flow analysis, not a new method-entry or probe-offset tracing experiment.

See `COMPARISON.md`, `comparison.json`, `MANUSCRIPT_COMPARISON.md` and `manuscript_comparison.json`. They include per-subject outcomes, Table I–V cells, numerical prose claims, random baselines, Wilson/bootstrap intervals, run-2 sensitivity, failed-killer witnesses and succeedingTests counts. The final DOCX is identified by digest, not copied into this repository.

Manuscript comparison: 320 claim/cell entries; 67 changed; unmatched extraction patterns: 0. Historical execution observations and literature/configuration facts are kept separate from newly derived mutant outcomes.

## Java and deterministic verification

Production selector: 1349 unique invocations, 3926 weighted occurrences, 0 full-set mismatches, 0 non-SELECTED modes. Loader differing entries: 0; raw/loaded U: 58/58.
The existing harness and hash-verified pinned selector are reused. Runtime JAR/dependency hashes and commands are in `java/runtime.json`. Identical map/class/method inputs may reuse already executed Java results from the preserved attempt; final PIT occurrence weights are recomputed. `invocationProvenance` distinguishes these from fresh invocations. Class/constructor policies remain offline research comparisons.

| Existing check | Exit | Last line |
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

Unified verification: `VERIFY PASSED: unified raw-input re-derivation, all policies/statistics/diagnostics, Java full sets, unchanged six subjects and original-file hashes`.

## Boundaries

CPU exposure and thread configuration are part of the test-execution environment, not merely performance controls. Here, availableProcessors() determines a JGraphT test executor size, and production partitioning uses that size. Changing the JVM-visible processor count can therefore change paths and fault detection even when the source, test scope and PIT thread setting are unchanged. Limiting operating-system CPU utilization is not equivalent to setting ActiveProcessorCount. PIT workers, test executors, and JVM ergonomic threads are separate controls. Future controlled comparisons should record and hold these effective values constant. The retained source supports this mechanism; without a matched counterfactual run it does not prove that CPU settings caused every changed status. This is an iteration finding, not an edit to the current manuscript.
Fixed configuration does not make repeated PIT executions deterministic. Differences can include changed operator semantics and execution-dependent statuses/killing sets; not every numerical difference is attributed uniquely to a specific operator substitution.
Current-results verification logs are separate from the unified verification. Historical model agreement is not reused as production Java proof for new records.

## Repository publication

Commit identity is recorded in the final publication note below. Only `iterations/pit-unify/` is added. `main` and all tags remain untouched. Publication command: `git push origin iteration-pit-unify`.

Evidence commit: `b362ef703af097fe1547faa4311428e52ac79e1d`.
This identifies the complete results and verification snapshot; a documentation-only
follow-up records publication metadata. Both disposable subject checkouts are clean.
The scoped Python/Markdown whitespace check passes; raw build/PIT logs deliberately
retain tool-emitted trailing spaces. No manuscript DOCX/PDF is included, including
inside the preserved intermediate-attempt archive. See `publication.json` for
publication state and commands; neither this commit nor numerical verification
resolves the recorded CPU environment confound.
