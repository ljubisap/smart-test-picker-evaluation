# Spring Security mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Spring Security 7.1.1 (`spring-security-core`). Inputs were frozen
in commit `47d0c42194c7e1dbd658530e3db9b3faa311897a` before outcomes were
inspected. See `config/subject.json` and `config/sample_classes.json`.

The Gradle adapter is `config/pit.init.gradle`; shared result evaluation is
performed by `analysis/evaluate_subject.py` without project-specific selector
logic.

The preserved first attempt shows that PIT 1.17.4 cannot transform JDK 25 class
files (major version 69). The official `-PtestToolchain=21` build mode preserves
the native population and is re-frozen for the canonical mutation campaign;
see `docs/JDK21_REFREEZE.md`. The original blocker evidence remains retained.
