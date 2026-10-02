# Quarkus Arc mutation evaluation

This subject extends the repository's existing killed-mutant inclusiveness
protocol to Quarkus 3.40.1. Tests come from
`independent-projects/arc/tests`; mutable production code comes from the Arc
processor module. Inputs were frozen in commit
`47d0c42194c7e1dbd658530e3db9b3faa311897a` before outcomes were inspected.

The test-module-wide oracle is structural and was frozen because processor
behavior crosses test-package boundaries. PIT receives the exact 572 test
classes represented by the already-frozen 684-identity BASE runnable
inventory. This is a scope translation, not a narrower oracle. See
`config/runnable-test-inventory.json` and `docs/PIT_BLOCKER.md`.

The original broad `io.quarkus.arc.test.*` translation admitted 6,044 compiled
test, helper, and Quarkus-generated classes to PIT discovery. A generated Arc
bean then crashed the JUnit 5 finder before mutation. Translating the same
frozen oracle to exact runnable class names resolves the discovery defect:
all 16 sampled classes complete, producing 1,639 mutations and 1,083 KILLED
mutations.
