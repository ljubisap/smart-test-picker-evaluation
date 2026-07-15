# Failure Modes - Spring Framework (spring-core)

## Identified Unsafe Pattern: Exception-Masked Coverage

All 11 unsafe mutations (2.42%) follow a single, well-characterized pattern.

### Pattern Summary

| Aspect | Value |
|--------|-------|
| Mutator | `VoidMethodCallMutator` |
| Mutation action | Removes call to guard clause (`Assert.notNull`, `Assert.isAssignable`, `checkMultiplier`) |
| Killing test type | Tests that exercise only the guard clause (pass null/invalid arg, expect exception) |
| JaCoCo effect | Test does not register method-level coverage due to exception before probe activation |
| Plugin behavior | Does not select the killing test because its coverage map entry has no method-level record for the mutated method |

### Root Cause: JaCoCo Probe-Based Instrumentation

JaCoCo inserts probes at basic block boundaries. When a test calls a method and an exception is thrown inside a called method (e.g., `Assert.notNull`) before control returns to the calling method's probe point, JaCoCo records zero coverage for the calling method.

```
canConvert(String.class, null):
  L133: INVOKESTATIC Assert.notNull(null, "...")  -> exception thrown inside Assert.notNull
  ---- JaCoCo probe here is never reached ----
  L134: return canConvert(...)  -> never executed
```

Result: JaCoCo reports `canConvert` method as not covered (instruction covered=0, missed=14).

The test DOES enter the method (the bytecode for the INVOKESTATIC instruction is executed) but the exception propagates before JaCoCo's probe fires. This is not a line-level issue but a fundamental property of probe-based coverage: probes at block exits cannot observe exceptions that leave mid-block.

### This IS a Real False Negative

This pattern represents a genuine false negative in a real development workflow:

1. Developer accidentally removes or weakens the `Assert.notNull` check in `canConvert`
2. Git diff marks `canConvert` as changed
3. Plugin selects 100 tests that cover `canConvert` via method-level match
4. All 100 pass (they use valid arguments)
5. The test that would catch the regression (`canConvertIllegalArgumentNullTargetTypeFromClass`) is NOT selected because it has no method-level coverage for `canConvert`
6. Null-contract regression reaches main

The argument that "normal tests would catch it" is incorrect: valid-input tests verify return values, not precondition enforcement. A removed null check does not change the output for valid inputs.

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

### Scope of the Problem

This failure mode potentially affects any RTS approach relying solely on standard JaCoCo probe coverage as its dependency signal.

`VoidMethodCallMutator` is part of PIT's default mutator set (DEFAULTS). The 11 unsafe mutations are not an artifact of using a non-standard operator.

### Sensitivity Analysis

| Mutator Set | Inclusiveness | Mutations |
|-------------|--------------|-----------|
| All mutators (DEFAULTS) | 97.58% (443/454) | 454 |
| Excluding VoidMethodCallMutator | 100.00% (415/415) | 415 |
| VoidMethodCallMutator only | 71.79% (28/39) | 39 |

All false negatives are localized to a single mutator operating on guard-clause calls. No other mutation type produces a false negative.

### Possible Mitigation: Constructor-Only Footprint Rule

A conservative mitigation: for a change in method M of class C, additionally select tests that cover C but whose method footprint on C consists only of constructors (`<init>`, `<clinit>`). This captures the signature of exception-on-entry tests.

Evaluated on all four projects:

| Project | Original | With rule | Additional tests selected |
|---------|----------|-----------|--------------------------|
| Commons Lang | 99.87% | 99.87% | +2.8 avg |
| JGraphT | 99.81% | 100.00% | +21.9 avg |
| Spring Core | 97.58% | 98.46% | +4.3 avg |
| PetClinic | 100.00% | 100.00% | +2.0 avg |

The rule does not fully resolve all spring-core false negatives because some killing tests have non-constructor method footprints (e.g., `Assert#notNull`, `close`, `getType`). A more aggressive variant (footprint size <= 3) achieves 100% but at higher selection cost.

This mitigation is not implemented in the production plugin. It is documented here as an evaluated prototype for future work.
