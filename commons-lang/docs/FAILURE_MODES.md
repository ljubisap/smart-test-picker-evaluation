# Failure Mode Analysis

## Summary

Out of 772 KILLED mutations, exactly **1 mutation** was not safely covered by the plugin's selection. This documents the root cause and its implications.

## The Unsafe Mutation

| Field | Value |
|-------|-------|
| Class | `org.apache.commons.lang3.reflect.FieldUtils` |
| Method | `removeFinalModifier` |
| Line | 563 |
| Mutator | `VoidMethodCallMutator` |
| Killing Test | `FieldUtilsTest#testRemoveFinalModifierNullPointerException` |

### PIT XML (from `results/per-class/org.apache.commons.lang3.reflect.FieldUtils/mutations.xml`)

```xml
<mutation detected="true" status="KILLED" numberOfTestsRun="1">
  <sourceFile>FieldUtils.java</sourceFile>
  <mutatedClass>org.apache.commons.lang3.reflect.FieldUtils</mutatedClass>
  <mutatedMethod>removeFinalModifier</mutatedMethod>
  <methodDescription>(Ljava/lang/reflect/Field;)V</methodDescription>
  <lineNumber>563</lineNumber>
  <mutator>org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator</mutator>
  <killingTests>
    org.apache.commons.lang3.reflect.FieldUtilsTest.[engine:junit-jupiter]/
    [class:org.apache.commons.lang3.reflect.FieldUtilsTest]/
    [method:testRemoveFinalModifierNullPointerException()]
  </killingTests>
</mutation>
```

## Root Cause: Exception-Path Coverage Gap

### What Happened

The mutation removes a void method call at the entry of `removeFinalModifier()`. The killing test `testRemoveFinalModifierNullPointerException` passes a null argument that causes a `NullPointerException` at line 563  - **before any instrumented line executes**.

### Why JaCoCo Doesn't Record Coverage

JaCoCo instruments bytecode at the line level. When an exception occurs at the very first instruction of a method (before any line counter is incremented), JaCoCo records **no coverage** for that test-method pair. The test DOES exercise the method, but JaCoCo's instrumentation model cannot observe it.

### Coverage Map State

```
FieldUtilsTest#testRemoveFinalModifierNullPointerException:
  classes: ["org.apache.commons.lang3.builder.ToStringStyle"]
  methods: ["org.apache.commons.lang3.builder.ToStringStyle#getRegistry"]
```

The test does NOT cover `org.apache.commons.lang3.reflect.FieldUtils` at class level. It only covers `ToStringStyle` (likely from a static initializer or JUnit lifecycle). The `FieldUtils` class is completely absent from this test's coverage entry.

### Selection Algorithm Behavior

1. **Method-level match:** Check if `FieldUtils#removeFinalModifier` is in test's methods -> NO
2. **Class-level fallback:** Check if `FieldUtils` is in test's classes -> NO (`FieldUtils` is not in the classes list at all)
3. Result: Test is NOT selected because it has no observable relationship to `FieldUtils` in the coverage map

### Classification: Type C False Negative

This is the most extreme variant of the exception-masked pattern. The test calls `FieldUtils.removeFinalModifier(null)` which delegates to `removeFinalModifier(null, true)`. The NPE occurs when dereferencing the null `Field` argument before any JaCoCo probe in `FieldUtils` fires. As a result, `FieldUtils` does not appear in the coverage map at all for this test.

No coverage-map-level mitigation can address this case because the test is completely invisible to the target class.

### This IS a Real False Negative

If a developer removes the delegation in `removeFinalModifier(Field)` or changes the null-handling behavior, the test that validates null-argument behavior would not be selected. This is a genuine workflow false negative, not an evaluation artifact.

## Implications

### Frequency in This Evaluation

This failure mode occurred once in our sample of 772 killed mutations across 21 classes (0.13%). This does not prove the pattern is rare in general; it measures occurrence within this specific sampled evaluation.

### Possible Mitigations

| Approach | Trade-off |
|----------|-----------|
| Constructor-only footprint rule | Does not help for Type C (class absent from map) |
| Static analysis for exception paths | Adds complexity; may introduce false positives |
| Run full suite periodically | Catches all false negatives at the cost of execution time |

### Note on Terminology

This is an inherent property of JaCoCo probe-based instrumentation, not a line-level coverage issue specifically. JaCoCo method counters also derive from probe-observed instruction coverage. The problem affects any JaCoCo-based per-test RTS tool.

## Other Classes: 100% Safety

All other 20 classes achieved perfect 100% inclusiveness, confirming the failure mode is specific to the exception-path scenario, not a systematic weakness.

## Normalization Bugs Found and Fixed During Development

During evaluator development, two normalization bugs caused false "unsafe" results. Both were fixed before final evaluation. Documenting them here for reproducibility and to explain the normalizer's design.

### Bug 1: Nested Class  - Taking First Instead of Last

**Symptom:** Certain mutations in classes like `ComparableUtils` showed as unsafe.

**Root cause:** PIT uses `[nested-class:X]` tags for inner classes. When multiple nested levels exist, the deepest class name is the one JaCoCo uses. The evaluator initially took `nested_matches[0]` (first/outermost) instead of `nested_matches[-1]` (last/deepest).

**PIT format example:**
```
[class:org.apache.commons.lang3.compare.ComparableUtils]/
[nested-class:AbstractComparableUtils]/
[nested-class:InRange]/
[method:test()]
```

**Fix:** `simple_class = nested_matches[-1]` -> normalizes to `InRange#test`

### Bug 2: Parameterized Tests  - Unrecognized `[test-template:]` Tag

**Symptom:** Some mutations showed 0 killing tests (normalizer returned `None`).

**Root cause:** PIT encodes `@ParameterizedTest` methods with `[test-template:name(params)]` instead of `[method:name()]`. The normalizer only looked for `[method:]`.

**PIT format example:**
```
[class:org.apache.commons.lang3.math.FractionTest]/
[test-template:testCompareTo(String, String, int)]/
[test-template-invocation:#3]
```

**Fix:** Fallback to `re.search(r'\[test-template:([^\]]+)\]', pit_test_id)` when `[method:]` is not found.

Both fixes are in `normalize_pit_test_name()` in scripts `03_evaluate.py` and `04_baselines.py`.
