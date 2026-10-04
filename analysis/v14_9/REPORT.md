# RAD1 v14.9 failed-killer impact report

## Verdict

`FAILED_KILLER_NO_REPORTED_OUTCOME_IMPACT`

The ten eligible spring-core records that list
`AnnotationMetadataTests#standardAnnotationMetadata_688ec36` as a PIT killing
identity were reconciled against the committed v14.6 per-record selected sets.

- `k_miss = 0`: none is among the eleven spring-core base residual misses.
- `k_only = 0`: the failed test is never the only selected base killer.
- `k_other = 10`: every record is base-inclusive through at least one other
  selected killer.

All ten also remain inclusive under the constructor variant and class baseline.
The complete mutation IDs, all killing identities, and policy-specific selected
killer intersections are in `failed_killer_impact.json`.

## Manuscript

The `k_miss = 0` text variant was applied. Section 4.3 now states that all ten
records are base-inclusive and that the collection failure changes no reported
outcome. Section 6.4 flags the records and states the same measured result. The
version is 14.9.

Outputs outside the evaluation repository:

- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_9.md`
- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_9.docx`
- `/Users/D061177/work/issta/rad1-v14-4/RAD1_v14_9.pdf`
- `/Users/D061177/work/issta/rad1-v14-4/V14_9_VERIFICATION.md`
- `/Users/D061177/work/issta/rad1-v14-4/claims-to-evidence.md`
- `/Users/D061177/work/issta/rad1-v14-4/OPEN_ISSUES.md`

The PDF has 11 pages and every page was visually inspected. There is no
clipping, overlap, or split table row. The DOCX has five native tables; Table 5
has exactly seven rows and one native line break between its two killer
identities. The manuscript has 22 numbered references, and the PDF text has no
backtick.

## Verification

All commands exited zero. Machine-readable results and complete logs are next
to this report.

| Check | Result |
|---|---|
| Unit tests | 68 tests, `OK` |
| Failure-mode verification | PASS |
| Historical selector equivalence | PASS |
| Artifact freeze/checksums | PASS |
| Recollection verification | PASS |
| B2 verification | PASS |
| v14.6 verification | PASS |
| v14.7 verification | PASS |
| v14.8 verification | PASS |
| v14.9 impact recomputation | PASS: `k_miss=0`, `k_only=0`, `k_other=10` |

No map, PIT record, selector, evaluator, or `results/v14_6-*` file changed. No
PIT, coverage collection, subject build, or subject test ran.

## Repository completion

The evidence commit SHA is recorded after the initial commit. The final
follow-up commit only records completion metadata and logs; tag `rad1-v14.9`
resolves that final commit.

Push command:

```text
git push origin main rad1-v14.6 rad1-v14.7 rad1-v14.8 rad1-v14.9
```

The confirmed remote tag references are appended after push.
