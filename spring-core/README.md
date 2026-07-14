# Spring Framework — spring-core Evaluation

Safety evaluation of Smart Test Picker against PIT mutation testing ground truth for the `spring-core` module of Spring Framework 6.1.x.

## Results

| Metric | Value |
|--------|-------|
| Tests in coverage map | 3,624 |
| KILLED mutations | 454 |
| Classes evaluated | 18 |
| **Inclusiveness (Safety)** | **97.58%** |
| Avg selection size | 80.3 tests |
| Selection rate | 2.22% |
| **Test reduction** | **97.78%** |
| Unsafe mutations | 11 |

## Baseline Comparison

| Selector | Safety | Avg Selected | Reduction |
|----------|--------|-------------|-----------|
| Coverage (proposed) | 97.58% | 80.3 | 97.78% |
| Class-level only | 100.00% | 527.5 | 85.45% |
| Random(k=per-mutation) | 17.18% | 80.3 | 97.78% |

## Unsafe Mutations Analysis

All 11 unsafe mutations follow a single pattern: `VoidMethodCallMutator` removes a guard clause call (`Assert.notNull`), and the killing test exercises only that guard. JaCoCo's probe-based instrumentation does not register method-level coverage when an exception exits before the probe activates.

**Excluding `VoidMethodCallMutator`: 100% safety (415/415).**

See [docs/FAILURE_MODES.md](docs/FAILURE_MODES.md) for detailed analysis.

## Quick Verification

```bash
# Uses committed coverage map + mutations — no build needed
python3 scripts/03_evaluate.py --project-dir /any/path
python3 scripts/04_baselines.py --project-dir /any/path
```

## Full Reproduction

See [docs/REPRODUCE.md](docs/REPRODUCE.md) for step-by-step instructions.

## Project Details

- **Subject:** Spring Framework `spring-core` module
- **Version:** 6.1.22-SNAPSHOT
- **Commit:** `99a366baf6640b275d08dde60f05da719139bb6a`
- **Build:** Gradle 8.14, Java 21
- **Sampling:** Curated stratified — 1 class per subpackage (22 attempted, 18 with mutations)
