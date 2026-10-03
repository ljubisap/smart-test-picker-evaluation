# Historical result scope notes

`selector_equivalence.json` records agreement between the historical Python edge-only evaluator and a second Python model. It is not Java execution and omits the NO_COVERAGE branch at STP `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`.

`final-verification.json` incorporates that historical model-agreement check; its recorded bytes are preserved, and current production-selector verification is reported separately under `analysis/v14_4_rederivation/`.

`hibernate/p0-container-oracle/final-decision.json` and the quantitative block
in its adjacent `report.md` record the historical edge-only aggregate at the
time of the container-only adjudication. The adjudication remains valid; its
aggregate totals are superseded by `b2-summary-tables.json`.

`eight-subject-summary.json` is preserved byte-for-byte from `8d4cc49` and is
the legacy edge-only summary. The current evaluated-policy results are
`b2-summary-tables.json` and the supporting `b2-*.json` artifacts.

The following per-subject aggregate files are historical inputs/outputs and
are superseded for current cross-subject reporting by `results/b2-*.json`:

- `commons-lang/results/aggregated/evaluation_summary.json`
- `commons-lang/results/aggregated/baseline_comparison.json`
- `jgrapht/results/aggregated/evaluation_summary.json`
- `jgrapht/results/aggregated/baseline_comparison.json`
- `spring-core/results/aggregated/evaluation_summary.json`
- `spring-core/results/aggregated/baseline_comparison.json`
- `petclinic/results/aggregated/evaluation_summary.json`
- `petclinic/results/aggregated/baseline_comparison.json`
- `flink/results/aggregated/evaluation_summary.json`
- `spring-security/results/aggregated/evaluation_summary.json`
- `hibernate/results/aggregated/evaluation_summary.json`
- `quarkus/results/aggregated/evaluation_summary.json`
- `joda-time/results/aggregated/evaluation_summary.json` (supplementary study,
  outside the eight-subject denominator)
- `lightweight-stream-api/results/aggregated/evaluation_summary.json`
  (supplementary study, outside the eight-subject denominator)
