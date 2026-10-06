# A / B / C comparison

A: current canonical data. B: preserved unified CPU=1 iteration. C: fresh explicit DEFAULTS jobs without the override. No current result is promoted.

| State | Eligible | Base inclusive | Constructor inclusive | Class inclusive |
|---|---:|---:|---:|---:|
| A | 4010 | 3991 | 3998 | 4009 |
| B | 3926 | 3907 | 3914 | 3925 |
| C | 3931 | 3912 | 3919 | 3930 |

## Per-subject outcomes

| Subject | State | Eligible | Base inclusive | Constructor inclusive | Class inclusive | Base mean selected |
|---|---|---:|---:|---:|---:|---:|
| commons-lang | A | 772 | 771 | 771 | 771 | 22.01036269 |
| commons-lang | B | 772 | 771 | 771 | 771 | 22.01036269 |
| commons-lang | C | 772 | 771 | 771 | 771 | 22.01036269 |
| jgrapht | A | 517 | 516 | 517 | 517 | 89.70406190 |
| jgrapht | B | 468 | 467 | 468 | 468 | 88.15170940 |
| jgrapht | C | 473 | 472 | 473 | 473 | 87.32558140 |
| spring-core | A | 454 | 443 | 447 | 454 | 94.61453744 |
| spring-core | B | 419 | 408 | 412 | 419 | 96.00715990 |
| spring-core | C | 419 | 408 | 412 | 419 | 96.00715990 |
| petclinic | A | 94 | 94 | 94 | 94 | 13.72340426 |
| petclinic | B | 94 | 94 | 94 | 94 | 13.72340426 |
| petclinic | C | 94 | 94 | 94 | 94 | 13.72340426 |
| flink | A | 349 | 349 | 349 | 349 | 37.22636103 |
| flink | B | 349 | 349 | 349 | 349 | 37.22636103 |
| flink | C | 349 | 349 | 349 | 349 | 37.22636103 |
| spring-security | A | 340 | 335 | 337 | 340 | 59.85882353 |
| spring-security | B | 340 | 335 | 337 | 340 | 59.85882353 |
| spring-security | C | 340 | 335 | 337 | 340 | 59.85882353 |
| hibernate | A | 401 | 400 | 400 | 401 | 297.24688279 |
| hibernate | B | 401 | 400 | 400 | 401 | 297.24688279 |
| hibernate | C | 401 | 400 | 400 | 401 | 297.24688279 |
| quarkus | A | 1083 | 1083 | 1083 | 1083 | 269.65189289 |
| quarkus | B | 1083 | 1083 | 1083 | 1083 | 269.65189289 |
| quarkus | C | 1083 | 1083 | 1083 | 1083 | 269.65189289 |

## Raw correspondence

| Comparison | Subject | Left records | Right records | Correspondence / status counts |
|---|---|---:|---:|---|
| A_to_C | jgrapht | 804 | 803 | {'MISSING_FROM_RIGHT': 277, 'FRESH_ONLY': 279, 'ONE_TO_ONE': 464, 'NO_COVERAGE -> NO_COVERAGE': 50, 'SURVIVED -> SURVIVED': 87, 'KILLED -> KILLED': 281, 'MEMORY_ERROR -> MEMORY_ERROR': 4, 'AMBIGUOUS_MULTIPLICITY': 12, 'TIMED_OUT -> TIMED_OUT': 41, 'killingSetDifferences': 7, 'KILLED -> SURVIVED': 1} |
| A_to_C | spring-core | 563 | 557 | {'ONE_TO_ONE': 342, 'KILLED -> KILLED': 255, 'MISSING_FROM_RIGHT': 190, 'FRESH_ONLY': 188, 'SURVIVED -> SURVIVED': 29, 'NO_COVERAGE -> NO_COVERAGE': 51, 'TIMED_OUT -> TIMED_OUT': 7} |
| B_to_C | jgrapht | 803 | 803 | {'ONE_TO_ONE': 708, 'NO_COVERAGE -> NO_COVERAGE': 66, 'AMBIGUOUS_MULTIPLICITY': 47, 'SURVIVED -> SURVIVED': 140, 'KILLED -> KILLED': 416, 'MEMORY_ERROR -> MEMORY_ERROR': 8, 'TIMED_OUT -> TIMED_OUT': 73, 'killingSetDifferences': 12, 'SURVIVED -> KILLED': 5} |
| B_to_C | spring-core | 557 | 557 | {'ONE_TO_ONE': 506, 'KILLED -> KILLED': 383, 'AMBIGUOUS_MULTIPLICITY': 24, 'SURVIVED -> SURVIVED': 55, 'NO_COVERAGE -> NO_COVERAGE': 61, 'TIMED_OUT -> TIMED_OUT': 7} |

## Previously changed transit-routing records

Matched A KILLED → B SURVIVED records: 6. C outcomes: {'SURVIVED': 1, 'KILLED': 5}.
All identities, raw and normalized killing sets, statuses and eligible policy results are retained in comparison_records.json.gz.

B to C changes CPU override and any explicitly recorded worker fallback; A to C also changes the observed operator set and may differ in unrecorded historical environment. Neither comparison proves determinism or a sole cause.

| Method / line | Mutator and description | A | B | C |
|---|---|---|---|---|
| computeAVAndLF / 363 | ConditionalsBoundaryMutator: changed conditional boundary | KILLED | SURVIVED | SURVIVED |
| workerSegmentEnd / 1308 | MathMutator: Replaced integer division with multiplication | KILLED | SURVIVED | KILLED |
| workerSegmentEnd / 1308 | MathMutator: Replaced integer multiplication with division | KILLED | SURVIVED | KILLED |
| workerSegmentStart / 1296 | MathMutator: Replaced integer addition with subtraction | KILLED | SURVIVED | KILLED |
| workerSegmentStart / 1296 | MathMutator: Replaced integer division with multiplication | KILLED | SURVIVED | KILLED |
| workerSegmentStart / 1296 | PrimitiveReturnsMutator: replaced int return with 0 for org/jgrapht/alg/shortestpath/TransitNodeRoutingPrecomputation::workerSegmentStart | KILLED | SURVIVED | KILLED |
