# Failure Mode Analysis - JGraphT

## Summary

Out of 517 KILLED mutations across 20 classes, exactly **1 mutation** was not safely covered by the plugin's selection (inclusiveness: 99.81%). This documents the root cause.

## The Unsafe Mutation

| Field | Value |
|-------|-------|
| Class | `org.jgrapht.alg.tour.ChristofidesThreeHalvesApproxMetricTSP` |
| Method | `getTour` |
| Line | 97 |
| Mutator | `VoidMethodCallMutator` |
| Mutation | Removed call to `checkGraph` (guard/validation method) |
| Killing Tests | `testGetTour0`, `testGetTour2` |

## Classification: Type A (Constructor-Only Footprint)

The killing tests (`testGetTour0`, `testGetTour2`) cover the class but their method footprint on `ChristofidesThreeHalvesApproxMetricTSP` contains only `<init>`. The mutated method `getTour` is absent from their coverage.

This matches the exception-masked coverage pattern: the test calls `getTour()` which invokes `checkGraph()` (a validation method). `checkGraph` throws an exception before JaCoCo's probe for `getTour` fires, so JaCoCo records zero method coverage for `getTour` in these tests.

## Selection Algorithm Behavior

1. **Method-level match for `getTour`:** 8 tests (`testGetTour3`-`testGetTour10`) have method-level coverage for `getTour` and are selected
2. **Killing tests `testGetTour0`, `testGetTour2`:** Cover the class but do NOT have `getTour` in their methods list (only `<init>`)
3. **Class-level fallback:** Does not apply because other tests DO have method-level info for this class
4. **Result:** Killing tests not selected -- unsafe

## This IS a Real False Negative

If a developer removes the `checkGraph()` call from `getTour()`:
- Git diff marks `getTour` as changed
- Plugin selects 8 tests that cover `getTour` via method-level match
- All 8 pass (they provide valid graphs)
- `testGetTour0` and `testGetTour2` (which test invalid-graph behavior) are NOT selected
- Invalid-graph regression reaches main

## Mitigation: Constructor-Only Footprint Rule

The constructor-only footprint rule resolves this case: since the killing tests have only `<init>` in their method footprint for this class, the rule adds them to the selection.

| Selector | Inclusiveness | Avg Selected |
|----------|--------------|--------------|
| Original | 99.81% (516/517) | 87.7 |
| With constructor-only rule | 100.00% (517/517) | 96.9 |

Cost: +21.9 additional tests selected on average.

## Cross-Project Pattern

This belongs to the same probe-shadowing family as spring-core's 11 false negatives and commons-lang's 1 false negative. All are caused by JaCoCo probe-based instrumentation not recording method coverage when an exception exits before the probe fires. This potentially affects any RTS approach relying solely on standard JaCoCo probe coverage as its dependency signal.

## All Other Classes: 100% Inclusiveness

The remaining 19 classes achieved perfect 100% inclusiveness:

| Class | KILLED | Safe |
|-------|--------|------|
| Graphs | 24 | 24 |
| DegeneracyBronKerboschCliqueFinder | 12 | 12 |
| LabelPropagationClustering | 4 | 4 |
| GreedyColoring | 7 | 7 |
| KosarajuStrongConnectivityInspector | 16 | 16 |
| SzwarcfiterLauerSimpleCycles | 25 | 25 |
| ListenableLayoutModel2D | 9 | 9 |
| PushRelabelMFImpl | 40 | 40 |
| AHUUnrootedTreeIsomorphismInspector | 14 | 14 |
| BinaryLiftingLCAFinder | 39 | 39 |
| LeichtHolmeNewmanIndexLinkPrediction | 5 | 5 |
| BlossomVPrimalUpdater | 160 | 160 |
| ClosenessCentrality | 14 | 14 |
| TransitNodeRoutingPrecomputation | 30 | 30 |
| EsauWilliamsCapacitatedMinimumSpanningTree | 21 | 21 |
| UnorderedPair | 14 | 14 |
| RecursiveExactVCImpl | 32 | 32 |
| Distributor | 22 | 22 |
| UndirectedSpecifics | 20 | 20 |
