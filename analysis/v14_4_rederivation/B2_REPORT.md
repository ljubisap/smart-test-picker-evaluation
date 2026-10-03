# B2 final report

## Verdict

`B2_VERIFIED`

All gates G1-G7 passed: `{"G1": true, "G2": true, "G3": true, "G4": true, "G5": true, "G6": true, "G7": true}`. Gate source: `promotion_status.json:2-12` (evaluation repository HEAD `8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580`; dirty working-tree outputs are identified by hashes, not an invented commit).

## Evaluator and regression

The current evaluator implements `U ∪ (H if H else G)` in `analysis/evaluation_core.py:456-476`; legacy edge-only selection remains at `analysis/evaluation_core.py:431-453`. Class selection is `U ∪ G` at `analysis/evaluation_core.py:519-531`, and the unchanged constructor predicate remains at `analysis/evaluation_core.py:484-516`. The full regression suite ran 68 tests with zero failures (`regression_output.txt:1-5`).

## Re-derived results

- Base: 3991/4010 (99.52618453865337%; `summary_tables.json:438-end`).
- Constructor: 3998/4010 (99.70074812967582%).
- Class: 4009/4010 (99.97506234413964%).
- Spring Security base/constructor/class: 335/337/340 of 340 (`summary_tables.json:275`).
- Residual taxonomy and recovered records are in `residual_taxonomy.json:1-end`; labels in `results/failure_taxonomy.json` were not changed.
- Random baseline, Wilson intervals and 137-cluster bootstrap inputs/results are in `random_baseline.json:1-end`, `confidence_intervals.json:1-end`, and `bootstrap_cluster_inputs.json:1-end`.
- Cell-by-cell comparison with the earlier sensitivity has zero differences (`partb_delta.json:2`).
- Table 4 reports the exact analytical random-equal-budget expectation. The 1,000-trial Monte Carlo check uses one Bernoulli draw per record/trial with the exact uniform-subset intersection probability; its seed and full-precision comparison remain in `random_baseline.json:1-end`.
- `per_record_outcomes.json` stores each canonical sorted selected set once under its SHA-256 and references it from all 4,010 records. This is a lossless hosting-safe representation; `compact_per_record_outcomes.py:1-end` verifies counts and updates the promoted digest.

## Real Java verification

The unchanged selector was freshly built from STP commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, tree `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`; build/classpath/JAR/class hashes are in `java_build.json:1-end`. Production change input is documented with source lines in `change_input_mapping.md:1-20`. Production reader comparison found 0 differing entries and equal raw/loaded U sets totaling 34 (`loader_content_equality.json:1-end`). The public production selector was called 1351 times, covering 4010 weighted occurrences, with 0 full-set mismatches and 0 NONE/FULL_SUITE outcomes (`java_comparison.json:1-10`). Class and constructor comparisons remain evaluator-only research policies.

## Preservation and scope

Frozen maps, PIT XML, exclusions and `analysis/projects.json` have identical before/after aggregate hashes (`input_hashes_before.json:1-end`; `input_hashes_after.json:1-end`). Historical result bytes were archived under `analysis/history/pre_b2_8d4cc49/`; the two I-5-modified canonical JSON files were restored byte-for-byte and qualified in `results/HISTORICAL_SCOPE_NOTES.md:1-8` (`results_restore.json:1-end`). `results/contract_test.json` was not modified.

Actual execution scope: 68 local Python analysis tests; one isolated offline STP common-module build with tests excluded; eight-map loader comparison; 1,351 selection-only Java invocations. No PIT, coverage collection, subject build/test, source/test change, commit, or push was performed.

Deliverables are all files under `analysis/v14_4_rederivation/` plus the promoted paths enumerated in `promotion_status.json`.
