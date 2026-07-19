# Reproduction Steps

## Prerequisites

Complete all items in [REQUIREMENTS.md](REQUIREMENTS.md) before starting.

## Step 0: Sample Validation

The 20 evaluated classes are committed in `config/sample_classes.json`. Run validation:

```bash
python3 scripts/00_sample_classes.py --project-dir /path/to/jgrapht --verify
```

This confirms all sampled classes exist in the project at the evaluation commit.

## Step 1: Generate Coverage Map

```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/jgrapht
```

This runs the full test suite with JaCoCo per-test instrumentation, then generates:
- Per-test `.exec` files (JaCoCo binary format)
- Per-test XML reports
- `jgrapht-core/target/test-coverage-map.json`  - unified coverage map

**Duration:** ~7 minutes
**Output:** `<project-dir>/jgrapht-core/target/test-coverage-map.json`

To skip test execution (use existing `.exec` files):
```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/jgrapht --skip-tests
```

## Step 2: Run PIT Mutation Testing

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/jgrapht
```

Runs PIT per-class on all 20 sampled classes with:
- `fullMutationMatrix=true`  - all tests run against each mutation
- `targetTests` scoped to subpackage (prevents intractable test space)
- 10-minute timeout per class (30 min for BlossomVPrimalUpdater)

**Duration:** ~45 minutes
**Output:** `results/per-class/<FQN>/mutations.xml[.gz]`

To run a single class (debugging):
```bash
python3 scripts/02_run_pit.py --project-dir /path/to/jgrapht \
    --class org.jgrapht.alg.color.GreedyColoring
```

## Step 3: Evaluate Plugin Safety

```bash
python3 scripts/03_evaluate.py --project-dir /path/to/jgrapht
```

Simulates plugin behavior for each KILLED mutation:
1. Treats mutated class+method as "changed code"
2. Runs selection algorithm against coverage map
3. Checks if selected tests include at least one killing test

**Output:**
- `results/aggregated/evaluation_results.csv`
- `results/aggregated/evaluation_summary.json`

## Step 4: Baseline Comparison

```bash
python3 scripts/04_baselines.py --project-dir /path/to/jgrapht
```

Compares proposed selector against:
- Class-level only (no method granularity)
- Random selection (k = per-mutation proposed selection size)

**Output:** `results/aggregated/baseline_comparison.json`

## Verification

After all steps, verify results match expected values:

```bash
python3 -c "
import json
with open('results/aggregated/evaluation_summary.json') as f:
    s = json.load(f)
assert s['inclusiveness_pct'] == 99.81, f'Expected 99.81%, got {s[\"inclusiveness_pct\"]}%'
assert s['unsafe'] == 1, f'Expected 1 unsafe, got {s[\"unsafe\"]}'
assert s['total_mutations'] == 517, f'Expected 517 mutations, got {s[\"total_mutations\"]}'
print('All checks passed.')
"
```

## Expected Results

| Metric | Value |
|--------|-------|
| Tests in coverage map | 2,308 |
| KILLED mutations | 517 |
| Classes evaluated | 20 |
| Inclusiveness (Safety) | 99.81% |
| Avg selection size | 87.7 tests |
| Selection rate | 3.80% |
| Test reduction | 96.20% |
| Unsafe mutations | 1 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| PIT timeout on BlossomVPrimalUpdater | Handled automatically: script uses 1800s override for this class |
| PIT timeout on `Graphs` | Handled automatically: targetTests is narrowed to 3 root test classes in sample_classes.json |
| UndirectedSpecifics NO_COVERAGE | Handled automatically: targetTests is widened to `org.jgrapht.graph.*` in sample_classes.json |
| JPMS reflection errors | Verify `--add-opens` flags in PIT profile cover all sampled packages |
| Coverage map empty | Ensure `smart-test-picker` profile is active and plugin is in local Maven repo |
| "No mutations found" for a class | Class may have no mutable code; check PIT stdout.log |
