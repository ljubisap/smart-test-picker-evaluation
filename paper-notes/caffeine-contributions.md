# Caffeine  - Secondary Contributions to Paper 1

## Plugin Engineering Improvements Discovered

### 1. TestClassFilter False Positive
- `CaffeineSpec` (production class) filtered out because `endsWith("Spec")` heuristic
- Fix: need allowlist or smarter heuristic (e.g., only filter if also in test source set)
- Impact: 17 tests lost coverage link to CaffeineSpec without manual patching

### 2. Gradle 9.x Compatibility (Configuration Cache)
- `SmartTestPickerExtension.getRemoteStore()`  - abstract nested managed types break on Gradle 9.x
- Fix: commented out RemoteStoreExtension (not yet implemented anyway)
- `generateSmartReports` task captured `Project` in `doLast` lambda  - breaks config cache
- Fix: extract `buildDir`/`projectDir` before lambda, use `t.getLogger()` inside

### 3. Gradle 8.x vs 9.5 Validation
- Plugin now verified on both Gradle 8.x (PetClinic, Commons Lang) and 9.5 (Caffeine)
- `mavenLocal()` plugin resolution works in both
- `testImplementation("smart-test-picker-core")` works for JUnit extension registration

## Parametrized Test Limitation (Future Work)

- STP uses `context.getTestMethod().map(Method::getName)` for session IDs
- `@ParameterizedTest` invocations merge: 23 methods x N params -> 23 exec files (not Nx23)
- Caffeine's `@CacheSpec` generates 5,000-11,000 invocations per test class
- Coverage is MERGED across all invocations of same method -> still correct for selection
- Not a bug, but worth documenting as design trade-off (space vs granularity)

## Caffeine Project Profile

| Metric | Value |
|--------|-------|
| Build system | Gradle 9.5 (Kotlin DSL) |
| Java | 21 (requires `-PjavaVersion=21`) |
| Total test classes | 39 |
| Focused test classes (PIT scope) | 12 |
| @CacheSpec parametrized classes | ~27 (excluded from PIT) |
| Exec files generated | 424 |
| Coverage map tests | 284 |
| PIT target classes | 12 |
| Commit | 0dc7daf9 |

## Status: Paused

Coverage map generated, plugin integration verified. PIT run with `fullMutationMatrix=true` 
not yet executed. Pivoting to JGraphT as 3rd benchmark project (Maven-based, likely higher 
JUnit 5 adoption).
