# Spring Security mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Spring Security 7.1.1 (`spring-security-core`). Inputs were frozen
in commit `47d0c42194c7e1dbd658530e3db9b3faa311897a` before outcomes were
inspected. See `config/subject.json` and `config/sample_classes.json`.

The Gradle adapter is `config/pit.init.gradle`; shared result evaluation is
performed by `analysis/evaluate_subject.py` without project-specific selector
logic.

PIT 1.17.4 cannot transform the qualified JDK 25 class files (major version
69). See `docs/PIT_BLOCKER.md` and `results/blocked.json`; the evaluated PIT or
subject environment was not silently changed.
