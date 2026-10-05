# Separate PIT operator-set unification

This directory is an independent iteration. It does not replace any current result,
map, manuscript, or anonymous package. The baseline is recorded in `preflight.json`;
`baseline_hashes.json` covers every previously tracked file, not just analysis inputs.

## Execution

`scripts/run_campaigns.py` imports and executes the documented original runners:

- `jgrapht/scripts/02_run_pit.py`, all classes in `jgrapht/config/sample_classes.json`;
- `spring-core/scripts/02_run_pit.py`, all classes in `spring-core/config/sample_classes.json`.

Both original runners already declare PIT 1.17.4 and the JUnit integration resolves
1.2.1. The frozen matrices nevertheless contain the older conditional operator.
No runner source was edited and no fictitious version-only diff is claimed. New
matrix operator inventories provide execution evidence of the replacement.

Subject revisions are the explicitly requested recorded collection revisions in
`preflight.json`. Older revision strings in reproduction prose/sample metadata do
not override these fixed input revisions. Sampling lists and scopes themselves are
used unchanged.

JGraphT's disposable root POM receives the unchanged `jgrapht/config/pit_profile.xml`
profile. Spring uses its native `pitClasspath` task and the documented PIT CLI; no
Gradle PIT-plugin upgrade is needed. Compilation and classpath preparation do not
invoke a Gradle Test task or collect coverage. The PIT campaigns necessarily execute
tests as required by the task.

The initial Spring preparation built `testClasses` but did not materialize the
project runtime JARs named by `pitClasspath`. It was paused at the user's request.
On authorized resume, `scripts/resume_spring.py` preserves that attempt separately,
builds `:spring-core:jar`, `:spring-core:testFixturesJar`, and `:spring-jcl:jar`,
and runs the unchanged per-class runner. Missing-path and artifact-hash evidence is
in `pit/spring-core/runtime-prerequisites.json`. Only failed/interrupted initial
jobs are infrastructure retries; classes not yet reached are first attempts.
Neither the initial failures nor the interrupted job are silently discarded.

An operator-inventory gate then exposed a second integration issue: omitting
`--mutators` on the PIT 1.17.4 CLI selects a different fallback group from the
named `DEFAULTS`. `scripts/retry_explicit_defaults.py` adds exactly
`--mutators DEFAULTS` to enforce the already-declared policy. It does not edit
the documented runner or any subject file. Disassembly of OptionsParser,
GregorEngineFactory, Mutator and StandardMutatorGroups records this distinction.
The rejected intermediate results are archived, not used as unified results.

JDK 21 and recorded thread/timeout settings are retained. Each JVM receives
`-XX:ActiveProcessorCount=1` to constrain worker ergonomics; PIT's four configured
threads remain unchanged. Subjects run sequentially. Commands, environment, build
diffs, statuses and elapsed time are retained in `pit/`. A mutant-level timeout or
memory error is retained as that status and is not a reason for a favorable-outcome
retry. Only evidenced infrastructure failures permit at most two retries per class.

This CPU-exposure control is visible to subject code, not an OS-only quota.
JGraphT's transit-routing tests size an executor with `availableProcessors()`.
Accordingly, the dataset unifies PIT operator versions under this recorded
environment, but does not isolate PIT version as the sole causal explanation for
changes relative to older runs. `BLOCKERS.md` records the exact source lines and
`results/status_comparison.json.gz` separates comparable-record status transitions.

## Derivation

`projects_unified.json` differs from `analysis/projects_v14_6.json` only in the two
PIT file patterns. `scripts/derive.py` imports the unchanged evaluator, footprint
classification helpers and current random/interval procedures. The existing leaf
oracle exclusion remains in force. Unresolved killers are reported, not silently
turned into empty sets. No coverage map or source test is changed.

The Monte Carlo baseline retains the current exact-probability Bernoulli procedure,
seed formula and 1,000 trials. Class-cluster bootstrap retains the current pooled
class clusters, ordering, seed formula, 10,000 draws and quantile indices. These are
imports of existing functions, not replacements.

The loader's IDs include XML source path/ordinal when PIT does not supply indexes
and blocks. Moving a corresponding mutation into this iteration can therefore
change its ID. `comparison.json` distinguishes exact-ID persistence from a separate
class/method/descriptor/line/operator correspondence; it never rewrites mutation IDs
or automatically treats that correspondence as causal proof. New residual IDs need
source/control-flow evidence or are explicitly `UNDETERMINED`.

## Reproduction

From the repository root, after the two PIT campaigns complete:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/package_matrices.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/campaign_inventory.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/derive.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/causal_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/record_causal_review.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/java_replay.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/status_comparison.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/compare.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/scripts/manuscript_compare.py
PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/verify_unified.py --verify
```

The manuscript comparison requires the author's local final DOCX; it reads it only.
`package_matrices.py` is a one-time post-campaign step: deterministic gzip preserves
every XML byte while avoiding GitHub's file-size limit. Original uncompressed XML
is preserved outside the repository and its digest is in `matrix_packaging.json`.
For a clone containing packaged matrices, skip packaging and campaign execution.
The Java replay requires the hash-verified pinned runtime recorded in
`analysis/v14_4_rederivation/java_build.json`. The numerical verifier re-derives
outputs into a temporary directory under this iteration and checks recorded Java
full sets without requiring a new selector build. No manuscript binary is committed.

`java_replay.py --reuse-verified` may reuse actual Java outputs from the retained
intermediate replay only when map digests, class/method inputs, production artifact
hashes, harness hash and full evaluator-selected sets are identical. Occurrences
are reweighted from the final PIT inputs. If any required case is absent, the
entire current harness is executed again. `java/runtime.json` discloses reuse;
no Python model is substituted for a Java invocation.
