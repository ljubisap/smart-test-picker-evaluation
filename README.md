# Smart Test Picker — Evaluation Replication Package

Replication package for the empirical evaluation of **Smart Test Picker**, a lightweight regression test selection tool based on per-test runtime coverage.

This repository contains scripts, configurations, raw results, and documentation for reproducing the mutation-based safety evaluation described in Paper 1 (RAD 1).

## Benchmark Projects

| Project | Status | Tests | Mutations | Safety | Reduction |
|---------|--------|-------|-----------|--------|-----------|
| [Apache Commons Lang](commons-lang/) | Complete | 4589 | 772 | 99.87% | 99.64% |
| Caffeine | Planned | — | — | — | — |
| Apache Commons IO | Planned | — | — | — | — |
| Micronaut Core | Planned | — | — | — | — |

## Repository Structure

```
smart-test-picker-evaluation/
├── README.md               # This file
├── LICENSE                  # Apache License 2.0
├── .gitignore
└── commons-lang/           # First benchmark project
    ├── config/             # Sampling config, PIT Maven profile
    ├── scripts/            # Numbered evaluation scripts (00-04)
    ├── results/            # Raw PIT output + aggregated metrics
    └── docs/               # Methodology, reproduction, failure analysis
```

## Methodology

For each benchmark project:

1. **Generate coverage map** — Run full test suite with JaCoCo per-test instrumentation via Smart Test Picker plugin
2. **Run PIT mutation testing** — Per-class with `fullMutationMatrix=true` and subpackage-scoped tests
3. **Evaluate safety** — For each KILLED mutation, simulate plugin selection and check if killing test is included
4. **Baseline comparison** — Compare against class-level-only and random selectors

See `<project>/docs/METHODOLOGY.md` for detailed methodology per project.

## Requirements

- Java 17+, Maven 3.9+, Python 3.9+
- Smart Test Picker Maven plugin 0.1.11+ (built from source)

See `<project>/docs/REQUIREMENTS.md` for project-specific prerequisites.

## Quick Start

```bash
cd commons-lang
# Reproduce from scratch:
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang
python3 scripts/04_baselines.py --project-dir /path/to/commons-lang

# Or verify existing results:
cat results/aggregated/evaluation_summary.json | python3 -m json.tool
```

## Citation

```bibtex
@inproceedings{smarttestpicker2027,
  title     = {Lightweight Regression Test Selection via Per-Test Runtime
               Class and Method Coverage in Java},
  author    = {TBD},
  booktitle = {TBD},
  year      = {2027}
}
```

## License

This work is licensed under the [Apache License 2.0](LICENSE).
