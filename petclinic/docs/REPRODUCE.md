# Reproduce  - Spring PetClinic Evaluation

Guide for verifying the archived PetClinic evaluation artifacts.

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

## Full Reproduction Status

A build-from-source reproduction is **not currently self-contained** in this
package. Do not treat the commands in the quick-verification section as proof
that a fresh PetClinic build was reproduced.

The archived evaluation records:

- source benchmark `e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f`;
- coverage setup commit `cbb884f`;
- PIT setup commit `2bb92ff`.

The documented upstream repository does not currently advertise the source
benchmark object, and this package does not contain either setup commit or a
complete Smart Test Picker Gradle configuration. Consequently there is no
honest sequence that reconstructs the archived raw artifacts from a clean
upstream checkout using only this repository.

The following section documents the archived collection procedure for
provenance. It is not a from-scratch recipe until the source object and both
setup commits are published.

## Archived Collection Procedure (Not Self-Contained)

### Prerequisites

1. Java 21+
2. Spring PetClinic checkout at the evaluation commit:
   ```bash
   git clone https://github.com/spring-projects/spring-petclinic.git
   cd spring-petclinic
   git checkout e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f
   ```

3. Smart Test Picker plugin 0.1.0 (commit 70b3984626eb) in `mavenLocal`:
   ```bash
   cd /path/to/smart-test-picker-working
   git checkout 70b3984626eb  # pinned for this evaluation (corrected collector)
   ./gradlew publishToMavenLocal
   ```

4. PetClinic's `build.gradle` used separate Smart Test Picker and PIT setup
   commits. Only the PIT block is retained here in `config/pitest.gradle`; the
   complete Smart Test Picker setup is not retained in this package.

### Step 1: Generate Coverage Map (~1 min)

```bash
python3 scripts/01_generate_coverage_map.py --project-dir /path/to/spring-petclinic
```

What it does:
- `./gradlew clean test`  - runs 52 tests with JaCoCo per-test instrumentation
- `./gradlew generateSmartReports`  - converts `.exec` files to per-test XML
- `./gradlew generateTestCoverageJson`  - builds `build/test-coverage-map.json`

Output: `spring-petclinic/build/test-coverage-map.json` (52 test mappings)

### Step 2: Run PIT Mutation Testing (~2 min)

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/spring-petclinic
```

What it does:
- `./gradlew pitest`  - runs PIT with `fullMutationMatrix=true`
- Copies `build/reports/pitest/mutations.xml` to `results/mutations.xml`

Output: 139 mutations (94 KILLED, 34 SURVIVED, 11 NO_COVERAGE)

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
| Random(k=per-mutation) | 35.97% | 9.7 |

## Verifying Archived Artifacts

The following checks apply to the committed archived outputs:

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
| Source commit cannot be checked out | Expected with the currently documented upstream; use committed artifacts until the benchmark object and setup commits are published |
| Integration tests fail | They're excluded by default; if Docker isn't available, this is expected |
