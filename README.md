# Smart Test Picker — Evaluation Replication Package

This is the replication package for the paper:

> **Lightweight Regression Test Selection via Per-Test Runtime Class and Method Coverage in Java**
> *(submitted to ISSTA 2027)*

It contains scripts, configurations, raw results, and documentation for reproducing the mutation-based safety evaluation of Smart Test Picker, a regression test selection tool based on per-test runtime coverage captured via JaCoCo.

## Benchmark Projects

| Project | Tests | Mutations | Safety | Reduction | Status | Folder |
|---------|-------|-----------|--------|-----------|--------|--------|
| Apache Commons Lang | 4589 | 772 | 99.87% | 99.64% | Done | [commons-lang/](commons-lang/) |
| Spring PetClinic | 52 | TBD | TBD | TBD | Pilot (complete) | petclinic/ |
| Caffeine | TBD | TBD | TBD | TBD | Planned | caffeine/ |
| Apache Commons IO | TBD | TBD | TBD | TBD | Planned | commons-io/ |

## Repository Structure

```
smart-test-picker-evaluation/
├── README.md               # This file
├── LICENSE                  # Apache License 2.0
├── .gitignore
└── commons-lang/           # First benchmark project
    ├── README.md           # Project-specific quick start
    ├── config/             # Sampling config, PIT Maven profile
    ├── scripts/            # Numbered evaluation scripts (00-04)
    ├── results/            # Raw PIT output + aggregated metrics
    └── docs/               # Methodology, reproduction, failure analysis
```

See `<project>/docs/README.md` for project-specific reproduction details.

## Methodology

For each benchmark project:

1. **Generate coverage map** — Run full test suite with JaCoCo per-test instrumentation via Smart Test Picker plugin
2. **Run PIT mutation testing** — Per-class with `fullMutationMatrix=true` and subpackage-scoped tests
3. **Evaluate safety** — For each KILLED mutation, simulate plugin selection and check if killing test is included
4. **Baseline comparison** — Compare against class-level-only and random selectors

See `<project>/docs/METHODOLOGY.md` for detailed methodology per project.

## Requirements

- Java 21+, Maven 3.9.6+, Python 3.10+
- Smart Test Picker Maven plugin 0.1.11+ (built from source)
- No external Python packages (stdlib only)

See `<project>/docs/REQUIREMENTS.md` for project-specific prerequisites.

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
@inproceedings{smarttestpicker2027,
  title     = {Lightweight Regression Test Selection via Per-Test Runtime
               Class and Method Coverage in Java},
  author    = {Punosevac, Ljubisa},
  booktitle = {Proceedings of the International Symposium on Software
               Testing and Analysis (ISSTA)},
  year      = {2027},
  note      = {Under submission}
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
