# RAD1 v15 submission report

Date: 2026-10-04 (Europe/Berlin)

## Scope and outcome

The submission preparation started from evaluation tag `rad1-v14.9` and
`rad1-v14-4/RAD1_v14_9.md`. No PIT run, coverage collection, subject build,
subject test, map edit, PIT-record edit, selector/evaluator edit, or
`results/v14_6-*` edit was performed.

The deliverables are:

- `rad1-v15/paper.tex` and `rad1-v15/paper.pdf`: anonymous IEEEtran paper;
- `rad1-v15/RAD1_v15.md` and `rad1-v15/RAD1_v15.docx`: non-anonymous author records;
- `rad1-v15/anon-artifact/` and `rad1-v15/anon-artifact.zip`: history-free,
  anonymized replication package;
- this directory: the read-only succeeding-test audit, verifier, logs, and report.

## Step 1: failed-killer wording

`analysis/v14_9/failed_killer_impact.json` confirms that all ten affected
records have at least one killing identity other than the collection-failing
`standardAnnotationMetadata` test selected under each of the base,
constructor, and class policies (10/10 for every policy). Sections 4.3 and 6.4
were therefore changed to state that inclusiveness does not depend on counting
that failing test as the witness.

## Step 2: PIT succeeding tests

All eight subjects expose `succeedingTests` for every inspected PIT mutation
record. The detailed per-subject availability counts are in
`succeeding_tests_check.json`; no succeeding-test identity was unresolved.

For the 19 base residual misses, `f = 0`: no record has every selected test in
PIT's succeeding-test list. Across those records, 1,139 selected tests were not
executed by PIT against the exact mutant (`u_tests = 1139`). For the five
empty-footprint recoveries, only one edge-only selected set is wholly covered
by PIT succeeding tests. Consequently, neither optional manuscript sentence
from Step 2 was inserted. The committed verifier reports:

`PASS: v15 succeeding-tests audit verified; f=0, u_tests=1139, unresolved=0`

## Step 3: IEEE paper

The anonymous paper uses `\documentclass[conference,letterpaper]{IEEEtran}`,
BibTeX with `IEEEtran.bst`, and the 22 cited entries in `references.bib`. It has
five native LaTeX tables; Table 5 is a two-column `tabularx` table. The PDF has
9 pages: body material occupies pages 1--7 and references occupy pages 8--9.
This satisfies the 10-page body plus 2-page reference budget.

Every page was rendered to PNG and visually inspected. No clipping, overlap,
or split-table defect was observed. The case-insensitive token gate over both
`paper.tex` and extracted PDF text has zero matches. PDF SHA-256:

`8560d8fb2a234ea6d15c799e2dbf3edac870d9506d32aa51c593c25aad0f2287`

The paper contains the literal `ANON_URL` placeholder and the requested AI-use
acknowledgment. Both require author action before submission: upload the ZIP to
an anonymous host and replace `ANON_URL`; confirm or edit the acknowledgment.

## Step 4: anonymized artifact

The package was exported without Git history from `rad1-v14.9`, then augmented
only with the Step 2 script, output, and verifier. Text and metadata were
scrubbed; coverage footprint lists were not rewritten. `CITATION.cff` files
were removed and a new `ANON_CHECKSUMS.sha256` was generated.

The pre-scrub counts and zero-valued post-scrub counts are recorded in
`rad1-v15/artifact_scrub_report.json`. The final content scan, decompressed-GZIP
scan, and binary-class string scan found zero forbidden tokens. All required
checks passed inside the anonymous copy:

- unit tests: 68 tests, `OK`;
- B2 verifier: PASS;
- v14.6 verifier: PASS;
- v14.9 verifier: PASS (`k_miss=0`, `k_only=0`, `k_other=10`);
- v15 verifier: PASS (`f=0`, `u_tests=1139`, unresolved=0).

The ZIP is approximately 97 MiB and has SHA-256
`0291eda030c2c29508e8da1f206434c47dbb2392688905bfd1d50e9910cd8ac6`.

Suggested upload procedure:

1. create a private anonymous project on anonymous.4open.science (or an
   equivalent double-blind artifact host);
2. upload `anon-artifact.zip` without changing its bytes;
3. verify the host-provided download against the SHA-256 above;
4. replace `ANON_URL` in `paper.tex`, rebuild, and rerun the paper token gate.

## Step 5: evaluation-repository verification

`run_verifications.py` executed the complete current verification set. All 11
commands exited zero: the 68-test unit suite; historical failure-mode,
selector-equivalence, freeze, and recollection checks; B2; v14.6; v14.7;
v14.8; v14.9; and v15. Exact commands, exit codes, last lines, and individual
logs are in `verification_results.json` and `verify_*.log`.

The repository changes are limited to `analysis/v15/`. The evidence commit is
`8a7ae59513278992eecbbdb346b38deba75487d8`; `rad1-v15` is the authoritative
tag and includes this report-only follow-up. The task authorizes pushing
`main` and `rad1-v15`; remote confirmation is reported in the final handoff.

## Author actions

1. Replace `ANON_URL` after uploading the exact ZIP.
2. Confirm or edit the AI-use acknowledgment against the conference policy.
