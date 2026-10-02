# Hibernate ORM mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Hibernate ORM 7.4.11.Final, using the already-qualified frozen
`hibernate-core` representative scope. Inputs were frozen in commit
`47d0c42194c7e1dbd658530e3db9b3faa311897a` before PIT or STP outcomes were
inspected. See `config/subject.json` and `config/sample_classes.json`.

The original JDK 25 attempt was blocked because PIT 1.17.4 cannot process
class-file major version 69. The frozen campaign was repeated on SapMachine 21
without changing the subject, sample, PIT version, mutators, or `targetTests`.
Hibernate's external `-Porm.jdk.min=21` build setting and its bytecode-enhanced
test-engine system property are required. All 16 sampled classes then produced
valid PIT output.

Canonical evaluation uses `results/test-coverage-map.json.gz`,
`results/per-class/*/mutations.xml`, and the shared
`analysis/evaluate_subject.py` implementation. Detailed JDK 21 provenance is
in `docs/JDK21_REFREEZE.md`; the two observed misses are analyzed in
`docs/FAILURE_ANALYSIS.md`. Historical JDK 25 evidence remains under the
`jdk25-*` result paths and is not part of the mutation denominator.
