# Production change-input mapping

Repository: Smart Test Picker, commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, tree `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`.

- `GitChangeDetector#getChangedClasses` collects the FQN derived from every changed production `.java` path (`smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/change/GitChangeDetector.java:46-82`).
- `getChangedMethods` parses zero-context Git hunk headers, derives the same class FQN and appends `#` plus the unqualified method name (`GitChangeDetector.java:126-142,247-290`). No descriptor is added.
- `TestSelectionEngine` obtains both sets independently and passes them unchanged to `TestSelector.selectTests` (`smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/engine/TestSelectionEngine.java:168-178,201-203`).
- `TestSelector` derives its classes-with-method-information set from the prefix before `#` (`smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/selector/TestSelector.java:103-117`).

Therefore the frozen evaluator case `(C, M)` is supplied to the unchanged selector as:

```text
changedClasses = { C }
changedMethods = { C + "#" + M }
```

The harness calls the public production entry point `TestSelector.selectTests(File, Set<String>, Set<String>)`, which delegates to the logger-bearing production method (`TestSelector.java:62-249,263-265`). It does not reproduce selector logic.
