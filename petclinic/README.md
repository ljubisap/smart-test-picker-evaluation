# Spring PetClinic  - Evaluation Quick Start

Pilot benchmark project for Smart Test Picker's mutation-based safety evaluation.

## Key Results

| Metric | Value |
|--------|-------|
| Safety (Inclusiveness) | **100.00%** |
| Test Reduction | **81.30%** |
| Avg Selected Tests | 9.7 / 52 |
| KILLED Mutations | 94 |
| Unsafe Mutations | 0 |

## Project Profile

| | |
|---|---|
| Project | [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) |
| Build System | Gradle |
| Tests | 52 (unit + controller, excl. integration) |
| Production Classes | 14 (with KILLED mutations) |
| Commit | `e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f` |
| Sampling | None (all classes included  - small project) |

## Verify Existing Results (No Build Required)

```bash
cat results/aggregated/evaluation_summary.json | python3 -m json.tool
cat results/aggregated/baseline_comparison.json | python3 -m json.tool
```

## Reproduce from Scratch

```bash
# Prerequisites: Java 21, spring-petclinic checkout, Smart Test Picker plugin in mavenLocal

# Step 1: Generate coverage map (~1 min)
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/spring-petclinic

# Step 2: Run PIT mutation testing (~2 min)
python3 scripts/02_run_pit.py --project-dir /path/to/spring-petclinic

# Step 3: Evaluate safety (~1 sec)
python3 scripts/03_evaluate.py --project-dir /path/to/spring-petclinic

# Step 4: Baseline comparison (~1 sec)
python3 scripts/04_baselines.py --project-dir /path/to/spring-petclinic
```

## Directory Structure

```
petclinic/
|-- README.md                   # This file
|-- config/
|   |-- sample_classes.json     # All 14 classes with at least one KILLED mutation
|   |-- pitest.gradle           # PIT Gradle plugin config (copy-paste ready)
|   `-- pitest_config.md        # Human-readable config documentation
|-- scripts/
|   |-- 00_sample_classes.py    # Class listing + --verify mode
|   |-- 01_generate_coverage_map.py
|   |-- 02_run_pit.py
|   |-- 03_evaluate.py
|   `-- 04_baselines.py
|-- results/
|   |-- mutations.xml           # Raw PIT output (139 mutations, single file)
|   |-- test-coverage-map.json  # Coverage map (52 tests, included for verification)
|   `-- aggregated/
|       |-- evaluation_summary.json
|       |-- evaluation_results.csv
|       |-- pit_summary.json
|       `-- baseline_comparison.json
`-- docs/
    |-- README.md               # Navigation + commons-lang differences
    |-- REPRODUCE.md            # Step-by-step reproduction guide
    |-- METHODOLOGY.md
    |-- REQUIREMENTS.md
    `-- FAILURE_MODES.md
```

## Baseline Comparison

| Selector | Safety | Selection Rate | Avg Selected |
|----------|--------|---------------|--------------|
| **Coverage (plugin)** | **100.00%** | **18.70%** | **9.7** |
| Class-level only | 100.00% | 35.29% | 18.4 |
| Random(k=per-mutation) | 35.97% ± 2.95 | 18.70% | 9.7 |

The plugin achieves 100% killed-mutant inclusiveness within the evaluated 52-test scope while selecting fewer than half as many tests as the class-level-only selector. Random selection at the same per-mutation budget achieves 35.97% mean inclusiveness over 1000 trials.
