# Independent-subject input freeze

Date: 2026-10-01

This freeze precedes all PIT and STP evaluation output for Hibernate ORM, Apache
Flink, Quarkus, and Spring Security. Class selection used source structure,
functional role, concrete source availability, and the already-qualified test
scope only. Coverage-map contents, mutation outcomes, inclusiveness outcomes,
and failure cases were not consulted.

Common mutation protocol:

- PIT 1.17.4 and `pitest-junit5-plugin` 1.2.1;
- `fullMutationMatrix=true`;
- `DEFAULTS` mutators;
- only PIT `KILLED` mutants enter the inclusiveness denominator;
- class-level and 1,000-trial equal-budget random baselines use the existing
  shared evaluator semantics;
- the existing constructor-only mitigation is applied unchanged;
- STP commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, tree
  `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`, JaCoCo path only.

The authoritative project inputs are each project's `config/subject.json` and
`config/sample_classes.json`. Empty, failed, or mutation-free classes remain in
the frozen list and must be reported rather than removed.
