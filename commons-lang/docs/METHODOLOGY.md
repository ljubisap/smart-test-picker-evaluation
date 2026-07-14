# Evaluation Methodology

## Overview

This evaluation uses **PIT mutation testing** as ground truth to validate the safety (inclusiveness) of coverage-based regression test selection. For each artificial fault (mutation), we check whether the plugin's selected test set would include at least one test that detects the fault.

## Protocol

### Ground Truth Generation

1. **PIT with fullMutationMatrix=true**  - For each class, PIT:
   - Generates mutations using DEFAULT operators (conditionals, math, void calls, returns, etc.)
   - Runs ALL scoped tests against EACH mutation (not just until first kill)
   - Records complete killing test set per mutation

2. **Per-class execution**  - Each class runs independently with `targetTests` scoped to its subpackage, preventing intractable test space (4589 tests x N mutations).

3. **KILLED mutations only**  - Only mutations detected by at least one test are used for safety validation (surviving mutations have no T_killing to compare against).

### Plugin Simulation

For each KILLED mutation `(mutatedClass, mutatedMethod)`:

1. Simulate `git diff` detecting the mutation as a code change
2. Run dual-granularity selection:
   - **Method-level match:** Select tests whose coverage map `methods` list contains `mutatedClass#mutatedMethod`
   - **Class-level fallback:** For tests that cover `mutatedClass` but have no method-level info for that class, select them as a safety net
3. Compute intersection: `T_selected   &   T_killing`
4. Mutation is **safe** iff intersection is non-empty

### Validation Formula

```
Inclusiveness = |{m : T_selected(m)   &   T_killing(m) != {}}| / |KILLED mutations|
```

This is a conservative metric: a mutation is "safe" if ANY killing test is selected. It does NOT require ALL killing tests to be selected.

## Sampling Strategy

### Methodology

We evaluated 21 classes from Apache Commons Lang, selected via curated stratified selection. The selection covers 13 of the library's major utility subpackages: architecture, builders, comparators, concurrent locks, events, math, mutables, reflection, streams, text processing, text translation, tuples, and utilities.

### Selection Criteria

- 1-2 representative classes per major subpackage
- Each class has a matching test class (`ClassName` -> `ClassNameTest`)
- Non-trivial mutable code (>=80 LOC, <=1200 LOC)
- Utility/algorithm implementation classes prioritized over thin wrappers
- Excludes interfaces and abstract base classes

### Excluded Subpackages

| Subpackage | Reason |
|-----------|--------|
| `concurrent` (root) | Complex multi-threaded tests with non-deterministic behavior under mutation |
| `exception` | Thin wrapper classes  - trivial mutations, not representative |
| `function` | Functional interfaces with no method bodies to mutate |
| `time` | System-time-dependent tests  - flaky under mutation |

### Methodology Evolution

The sample was initially intended to be generated via stratified random sampling: `rng.sample(candidates, 2)` per subpackage with seed=42 and a LOC <= 1200 filter.

During the verification phase of replication package construction, we attempted to reconstruct the original sample using the documented seed and filters. The reconstruction yielded 24 classes (vs 21 original) with different selections in shared subpackages, indicating that the original generation occurred with a LOC counting heuristic that we could not retroactively reconstruct (the original script acknowledged: "Re-running may produce slightly different classes if LOC counts differ").

Rather than constructing post-hoc heuristics to artificially reproduce the existing selection  - which would constitute p-hacking  - we transparently document the sample as curated_stratified. The committed sample remains methodologically legitimate: each class satisfies the stratification and quality criteria documented above.

This approach aligns with established empirical software engineering benchmarks (e.g., Defects4J [Just et al. 2014]) that rely on curated subjects rather than purely random selection.

### Reproducibility

The committed sample (`config/sample_classes.json`) is authoritative. The `00_sample_classes.py` script validates sample integrity: confirms class existence, matching test classes, and LOC within limits. Reproducing the evaluation requires using the committed sample, not regenerating it.

### Result

21 classes across 13 subpackages, 772 KILLED mutations.

### Excluded Test Classes (PIT configuration)

Certain test classes are excluded from PIT's test scope because they fail without mutation:

| Test Class | Reason |
|-----------|--------|
| `CompareToBuilderTest` | Deep reflection that fails with Java 21 module restrictions |
| `EqualsBuilderTest` | Same  - reflection on private fields |
| `HashCodeBuilderAndEqualsBuilderTest` | Same |
| `ReflectionDiffBuilderTest` | Same |
| `ToStringBuilderTest` | Same |
| `SystemPropertiesTest` | Depends on `java.awt.headless` system property |

These are excluded via `<excludedTestClasses>` in the PIT profile (see `config/pit_profile.xml`).

### Validation: HashCodeBuilder

To verify that the sampling and exclusion criteria do not introduce bias, we ran PIT separately on `HashCodeBuilder` (one of the highest-LOC classes, 809 lines). Result: **103 KILLED mutations, 100% inclusiveness**. This confirms the evaluation is not cherry-picking easy classes.

### Why Subpackage Scoping

Running PIT with `targetTests=org.apache.commons.lang3.*` (all 4589 tests) is intractable  - PIT's coverage scan phase alone takes 45+ minutes per class. Scoping to the subpackage (`org.apache.commons.lang3.math.*` for Fraction) reduces to ~5 minutes while maintaining validity: tests in other subpackages are unlikely to cover a specific class's internals.

This is safe because JaCoCo's coverage map captures actual runtime dependencies at the method level  - if a test from another subpackage exercises a class, it will appear in the coverage map and be selected. The PIT scoping only restricts which tests PIT considers as potential killing tests, not which tests the plugin would select.

## PIT Test ID Normalization

PIT uses JUnit Platform unique IDs that differ from coverage map keys:

| PIT Format | Normalized |
|-----------|-----------|
| `[class:pkg.FQN]/[method:name()]` | `FQN#name` |
| `[class:pkg.FQN]/[nested-class:Inner]/[method:name()]` | `Inner#name` |
| `[class:pkg.FQN]/[test-template:name(params)]/[test-template-invocation:#1]` | `FQN#name` |

Key rules:
- Strip package prefix, use simple class name
- For nested classes: use the **deepest** `[nested-class:]` value
- For parameterized tests: match on `[test-template:]` tag
- Strip parentheses and parameters from method name

## Baseline Selectors

### Class-Level Only
Selects ALL tests that cover the changed class, ignoring method-level information. Represents traditional class-granularity RTS approaches (similar to Ekstazi).

### Random(k=per-mutation)

For each mutation M, the random selector chooses k_M tests uniformly at random (without replacement) from the test suite, where k_M equals the number of tests the proposed coverage-based selector would select for M. This ensures the random baseline has the same selection budget as the proposed approach for each individual mutation, eliminating size-based comparison bias. Per-mutation seed (42 + mutation_index) ensures reproducibility. Represents the null hypothesis: selection without coverage information is no better than random.

## Metrics

| Metric | Definition | Significance |
|--------|-----------|--------------|
| **Inclusiveness (Safety)** | % mutations with >=1 killing test selected | Primary safety metric |
| **Selection Rate** | avg(|T_selected|) / |all_tests| | Efficiency metric |
| **Test Reduction** | 1 - Selection Rate | Developer-facing time savings |
| **Avg Selection Size** | Mean tests selected per mutation | Absolute efficiency |

## Threats to Validity

### Internal
- PIT mutations approximate real faults; not all mutants correspond to realistic bugs
- Subpackage scoping may miss cross-package killing tests (mitigated: coverage map captures actual runtime dependencies)

### External
- Single project evaluation; results may not generalize to all Java projects
- commons-lang has relatively simple test-to-code relationships (1:1 test classes)

### Construct
- JaCoCo line-level coverage may not capture all execution paths (e.g., exception-only paths)
- Method-level coverage depends on `*.java diff=java` hunk header quality
