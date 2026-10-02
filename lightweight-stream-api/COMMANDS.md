# Reproduction commands

All Gradle and PIT executions were limited to eight processors/workers. The subject source and tests remain byte-identical to `v1.2.2`; `config/gradle-8.14.patch` contains only the evaluation-time Gradle API translation required to load the 2021 build with Gradle 8.14 on JDK 21.

## Native baseline

```sh
GRADLE_OPTS='-XX:ActiveProcessorCount=8' \
GRADLE_USER_HOME=/Users/D061177/work/issta/lightweight-stream-api-modern-study/gradle-home \
/path/to/gradle-8.14/bin/gradle \
  -I config/jdk21.init.gradle clean :stream:test :streamTest:test \
  --no-daemon --max-workers=8 --console=plain
```

## STP qualification

```sh
gradle -I config/stp.init.gradle clean :stream:test :streamTest:test \
  --no-daemon --max-workers=8 --console=plain
gradle -I config/stp.init.gradle \
  :stream:generateTestCoverageJson :streamTest:generateTestCoverageJson \
  --no-daemon --max-workers=8 --console=plain
gradle -I config/stp.init.gradle :stream:selectTests :streamTest:selectTests \
  --no-daemon --max-workers=8 --console=plain
gradle -I config/stp.init.gradle :stream:smartTest :streamTest:smartTest \
  --no-daemon --max-workers=8 --console=plain
```

BASE collection uses JUnit Platform Vintage 5.9.3 to preserve the native JUnit 4.13.1 population while activating STP's launcher listener.

## PIT and analysis

```sh
cd /Users/D061177/work/issta/smart-test-picker-evaluation
python3 analysis/run_gradle_pit.py \
  --root /Users/D061177/work/issta/lightweight-stream-api-modern-study/subject \
  --task :stream:pitest \
  --init-script lightweight-stream-api/config/pit.init.gradle \
  --config lightweight-stream-api/config/sample_classes.json \
  --results lightweight-stream-api/results \
  --gradle-home /Users/D061177/work/issta/lightweight-stream-api-modern-study/gradle-home \
  --gradle-executable /path/to/gradle-8.14/bin/gradle \
  --timeout 1800 --cpus 8

python3 analysis/evaluate_subject.py \
  --subject lightweight-stream-api \
  --coverage-map lightweight-stream-api/results/test-coverage-map.json.gz \
  --results-dir lightweight-stream-api/results

python3 lightweight-stream-api/scripts/04_verify_selector_equivalence.py \
  --coverage-map lightweight-stream-api/results/test-coverage-map.json.gz \
  --results-dir lightweight-stream-api/results

python3 -m unittest discover -s analysis/tests -p 'test_*.py'
```

PIT uses 1.17.4, its built-in JUnit 4 integration, DEFAULTS, `fullMutationMatrix=true`, one frozen class per run, and the predeclared complete stream-module `targetTests` scope.
