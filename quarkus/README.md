# Quarkus Arc mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Quarkus 3.40.1. Tests come from
`independent-projects/arc/tests`; mutable production code comes from the Arc
processor module. Inputs were frozen in commit
`47d0c42194c7e1dbd658530e3db9b3faa311897a` before outcomes were inspected.

The test-module-wide `targetTests` policy is structural and was frozen because
processor behavior crosses test-package boundaries. See `config/subject.json`
and `config/sample_classes.json`.

The exact-test split-module diagnostic succeeds, but the predeclared complete
Arc scope fails in PIT's coverage minion. See `docs/PIT_BLOCKER.md` and
`results/blocked.json`. The scope was not narrowed after observing the failure.
