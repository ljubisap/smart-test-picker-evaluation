# Analysis Module

Shared evaluation logic and cross-project failure taxonomy for the Smart Test Picker replication package.

## Important: Evaluation Selector vs Production Selector

This module implements a **Python evaluation selector** (`select_original`) based on the documented selection rules.

**Historical model-agreement status:** For all 1,351 unique single-method change cases represented by the 4,010 evaluated leaf-oracle KILLED mutations, `evaluation_core.select_original()` produces exactly the same selected-test sets as the historical Python edge-only model (`verify_selector_equivalence.py`). The check does not execute Java and omits the later production NO_COVERAGE branch. One occurrence has zero exact method-coverage hits; the model escalation and evaluator fallback still agree, with no evaluator-only candidate. The remaining 4,009 occurrences have exact method hits.

A separate 21-case contract test (`commons-lang/scripts/contract_test.py`) confirms exact equality against the actual pinned Maven plugin (commit `70b3984626eb`).

**What is NOT covered:**
- Multi-method changes in a single commit
- Unmapped-test detection (Java `NewTestDetector`)
- Full-suite fallback triggers
- Cases where the mutated method is absent from all coverage (would trigger Java escalation)
- Projects other than Commons Lang for the actual plugin contract test

## Footprint and Causal Classification

For each unsafe mutation (class C, method M), every killing test's coverage footprint is classified independently of root cause:

- **Type A**: C present in coverage, method footprint for C is non-empty and contains only `<init>`/`<clinit>`
- **Type B**: C present in coverage, method footprint for C is non-empty, M is absent, but at least one non-constructor method exists
- **Type C**: C is completely absent from the test's coverage entry
- **MIXED**: different resolved killing-test entries exhibit different B/C shapes

Each mutation also has one manually audited causal mechanism:

- **EARLY_EXCEPTION_PROBE_SHADOWING**: execution enters the target method, but exceptional control flow prevents downstream probe attribution
- **PRE_TEST_ATTRIBUTION_GAP**: dependency-relevant custom-engine work executes before the leaf-test coverage session opens

The same footprint shape can arise from different causes. Footprint types must therefore not be presented as root-cause categories.

## Selectors

| Selector | Definition |
|----------|-----------|
| Original | Select T if C#M in T.methods, OR (C in T.classes AND T has no C# methods) |
| Constructor-only rule | Original + select T if C in T.classes AND all C# methods are constructors |
| Class-level baseline | Select T if C in T.classes (class-presence upper bound) |

The class-level baseline cannot recover Type C cases (target class absent from coverage map).

## Commands

```bash
# Generate canonical outputs
python3 analysis/analyze_failure_modes.py --write

# Verify outputs match committed artifacts (no external dependencies)
python3 analysis/analyze_failure_modes.py --verify

# Verify historical evaluator/model agreement (dataset-wide; not Java execution)
python3 analysis/verify_selector_equivalence.py --verify

# Run unit tests (includes synthetic divergence tests)
python3 -m unittest discover -s analysis/tests
```

## Outputs

- `results/failure_taxonomy.json` -- per-mutation footprint and causal-mechanism classification with full provenance
- `results/mitigation_comparison.json` -- original vs constructor-only vs class-level for all 4,010 leaf-oracle mutations
- `results/selector_equivalence.json` -- dataset-wide agreement between the historical Python evaluator and its Python edge-only semantic model (4,010 mutations, 1,351 unique cases); this is not production-Java execution and omits the later NO_COVERAGE branch
- `oracle_exclusions.json` -- audited PIT outcomes that cannot be assigned to a runnable leaf; raw PIT evidence remains preserved
- `results/recollection_comparison.json` -- old/new coverage map comparison after final recollection

## Manual Annotations

`failure_annotations.json` provides root-cause explanations for all 24 unsafe leaf-oracle mutations. These are manually authored based on source and lifecycle inspection and are NOT automatically derivable from the coverage footprint alone. The taxonomy script validates completeness and maps the audited annotation categories to stable causal-mechanism identifiers.

## Input Provenance

Both output files include SHA-256 hashes of all input coverage maps and PIT XML files, plus the full list of PIT files used. This allows verification that results were produced from the exact committed artifacts.

The per-project manifests record the exact Smart Test Picker revision used to collect each coverage map. The independent extension subjects use the frozen JaCoCo evaluation tree `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`.

## Historical edge-only results (superseded by `results/b2-*.json`)

- 24 unsafe mutations: footprint taxonomy 7 Type A, 10 Type B, 6 Type C, and 1 mixed B/C case
- Causal mechanisms: 23 early-exception/probe-shadowing and 1 pre-test attribution-gap case
- Original: 99.40% (3986/4010)
- Constructor-only rule: 99.58% (3993/4010, +7 recovered)
- Class-level baseline: 99.85% (4004/4010)
- One Hibernate miss remains a pre-leaf custom-engine attribution gap; a second PIT KILLED outcome was directly proven container-only and is documented outside the leaf oracle
- Both invariants hold: classPresentNoMethods=0, mutatedMethodPresent=0
- Historical evaluator/model agreement: 4010/4010 exact matches, 0 mismatches (Python model only; not the full production selector at `2e0954...`)
