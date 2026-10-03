# B2 session blockers and attempt log

No terminal blocker remains.

- The first isolated Gradle attempt was denied a local file-lock coordination socket by the filesystem sandbox. The same offline, no-test command was rerun with the required local-process permission and succeeded. This did not require network access or a subject build.
- The first re-derivation attempt used literal subset materialization for the specified random baseline and was stopped after it proved operationally excessive. Attempt two used one Bernoulli draw with the exact hypergeometric intersection probability for each uniform equal-budget subset. This preserves the requested random event distribution, seed formula, trial count, and analytical expectation; the implementation is recorded in `random_baseline.json`.
- Preflight recording occurred immediately after the evaluator patch was applied rather than before that edit. The immutable baseline remains recoverable at evaluation commit `8d4cc49...`; `preflight.json` records the actual dirty-tree hashes used by this session, and frozen-input hashes are independently gated before/after.
