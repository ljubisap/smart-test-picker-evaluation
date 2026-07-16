# Analysis Module

Shared evaluation logic and cross-project failure taxonomy for the Smart Test Picker replication package.

## Important: Evaluation Selector vs Production Selector

This module implements a **Python evaluation selector** (`select_original`) based on the documented selection rules.

**Equivalence status:** For all 560 unique single-method change cases represented by the 1,837 evaluated killed mutations, `evaluation_core.select_original()` produces exactly the same selected-test sets as the modeled production Java `TestSelector` semantics (`verify_selector_equivalence.py`). Every case has at least one exact method-coverage hit, so Java's zero-hit class escalation never activates and the Python per-test fallback produces no additional candidates.

A separate 21-case contract test (`commons-lang/scripts/contract_test.py`) confirms exact equality against the actual pinned Maven plugin (commit `70b3984626eb`).

**What is NOT covered:**
- Multi-method changes in a single commit
- Unmapped-test detection (Java `NewTestDetector`)
- Full-suite fallback triggers
- Cases where the mutated method is absent from all coverage (would trigger Java escalation)
- Projects other than Commons Lang for the actual plugin contract test

## Type Classification

For each unsafe mutation (class C, method M), each killing test's coverage footprint is classified:

- **Type A**: C present in coverage, method footprint for C is non-empty and contains only `<init>`/`<clinit>`
- **Type B**: C present in coverage, method footprint for C is non-empty, M is absent, but at least one non-constructor method exists
- **Type C**: C is completely absent from the test's coverage entry

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

# Verify selector equivalence (dataset-wide)
python3 analysis/verify_selector_equivalence.py --verify

# Run unit tests (includes synthetic divergence tests)
python3 -m unittest discover -s analysis/tests
```

## Outputs

- `results/failure_taxonomy.json` -- per-mutation Type A/B/C classification with full provenance
- `results/mitigation_comparison.json` -- original vs constructor-only vs class-level for all 1837 mutations
- `results/selector_equivalence.json` -- dataset-wide Python/Java selector comparison (1837 mutations, 560 unique cases)
- `results/recollection_comparison.json` -- old/new coverage map comparison after final recollection

## Manual Annotations

`failure_annotations.json` provides root-cause explanations for all 13 unsafe mutations. These are manually authored based on source inspection and are NOT automatically derivable from the coverage footprint alone. The taxonomy script validates that every unsafe mutation has a corresponding annotation.

## Input Provenance

Both output files include SHA-256 hashes of all input coverage maps and PIT XML files, plus the full list of PIT files used. This allows verification that results were produced from the exact committed artifacts.

Coverage maps were collected with Smart Test Picker commit `70b3984626eb` (0.1.0).

## Canonical Results

- 13 unsafe mutations: 5 Type A, 7 Type B, 1 Type C
- Original: 99.29% (1824/1837)
- Constructor-only rule: 99.56% (1829/1837, +5 recovered)
- Class-level baseline: 99.95% (1836/1837)
- Both invariants hold: classPresentNoMethods=0, mutatedMethodPresent=0
- Selector equivalence: 1837/1837 exact matches, 0 mismatches
