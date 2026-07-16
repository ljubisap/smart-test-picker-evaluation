# Smart Test Picker  - Evaluation Replication Package

This is the replication package for the paper:

> **Lightweight Regression Test Selection via Per-Test Runtime Class and Method Coverage in Java**
> *(prepared for submission to ISSTA 2027)*

It contains scripts, configurations, raw results, and documentation for reproducing the mutation-based inclusiveness evaluation of Smart Test Picker, a regression test selection tool based on per-test runtime coverage captured via JaCoCo.

## Benchmark Projects

| Project | Tests | Mutations | Inclusiveness | Reduction | Avg Sel. | Status | Folder |
|---------|-------|-----------|---------------|-----------|----------|--------|--------|
| Apache Commons Lang | 4692 | 772 | 99.87% | 99.64% | 17.0 | Done | [commons-lang/](commons-lang/) |
| JGraphT | 2308 | 517 | 99.81% | 96.69% | 76.4 | Done | [jgrapht/](jgrapht/) |
| Spring Framework (spring-core) | 3624 | 454 | 97.58% | 97.78% | 80.3 | Done | [spring-core/](spring-core/) |
| Spring PetClinic | 52 | 94 | 100.00% | 81.30% | 9.7 | Done (pilot) | [petclinic/](petclinic/) |

## Sampling Strategies

| Project | Strategy | Rationale |
|---------|----------|-----------|
| Commons Lang | curated_stratified | 1-2 representative classes per utility subpackage (13 subpackages) |
| JGraphT | curated_stratified | One class per algorithmic subpackage (20 subpackages) |
| Spring Framework | curated_stratified | One class per spring-core subpackage (22 subpackages), excl. infrastructure |
| PetClinic | all_classes | Small project; 17 classes mutated, 14 with killed mutants |

## Repository Structure

```
smart-test-picker-evaluation/
|-- README.md               # This file
|-- LICENSE                  # Apache License 2.0
|-- .gitignore
|-- commons-lang/           # Benchmark: Apache Commons Lang (Maven, 4692 tests)
|   |-- config/             # Sampling config, PIT Maven profile
|   |-- scripts/            # Numbered evaluation scripts (00-04)
|   |-- results/            # Raw PIT output + aggregated metrics
|   `-- docs/               # Methodology, reproduction, failure analysis
|-- jgrapht/                # Benchmark: JGraphT (Maven multi-module, Java modules via JPMS, 2308 tests)
|   |-- config/             # Sampling config (20 classes, curated stratified)
|   |-- scripts/            # Evaluation scripts (00-04)
|   |-- results/            # Raw PIT output + aggregated metrics
|   `-- docs/               # Methodology, reproduction, failure analysis
|-- spring-core/            # Benchmark: Spring Framework spring-core (Gradle, 3624 tests)
|   |-- config/             # Sampling config (22 classes, curated stratified)
|   |-- scripts/            # Evaluation scripts (02-04)
|   |-- results/            # Raw PIT output + aggregated metrics
|   `-- docs/               # Methodology, reproduction, failure analysis
`-- petclinic/              # Pilot: Spring PetClinic (Gradle, 52 tests)
|-- analysis/              # Shared evaluation core, taxonomy and verification
|   |-- evaluation_core.py  # Shared selectors, loading, resolution
|   |-- analyze_failure_modes.py  # Taxonomy and mitigation (--write, --verify)
|   |-- projects.json       # Project configuration
|   `-- failure_annotations.json  # Manual root-cause annotations
`-- results/               # Cross-project taxonomy and mitigation outputs
    |-- config/
    |-- scripts/
    |-- results/
    `-- docs/
```

See `<project>/docs/README.md` for project-specific reproduction details.

## Methodology

For each benchmark project:

1. **Generate coverage map** - Run full test suite with JaCoCo per-test instrumentation via Smart Test Picker plugin
2. **Run PIT mutation testing** - Per-class with `fullMutationMatrix=true` and subpackage-scoped tests (PetClinic uses whole-project single run)
3. **Evaluate inclusiveness** - For each KILLED mutation, simulate plugin selection and check if at least one PIT-reported killing test (from the configured test scope) is in the selected set
4. **Baseline comparison** - Compare against class-level-only and random selectors (1000 Monte Carlo trials + analytical expectation)

The evaluation measures **killed-mutant inclusiveness**: the fraction of killed mutations for which the selector would have included at least one killing test. The term "safety" is used as shorthand in scripts and output.

Note: For Commons Lang, JGraphT, and spring-core, PIT `targetTests` is scoped to the subpackage of each target class. PetClinic uses its configured whole-project 52-test scope. Cross-package killing tests are not measured for the per-class projects. Results reflect inclusiveness within the configured test scope, not the complete test suite.

See `<project>/docs/METHODOLOGY.md` for detailed methodology per project.

## Requirements

- Java 21+, Maven 3.9.6+, Python 3.10+
- Smart Test Picker plugin 0.1.0 (built from source, commit pinned per project)
- No external Python packages (stdlib only)

See `<project>/docs/REQUIREMENTS.md` for project-specific prerequisites.

## Quick Verification

```bash
# Unit tests (no external dependencies)
python3 -m unittest discover -s analysis/tests

# Verify taxonomy and mitigation outputs match committed artifacts
python3 analysis/analyze_failure_modes.py --verify

# Verify Python/Java selector equivalence
python3 analysis/verify_selector_equivalence.py --verify
```

## Quick Start

```bash
cd commons-lang

# Verify existing results (no build required):
cat results/aggregated/evaluation_summary.json | python3 -m json.tool

# Reproduce from scratch (requires commons-lang checkout + plugin):
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang
python3 scripts/04_baselines.py --project-dir /path/to/commons-lang
```

## Citation

If you use this work, please cite both the paper and the replication package:

```bibtex
@unpublished{smarttestpicker2027,
  title     = {Lightweight Regression Test Selection via Per-Test Runtime
               Class and Method Coverage in Java},
  author    = {Punosevac, Ljubisa},
  year      = {2026},
  note      = {Prepared for submission to ISSTA 2027}
}

@misc{smarttestpicker_replication2026,
  title        = {Smart Test Picker Evaluation Replication Package},
  author       = {Punosevac, Ljubisa},
  year         = {2026},
  howpublished = {\url{https://github.com/ljubisap/smart-test-picker-evaluation}},
  note         = {Replication package for paper ``Lightweight Regression
                  Test Selection via Per-Test Runtime Class and Method
                  Coverage in Java''}
}
```

## License

This work is licensed under the [Apache License 2.0](LICENSE).
