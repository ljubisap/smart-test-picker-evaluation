# Quarkus Arc PIT ground-truth blocker

PIT 1.17.4 does not directly understand Quarkus's tests/processor split. The
evaluation adapter supplies the processor's compiled output and source root to
the tests module without modifying source. This succeeds for an isolated real
Arc test (`SimpleInterceptorTest`) and generates 101 mutations for the pilot
class, proving the split-module adapter and JUnit5 integration work.

The predeclared Arc-wide targetTests policy, however, makes PIT send 6,044 test
and generated classes to its coverage minion. The minion exits with
`UNKNOWN_ERROR` while Arc bean-destruction lifecycle tests are running. Native
Arc qualification remains green; this is a PIT ground-truth integration
failure at the frozen scope.

Because narrowing targetTests after observing the failure would violate the
input freeze, Quarkus contributes no mutation denominator. The successful
single-test diagnostic is not promoted to a result.
