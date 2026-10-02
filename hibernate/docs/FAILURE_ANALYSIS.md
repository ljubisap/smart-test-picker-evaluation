# Hibernate false-negative analysis

The JDK 21 campaign contains 402 KILLED mutants. STP includes a PIT-reported
killing test for 400; the two misses share one newly observed lifecycle
mechanism.

## Pre-test custom-engine enhancement

Hibernate's `BytecodeEnhancedTestEngine` calls `enhanceTestClass` while it
constructs replacement test descriptors and enhanced classes. This work occurs
before execution of the leaf JUnit test method. STP's per-test JaCoCo session is
opened for the leaf execution, so dependencies exercised solely during this
engine preparation cannot be attributed to that leaf.

1. `BiDirectionalAssociationHandler#target`, line 180,
   `NullReturnValsMutator`: PIT reports the
   `MergeEnhancedDetachedOrphanRemovalTest` engine container as the killer.
   Both runnable methods represented by that container lack the target class
   entirely in their frozen coverage footprints. Class-level selection also
   misses it.
2. `PersistentAttributeTransformer#fieldReader`, line 312,
   `RemoveConditionalMutator_EQUAL_ELSE`: two PIT killing tests lack the target
   class; a third contains other transformer methods but not `fieldReader`.
   Class-level selection recovers this mutant, but the frozen constructor-only
   mitigation does not.

These are not early-exception/probe-shadowing cases. Their coverage-footprint
shapes are respectively Type C and mixed Type B/C, but their causal mechanism
is recorded as `NEW_TYPE`: dependency execution outside the leaf-test
attribution window of a custom JUnit engine. No STP or mitigation rule was
changed in response.
