# PIT unification: execution findings

Final verification rejected the first derived dataset because spring-core still
contained the older conditional operator. PIT 1.17.4's CLI sets an empty mutator
list when `--mutators` is omitted; `GregorEngineFactory` then calls
`Mutator.newDefaults()`, whose bytecode includes NEGATE_CONDITIONALS. This differs
from `Mutator.fromStrings(["DEFAULTS"])`: `StandardMutatorGroups` registers the
named group with REMOVE_CONDITIONALS_EQUAL_ELSE and ORDER_ELSE. The documented
Spring runner omitted the option. The isolated retry adds exactly
`--mutators DEFAULTS`, preserving the declared policy and all scopes/settings.
It is a command-configuration adapter beyond the version pin; the original script
and subject are unchanged. Full bytecode evidence is in `pit-default-resolution/`.
The rejected matrices, numerical outputs and Java replay are archived under
`attempts/implicit-defaults.tar.gz`; they are not final iteration results.

No unresolved blocker at preflight. Findings and any failures are recorded here without changing the baseline treatment.

- `main` and the peeled `rad1-v15` tag both resolve to `3bdf61c0b7481fe6da25e4bd335b91a348a4f837`. The tag-object hash is not a different source commit.
- The two documented PIT runners already specify 1.17.4 / JUnit plugin 1.2.1. Original JGraphT stdout (each per-class log, line 7) already reports pitest-maven:1.17.4 while its matrix contains NegateConditionalsMutator. An older operator is not proof of an older PIT version. Runner sources remain unchanged; Spring's final execution uses the explicit named-group command adapter described above.
- The native spring-core checkout already defines `pitClasspath`. The documented runner detects/reuses it; the duplicate-task init script from the separate anonymous-package replay is not used.
- The first spring-core attempt was interrupted at the user's request during AbstractResource. Seven preceding jobs failed. The resolved runtime classpath referenced unbuilt main and test-fixtures project JARs: `testClasses` plus `pitClasspath` did not produce them. On explicit resume, preserve the initial attempt and build only the requisite JAR tasks before an infrastructure retry. This does not change source, tests, targetTests, versions, or PIT settings. Missing JARs are established; attribution of every initial failure to them must be checked against retry evidence.
- Resume outcome: all required runtime JARs were produced by test-free Gradle tasks. RepeatableContainers, AbstractDataBufferDecoder, TypeDescriptor, ConvertingComparator, GenericConversionService, and PropertySource then produced valid matrices. SerializableTypeWrapper, AbstractResource, DataBufferUtils, and PathMatchingResourcePatternResolver still fail PIT's unmutated coverage-phase check (19 test failures in their broad scopes). These are the same four previously unusable classes; DataBufferUtils previously timed out instead. No further retry is justified solely by these baseline failures, and no scope, timeout, skipFailingTests, or source change is applied. All 22 classes remain accounted for; 18 matrices are usable.
- One newly produced JGraphT matrix is about 190 MiB, exceeding GitHub's single-file limit. New matrices are therefore stored as deterministic gzip. `matrix_packaging.json` proves byte-identical decompression and records the retained raw-original locations. Frozen matrices are untouched.
- **Interpretation limit: CPU exposure is an additional environment control, not a PIT-version change.** The runner inherited `JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=1` to protect the shared machine. The documented PIT thread count remains four, but JGraphT's `TransitNodeRoutingPrecomputationTest.java:75` sizes its executor from `availableProcessors()`. Production code reads that size at `TransitNodeRoutingPrecomputation.java:248` and uses it at lines 363, 1296 and 1308. At parallelism one, several partition arithmetic mutants become observationally equivalent on that execution path. Six otherwise comparable KILLED-to-SURVIVED changes are in this class (see `results/status_comparison.json.gz`). The source explains a plausible CPU-sensitive mechanism; historical effective processor count is not established here, and no isolated counterfactual replay is claimed. Thus this is a PIT-1.17.4 unified-operator dataset under the recorded CPU control, **not a demonstrated PIT-version-only causal comparison**. Do not promote it or attribute all differences to DEFAULTS replacement. No status-driven rerun or changed timeout/scope is used to conceal this limitation.
