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
  classes: [..., "org.apache.commons.lang3.reflect.FieldUtils", ...]
  methods: [...]  <- does NOT contain "FieldUtils#removeFinalModifier"
```

The test covers the class (it calls other methods too), but the specific method `removeFinalModifier` is NOT in its method coverage list because JaCoCo never registered a covered line.

### Selection Algorithm Behavior

1. **Method-level match:** Check if `FieldUtils#removeFinalModifier` is in test's methods -> NO
2. **Class-level fallback:** Check if `FieldUtils` is in test's classes AND test has no method info for that class -> `FieldUtils` IS in classes, BUT test has other method-level entries for `FieldUtils` (from other test methods in the same class) -> Fallback does NOT apply
3. Result: Test is NOT selected

### Why This Is Not a Bug

The dual-granularity algorithm works correctly:
- It has method-level info for `FieldUtils` (many other methods are covered)
- Therefore it trusts method-level matching and does NOT fall back to class-level
- But the specific exception-only path has no method coverage to match against

This is an **inherent limitation** of line-level coverage instrumentation, not a bug in the selection algorithm.

## Implications

### Frequency

This failure mode requires ALL of:
1. A test that exercises a method ONLY via an exception path
2. The exception must occur before ANY instrumented line executes
3. The method must be in a class where OTHER methods DO have method-level coverage (preventing class-level fallback)

This combination is extremely rare in practice. In our sample of 772 mutations across 21 classes, it occurred exactly once (0.13%).

### Possible Mitigations

| Approach | Trade-off |
|----------|-----------|
| Always include class-level fallback | Would select ~3x more tests (49 vs 17 avg), reducing the precision advantage of method-level selection |
| Bytecode-level coverage (not line-level) | Would require different instrumentation approach, not supported by JaCoCo |
| Static analysis for exception paths | Adds complexity; may introduce false positives |
| Accept 99.87% safety | Practical choice  - full suite as periodic safety net |

### Recommendation

Accept this as a known limitation. The 99.87% safety rate already exceeds the literature standard for RTS tools (typically 95-99%). Running the full suite periodically (e.g., nightly or on merge to main) provides complete safety while enjoying 99.64% test reduction on feature branches.

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
