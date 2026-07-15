# Methodology  - Spring PetClinic Pilot Evaluation

## Overview

Spring PetClinic serves as the **pilot benchmark**  - a small, well-understood project used to verify the complete evaluation pipeline before applying it to larger benchmarks (Apache Commons Lang, Caffeine, etc.).

## Why PetClinic?

1. **Small & fast**  - 52 tests, 14 production classes, PIT completes in ~2 minutes
2. **Gradle-based**  - Tests the Gradle plugin path (vs. Maven for commons-lang)
3. **Spring Boot app**  - Exercises DI, controller layers, JPA entities  - real-world patterns
4. **Known coverage map**  - Already used as proof-of-concept during plugin development

## Evaluation Protocol

### Phase 1: Coverage Map Generation

Run the full test suite with Smart Test Picker's JaCoCo per-test instrumentation:

```bash
./gradlew clean test generateSmartReports generateTestCoverageJson
```

Output: `build/test-coverage-map.json` containing per-test class and method coverage.

### Phase 2: PIT Mutation Testing

Run PIT with `fullMutationMatrix=true` to get complete killing test information:

```bash
./gradlew pitest
```

Output: `build/reports/pitest/mutations.xml` containing all mutations with their killing tests.

### Phase 3: Safety Evaluation

For each KILLED mutation:
1. Extract `mutatedClass` and `mutatedMethod`  - simulate as a "changed" method
2. Run plugin's dual-granularity selection against the coverage map
3. Check if `T_selected intersect T_killing is non-empty` (at least one killing test was selected)

**Inclusiveness (Safety)** = % of KILLED mutations where the plugin would have selected at least one killing test.

### Phase 4: Baseline Comparison

Compare against:
- **Class-level only**  - select all tests touching the mutated class (no method-level filtering)
- **Random(k=per-mutation)**  - for each mutation M, the random selector chooses k_M tests uniformly at random (without replacement) from the test suite, where k_M equals the number of tests the proposed coverage-based selector would select for M. This ensures the random baseline has the same selection budget as the proposed approach for each individual mutation, eliminating size-based comparison bias. Per-mutation seed (42 + mutation_index) ensures reproducibility.

## Differences from Commons Lang

| Aspect | Commons Lang | PetClinic |
|--------|-------------|-----------|
| Build system | Maven | Gradle |
| Sampling | Stratified random (21/~200 classes) | All classes (small project) |
| PIT execution | Per-class (subpackage scoped) | All at once (tractable) |
| PIT output | Per-class dirs with `mutations.xml` | Single `mutations.xml` |
| Test count | 4692 | 52 |
| PIT runtime | ~5 min per class | ~2 min total |

## Scope of Mutations

PIT targets all classes matching `org.springframework.samples.petclinic.*`:
- **17 classes** received mutations (142 total)
- **14 classes** have at least one KILLED mutation (94 total)
- **3 classes** have only SURVIVED/NO_COVERAGE mutations (system config classes)

Safety evaluation uses only KILLED mutations  - the 14-class count is the relevant denominator.

## Excluded Test Classes

Four integration test classes are excluded from both PIT and the coverage map:

| Class | Reason |
|-------|--------|
| `MySqlIntegrationTests` | Requires Docker (Testcontainers) |
| `PostgresIntegrationTests` | Requires Docker (Testcontainers) |
| `PetClinicIntegrationTests` | Full Spring Boot integration test |
| `CrashControllerIntegrationTests` | Error handling integration test |

These tests exercise infrastructure, not production logic. Their exclusion is symmetric  - excluded from both PIT scope and coverage map  - so it doesn't affect safety evaluation validity.

## Mutation Score

PetClinic's mutation score is **66.2%** (94 KILLED / 142 total). This is lower than commons-lang (82.8%) because:
- Several model classes have boilerplate getters/setters that aren't directly tested
- Configuration classes (`CacheConfiguration`, `WebConfiguration`) have no unit tests
- Some controller paths are only tested via integration tests (excluded)

This doesn't affect our safety evaluation  - we only examine KILLED mutations.
