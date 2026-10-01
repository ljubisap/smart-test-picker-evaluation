# PIT test-scope adjudication

The subject freeze defines the canonical Flink oracle as the scheduler unit
tests selected by Surefire's `org.apache.flink.runtime.scheduler.**.*Test`
pattern. Flink's separate `*ITCase` convention is outside that oracle.

The first diagnostic PIT invocation translated the functional package scopes
to PIT package globs but did not carry over the pre-existing `*Test` suffix
boundary. Consequently PIT admitted `RescaleTimelineITCase`, whose identity
correctly had no entry in the frozen 665-test coverage map. The evaluator
failed closed on that unresolved killing identity; no inclusiveness result was
computed.

The canonical PIT profile therefore excludes `*ITCase` and `*ITCaseBase` to
implement the already-frozen subject scope. All per-class PIT matrices are
regenerated with that profile. The pre-correction matrices are retained under
`results/pre-scope-correction/` as diagnostic evidence and are not included in
headline results. This is a translation/configuration correction, not a
result-driven target-test decision: the unit-test boundary predates PIT and is
recorded in `config/subject.json` and the Flink qualification evidence.
