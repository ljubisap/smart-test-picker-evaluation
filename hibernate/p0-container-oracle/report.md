# Hibernate container-to-leaf P0 resolution

## Decision

`CONTAINER_ONLY_KILL`

PIT's KILLED result is real, but it is not a leaf-test killing identity compatible with the paper's leaf-level oracle. The exact mutant fails during `BytecodeEnhancedTestEngine` discovery/enhancement before either runnable leaf starts.

## Existing evidence

| Evidence | Meaning |
|---|---|
| PIT `killingTests` is the enhanced-engine class container | container failure |
| PIT `numberOfTestsRun=0` | no PIT-counted leaf execution; not sufficient alone |
| one leaf appears in `coveringTests` | pristine coverage only |
| evaluator expands the container to two coverage keys | normalization only |

## Direct experiment

Native discovery/source evidence identifies exactly two leaves. Each passes when selected alone on pristine bytecode. PIT `+EXPORT` produced the exact mutant (index 28, block 9), with SHA-256 `a1c1a054...`; no source approximation was used.

Against that class, selecting either leaf alone produces a synthetic `initializationError`. Lifecycle logging never reports the real leaf as started. The stack passes through `BytecodeEnhancedTestEngine.doDiscover`, `enhanceTestClass`, `EnhancerImpl`, and then the mutant-dependent null at `BiDirectionalAssociationHandler.entityType`. A class-container selector produces the identical failure.

## Oracle treatment

The old container-to-all-leaves normalization is not a valid killing-test oracle for this record. The smallest defensible treatment is to exclude exactly this record from leaf-level inclusiveness and retain it in this separate container-only evidence category. Raw PIT output is unchanged.

Canonical analysis uses `analysis/oracle_exclusions.json`; it does not alter STP, selector semantics, coverage, PIT, or any other mutation.

## Quantitative impact

After deterministic regeneration:

- Hibernate: 401 KILLED, 400 inclusive, one leaf-level miss.
- Main aggregate: 4,010 KILLED, 3,986 inclusive, 24 misses.
- Footprints: A=7, B=10, C=6, MIXED=1.
- Causes: 23 early-exception annotations, one pre-test attribution-gap miss.
- Constructor mitigation: 3,993/4,010.
- Class baseline: 4,004/4,010.

The final generated JSON files are authoritative for rounded percentages and mean selection sizes.
