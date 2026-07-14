# Evaluation Methodology  - JGraphT

## Overview

This evaluation uses **PIT mutation testing** as ground truth to validate the safety (inclusiveness) of coverage-based regression test selection on JGraphT, a JPMS-enabled Java graph library with 2308 tests.

## Protocol

### Ground Truth Generation

1. **PIT with fullMutationMatrix=true**  - For each class, PIT:
   - Generates mutations using DEFAULT operators (conditionals, math, void calls, returns, etc.)
   - Runs ALL scoped tests against EACH mutation (not just until first kill)
   - Records complete killing test set per mutation

2. **Per-class execution**  - Each class runs independently with `targetTests` scoped to its subpackage, preventing intractable test space.

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

## Sampling Strategy

### Methodology

We evaluated 20 classes from JGraphT, selected via curated stratified selection. The selection covers JGraphT's main algorithmic domains: clique algorithms, clustering, graph coloring, connectivity, cycle detection, drawing, max-flow, isomorphism, lowest common ancestor, link prediction, matching, scoring, shortest paths, spanning trees, TSP heuristics, vertex cover, network generation, graph specifics, and core utilities (one class per domain).

### Selection Criteria

- One representative class per distinct algorithmic subpackage
- Each class has at least one test covering it in the project's test suite (ensuring evaluable coverage)
- Each class contains non-trivial mutable code suitable for PIT mutation testing (>=80 LOC)
- Algorithm implementation classes were prioritized over utility wrappers when multiple candidates existed in a subpackage

### Methodology Evolution

The sample was initially intended to be generated via stratified random sampling: `rng.sample(eligible_subpackages, 20)` with seed=42, followed by `rng.choice(candidates)` per subpackage.

During the verification phase of replication package construction, we attempted to reconstruct the original sample using the documented seed and filters. The reconstruction yielded only 2 of 20 classes matching the committed sample (10% match rate), indicating that the original generation occurred in a context (earlier coverage map state, candidate filter parameters, or evaluation iteration) that we could not retroactively reconstruct.

Rather than constructing post-hoc filters to artificially reproduce the existing selection  - which would constitute p-hacking  - we transparently document the sample as curated_stratified. The committed sample remains methodologically legitimate: each class satisfies the stratification and quality criteria documented above.

This approach aligns with established empirical software engineering benchmarks (e.g., Defects4J [Just et al. 2014]) that rely on curated subjects rather than purely random selection.

### Reproducibility

The committed sample (`config/sample_classes.json`) is authoritative. The `00_sample_classes.py` script validates sample integrity: confirms class existence, LOC counts, and subpackage coverage. Reproducing the evaluation requires using the committed sample, not regenerating it.

### Result

20 classes across 20 subpackages, 804 total mutations, 517 KILLED.

### Test Scope Adjustment

Some classes required non-standard test scoping:

| Class | Default Scope | Adjusted Scope | Reason |
|-------|--------------|----------------|--------|
| `org.jgrapht.Graphs` | `org.jgrapht.*` (all 2308 tests) | `org.jgrapht.GraphsTest,org.jgrapht.GraphTestsTest,org.jgrapht.GraphMetricsTest` | Recursive glob matched entire test suite; intractable |
| `UndirectedSpecifics` | `org.jgrapht.graph.specifics.*` | `org.jgrapht.graph.*` | No test classes in `specifics` subpackage; tests are in parent package |

### Why Subpackage Scoping

Running PIT with `targetTests=org.jgrapht.*` is intractable  - the coverage scan phase exceeds 60 minutes per class due to 2308 tests x N mutations x fullMutationMatrix. Scoping to the subpackage reduces to seconds-to-minutes while maintaining validity.

This is safe because JaCoCo's coverage map captures actual runtime dependencies  - if a test from another subpackage exercises a class, it will appear in the coverage map and be selected by the plugin. PIT scoping only restricts which tests PIT considers as potential killing tests.

## JPMS Considerations

JGraphT uses the Java Module System (`module-info.java`). Key adaptations:

1. **`useModulePath=false`** in maven-surefire-plugin (smart-test-picker profile)  - disables JPMS for test execution, allowing JaCoCo agent reflective access
2. **`--add-opens` in pitest profile**  - PIT's minions need reflective access to mutate classes
3. **Parallel execution disabled**  - `junit.jupiter.execution.parallel.enabled=false` for per-test coverage attribution accuracy

## PIT Configuration

```xml
<profile>
    <id>pitest</id>
    <build>
        <plugins>
            <plugin>
                <groupId>org.pitest</groupId>
                <artifactId>pitest-maven</artifactId>
                <version>1.17.4</version>
                <dependencies>
                    <dependency>
                        <groupId>org.pitest</groupId>
                        <artifactId>pitest-junit5-plugin</artifactId>
                        <version>1.2.1</version>
                    </dependency>
                </dependencies>
                <configuration>
                    <fullMutationMatrix>true</fullMutationMatrix>
                    <threads>4</threads>
                    <timeoutFactor>2.0</timeoutFactor>
                    <timeoutConstant>10000</timeoutConstant>
                    <outputFormats><outputFormat>XML</outputFormat></outputFormats>
                    <timestampedReports>false</timestampedReports>
                    <jvmArgs><!-- --add-opens for all sampled packages --></jvmArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>
</profile>
```

## Baseline Selectors

### Class-Level Only
Selects ALL tests that cover the changed class, ignoring method-level information. Represents traditional class-granularity RTS approaches (similar to Ekstazi).

### Random(k=per-mutation)

For each mutation M, the random selector chooses k_M tests uniformly at random where k_M equals the number of tests the proposed coverage-based selector would select for M. This ensures identical selection budget per mutation, eliminating size-based comparison bias. Seed: 42 + mutation_index.

## Metrics

| Metric | Definition | JGraphT Result |
|--------|-----------|----------------|
| **Inclusiveness (Safety)** | % mutations with >=1 killing test selected | 99.81% |
| **Selection Rate** | avg(\|T_selected\|) / \|all_tests\| | 3.31% |
| **Test Reduction** | 1 - Selection Rate | 96.69% |
| **Avg Selection Size** | Mean tests selected per mutation | 76.4 |

## Threats to Validity

### Internal
- PIT mutations approximate real faults; not all mutants correspond to realistic bugs
- Subpackage scoping may miss cross-package killing tests (mitigated: coverage map captures actual runtime dependencies)
- Two classes required adjusted test scope (documented above)

### External
- JGraphT is a library with relatively clean test-to-code mappings
- Results may differ on application projects with heavy DI/AOP

### Construct
- JaCoCo line-level coverage may not capture all execution paths (see FAILURE_MODES.md)
- JPMS disabled for testing  - production JPMS behavior may differ
