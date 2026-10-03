# Legacy-number grep audit

Command:

```text
rg --pcre2 -n "3,986|(?<![0-9])3986(?![0-9])|99\.40" . \
  -g '!analysis/history/**' -g '!analysis/v14_*/**' -g '!.git/**'
```

The remaining metric occurrences are explicitly historical:

- `analysis/README.md:84` is inside the header “Historical edge-only results”.
- `docs/EIGHT_SUBJECT_EXTENSION_REPORT.md:26` is under the top-level
  “HISTORICAL EDGE-ONLY REPORT” banner.
- `hibernate/p0-container-oracle/report.md:37` is under the top-level
  “HISTORICAL EDGE-ONLY REPORT” banner.
- `hibernate/p0-container-oracle/final-decision.json:11,22` is the preserved
  decision-time edge-only aggregate; `results/HISTORICAL_SCOPE_NOTES.md`
  explicitly marks those totals historical.
- `results/eight-subject-summary.json:410` is the byte-preserved legacy
  edge-only summary identified in `results/HISTORICAL_SCOPE_NOTES.md`.
- `results/final-verification.json:30` is byte-preserved historical
  model-verification evidence identified in `results/HISTORICAL_SCOPE_NOTES.md`.

The five matches in
`lightweight-stream-api/results/aggregated/mutation_results.json` are not
metric claims: `3986` is a suffix inside the logical test identity
`IterateTest#testIterateWithPredicate_7dd3986`.

Current results are `results/b2-summary-tables.json`.
