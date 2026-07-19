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
#   Avg Selection Size:      80.6 tests
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
./gradlew :spring-core:test
./gradlew :spring-core:generateTestCoverageJson
```

Note: the two commands must be run separately because the test task exits with a non-zero code due to expected test failures. Running them as a single command line would prevent the second task from executing.

Output: `spring-core/build/test-coverage-map.json` (3,624 test mappings)

Note: 3-5 reflection-based tests may fail due to JaCoCo instrumentation adding synthetic fields (BridgeMethodResolverTests, MergedAnnotationsTests, AnnotationMetadataTests). The exact count varies between runs. This does not affect coverage map generation.

### Step 2: Run PIT Mutation Testing (~15 min)

```bash
# From the evaluation repository root:
python3 spring-core/scripts/02_run_pit.py \
  --project-dir /path/to/spring-framework-6 \
  --results-dir /path/to/fresh-results
```

Requires PIT 1.17.4 jars in local Maven repository. The script downloads them automatically if missing.

The PIT runner will exit with code 1 because 3 classes fail baseline tests and 1 times out. This is expected. The 18 OK classes produce valid `per-class/<FQN>/mutations.xml` files.

Output: `/path/to/fresh-results/per-class/<FQN>/mutations.xml` (18 classes with results)

### Step 3: Evaluate Safety (<1 sec)

```bash
# Copy the fresh coverage map into results for evaluation:
cp /path/to/spring-framework-6/spring-core/build/test-coverage-map.json \
   /path/to/fresh-results/test-coverage-map.json

python3 spring-core/scripts/03_evaluate.py \
  --project-dir /path/to/spring-framework-6 \
  --results-dir /path/to/fresh-results \
  --coverage-map /path/to/fresh-results/test-coverage-map.json
```

Output: `/path/to/fresh-results/aggregated/evaluation_summary.json`

### Step 4: Baseline Comparison (<1 sec)

```bash
python3 spring-core/scripts/04_baselines.py \
  --project-dir /path/to/spring-framework-6 \
  --results-dir /path/to/fresh-results \
  --coverage-map /path/to/fresh-results/test-coverage-map.json
```

Output: `/path/to/fresh-results/aggregated/baseline_comparison.json`

### Using canonical artifacts instead

To reproduce the reported results exactly (without re-running PIT), omit `--results-dir` and `--coverage-map`. The scripts default to the committed canonical artifacts:

```bash
python3 spring-core/scripts/03_evaluate.py --project-dir /any/path
python3 spring-core/scripts/04_baselines.py --project-dir /any/path
```

## Verification (canonical artifacts)

The following check verifies the committed canonical results. Run from the evaluation repository root:

```bash
python3 -c "
import json
with open('spring-core/results/aggregated/evaluation_summary.json') as f:
    s = json.load(f)
assert s['inclusiveness_pct'] == 97.58, f'Expected 97.58%, got {s[\"inclusiveness_pct\"]}%'
assert s['unsafe'] == 11, f'Expected 11 unsafe, got {s[\"unsafe\"]}'
assert s['total_mutations'] == 454, f'Expected 454 mutations, got {s[\"total_mutations\"]}'
print('All checks passed.')
"
```

Note: these assertions apply to the canonical committed PIT artifacts (454 KILLED). A fresh PIT run may produce a different KILLED count due to documented PIT non-determinism; in that case, verify inclusiveness percentage rather than exact mutation counts.

## Expected Results (canonical)

| Metric | Value |
|--------|-------|
| Tests in coverage map | 3,624 |
| KILLED mutations | 454 |
| Classes evaluated | 18 |
| Inclusiveness (Safety) | 97.58% |
| Avg selection size | 80.6 tests |
| Selection rate | 2.22% |
| Test reduction | 97.78% |
| Unsafe mutations | 11 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Plugin not found | Ensure `pluginManagement` + `mavenLocal()` are added to settings/build |
| 3-5 test failures (BridgeMethodResolver, MergedAnnotations, AnnotationMetadata) | Expected  - JaCoCo instrumentation adds synthetic fields, confuses reflection tests; exact count varies |
| DataBufferUtils PIT timeout | Expected  - 1078 LOC reactive class, 600s timeout exceeded |
| PIT "tests did not pass without mutation" | Baseline tests for that class fail independently of mutation (e.g. SerializableTypeWrapper, AbstractResource, PathMatchingResourcePatternResolver). PIT refuses to mutate such classes. |
| Coverage map has fewer tests than test suite | Expected  - only tests covering spring-core classes are mapped |
| Fresh PIT gives different KILLED count | PIT results can vary between runs, particularly for timeout-sensitive tests and code affected by static initialization. `fullMutationMatrix=true` is a partially supported PIT feature. The committed `per-class/*/mutations.xml` files are the canonical artifacts used to reproduce the reported evaluation results. |
| Fresh coverage map differs from canonical | Expected  - per-test method coverage can vary slightly between runs due to JIT compilation, class-loading order, and thread timing. The canonical committed map is the evaluation input. Fresh maps produce identical headline results despite content-level differences in individual test footprints. |
| PIT runner exits with code 1 | Expected when any class has FAILED or TIMEOUT status. The 18 OK classes still produce valid `mutations.xml` files usable for evaluation. |

## Commit Metadata

- **Source benchmark:** `99a366baf6640b275d08dde60f05da719139bb6a` (Spring Framework 6.1.x)
- **Evaluation setup:** `25838a3` (adds STP plugin, mavenLocal, .gitattributes on top of 99a366b; does not modify production Java code)

The coverage map metadata records the evaluation HEAD (`25838a3`) because that is the commit present during collection. PIT targets the same production classes present in the source benchmark.
