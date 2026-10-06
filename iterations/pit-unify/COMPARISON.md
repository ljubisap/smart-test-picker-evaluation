# Unified PIT comparison

This is a separate iteration; current results and manuscript are unchanged. Mutation IDs are not normalized across XML paths. Exact-ID and semantic correspondence are reported separately.

| Subject | Current mutations / eligible / inclusive / misses | Unified mutations / eligible / inclusive / misses | Six-subject invariance |
|---|---|---|---|
| commons-lang | 932 / 772 / 771 / 1 | 932 / 772 / 771 / 1 | PASS |
| jgrapht | 804 / 517 / 516 / 1 | 803 / 468 / 467 / 1 | Replacement matrix |
| spring-core | 563 / 454 / 443 / 11 | 557 / 419 / 408 / 11 | Replacement matrix |
| petclinic | 139 / 94 / 94 / 0 | 139 / 94 / 94 / 0 | PASS |
| flink | 681 / 349 / 349 / 0 | 681 / 349 / 349 / 0 | PASS |
| spring-security | 520 / 340 / 335 / 5 | 520 / 340 / 335 / 5 | PASS |
| hibernate | 1061 / 401 / 400 / 1 | 1061 / 401 / 400 / 1 | PASS |
| quarkus | 1639 / 1083 / 1083 / 0 | 1639 / 1083 / 1083 / 0 | PASS |

Full operator distributions, policies, intervals, random baselines, residual correspondence, repeat-collection, failed-killer and succeedingTests evidence are in `comparison.json`. Every changed claim is listed in `manuscript_comparison.json` / `MANUSCRIPT_COMPARISON.md`.

## Meaning changes

- The statement that no PIT campaign was rerun no longer describes this iteration: JGraphT and spring-core were replayed at the recorded revisions.
- The two replacement matrices use observed PIT 1.17.4 DEFAULTS rather than the negate-conditional operator found in their stored matrices; the other six matrices are unchanged.
- NegateConditionals is not sufficient evidence of an older PIT version: original JGraphT logs already report pitest-maven 1.17.4, and the PIT 1.17.4 CLI implicit default differs from explicit --mutators DEFAULTS. Spring required that explicit named-group adapter. A manuscript must describe operator/configuration unification, not an established version-only cause.
- Historical evaluator/model agreement and historical plugin-contract statements remain historical observations, not validation of the replacement matrices.
- Residual causal claims must follow failure_annotations_unified.json; an UNDETERMINED annotation cannot be described as a proven early-exception mechanism.
- Method-name counts, case-weighted means, intervals, repeat-collection sensitivity and succeedingTests witnesses describe the new eligible records and must be updated together.
- The CPU control ActiveProcessorCount=1 changes availableProcessors(), which JGraphT TransitNodeRoutingPrecomputationTest uses to size its executor. Consequently this iteration is not established as a PIT-version-only causal experiment; see BLOCKERS.md and results/status_comparison.json.gz.
- CPU exposure and thread settings should be reported as test-execution conditions, not only speed controls. Distinguish JVM-visible processor count, PIT workers, and subject executor parallelism from OS CPU utilization limits. The observed source mechanism is not a controlled attribution of every changed PIT status.
