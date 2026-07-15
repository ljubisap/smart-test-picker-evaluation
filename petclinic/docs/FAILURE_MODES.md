# Failure Mode Analysis  - Spring PetClinic

## Summary

Out of 94 KILLED mutations across 14 classes with killed mutants (17 total mutated), **zero mutations** were missed by the plugin's selection algorithm.

**Inclusiveness: 100.00% (94/94)**

## No Unsafe Mutations

Unlike Apache Commons Lang (which had 1 unsafe mutation due to an exception-path coverage gap), Spring PetClinic achieved 100% killed-mutant inclusiveness. This was observed for a small project with:

- Simple test structure (no deeply nested test classes)
- Straightforward method coverage (no exception-only test paths)
- Good test-to-production mapping (each controller has a dedicated test class)

## Why No Probe-Shadowed False Negative Was Observed

The exception-path coverage gap that caused the single failure in commons-lang requires ALL of:

1. A test that exercises a method ONLY via an exception path
2. The exception must occur before the corresponding JaCoCo probe activates
3. The method must be in a class where OTHER methods DO have method-level coverage

No probe-shadowed false negative was observed among the 94 evaluated killed mutants  - tests exercise methods through normal execution paths, and exception tests (like `PetValidator` validation) still cover instrumented lines before throwing.

## Per-Class Results

All 14 classes with KILLED mutations achieved 100% safety:

| Class | Mutations (KILLED) | Safety |
|-------|-------------------|--------|
| OwnerController | 24 | 100% |
| PetController | 20 | 100% |
| Owner | 14 | 100% |
| PetValidator | 8 | 100% |
| VisitController | 5 | 100% |
| Vet | 4 | 100% |
| VetController | 4 | 100% |
| BaseEntity | 3 | 100% |
| Pet | 3 | 100% |
| PetTypeFormatter | 3 | 100% |
| Person | 2 | 100% |
| Vets | 2 | 100% |
| NamedEntity | 1 | 100% |
| Visit | 1 | 100% |

## Normalization

PIT test IDs in PetClinic use the standard `[class:FQN]/[method:name()]` format. No nested classes or parameterized tests are present, so the normalization edge cases documented for commons-lang (nested-class ordering, test-template fallback) don't apply here.
