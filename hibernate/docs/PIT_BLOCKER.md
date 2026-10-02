# Historical Hibernate JDK 25 PIT blocker

Hibernate's qualified Gradle/JDK 25 baseline is healthy. The native control
`BasicSessionTest` passes on SapMachine 25.0.4.1. PIT 1.17.4, however, cannot
complete its coverage-generation phase: its minion exits with
`UNKNOWN_ERROR` both for the frozen 932-class enhancement scope and for a
single-test-class diagnostic.

A subsequent Spring Security pilot on the same SapMachine 25 environment
exposed PIT's suppressed transformer cause explicitly: PIT 1.17.4's relocated
ASM rejects class-file major version 69. This is consistent with Hibernate's
immediate minion exit on the same class-file/JDK level.

The integration uses the current Gradle-PIT 1.19.0 adapter solely to support
Gradle 9.5; the PIT engine remains 1.17.4 and the JUnit5 plugin remains 1.2.1.
The older Gradle adapter 1.15.0 was independently rejected because it calls the
removed Gradle 9 `ReportingExtension.baseDir` API.

This evidence remains the authoritative record for the failed JDK 25 attempt.
The later JDK 21 refreeze preserved Hibernate, PIT, the sample, and all
`targetTests` scopes and produced a valid oracle; see `JDK21_REFREEZE.md`.
