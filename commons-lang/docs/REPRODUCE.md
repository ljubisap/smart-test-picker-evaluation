# Reproduction Steps

## Prerequisites

Complete all items in [REQUIREMENTS.md](REQUIREMENTS.md) before starting.

## Step 0: Sample Validation

The 21 evaluated classes are committed in `config/sample_classes.json`. Run validation:

```bash
python3 scripts/00_sample_classes.py --project-dir /path/to/commons-lang --verify
```

This confirms all sampled classes exist, have matching test classes, and meet LOC criteria.

## Step 1: Generate Coverage Map

Before running this step, complete the subject-project setup in
[`REQUIREMENTS.md`](REQUIREMENTS.md), including both supplied Maven profiles.

```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang
```

This runs the full test suite with JaCoCo per-test instrumentation, then generates:
- Per-test `.exec` files (JaCoCo binary format)
- Per-test XML reports
- `target/test-coverage-map.json`  - unified coverage map

**Duration:** ~15-25 minutes (depends on hardware and warm/cold cache)
**Output:** `<project-dir>/target/test-coverage-map.json`

To skip test execution (use existing `.exec` files):
```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/commons-lang --skip-tests
```

## Step 2: Run PIT Mutation Testing

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang \
  --results-dir /path/to/fresh-results
```

Runs PIT per-class on all 21 sampled classes with:
- `fullMutationMatrix=true`  - all tests run against each mutation
- `targetTests` scoped to subpackage (prevents intractable test space)
- 10-minute timeout per class

**Duration:** ~5-10 minutes (21 classes sequentially)
**Output:** `/path/to/fresh-results/per-class/<FQN>/mutations.xml`

To run a single class (debugging):
```bash
python3 scripts/02_run_pit.py --project-dir /path/to/commons-lang \
    --class org.apache.commons.lang3.math.Fraction
```

## Step 3: Evaluate Plugin Safety

```bash
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang \
  --results-dir /path/to/fresh-results \
  --coverage-map /path/to/commons-lang/target/test-coverage-map.json
```

Simulates plugin behavior for each KILLED mutation:
1. Treats mutated class+method as "changed code"
2. Runs selection algorithm against coverage map
3. Checks if selected tests include at least one killing test

**Output:**
- `/path/to/fresh-results/aggregated/evaluation_results.csv`
- `/path/to/fresh-results/aggregated/evaluation_summary.json`

## Step 4: Baseline Comparison

```bash
python3 scripts/04_baselines.py --project-dir /path/to/commons-lang \
  --results-dir /path/to/fresh-results \
  --coverage-map /path/to/commons-lang/target/test-coverage-map.json
```

Compares proposed selector against:
- Class-level only (no method granularity)
- Random selection (k = per-mutation proposed selection size)

**Output:** `/path/to/fresh-results/aggregated/baseline_comparison.json`

## Verification

After all steps, verify the freshly generated result (not the committed
canonical artifact):

```bash
python3 -c "
import json
with open('/path/to/fresh-results/aggregated/evaluation_summary.json') as f:
    s = json.load(f)
assert s['inclusiveness_pct'] == 99.87, f'Expected 99.87%, got {s[\"inclusiveness_pct\"]}%'
assert s['unsafe'] == 1, f'Expected 1 unsafe, got {s[\"unsafe\"]}'
assert s['total_mutations'] == 772, f'Expected 772 mutations, got {s[\"total_mutations\"]}'
print('All checks passed.')
"
```

## Expected Results

| Metric | Value |
|--------|-------|
| Tests in coverage map | 4692 |
| KILLED mutations | 772 |
| Classes evaluated | 21 |
| Inclusiveness (Safety) | 99.87% |
| Avg selection size | 17.0 tests |
| Selection rate | 0.36% |
| Test reduction | 99.64% |
| Unsafe mutations | 1 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| PIT "tests did not pass without mutation" | Verify `excludedTestClasses` in PIT profile includes failing tests |
| PIT timeout on LockingVisitors | Expected  - uses threads; increase timeout or exclude |
| Coverage map empty | Ensure `smart-test-picker` profile is active and plugin is in local Maven repo |
| "No mutations found" for a class | Class may have no mutable code; check PIT stdout.log |

## Step 5: Contract Test (Python-Java Equivalence)

```bash
python3 scripts/contract_test.py \
  --project-dir /path/to/commons-lang \
  --mvn /path/to/mvn
```

Requires: coverage map in `target/test-coverage-map.json` (from Step 1), plugin 0.1.0
(commit `70b3984626eb`) in mavenLocal.

For each of the 21 sampled classes, the script:
1. Inserts a marker comment in the first killed mutation's method
2. Commits the change
3. Runs the production `select-tests` Maven mojo
4. Compares Java `selectedTests` with Python `evaluation_core.select_original()`
5. Reverts the commit (try/finally guaranteed)

**Expected output:** 21 EXACT, 0 MISMATCH, 0 INFRA_FAILURE

**Duration:** ~3 minutes (21 Maven invocations)
