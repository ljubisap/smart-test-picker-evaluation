# Joda-Time modern supplementary study

This subject is a modern follow-up motivated by historical reports of unexplained Joda-Time misses. It is deliberately separate from the frozen canonical eight-subject denominator.

The sample and `targetTests` policies in `config/sample_classes.json` were frozen before PIT mutation outcomes or STP inclusiveness results were inspected.

Result: 1,241 PIT mutations, 896 KILLED, and 896/896 STP-inclusive KILLED mutants. This subject is not included in the canonical eight-subject aggregate.

- `REPORT.md`: qualification, mutation results, limitations, and historical-motivation boundary
- `COMMANDS.md`: reproduction commands
- `results/test-coverage-map.json.gz`: canonical per-test map
- `results/per-class/`: one PIT full-matrix run per frozen class
- `results/aggregated/`: per-mutant results, baselines, mitigation, and historical Python evaluator/model agreement
