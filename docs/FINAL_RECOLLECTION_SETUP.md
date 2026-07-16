# Final Recollection Setup

Preflight verification for the final coverage-map recollection with the corrected Smart Test Picker collector.

## Corrected Collector

| Field | Value |
|-------|-------|
| Full SHA | `70b3984626ebed16db015c7c261eda132e999f10` |
| Branch | `fix/unique-session-id` |
| Fixes | unique hash-suffixed session IDs (`d42e7d2`), append semantics for parameterized tests (`70b3984`) |
| Old documented pin | `50b44591fe7e9aefb1c0d9ceabce2c8b743f3778` (ancestor; missing both fixes) |
| Artifact version | `0.1.0` |
| Installed | 2026-07-15 23:26 UTC+2 |
| Java | OpenJDK 21.0.11 (SapMachine) |
| Maven | Apache Maven 3.9.15 |
| Gradle | 8.14 |

The old pin `50b4459` was documented before the two collection fixes were implemented. The corrected collector produces hash-suffixed session IDs (`SimpleClass#method_a7f3b2c`) and appends parameterized-test execution data instead of overwriting.

## Benchmark Projects

### Commons Lang ✅ Already recollected

| Field | Value |
|-------|-------|
| Repository | `https://github.com/apache/commons-lang` |
| Benchmark commit | `4492c322d072afdd48d0c8323433c7f5e53dcf53` |
| Evaluation branch | `smart-test-picker-eval` |
| Build tool | Maven |
| Coverage map tests | 4692 |
| Verified | Identical content to committed `test-coverage-map.json.gz` |

### JGraphT

| Field | Value |
|-------|-------|
| Repository | `https://github.com/jgrapht/jgrapht` |
| Benchmark commit | `719212a1fe0bbbf62210159f50920a71e80b73ed` |
| Evaluation branch | `smart-test-picker-eval` (created from benchmark) |
| Build tool | Maven |
| STP profile | `smart-test-picker` in `jgrapht-core/pom.xml` |
| Extension auto-detect | `jgrapht-core/src/test/resources/junit-platform.properties` |
| .gitattributes | `*.java diff=java` |
| Collection command | `python3 jgrapht/scripts/01_generate_coverage_map.py --project-dir <path> --mvn <mvn>` |
| Output path | `jgrapht-core/target/test-coverage-map.json` |
| Old test count | 2308 (no hash suffix) |

### Spring Core

| Field | Value |
|-------|-------|
| Repository | `https://github.com/spring-projects/spring-framework` |
| Benchmark commit | `99a366baf6640b275d08dde60f05da719139bb6a` (6.1.x) |
| Evaluation branch | `smart-test-picker-eval` (created from benchmark) |
| Build tool | Gradle |
| STP plugin | `com.sap.oss.smart-test-picker` v0.1.0 in `spring-core/spring-core.gradle` |
| .gitattributes | `*.java diff=java` (appended to original) |
| Collection command | `./gradlew :spring-core:clean :spring-core:test :spring-core:generateSmartReports :spring-core:generateTestCoverageJson` |
| Output path | `spring-core/build/test-coverage-map.json` |
| Old test count | 3624 (no hash suffix) |

**Note:** The local checkout at `/Users/D061177/work/moje/spring-framework` (v5.0.7.RELEASE) is NOT the evaluation checkout. Use `/Users/D061177/work/moje/spring-framework-6`.

### PetClinic

| Field | Value |
|-------|-------|
| Repository | `https://github.com/spring-projects/spring-petclinic` |
| Benchmark commit | `e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f` |
| Evaluation branch | `smart-test-picker-eval` (created from benchmark) |
| Build tool | Gradle |
| STP plugin | `com.sap.oss.smart-test-picker` v0.1.0 in `build.gradle` |
| .gitattributes | `*.java diff=java` (appended) |
| Collection command | `python3 petclinic/scripts/01_generate_coverage_map.py --project-dir <path>` |
| Output path | `build/test-coverage-map.json` |
| Old test count | 52 (no hash suffix) |

## Expected Format Change

The corrected collector produces hash-suffixed test keys:

```
OLD: AnnotationUtilsTest#testBothArgsNull
NEW: AnnotationUtilsTest#testBothArgsNull_370326c
```

This changes raw key strings but NOT the logical test identity. The evaluation scripts use `base_to_keys` normalization which handles both formats. PIT killing-test resolution proceeds via normalized base names.

If the corrected collector also recovers previously lost tests (due to collision or overwrite in the old collector), the logical test count may increase.

## Documentation Pin Updates

References to the old STP commit `50b44591fe7e` that must be updated:

- `commons-lang/docs/REQUIREMENTS.md`
- `jgrapht/docs/REQUIREMENTS.md`
- `spring-core/docs/REQUIREMENTS.md`
- `spring-core/docs/REPRODUCE.md`
- `petclinic/docs/REQUIREMENTS.md` (×2)
- `petclinic/docs/REPRODUCE.md`

All should reference `70b3984626ebed16db015c7c261eda132e999f10`.

## Decision Tree (if results change)

| Scenario | Action |
|----------|--------|
| Key format change only (same logical count) | Update maps, no PIT rerun |
| Logical test count increases | Update `projects.json` expected, regenerate evaluation |
| PIT killing ID unresolved | Stop, fix resolver |
| Selected-set change without safety flip | Update statistics |
| Unsafe → safe flip | Remove from taxonomy, update annotations |
| Safe → unsafe flip | Manual root-cause analysis required |
| Mutation count or PIT hash change | Stop (should not happen from recollection alone) |
