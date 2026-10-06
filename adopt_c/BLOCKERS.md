# Adoption gates and evidence boundaries

All adoption gates passed. The repository checks, manuscript checks, and exact-ZIP checks each completed two passes; see `gates.json` and `REPORT.md`.

Historical B/C verifiers include a whole-working-tree preservation assertion. The required new historical-scope paragraph deliberately changes one of those old hashed documentation files. Their calculation and preservation checks will therefore be run against a separate unchanged historical snapshot; current repository checks and the new adoption verifier run against the adoption tree. No old verifier or evidence will be rewritten to manufacture a pass.

The manuscript and anonymous package remain outside this repository. Their checks and file digests, not manuscript or anonymous-archive contents, are recorded here.

The original JGraphT effective mutator option is not independently retained. Its XML proves the implicit operator population, but the later retained Maven profile names DEFAULTS. The manuscript narrows the requested historical explanation rather than inventing an original invocation. The replacement executions have direct version/operator/environment evidence. See `provenance_review.json`.

One duplicate raw XML is 199,104,776 bytes, above GitHub's single-file limit. The pre-existing canonical gzip already retains those exact bytes; no C file was rewritten or deleted. Only that redundant raw copy is omitted from Git staging. The new verifier checks its decompressed hash in a fresh clone; `portability_check.json` proves this works in a relocated snapshot. See `storage_manifest.json`.
