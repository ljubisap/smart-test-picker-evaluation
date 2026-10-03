# Legacy verification after B2

This hygiene pass separates legacy edge-only verification from the current B2
policy. No PIT, build, coverage collection, or B2 result recomputation ran.

| Check | Exit | Last non-empty line |
|---|---:|---|
| `python3 -m unittest discover -s analysis/tests` | 0 | `OK` (68 tests) |
| `python3 analysis/analyze_failure_modes.py --verify` | 0 | `VERIFY PASSED: all outputs match committed artifacts` |
| `python3 analysis/verify_selector_equivalence.py --verify` | 0 | `VERIFY PASSED: historical evaluator/model agreement matches committed artifact` |
| `python3 analysis/freeze_artifacts.py --verify` | 0 | `verified spring-security: 25 artifacts` |
| `python3 analysis/verify_recollection.py --verify` | 0 | `VERIFY PASSED: recollection_comparison.json (1837 mutations, 187 selected-set differences, 0 safety flips)` |
| `python3 analysis/v14_4_rederivation/verify_b2.py --verify` | 0 | `VERIFY PASSED: B2 base/constructor/class summaries and selected-set IDs match frozen inputs` |

`results/` data JSON is unchanged. The only expected path under that directory
in this hygiene diff is documentation:
`results/HISTORICAL_SCOPE_NOTES.md`. No frozen coverage map or PIT file changed.
