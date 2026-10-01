# Spring Security PIT ground-truth blocker

The frozen PIT 1.17.4 engine cannot instrument Spring Security's JDK 25 class
files. Its coverage transformer throws:

```text
java.lang.IllegalArgumentException: Unsupported class file major version 69
```

The pilot discovered 11 tests and generated 22 mutations for
`RoleHierarchyImpl`, but all 22 are `NO_COVERAGE`; therefore there is no valid
KILLED-mutant denominator. This also supplies the concrete missing detail for
Hibernate's JDK 25 PIT minion exit.

The Gradle integration adapter is 1.19.0 for Gradle 9 compatibility, while the
PIT engine and JUnit5 plugin remain exactly 1.17.4 and 1.2.1. The subject is
stopped rather than changing PIT, lowering the qualified JDK, or substituting
a different Spring Security release.
