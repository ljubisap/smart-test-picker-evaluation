# Pending RAD1 v11 edits (apply AFTER the final literature commit)

This document supersedes v10_1_pending_manuscript_edits.md.

The critical change: the "first JaCoCo + mutation evaluation" novelty claim
is no longer defensible. Dreier (2017) already combined JaCoCo per-test
method-coverage selection with PIT mutation evaluation on 12 Java systems.

---

## CRITICAL: Replace the novelty claim

### Remove from Abstract, Section 2.5, and anywhere else it appears:

> "this is the first work to quantify the fault-detection inclusiveness of
> JaCoCo-based per-test selection against mutation testing"

### Replace with (Abstract and Section 2.5):

> To the best of our knowledge, no prior study has provided a complete
> probe-level causal analysis of all observed false negatives in a
> JaCoCo-based per-test selector, together with an explicit failure taxonomy,
> a measured mitigation, and a characterization of the residual observability
> boundary.

---

## Section 2.1 — add after the Rothermel and Harrold sentence

Harrold et al. developed an early safe regression-test-selection technique
specifically for Java, handling incomplete programs and external libraries
[Harrold et al., OOPSLA 2001]. HyRTS later combined file- and method-level
dependency granularities to balance safety and selection precision
[Zhang, ICSE 2018]. More recently, JcgEks integrates Ekstazi's dynamic file
dependencies with static method call graph analysis, reporting 29% less
end-to-end time and 30.9% fewer test classes than Ekstazi across 1,000
revisions of 20 projects [Zhang et al., ASE 2024].

---

## Section 2.2 — add BEFORE the Skippy paragraph (closest predecessors)

### Dreier/Teamscale paragraph (MUST appear first as closest predecessor):

An especially close predecessor is Dreier's 2017 master's thesis, which
implemented JaCoCo-based per-test method coverage and change-based test
selection in Teamscale, integrated the approach with Maven and Gradle, and
evaluated fault detection using PIT across twelve Java systems including
Apache Commons Lang. The selected tests detected 99.2% of the mutants
detected by the full suites. Amann and Jürgens subsequently described the
same test-wise-coverage Test-Impact Analysis line of work in their published
account of Change-Driven Testing, reporting 99.3% fault detection across
twelve or more systems [Amann and Jürgens, 2020]. Our study therefore does
not claim the first combination of JaCoCo-based per-test selection and
mutation analysis. Instead, it performs a complete per-mutant killing-test
inclusiveness audit, traces every observed false negative to JaCoCo probe
semantics, derives an explicit failure taxonomy, evaluates a targeted
mitigation, and characterizes the residual observability boundary.

### SPIRITuS/Shin paragraph (after Dreier):

SPIRITuS uses method-level code coverage together with lexical change
information to select regression tests and evaluates the resulting
reduction/fault-detection trade-off on 389 mutation-generated faulty versions
of fourteen Java programs [Romano et al., IST 2018]. It is a close
predecessor in method-level coverage-based selection, but it does not use
JaCoCo as the dependency signal or study probe-level coverage failures. Shin
et al. compared four Java RTS tools, including the coverage-based OpenClover,
and evaluated the fault-detection ability of their selected suites using PIT
with 30,354 mutants [Shin, Ghosh, Vijayasarathy, JSS 2022]. Their study
compares tool effectiveness across revisions rather than performing per-mutant
killing-test inclusiveness analysis or examining the mechanisms by which
coverage-based dependencies are missed.

### Tool ecosystem additions (after Skippy):

Add one sentence: Parasoft Jtest provides commercial Java test-impact analysis
that correlates test-execution and coverage data with code changes;
implementation details and reproducible evaluation artifacts are not publicly
available. In the open-source ecosystem, junit4git and Tia also provide
JaCoCo-based test-impact functionality without published fault-detection
evaluations.

---

## Section 2.5 — replace the literature TODO

Use Option A (search is now COMPLETED):

The literature search covered major software-engineering publication databases,
venue proceedings, open-source tool ecosystems, and public industrial-tool
documentation through July 2026. The complete queries, eligibility criteria,
screening decisions, and backward/forward snowballing are documented in the
replication package (docs/LITERATURE_SEARCH.md).

---

## Section 2.5 — revise the research gap paragraph

Remove: "Furthermore, although JaCoCo has been used for RTS before (Skippy
[9], Teamscale [11]), the fault-detection implications of using probe-based
coverage as a dependency proxy have not been systematically characterized."

Replace with: "Although per-test JaCoCo-based selection has been evaluated
for aggregate fault detection (Dreier, 2017; Amann and Jürgens, 2020) and
method-level coverage-based RTS has been assessed on mutant-seeded faulty
versions (Romano et al., 2018), the probe-level mechanisms by which
JaCoCo-based selection misses individual fault-detecting tests have not been
systematically identified, taxonomized, or mitigated. This paper addresses
that gap."

---

## Comparison Table (Table 1) — add Teamscale/Dreier row

| Feature | Smart Test Picker | Dreier/Teamscale | Ekstazi | STARTS | Skippy |
|---------|-------------------|------------------|---------|--------|--------|
| Analysis type | Dynamic (JaCoCo) | Dynamic (JaCoCo) | Dynamic (agent) | Static | Dynamic (JaCoCo) |
| Dependency granularity | Class + method | Method | File/class | Class | Class |
| Per-mutant inclusiveness audit | Yes (this paper) | Aggregate (99.2%) | No | No | No |
| Probe-level failure analysis | Yes | No | n/a | n/a | No |
| Failure taxonomy + mitigation | Yes | No | No | No | No |

---

## References — add entries for

- Dreier, F. Obtaining Coverage per Test Case. Master's thesis, Technical
  University of Munich, 2017.
- Amann, S. and Jürgens, E. Change-Driven Testing. In: The Future of Software
  Quality Assurance, Springer, 2020. DOI: 10.1007/978-3-030-29509-7_1.
- Harrold, M.J., Jones, J.A., Li, T., and Liang, D. Regression Test Selection
  for Java Software. OOPSLA 2001.
- Zhang, L. Hybrid Regression Test Selection. ICSE 2018.
  DOI: 10.1145/3180155.3180198.
- Romano, S., Scanniello, G., Antoniol, G., and Marchetto, A. SPIRITuS: a
  SimPle Information Retrieval regressIon Test Selection approach. IST 2018.
  DOI: 10.1016/j.infsof.2018.03.004.
- Shin, M.K., Ghosh, S., and Vijayasarathy, L.R. An Empirical Comparison of
  Four Java-based Regression Test Selection Techniques. JSS 2022.
  DOI: 10.1016/j.jss.2021.111174.
- Zhang, C., Li, B., Chen, Z., and Hao, D. Hybrid Regression Test Selection by
  Integrating File and Method Dependences (JcgEks). ASE 2024.
  DOI: 10.1145/3691620.3695062.
- Machalica, M., Samber, A., Behrndt, M., Branscomb, B., and Cadar, C.
  Predictive Test Selection. ICSE-SEIP 2019.
  DOI: 10.1109/ICSE-SEIP.2019.00018.
- Parasoft. Jtest Test Impact Analysis. Product documentation.

---

## Contributions list (Section 1) — revise bullet 2

Replace: "A mutation-based evaluation of killed-mutant inclusiveness..."

With: "A reproducible per-mutant killed-mutant inclusiveness audit on four
open-source projects using PIT killing-test matrices, with Monte Carlo and
analytical random baselines, extending prior aggregate fault-detection
evaluations of JaCoCo-based selection (Dreier, 2017) to individual-mutant
granularity with full killing-test resolution."

---

## Discussion (Section 5) — add acknowledgment

After the first paragraph add:

> Dreier's 2017 evaluation of Teamscale's test-wise coverage reported 99.2%
> aggregate fault detection across twelve systems. Our per-mutant audit on four
> systems yields comparable headline figures (97.58%–100%) but additionally
> identifies the precise probe-level mechanism behind every observed miss and
> demonstrates that all false negatives share a single causal pattern. This
> level of causal detail was not present in prior aggregate evaluations.
