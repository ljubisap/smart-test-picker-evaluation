# T5 — collector differences: `70b398...` to `2e0954...`

Source repository: `/Users/D061177/work/issta/hibernate-orm-stp-qualification/stp-source`

Commands:

```text
git log --oneline --reverse 70b3984626eb..2e0954b5b590 -- <restricted paths>
git diff --stat 70b3984626eb 2e0954b5b590 -- <restricted paths>
```

Restricted production paths:

- `smart-test-picker-common/src/main/java/com/sap/oss/smarttestpicker/mapper/CoverageMapperJaxb.java`
- `smart-test-picker-core/src/main/java/com/sap/oss/smarttestpicker/JacocoPerTestListener.java`
- `smart-test-picker-maven/src/main/java/com/sap/oss/smarttestpicker/maven/GenerateCoverageMapMojo.java`
- `smart-test-picker/src/main/java/com/sap/oss/smarttestpicker/SmartTestPickerExtension.java`

The extension file has no change in this range. The restricted diff stat is 142 insertions and 7 deletions over the other three files.

## Relevant commits

1. `0039cd7e7ca7838086ae506b0709e9356b0bca2c` — `feat: define coverage map schema v1 and fragment contract`
   - Replaces `HashMap` with `TreeMap` in `CoverageMapperJaxb` for deterministic map/metric/coverage serialization.
   - It changes output ordering, not which execution is recorded or attributed.
2. `1151bbd99faf3c172bb42e7625cf4ba828da7b94` — `fix: preserve zero-coverage tests in JaCoCo selection`
   - Retains `session_*.xml` reports whose JaCoCo `<report>` has no package list and emits an empty class/method footprint.
   - This changes which logical tests survive conversion: successfully collected zero-coverage tests are represented instead of disappearing.
3. `7c69ec0785b0d66e9a83780bb967783a9d5b1919` — `Implement JZC-02A method-exact Maven execution`
   - `JacocoPerTestListener` writes optional per-session identity metadata: test-class FQN, logical method, engine, and execution shape.
   - `CoverageMapperJaxb` loads that metadata, exposes `executionIdentities`, and still derives coverage edges from the same JaCoCo XML.
   - `GenerateCoverageMapMojo` passes the Maven artifact/module identity into the map engine.
   - This changes retained attribution/execution metadata and enables exact execution planning; it does not add descriptors to production method edges and does not change JaCoCo probe coverage itself.

The net converter line remains `coveredMethods.add(classFqn + "#" + method.getName())` at both endpoint commits. Thus production method edges are name-only at both collection identities.
