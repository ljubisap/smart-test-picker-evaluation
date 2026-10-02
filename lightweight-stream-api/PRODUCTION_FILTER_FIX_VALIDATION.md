# Production-class filter fix validation

The modern follow-up qualification exposed an STP implementation defect outside the frozen
mutation scope: production classes in `com.annimon.stream.test` were removed by an FQN naming
heuristic. The generic output-ownership fix is STP commit
`a95a1ae9c7ba099a201c3c861f289b4a8002e62c` (tree
`9a86aea04cd728a027cc423cd29ba5df793df96c`).

On Lightweight-Stream-API v1.2.2, the `streamTest` scope changed from 110/110 false
`NO_COVERAGE` identities to 0/110, with 308 class and 569 method edges recovered from the
same raw JaCoCo evidence. The warm result remained `NONE` with zero executed tests.

The canonical mutation campaign was not rerun. It targets `stream`, not `streamTest`, and the
new `stream` `testMappings`, `classMetrics`, and `executionIdentities` are exactly equal to the
frozen canonical map (timestamp excluded). Consequently every selected set for all 419 KILLED
mutants remains unchanged. The canonical mutation artifacts and denominator were not modified.

Complete before/after evidence is outside this repository under
`production-class-filter-fix/` in the evaluation workspace.
