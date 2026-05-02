# Reproduction Steps

## Prerequisites

Complete all items in [REQUIREMENTS.md](REQUIREMENTS.md) before starting.

## Step 1: Generate Coverage Map

```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang
```

This runs the full test suite with JaCoCo per-test instrumentation, then generates:
- Per-test `.exec` files (JaCoCo binary format)
- Per-test XML reports
- `target/test-coverage-map.json` — unified coverage map

**Duration:** ~10 minutes  
**Output:** `<project-dir>/target/test-coverage-map.json`

To skip test execution (use existing `.exec` files):
```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang --skip-tests
```

## Step 2: Run PIT Mutation Testing

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang
```

Runs PIT per-class on all 21 sampled classes with:
- `fullMutationMatrix=true` — all tests run against each mutation
- `targetTests` scoped to subpackage (prevents intractable test space)
- 10-minute timeout per class

**Duration:** ~5 minutes  
**Output:** `results/per-class/<FQN>/mutations.xml`

To run a single class (debugging):
```bash
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang \
    --class org.apache.commons.lang3.math.Fraction
```

## Step 3: Evaluate Plugin Safety

```bash
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang
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
python3 scripts/04_baselines.py --project-dir /path/to/commons-lang
```

Compares proposed selector against:
- Class-level only (no method granularity)
- Random selection (k = avg proposed selection size)

**Output:** `results/aggregated/baseline_comparison.json`

## Verification

After all steps, verify results match expected values:

```bash
python3 -c "
import json
with open('results/aggregated/evaluation_summary.json') as f:
    s = json.load(f)
assert s['inclusiveness_pct'] == 99.87, f'Expected 99.87%, got {s[\"inclusiveness_pct\"]}%'
assert s['unsafe_count'] == 1, f'Expected 1 unsafe, got {s[\"unsafe_count\"]}'
assert s['pit_killed_mutations'] == 772, f'Expected 772 mutations, got {s[\"pit_killed_mutations\"]}'
print('All checks passed.')
"
```

## Expected Results

| Metric | Value |
|--------|-------|
| Tests in coverage map | 4589 |
| KILLED mutations | 772 |
| Classes evaluated | 21 |
| Inclusiveness (Safety) | 99.87% |
| Avg selection size | 16.7 tests |
| Selection rate | 0.36% |
| Test reduction | 99.64% |
| Unsafe mutations | 1 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| PIT "tests did not pass without mutation" | Verify `excludedTestClasses` in PIT profile includes failing tests |
| PIT timeout on LockingVisitors | Expected — uses threads; increase timeout or exclude |
| Coverage map empty | Ensure `smart-test-picker` profile is active and plugin is in local Maven repo |
| "No mutations found" for a class | Class may have no mutable code; check PIT stdout.log |
