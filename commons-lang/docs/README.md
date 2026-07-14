# Smart Test Picker Evaluation  - Apache Commons Lang

Replication package for evaluating the **Smart Test Picker** regression test selection plugin against PIT mutation testing ground truth.

## Key Results

| Selector | Safety | Selection Rate | Test Reduction |
|----------|--------|----------------|----------------|
| **Coverage (proposed)** | **99.87%** | 0.36% | **99.64%** |
| Class-level only | 99.87% | 1.08% | 98.92% |
| Random (k=per-mutation) | 1.94% | 0.36% | 99.64% |

- **772 KILLED mutations** across 21 classes (4589 tests in coverage map)
- **1 unsafe mutation**  - `FieldUtils.removeFinalModifier` (exception-path coverage gap)
- Method-level selection selects approximately 3x fewer tests than class-level (avg 17 vs 49) at identical measured safety

## Project Structure

```
commons-lang/
|-- config/
|   |-- sample_classes.json      # 21 sampled classes with metadata
|   `-- pit_profile.xml          # PIT Maven profile (add to pom.xml)
|-- scripts/
|   |-- 01_generate_coverage_map.py   # Generate per-test coverage map
|   |-- 02_run_pit.py                 # Run PIT per-class with timeout
|   |-- 03_evaluate.py                # Evaluate safety (inclusiveness)
|   `-- 04_baselines.py               # Compare against baselines
|-- results/
|   |-- per-class/<FQN>/mutations.xml # Raw PIT output per class
|   |-- aggregated/
|   |   |-- evaluation_summary.json   # Full evaluation results
|   |   |-- evaluation_results.csv    # Per-mutation CSV
|   |   |-- baseline_comparison.json  # Selector comparison
|   |   `-- pit_summary.json          # PIT run summary
|   `-- progress.log                  # PIT run progress log
`-- docs/
    |-- README.md                     # This file
    |-- REQUIREMENTS.md               # Prerequisites
    |-- REPRODUCE.md                  # Step-by-step reproduction
    |-- METHODOLOGY.md                # Evaluation methodology
    `-- FAILURE_MODES.md              # Analysis of unsafe mutations
```

## Quick Start

See [REPRODUCE.md](REPRODUCE.md) for full step-by-step instructions.

```bash
# 1. Generate coverage map (requires Smart Test Picker plugin)
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang

# 2. Run PIT mutation testing
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang

# 3. Evaluate safety
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang

# 4. Compare baselines
python3 scripts/04_baselines.py --project-dir /path/to/commons-lang
```

## Subject Project

- **Project:** Apache Commons Lang 3.21.0-SNAPSHOT
- **Commit:** `8538458e7aeb1455a5942f60fe0b4930da6c5d68`
- **Test suite:** 4589 test methods (JUnit 5)
- **Sample:** 21 classes, curated stratified (1-2 per subpackage, see [METHODOLOGY.md](METHODOLOGY.md))

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for detailed methodology including:
- Mutation-based ground truth validation
- Dual-granularity selection algorithm
- PIT test ID normalization
- Subpackage-scoped test targeting strategy
