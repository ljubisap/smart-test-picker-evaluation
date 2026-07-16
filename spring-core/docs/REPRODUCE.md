# Reproduction Steps  - Spring Framework (spring-core)

## Quick Verification (No Build Required)

The evaluation results can be verified using only the committed data:

```bash
cd spring-core/

# Verify evaluation results
python3 scripts/03_evaluate.py --project-dir /any/path

# Verify baseline comparison
python3 scripts/04_baselines.py --project-dir /any/path

# Expected output from 03_evaluate.py:
#   Inclusiveness (Safety):  97.58% (443/454)
#   Avg Selection Size:      80.3 tests
#   Selection Rate:          2.22%
#   Test Reduction:          97.78%
```

## Full Reproduction (Build Required)

### Prerequisites

1. Java 21+ (SapMachine or Temurin)
2. Spring Framework checkout:
   ```bash
   git clone --depth 1 --branch 6.1.x https://github.com/spring-projects/spring-framework.git spring-framework-6
   cd spring-framework-6
   git checkout 99a366baf6640b275d08dde60f05da719139bb6a
   ```

3. Smart Test Picker plugin 0.1.0 in `mavenLocal`:
   ```bash
   cd /path/to/smart-test-picker-working
   git checkout 70b3984626eb  # pinned for this evaluation (corrected collector)
   ./gradlew publishToMavenLocal
   ```

4. Modify `spring-framework-6/settings.gradle`  - add `pluginManagement` block:
   ```groovy
   pluginManagement {
       repositories {
           mavenLocal()
           gradlePluginPortal()
           mavenCentral()
       }
   }
   ```

5. Modify `spring-framework-6/build.gradle`  - add `mavenLocal()` to allprojects repositories:
   ```groovy
   configure(allprojects) { project ->
       repositories {
           mavenLocal()  // <- add this line
           mavenCentral()
           ...
       }
   }
   ```

6. Modify `spring-framework-6/spring-core/spring-core.gradle`  - add plugins and dependency:
   ```groovy
   plugins {
       id 'me.champeau.mrjar'
       id 'jacoco'
       id 'com.sap.oss.smart-test-picker' version '0.1.0'
   }
   ```
   And in `dependencies`:
   ```groovy
   testRuntimeOnly("com.sap.oss.smart-test-picker:smart-test-picker-core:0.1.0")
   ```

7. Add `.gitattributes` in project root:
   ```
   *.java diff=java
   ```

### Step 1: Generate Coverage Map (~3 min)

```bash
cd spring-framework-6
./gradlew :spring-core:test :spring-core:generateTestCoverageJson
```

Output: `spring-core/build/test-coverage-map.json` (3,624 test mappings)

Note: 3 reflection-based tests fail due to JaCoCo instrumentation adding synthetic fields. This does not affect coverage map generation.

### Step 2: Run PIT Mutation Testing (~15 min)

```bash
python3 scripts/02_run_pit.py --project-dir /path/to/spring-framework-6
```

Requires PIT 1.17.4 jars in local Maven repository. The script downloads them automatically if missing.

Output: `results/per-class/<FQN>/mutations.xml`

### Step 3: Evaluate Safety (<1 sec)

```bash
python3 scripts/03_evaluate.py --project-dir /path/to/spring-framework-6
```

Output: `results/aggregated/evaluation_summary.json`

### Step 4: Baseline Comparison (<1 sec)

```bash
python3 scripts/04_baselines.py --project-dir /path/to/spring-framework-6
```

Output: `results/aggregated/baseline_comparison.json`

## Verification

```bash
python3 -c "
import json
with open('results/aggregated/evaluation_summary.json') as f:
    s = json.load(f)
assert s['inclusiveness_pct'] == 97.58, f'Expected 97.58%, got {s[\"inclusiveness_pct\"]}%'
assert s['unsafe'] == 11, f'Expected 11 unsafe, got {s[\"unsafe\"]}'
assert s['total_mutations'] == 454, f'Expected 454 mutations, got {s[\"total_mutations\"]}'
print('All checks passed.')
"
```

## Expected Results

| Metric | Value |
|--------|-------|
| Tests in coverage map | 3,624 |
| KILLED mutations | 454 |
| Classes evaluated | 18 |
| Inclusiveness (Safety) | 97.58% |
| Avg selection size | 80.3 tests |
| Selection rate | 2.22% |
| Test reduction | 97.78% |
| Unsafe mutations | 11 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Plugin not found | Ensure `pluginManagement` + `mavenLocal()` are added to settings/build |
| 3 test failures (BridgeMethodResolver, AnnotationMetadata) | Expected  - JaCoCo instrumentation adds synthetic fields, confuses reflection tests |
| DataBufferUtils PIT timeout | Expected  - 1078 LOC reactive class, 600s timeout exceeded |
| "No mutations found" | Class is abstract/interface with no mutable code (e.g. AbstractResource) |
| Coverage map has fewer tests than test suite | Expected  - only tests covering spring-core classes are mapped |
