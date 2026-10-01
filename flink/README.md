# Apache Flink mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Flink 2.3.0 (`flink-runtime`, frozen scheduler unit-test scope).
Inputs were frozen in commit `47d0c42194c7e1dbd658530e3db9b3faa311897a`
before PIT or STP outcomes were inspected. See `config/subject.json`,
`config/sample_classes.json`, and `docs/SCOPE_ADJUDICATION.md`.

Canonical commands use `analysis/run_maven_pit.py` and
`analysis/evaluate_subject.py`; PIT is sequential per class, uses three worker
threads, `fullMutationMatrix=true`, `DEFAULTS`, PIT 1.17.4, and JUnit5 plugin
1.2.1. `results/test-coverage-map.json.gz` is the qualified 665-test STP map.
