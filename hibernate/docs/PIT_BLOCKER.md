# Hibernate PIT ground-truth blocker

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

Following the study stop rule, Hibernate is retained as a frozen attempted
subject but contributes no mutant observations or inclusiveness denominator.
The experiment does not downgrade Hibernate, replace PIT, narrow targetTests,
or replace the project.
