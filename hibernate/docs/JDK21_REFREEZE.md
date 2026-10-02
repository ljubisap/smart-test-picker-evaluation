# Hibernate JDK 21 mutation-environment refreeze

The subject, release commit, 16-class sample, functional `targetTests` scopes,
PIT 1.17.4, JUnit5 plugin 1.2.1, `DEFAULTS`, and
`fullMutationMatrix=true` are unchanged from the pre-result freeze.

Hibernate 7.4.11.Final declares `orm.jdk.min=25`, although its production and
test bytecode target Java 17. The JDK 21 replay uses the project's external
Gradle override `-Porm.jdk.min=21`; no subject file is edited. Gradle reports
compiler/launcher 21 and release 17. The qualified oracle remains 1,495 raw
invocations, four skipped, and zero failures/errors.

PIT additionally needs
`-Dhibernate.testing.bytecode.enhancement.extension.engine.enabled=true`.
Without it, Hibernate's `BytecodeEnhancementPostDiscoveryFilter` intentionally
aborts discovery. This setting reproduces the subject's native enhanced-test
lifecycle; it does not filter or change the test population.

The preserved diagnostics show the closure sequence: `diagnostic-jdk21-valid`
records rejection of an unconfigured JDK 21 build; `diagnostic-pit-jdk21-valid`
records an early attempt whose PIT JVM still pointed at JDK 25;
`diagnostic-jdk21-override` reaches a JDK 21 PIT minion but reports only
`UNKNOWN_ERROR`; `diagnostic-jdk21-verbose` exposes the missing enhanced-engine
property; and `diagnostic-jdk21-fixed` is the successful one-class control.
Only the canonical `results/per-class` campaign contributes to the evaluation.

All executions were sequential per sampled production class and bounded to at
most eight CPUs. The canonical run produced 1,061 PIT mutations across 16/16
usable classes. The fresh JDK 21 STP map contains 1,099 logical runnable
identities, identical in identity set to the earlier qualified map.

## Reproduction

With `JAVA_HOME_21` pointing to SapMachine 21 and the Hibernate checkout at
the commit recorded in `config/subject.json`:

```bash
JAVA_HOME="$JAVA_HOME_21" PIT_JVM_PATH="$JAVA_HOME_21/bin/java" \
python3 analysis/run_gradle_pit.py \
  --root ../hibernate-orm-stp-qualification/subject \
  --task :hibernate-core:pitest \
  --init-script hibernate/config/pit.init.gradle \
  --config hibernate/config/sample_classes.json \
  --results hibernate/results \
  --gradle-home ../hibernate-orm-stp-qualification/gradle-home \
  --timeout 3600 --cpus 8 \
  --gradle-arg=-Porm.jdk.min=21

python3 analysis/evaluate_subject.py \
  --subject hibernate \
  --coverage-map hibernate/results/test-coverage-map.json.gz \
  --results-dir hibernate/results

python3 analysis/analyze_failure_modes.py --verify
python3 analysis/verify_selector_equivalence.py --verify
python3 analysis/freeze_artifacts.py --verify
```

The init script supplies Hibernate's documented enhanced-engine switch to each
PIT minion. It also passes `-XX:ActiveProcessorCount` and configures PIT's
thread count from the same `--cpus` bound.
