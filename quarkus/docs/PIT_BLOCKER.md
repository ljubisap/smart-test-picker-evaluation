# Quarkus Arc PIT discovery blocker and resolution

PIT 1.17.4 does not directly understand Quarkus's tests/processor split. The
evaluation adapter supplies the processor's compiled output and source root to
the tests module without modifying source. This succeeds for an isolated real
Arc test (`SimpleInterceptorTest`) and generates 101 mutations for the pilot
class, proving the split-module adapter and JUnit5 integration work.

The initial Arc-wide `io.quarkus.arc.test.*` translation made PIT send 6,044
compiled test, helper, and generated classes to its coverage minion. Verbose
diagnosis isolated the first fatal class to
`DependentPreDestroyOnlyCalledOnceTest$MyInterceptedBean_Bean$0`. PIT's JUnit 5
finder called `Class.getEnclosingClass()` while attempting to discover this
generated bean as a test, and the JVM raised:

```
IncompatibleClassChangeError: ...MyInterceptedBean_Bean and
...MyInterceptedBean_Bean$0 disagree on InnerClasses attribute
```

The exception originates at `JUnit5TestUnitFinder.findTestUnits`, before PIT
mutation execution and before STP selection. The preceding Arc destruction
errors in the log are expected test behavior and are not the fatal cause.

## Resolution

The already-frozen BASE coverage map contains 684 runnable identities across
572 exact test classes. The PIT profile is rendered from that inventory, using
an exact `targetTests` entry for every runnable class. This preserves the full
qualified oracle while excluding compiled helpers and generated classes that
were never runnable tests. No sample, test identity, production source, test
source, STP version, PIT version, mutator, or denominator rule changes.

With the corrected scope translation, all 16 pre-frozen sampled classes pass
under PIT 1.17.4 / pitest-junit5-plugin 1.2.1 using at most eight CPUs:

- 16/16 class jobs successful;
- 0 failures and 0 timeouts;
- 1,639 total PIT mutations;
- 1,083 KILLED mutations in the common operational oracle.

The original failure and verbose stack trace remain under
`results/pre-runnable-inventory-correction/`.
