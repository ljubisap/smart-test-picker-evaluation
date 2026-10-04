# RAD1 v14.8 close report

## Outcome

`V14_8_CLOSED`

The read-only evidence checks and manuscript corrections completed without
changing any map, PIT record, selector, evaluator output, or `results/v14_6-*`
file. No PIT, coverage collection, subject build, or subject test was run.

## Manuscript corrections

- The duplicate cells were removed from the Table 3 aggregate row and Table 4
  Quarkus row. A raw-Markdown scan found no other pipe-table cell-count error.
- Table 5 is a pipe table with seven native DOCX rows (header plus six
  diagnostic steps). Both PIT killing identities occupy one cell separated by
  one native Word line break. The final selection row states that 114 tests are
  selected and neither PIT-reported killing test is selected.
- The requested analyzed/adopted-map wording was applied in Sections 4.4, 6.2,
  and 8.
- The exact maximum Monte Carlo/analytical difference is
  `0.050597641421646244` percentage points
  (`results/v14_6-random-baseline.json`), so the manuscript's rounded-up
  `0.051` bound remains unchanged.
- The manuscript version is 14.8.

Outputs outside the evaluation repository:

- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_8.md`
- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_8.docx`
- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_8.pdf`
- `/Users/D061177/work/issta/rad1-v14-4/V14_8_VERIFICATION.md`
- `/Users/D061177/work/issta/rad1-v14-4/claims-to-evidence.md`
- `/Users/D061177/work/issta/rad1-v14-4/OPEN_ISSUES.md`

The PDF has 11 pages. Every page was visually inspected; no clipping, overlap,
or split table row was observed. The PDF text contains zero backticks. The DOCX
contains five native tables, and Table 5 contains exactly seven `w:tr` elements.
The manuscript contains 22 numbered references.

## spring-core adopted-collection outcomes

The adopted collection log reports 4,704 executions, three failures, and 28
skips (`recollection_2e0954/spring-core-run1-test.log:65-78`):

1. `BridgeMethodResolverTests#testInterfaceHierarchy` —
   `org.opentest4j.AssertionFailedError` at line 351; adopted footprint 21
   classes / 92 methods; present in the 70b398 map; not a killer of any eligible
   record.
2. `BridgeMethodResolverTests#testClassHierarchy` —
   `org.opentest4j.AssertionFailedError` at line 351; adopted footprint 20
   classes / 87 methods; present in the 70b398 map; not a killer of any eligible
   record.
3. `AnnotationMetadataTests#standardAnnotationMetadata` —
   `java.lang.AssertionError` at line 506; adopted footprint 51 classes / 249
   methods; present in the 70b398 map; listed as a killing identity by ten
   eligible mutation records.

The full ten mutation IDs are in `springcore_test_outcomes.json`. The original
collection instructions identify instrumentation-sensitive failures in the same
test classes (`spring-core/docs/REPRODUCE.md:94,182`), but retain no exact
method-level failure list. The manuscript therefore does not assert exact
per-method equality with the original run.

The adopted map is run 1 at
`recollection_2e0954/spring-core/test-coverage-map.json`, SHA-256
`bfeafc4bb2a7221243c1f7fb407938472b582462a8cad071cbc90152eb83e32d`.

## Verification

All commands exited zero; complete logs and the machine-readable result are in
this directory.

| Check | Result |
|---|---|
| Unit tests | 68 tests, `OK` |
| `analyze_failure_modes.py --verify` | PASS |
| `verify_selector_equivalence.py --verify` | PASS |
| `freeze_artifacts.py --verify` | PASS |
| `verify_recollection.py --verify` | PASS |
| `verify_b2.py --verify` | PASS |
| `verify_v14_6.py --verify` | PASS |
| `verify_v14_7.py --verify` | PASS |
| `verify_v14_8.py --verify` | PASS; 3 failures reconciled, 10 eligible killer records |

The required manuscript grep is empty. `git diff --check` passes. No file under
`results/v14_6-*`, `recollection_2e0954/`, or the subject PIT/map paths changed.

## Repository finish

The evidence implementation and report were committed as
`358a81e59557b91b04a8896bdbea043c7dd3d58a`; the `rad1-v14.8` tag points to the
follow-up that records these completion details and retained logs. Nothing is
pushed.
The manual push command is:

```text
git push origin main rad1-v14.8
```
