# Methodology  - Spring Framework (spring-core)

## Subject Project

- **Project:** Spring Framework  - `spring-core` module
- **Version:** 6.1.22-SNAPSHOT
- **Commit:** `99a366baf6640b275d08dde60f05da719139bb6a`
- **Build tool:** Gradle 8.14
- **Java:** 21 (SapMachine)
- **Test framework:** JUnit 5 (JUnit Platform)
- **Tests:** 4,705 test methods (3,624 with coverage on spring-core classes)

## Sampling Strategy: Curated Stratified

One representative class per subpackage, excluding infrastructure packages (`aot`, `asm`, `cglib`).

**Selection criteria:**
- Lines of code: 80-1200
- At least 3 tests covering the class
- One class per subpackage (22 subpackages -> 22 classes)

**Excluded packages:**
- `org.springframework.aot.*`  - AOT compile-time infrastructure, not representative of runtime behavior
- `org.springframework.asm`  - vendored ASM bytecode library
- `org.springframework.cglib.core`  - vendored CGLIB proxy library

## Coverage Map Generation

The Smart Test Picker Gradle plugin (`com.sap.oss.smart-test-picker:0.1.0`) was applied to the `spring-core` module with JaCoCo instrumentation. The plugin:

1. Configures JaCoCo agent for per-test session isolation
2. Runs all 4,705 tests, producing 7,148 per-test `.exec` files
3. Converts `.exec` files to per-test XML reports (7,120 generated, 27 skipped  - no coverage)
4. Builds a unified JSON coverage map with method-level granularity

**Result:** 3,624 tests mapped to 579 classes, all with method-level coverage information.

## PIT Mutation Testing

PIT 1.17.4 was run per-class via command-line interface against pre-compiled Gradle output.

**Configuration:**
- `fullMutationMatrix=true`  - all tests run against each mutation
- `threads=4`
- `timeoutConst=10000`
- `mutators=DEFAULTS` (PIT default mutator group)
- `targetTests` scoped to parent subpackage per class
- JVM args: `--add-opens=java.base/java.lang=ALL-UNNAMED`

**Results:**
- 22 classes attempted
- 18 produced mutations (4 had no mutable code, 0 timed out)
- 563 total mutations generated
- 454 KILLED (used for evaluation)

## Evaluation Protocol

For each KILLED mutation:
1. Treat the mutated class + method as "changed code"
2. Simulate the plugin's dual-granularity selection algorithm
3. Check if at least one killing test is in the selected set

**Safety (inclusiveness)** = % of mutations where the selected set includes a killing test.

## Baseline Selectors

1. **Coverage (proposed):** Method-level match first; class-level fallback when no method info exists
2. **Class-level only:** Select all tests covering the changed class, ignoring method information
3. **Random(k=per-mutation):** For each mutation, randomly select k tests where k = proposed selector's selection size. Repeated 1000 times with analytical expected value for validation. Per-mutation seed (42 + trial * N + i).
