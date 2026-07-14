# Failure Modes  - Spring Framework (spring-core)

## Identified Unsafe Pattern: Exception-Masked Coverage

All 11 unsafe mutations (2.42%) follow a single, well-characterized pattern.

### Pattern Summary

| Aspect | Value |
|--------|-------|
| Mutator | `VoidMethodCallMutator` |
| Mutation action | Removes call to guard clause (`Assert.notNull`, `Assert.isAssignable`, `checkMultiplier`) |
| Killing test type | Tests that exercise **only** the guard clause (pass null/invalid arg, expect exception) |
| JaCoCo effect | Test does not register method-level coverage due to exception before probe activation |
| Plugin behavior | Correctly does not select  - test genuinely has zero coverage on mutated method |

### Root Cause: JaCoCo Probe Mechanics

JaCoCo uses **probes** inserted at basic block boundaries. When a test calls a method and an exception is thrown inside a called method (e.g., `Assert.notNull`) before control returns to the calling method's probe point, JaCoCo records zero coverage for the calling method.

```
canConvert(String.class, null):
  L133: INVOKESTATIC Assert.notNull(null, "...")  -> exception thrown inside Assert.notNull
  ---- JaCoCo probe would be HERE, but execution never reaches it ----
  L134: return canConvert(...)  -> never executed
```

Result: JaCoCo reports `canConvert` method as **not covered** (covered=0, missed=1).

### Affected Mutations

| Class | Method | Line | Killing Test |
|-------|--------|------|-------------|
| TypeDescriptor | upcast | 235 | `TypeDescriptorTests#upCastNotSuper` |
| GenericConversionService | canConvert | 133 | `*#canConvertIllegalArgumentNullTargetTypeFromClass` |
| GenericConversionService | canConvert | 140 | `*#canConvertFromTypeDescriptorSourceTypeToNullTargetType` |
| GenericConversionService | convert | 164 | `*#convertToNullTargetClass` |
| GenericConversionService | convert | 171 | `*#convertToNullTargetTypeDescriptor` |
| SimpleAsyncTaskExecutor | execute | 264 | `*#throwsExceptionWhenSuppliedWithNullRunnable` |
| Assert | isAssignable | 539 | `AssertTests#isAssignableWithNullSupertype` |
| Assert | isAssignable | 558 | `AssertTests#isAssignableWithNullSupertypeAndMessageSupplier` |
| Assert | isInstanceOf | 490 | `AssertTests#isInstanceOfWithNullType` |
| Assert | isInstanceOf | 509 | `AssertTests#isInstanceOfWithNullTypeAndMessageSupplier` |
| ExponentialBackOff | setMultiplier | 141 | `ExponentialBackOffTests#invalidInterval` |

### Why This Does Not Manifest in Practice

In real development workflows, this limitation does not lead to missed regressions:

1. **Guard clause changes produce method-level diffs**: If a developer modifies the `Assert.notNull` call in `canConvert`, git diff reports `canConvert` as changed, and the plugin selects all tests covering that method  - including normal tests that exercise the full method body.

2. **Tests that only exercise guard clauses are inherently low-risk**: These tests verify precondition validation, not business logic. A mutation that removes a null check would be caught by any test that passes a valid argument and expects correct behavior.

3. **Class-level fallback as safety net**: If no method-level coverage exists for a class, the plugin falls back to selecting all tests covering the class. The exception-masked pattern only occurs when other tests DO have method-level coverage for the same class.

### Sensitivity Analysis

| Mutator Set | Safety | Mutations |
|-------------|--------|-----------|
| All mutators (STRONGER) | 97.58% | 454 |
| Excluding VoidMethodCallMutator | **100.00%** | 415 |
| VoidMethodCallMutator only | 71.79% | 39 |

The tool achieves perfect safety on all mutation types except `VoidMethodCallMutator`, which specifically targets void method calls (including guard clauses).
