# Reproduce — Spring PetClinic Evaluation

Complete step-by-step guide for reproducing the PetClinic safety evaluation from scratch.

## Quick Verification (No Build Required)

The evaluation results can be verified using only the committed data:

```bash
cd petclinic/

# Verify evaluation results
python3 scripts/03_evaluate.py --project-dir /any/path  # uses results/test-coverage-map.json

# Verify baseline comparison
python3 scripts/04_baselines.py --project-dir /any/path  # uses results/test-coverage-map.json

# Verify sampling (all classes, no sampling)
python3 scripts/00_sample_classes.py --verify
```

Expected output from `03_evaluate.py`:
```
Inclusiveness (Safety):  100.00% (94/94)
Avg Selection Size:      9.7 tests
Selection Rate:          18.70%
Test Reduction:          81.30%
```

## Full Reproduction (Build Required)

### Prerequisites

1. Java 21+
2. Spring PetClinic checkout at the evaluation commit:
   ```bash
   git clone https://github.com/spring-projects/spring-petclinic.git
   cd spring-petclinic
   git checkout e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f
   ```

3. Smart Test Picker plugin 0.1.9+ in `mavenLocal`:
   ```bash
   cd /path/to/smart-test-picker-working
   ./gradlew publishToMavenLocal
   ```

4. PetClinic's `build.gradle` must include the PIT and Smart Test Picker plugin config.
   See `config/pitest.gradle` for the exact PIT block to add.

### Step 1: Generate Coverage Map (~1 min)

```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/spring-petclinic
```

What it does:
- `./gradlew clean test` — runs 52 tests with JaCoCo per-test instrumentation
- `./gradlew generateSmartReports` — converts `.exec` files to per-test XML
- `./gradlew generateTestCoverageJson` — builds `build/test-coverage-map.json`

Output: `spring-petclinic/build/test-coverage-map.json` (52 test mappings)

### Step 2: Run PIT Mutation Testing (~2 min)

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/spring-petclinic
```

What it does:
- `./gradlew pitest` — runs PIT with `fullMutationMatrix=true`
- Copies `build/reports/pitest/mutations.xml` to `results/mutations.xml`

Output: 142 mutations (94 KILLED, 37 SURVIVED, 11 NO_COVERAGE)

### Step 3: Evaluate Safety (<1 sec)

```bash
python3 scripts/03_evaluate.py --project-dir /path/to/spring-petclinic
```

What it does:
- For each of 94 KILLED mutations, simulates plugin selection
- Checks if at least one killing test would have been selected
- Writes `results/aggregated/evaluation_summary.json`

Expected: 100.00% inclusiveness (94/94), 0 unsafe mutations

### Step 4: Baseline Comparison (<1 sec)

```bash
python3 scripts/04_baselines.py --project-dir /path/to/spring-petclinic
```

What it does:
- Runs class-level-only selector and random(k=per-mutation) selector
- Writes `results/aggregated/baseline_comparison.json`

Expected:
| Selector | Safety | Avg Selected |
|----------|--------|-------------|
| Coverage (plugin) | 100.00% | 9.7 |
| Class-level only | 100.00% | 18.4 |
| Random(k=per-mutation) | 37.23% | 9.7 |

## Verifying Reproduction

After running all 4 steps, compare outputs:

```bash
# Should show 100.0% inclusiveness, 94 mutations, 52 tests
cat results/aggregated/evaluation_summary.json | python3 -m json.tool

# Cross-check: mutations.xml KILLED count
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('results/mutations.xml')
killed = [m for m in tree.getroot().findall('mutation') if m.get('status')=='KILLED']
print(f'KILLED mutations: {len(killed)}')
assert len(killed) == 94, f'Expected 94, got {len(killed)}'
print('OK')
"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `gradlew: Permission denied` | `chmod +x gradlew` |
| Coverage map not generated | Ensure Smart Test Picker plugin is in `mavenLocal` and configured in `build.gradle` |
| PIT fails with OOM | Increase `-Xmx` in pitest config: `jvmArgs = ['-Xmx4g']` |
| Wrong mutation count | Ensure you're on commit `e4a6ebe3` — different commits may have different code |
| Integration tests fail | They're excluded by default; if Docker isn't available, this is expected |
