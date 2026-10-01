# Hibernate ORM mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Hibernate ORM 7.4.11.Final, using the already-qualified frozen
`hibernate-core` representative scope. Inputs were frozen in commit
`47d0c42194c7e1dbd658530e3db9b3faa311897a` before PIT or STP outcomes were
inspected. See `config/subject.json` and `config/sample_classes.json`.

The Gradle adapter is `config/pit.init.gradle`; shared result evaluation is
performed by `analysis/evaluate_subject.py` with the repository's existing
selector, class-only baseline, random equal-budget baseline, and unchanged
constructor-only mitigation.

The frozen subject could not produce a defensible PIT oracle. See
`docs/PIT_BLOCKER.md` and `results/blocked.json`; no zero-valued mutation result
is imputed.
