# Spring Security JDK 21 environment correction

Date: 2026-10-01

The original mutation attempt used the qualification environment's default
JDK 25 toolchain. PIT 1.17.4 cannot transform class-file major version 69, so
that attempt remains preserved in `PIT_BLOCKER.md` and `results/blocked.json`.

Spring Security's build exposes the official `-PtestToolchain` property. A
native control with `-PtestToolchain=21` passed the unchanged
`:spring-security-core:test` target with exactly 1,509 raw invocations and four
skips, matching the qualified JDK 25 oracle. Production classes continue to use
the project's release-17 target. The JDK 21 environment is therefore frozen
before inspecting any JDK 21 PIT mutation outcomes:

- subject release/commit: unchanged (`7.1.1`, `a825937...`);
- sampled 18 classes and all `targetTests` scopes: unchanged;
- STP/PIT/JUnit plugin versions and selector semantics: unchanged;
- JDK: SapMachine 21.0.12.1+1-LTS;
- Gradle property: `-PtestToolchain=21`;
- CPU bound: `--max-workers=8`, `-XX:ActiveProcessorCount=8`, PIT threads 8.

A fresh JDK 21 STP map contains the same 1,440 logical runnable identities.
Its compressed artifact is `results/test-coverage-map.json.gz`.

This is an environment correction made to use an upstream-supported build
mode, not a change to the subject, sample, oracle population, or evaluation
algorithm.
