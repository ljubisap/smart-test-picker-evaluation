# Reproduction commands

All Java/PIT processes were capped at eight available processors. Paths below are the frozen local workspace paths; the equivalent committed supplementary inputs live under `smart-test-picker-evaluation/joda-time/`.

## Native baseline

```sh
cd /Users/D061177/work/issta/joda-time-modern-study/subject
MAVEN_OPTS='-XX:ActiveProcessorCount=8 -Dmaven.repo.local=/Users/D061177/work/issta/joda-time-modern-study/m2' \
  /Users/D061177/Programs/apache-maven-3.8.6/bin/mvn -B \
  -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 test
```

The compiler properties are external JDK-21 compatibility configuration; the release sources and tests remain unchanged.

## STP qualification

The external profile is installed reproducibly by:

```sh
python3 /Users/D061177/work/issta/joda-time-modern-study/scripts/install_profile.py \
  --pom /Users/D061177/work/issta/joda-time-modern-study/subject/pom.xml \
  --profile /Users/D061177/work/issta/joda-time-modern-study/config/coverage_profile.xml
```

The canonical goals are `test`, `jacoco-per-test-reports`, `generate-coverage-map`, `select-tests`, and `smart-test`, with profile `coverage-per-test` for BASE and `smart-test` for child execution. The exact outputs and child command are preserved under `raw/qualification/`.

## PIT and evaluation

```sh
cd /Users/D061177/work/issta/smart-test-picker-evaluation
python3 joda-time/scripts/02_run_pit.py \
  --project-dir /Users/D061177/work/issta/joda-time-modern-study/subject \
  --local-repo /Users/D061177/work/issta/joda-time-modern-study/m2 \
  --results-dir joda-time/results

python3 analysis/evaluate_subject.py \
  --subject joda-time \
  --coverage-map joda-time/results/test-coverage-map.json.gz \
  --results-dir joda-time/results

python3 joda-time/scripts/04_verify_selector_equivalence.py \
  --coverage-map joda-time/results/test-coverage-map.json.gz \
  --results-dir joda-time/results

python3 -m unittest discover -s analysis/tests -p 'test_*.py'
```

PIT configuration: 1.17.4, built-in JUnit 3/4 support, DEFAULTS, `fullMutationMatrix=true`, one frozen target class per run, eight threads, and the predeclared package-functional `targetTests` values in `sampling.json`.
