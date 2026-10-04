# V14.5 recollection blockers

Decision branch: **C — recollected maps not adopted**.

## Commons Lang

- Attempt 1 used the default Maven 3.8.6 and was rejected by the subject's Maven 3.9+ enforcer rule.
- Attempt 2 used Maven 3.9.15 and collected 4,697 session files, but the native test task failed because `ArrayUtilsConcatTest` could not initialize Mockito's `MockMaker`.
- The test task reported one error and did not proceed to map conversion. No new map is claimed.

## JGraphT

- The native test target passed and produced 2,309 session files.
- Conversion attempt 1 could not write a Maven `.lastUpdated` file outside the sandbox.
- Conversion attempt 2 showed that the first collector build had not published the `smart-test-picker-common:0.2.0` POM. The complete publication was corrected in the second collector-build attempt, after the fixed two-attempt subject limit.
- No new map is claimed.

## Spring Core

- The documented three instrumentation-sensitive tests failed; report generation still completed.
- The 2e0954 converter retained 3,624 covered sessions and 14 empty sessions, producing 3,638 identities instead of the required frozen population of 3,624.
- The generated map is preserved for diagnosis but is not adopted.

## PetClinic

- Attempt 1 was green but used the project's Java 17 toolchain.
- Attempt 2 changed only the build toolchain configuration to JDK 21 and was green.
- The 2e0954 converter retained 52 covered sessions and four empty sessions, producing 56 identities instead of the required frozen population of 52.
- The generated map is preserved for diagnosis but is not adopted.

No PIT process was run, and no frozen map, PIT record, scope, subject source, or subject test was changed.
