# RAD1 v14.7 finish report

## Scope

This session used tag `rad1-v14.6` (`df63a8feba445e1bd9cba46b24d6a6abf75139c9`) and performed read-only analysis over the adopted v14.6 maps and frozen PIT records. No PIT, coverage collection, subject build/test, map change, selector change, constructor-rule change, Hibernate-exclusion change, or `results/v14_6-*` change was made.

## spring-core run-2 sensitivity

Both maps resolve all 454 eligible killing records. Results:

| Policy | Run 1 inclusive / mean selected | Run 2 inclusive / mean selected | Different selected sets |
|---|---:|---:|---:|
| Base | 443/454 / 94.61453744493392 | 443/454 / 94.58810572687224 | 6 |
| Constructor | 447/454 / 98.91629955947137 | 447/454 / 98.8898678414097 | 6 |
| Class | 454/454 / 543.1828193832599 | 454/454 / 542.9185022026431 | 60 |

The same eleven mutation IDs remain base-policy misses, with the same footprint types: four Type A and seven Type B. No miss enters or leaves the residual set. Only spring-core was collected twice. Full mutation IDs and killer footprints are in `springcore_run2_sensitivity.json`.

## Worked example

For `GenericConversionService#canConvert`, line 133, `VoidMethodCallMutator`, PIT ordinal 17:

- name-level H count: 100;
- empty-footprint U count: 14;
- base selection: 114 = 100 H + 14 U, with no other entries;
- both reported killers have only `GenericConversionService#<init>` in the target-class method footprint and lack `canConvert`;
- mutation footprint: Type A;
- base remains non-inclusive; the constructor-only rule recovers it.

Source: `worked_example_v14_6.json`.

## `.test.` segment rescan

No production class with a literal package segment equal to `test` occurs in any adopted v14.6 map. Static inspection at every recorded subject revision, including spring-core `25838a3` under `spring-core/src/main/java/`, finds no such class in any of the eight qualified production scopes. There are no remaining source-scope gaps (`test_segment_v14_6.json`).

## Provenance

`provenance_v14_6.csv` records one row per subject: collector pin, source revision, JDK, build tool, JaCoCo agent/report versions with evidence status, adopted map path/digest, and collection/environment status. The previous provenance evidence remains unchanged as historical material.

## Manuscript changes

RAD1 v14.7:

- states in Section 3.1 that all eight maps use one collector revision;
- removes “historical map inputs” from the Section 3.2 heading;
- cites `analysis/v14_7/provenance_v14_6.csv`;
- corrects Table 5 to show both killers, Type A constructor-only footprints, H=100, U=14, and base size 114;
- adds Section 6.5 with the repeat-collection sensitivity result;
- replaces the seven-source-scope `.test.` statement with the complete eight-scope result;
- records in Internal Validity that six base sets changed while inclusiveness and residual misses did not;
- adds the measured repeat-collection result to the Abstract;
- retains all v14.6 headline evaluation values.

The synchronized Markdown/DOCX/PDF contain 22 references and five tables. Forbidden-process-term grep is empty. The 11-page PDF was visually inspected; no clipping, overlap, or split table row was observed.

## Verification

All required checks pass:

- 68 analysis unit tests;
- historical failure-mode verification;
- historical selector-equivalence verification;
- frozen-artifact verification;
- historical recollection verification;
- B2 current-policy verification;
- complete v14.6 deterministic re-derivation;
- v14.7 recomputation of Steps 1–3.

Logs are stored beside this report.

## Repository finish

Evidence commit: `125331b06b161dcd49f70bda456259f3ad33a2db`.

Final local tag: `rad1-v14.7`; not pushed. Manual publication command after review: `git push origin main rad1-v14.7`.
