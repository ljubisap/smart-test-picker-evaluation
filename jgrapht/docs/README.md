# JGraphT Evaluation  - Replication Package

## Project Details

| Field | Value |
|-------|-------|
| Project | JGraphT  - Java Graph Library |
| Version | 1.6.0-SNAPSHOT |
| Repository | https://github.com/jgrapht/jgrapht |
| Commit | `719212a1fe0bbbf62210159f50920a71e80b73ed` |
| Module | jgrapht-core |
| Java | 21 (SapMachine) |
| Build | Maven 3.8.6 (no wrapper) |
| JUnit | Jupiter 6.0.3 |
| JPMS | Yes (module-info.java)  - disabled via `useModulePath=false` for STP |

## Coverage Map Statistics

| Metric | Value |
|--------|-------|
| Total tests mapped | 2,308 |
| Total classes covered | 563 |
| Total methods covered | 3,133 |
| Coverage map generation time | ~7 minutes |

## PIT Mutation Testing Results

| Metric | Value |
|--------|-------|
| Sampled classes | 20 |
| Completed | 20 |
| Failed | 0 |
| Total mutations | 804 |
| KILLED mutations | 517 |

### Test Scope Adjustments

Two classes required non-standard test scoping:

1. `org.jgrapht.Graphs`  - `targetTests` narrowed to 3 root-package test classes (recursive `org.jgrapht.*` was intractable with 2308 tests x fullMutationMatrix)
2. `org.jgrapht.graph.specifics.UndirectedSpecifics`  - `targetTests` widened to `org.jgrapht.graph.*` (no test classes exist in `graph.specifics` subpackage)

## Evaluation Results

### Safety (Inclusiveness)

| Selector | Safety | Avg Selected | Selection Rate | Test Reduction |
|----------|--------|-------------|----------------|----------------|
| **Coverage (proposed)** | **99.81%** | 76.4 | 3.31% | **96.69%** |
| Class-level only | 100.00% | 206.3 | 8.94% | 91.06% |
| Random (k=per-mutation) | 27.89% | 76.4 | 3.31% | 96.69% |

### Key Findings

- The dual-granularity (method + class) selector achieves **99.81% safety** with **96.69% test reduction**  - one missed mutation out of 517 KILLED mutations across 20 classes.
- Method-level selection provides **2.7x fewer tests** than class-level only (76.4 vs 206.3 avg selected) with only 0.19% safety loss.
- Random selection at the same budget (76.4 tests) achieves only 27.89% inclusiveness  - proving coverage-based selection is non-trivial.

### Unsafe Mutation Analysis

Single unsafe mutation:
- **Class:** `ChristofidesThreeHalvesApproxMetricTSP`
- **Method:** `getTour` (line 97)
- **Killing tests:** `testGetTour0`, `testGetTour2`
- **Root cause:** These two tests cover the class but do NOT have method-level coverage attribution for `getTour` in the coverage map. The dual-granularity algorithm sees method-level info for other tests covering this class and excludes these two via method-only matching.
- **Impact:** Structural limitation of line-level instrumentation  - same pattern as Commons Lang's `FieldUtils` case.

See [FAILURE_MODES.md](FAILURE_MODES.md) for full analysis.

## Sampling Strategy

- Method: curated stratified selection (one class per algorithmic subpackage)
- 20 classes from 20 distinct subpackages
- LOC range: 83  - 1,310
- Criteria: test coverage, non-trivial mutable code (>=80 LOC), algorithm implementation prioritized
- See [METHODOLOGY.md](METHODOLOGY.md) for selection criteria and methodology evolution notes

## Reproduction Steps

```bash
# 1. Clone JGraphT at the evaluation commit
git clone https://github.com/jgrapht/jgrapht.git
cd jgrapht
git checkout 719212a1fe0bbbf62210159f50920a71e80b73ed

# 2. Generate coverage map (requires smart-test-picker-maven 0.1.0 in mavenLocal)
mvn verify -Psmart-test-picker -pl jgrapht-core

# 3. Run PIT on sampled classes
python3 scripts/02_run_pit.py --project-dir /path/to/jgrapht

# 4. Evaluate
python3 scripts/03_evaluate.py --project-dir /path/to/jgrapht

# 5. Baseline comparison
python3 scripts/04_baselines.py --project-dir /path/to/jgrapht
```

## File Layout

```
jgrapht/
|-- config/
|   `-- sample_classes.json          # 20 sampled classes with metadata
|-- scripts/
|   |-- 02_run_pit.py                # PIT runner (per-class, 10min timeout)
|   |-- 03_evaluate.py               # Safety evaluation vs PIT ground truth
|   `-- 04_baselines.py              # Baseline comparison (class-only, random)
|-- results/
|   |-- per-class/                   # Per-class PIT XML + logs
|   |   |-- org.jgrapht.alg.color.GreedyColoring/
|   |   |   |-- mutations.xml
|   |   |   |-- stdout.log
|   |   |   `-- stderr.log
|   |   `-- ...  (20 classes)
|   |-- aggregated/
|   |   |-- pit_summary.json         # PIT run summary
|   |   |-- evaluation_summary.json  # Safety metrics
|   |   |-- evaluation_results.csv   # Per-mutation results
|   |   `-- baseline_comparison.json # Three-way comparison
|   `-- progress.log                 # Timestamped run log
`-- docs/
    |-- README.md                    # This file
    |-- METHODOLOGY.md               # Detailed evaluation methodology
    `-- FAILURE_MODES.md             # Unsafe mutation root cause analysis
```

## Comparison with Other Benchmark Projects

| Metric | PetClinic | Commons Lang | **JGraphT** |
|--------|-----------|-------------|------------|
| Total tests | 52 | 4,692 | 2,308 |
| Classes sampled | 14 | 21 | 20 |
| Mutations (KILLED) | 94 | 772 | 517 |
| Safety | 100% | 99.87% | 99.81% |
| Test Reduction | 81.30% | 99.64% | 96.69% |
| Avg Selected | 9.7 | 17.0 | 76.4 |
| Build system | Gradle | Maven | Maven |
| JPMS | No | No | Yes |
