# Literature Search Protocol

This document supports two claims made in the paper "Lightweight Regression Test
Selection via Per-Test Runtime Class and Method Coverage in Java":

1. (Section 2.2) "To the best of our knowledge, based on our review of published
   Java RTS and JaCoCo-based test-impact approaches, this is the first work to
   quantify the fault-detection inclusiveness of JaCoCo-based per-test selection
   against mutation testing."
2. (Section 2.5) "To the best of our knowledge, none of the reviewed approaches
   combines per-test method-level runtime coverage mapping with dual-granularity
   selection in a single pass, direct Git-based method-context extraction from
   committed, staged, and working-tree changes, explicit per-test selection
   reasoning, and actionable coverage feedback for developers."

Both claims are scoped by "to the best of our knowledge". This document records
how that knowledge was assembled, so the reader can assess its coverage.

## 1. Review process actually followed

The related-work corpus was assembled incrementally during tool development and
evaluation (2025 - 2026), not through a single up-front systematic search. The
process consisted of the steps below. The final verification pass (Section 2)
is performed separately, before manuscript freeze, and its completion is
recorded in the search log.

The incremental process consisted of:

- Backward and forward snowballing from two seed papers: Ekstazi (Gligoric,
  Eloussi, Marinov, ISSTA 2015) and STARTS (Legunsen, Shi, Marinov, ASE 2017),
  including follow-up work from the same groups and from the TUM Pretschner
  group (DIRTS, BinaryRTS; both ICST 2023).
- Citation chasing from survey and foundational material on safe RTS
  (Rothermel and Harrold).
- Tool-ecosystem search for JaCoCo-based selection tools: GitHub search
  (terms: "test selection", "test impact", "JaCoCo selection", "skip tests
  coverage"), Gradle Plugin Portal, and Maven Central. This surfaced Skippy
  (archived September 2025).
- Vendor documentation review for industrial test-impact systems: Teamscale
  (CQSE) and Develocity Predictive Test Selection (Gradle Inc.).
- Exploratory discovery through general-purpose web and literature search
  tools. Every retained candidate identified through exploratory discovery was verified
  against a primary source (paper, official documentation, or repository)
  before inclusion.
- iJaCoCo (Wang, Wang, Nie, ASE 2024) was identified via forward citation
  from Ekstazi and confirmed in ASE 2024 proceedings (DOI 10.1145/3691620.3695551).

## 2. Verification search - STATUS: IN PROGRESS

An initial discovery pass was run on 2026-07-16 (see Search Log). The full
verification pass across all sources and queries below is NOT yet complete.
Until it is, this document describes a planned and partially executed
protocol; the manuscript TODO in Section 2.5 must remain in place. After the
full pass, change this heading to "Systematic verification search
(completed <date>)" and finalize Sections 10-12.

## 2.1 Search Question

The verification search investigated whether prior published work or publicly
documented tools combine:

1. Java/JVM regression test selection;
2. per-test dynamic coverage collected with JaCoCo or a comparable
   off-the-shelf coverage mechanism;
3. method-level or dual class/method selection;
4. a systematic fault-detection or mutation-based inclusiveness evaluation.

This is a structured search focused on the manuscript's novelty claims, not a
systematic review of all regression-testing research.

## 3. Search Cutoff

- Initial discovery pass: 2026-07-16; full pass: [TODO: date when completed]
- Publications and tool information available through: 2026-07-16
- Language: English
- Primary domain: Java and JVM regression test selection
- Secondary domain: directly comparable RTS approaches in other languages
- Direct venue/proceedings verification window: 2010-2026
- Earlier foundational work (1996-2001): identified through backward snowballing

## 4. Sources

### Completed
- General web search (initial discovery pass, 2026-07-16)
- Official tool and product documentation consulted so far (Teamscale,
  Develocity, Parasoft, Skippy repository)
- DBLP API (bibliographic verification and DOI resolution, 2026-07-16;
  partial — some queries timed out due to network instability)

### Pending
- ACM Digital Library (full query execution)
- IEEE Xplore (full query execution)
- Google Scholar (broad discovery verification)
- arXiv
- GitHub, Gradle Plugin Portal, Maven Central (open tools verification)

Technical claims were verified against publisher pages, papers, official
repositories, or official documentation whenever available.

## 5. Search Queries

Planned verification queries (execution status per query is recorded in
docs/literature_search_log.csv; queries not present there with a real date
have not been executed):

- "regression test selection" Java
- "regression test selection" JVM
- "test impact analysis" Java
- "predictive test selection" Java
- "method-level regression test selection" Java
- "per-test coverage" Java "test selection"
- "test-level coverage" Java "test selection"
- JaCoCo "regression test selection"
- JaCoCo "test impact analysis"
- JaCoCo "test selection"
- ("mutation testing" OR PIT) "regression test selection"
- ("mutation testing" OR PIT) "test impact analysis"
- ("fault detection" OR inclusiveness OR safety) "regression test selection"
- JUnit JaCoCo test impact
- Gradle Maven test impact analysis
- Java coverage based selective testing
- Java JaCoCo affected tests

Search log: see docs/literature_search_log.csv (date, source, exact query,
results screened, candidates retained).

## 6. Inclusion Criteria

A publication or tool was retained when it met one or more of:

- selects regression tests based on production-code changes;
- targets Java or the JVM;
- uses static or dynamic dependency information relevant to the comparison;
- uses JaCoCo or another coverage-based dependency signal;
- performs selection at test-class or test-method level;
- evaluates safety, inclusiveness, fault detection, or mutation effectiveness;
- represents a directly relevant industrial test-impact system.

## 7. Exclusion Criteria

Excluded unless directly relevant to the novelty analysis:

- test prioritization without selection;
- change-independent test-suite minimization;
- test generation; fault localization;
- coverage optimization not ending in test selection;
- non-JVM work without a directly transferable RTS design;
- informal descriptions without sufficient technical information.

## 8. Screening Procedure

Stopping rule for broad-result engines (Google Scholar, web search): the first
50 results per query were screened, or screening stopped earlier after two
consecutive result pages produced no potentially relevant candidates.

For each query: titles screened; abstracts or tool summaries inspected; full
texts or primary documentation reviewed for potentially relevant candidates;
classification as directly relevant / near-neighbor / excluded, with a recorded
reason for every plausible near-neighbor. Candidates: see
docs/literature_candidates.csv.

## 9. Snowballing

Backward and forward reference checking from seed works:
Rothermel and Harrold; Harrold et al. (OOPSLA 2001, Java RTS); Ekstazi; STARTS;
Reflection-Aware Static RTS; DIRTS; BinaryRTS; iJaCoCo; Skippy.
Backward and forward reference checking is being performed from the listed
seed works; completed snowballing steps and retained candidates are recorded
in the search log and candidate table.

## 10. Included and Near-Neighbor Works

| Work/tool | Source | Year | Java/JVM | Signal | Selection unit | JaCoCo | Fault/mutation evaluation | Classification |
|---|---|---:|---|---|---|---|---|---|
| Rothermel and Harrold safe RTS | TSE | 1996 | General | Program analysis foundations | Tests | No | Formal safety framework | Foundational (snowballing) |
| Harrold et al. Java RTS | OOPSLA | 2001 | Yes | Static/program analysis | Tests | No | Safety/empirical | Foundational Java RTS - add to Section 2.1 |
| Ekstazi | ISSTA | 2015 | Yes | Dynamic file dependencies | Test class/method | No | Commit-history evaluation | Direct baseline |
| STARTS | ASE | 2017 | Yes | Static bytecode dependencies | Test class | No | Commit-history evaluation | Direct baseline |
| Reflection-Aware Static RTS (Shi, Hadzi-Tanovic, Zhang, Marinov, Legunsen) | PACMPL/OOPSLA | 2019 | Yes | Static + reflection handling | Test class | No | Empirical | Relevant Java RTS |
| Build-System-Aware Multi-language RTS (Elsner, Wuersching, Schnappinger, Pretschner, Graber, Dammer, Reimer) | ICSE-SEIP | 2022 | Multi | Build-system + non-code dependencies | Test | No | Industrial CI evaluation | Relevant Pretschner-group RTS |
| More Precise RTS via Semantics-Modifying Changes (Liu, Zhang, Nie, Gligoric, Legunsen) | ISSTA | 2023 | Yes | Static + semantic change reasoning | Test class | No | Empirical | Recent Java RTS near-neighbor |
| Empirical Comparison of Four Java RTS Techniques (Shin, Ghosh, Vijayasarathy) | JSS | 2022 | Yes | Various incl. coverage-based (OpenClover) | Test | No | Mutation-score-based fault-detection analysis of selected suites | MUST be discussed in manuscript Section 2.2: closest prior mutation-based evaluation of RTS effectiveness; does not measure mutation-level killing-test inclusiveness for JaCoCo-based per-test selection nor probe-level mechanisms |
| BabelRTS (Maurina, Cazzola, Ghosh) | TSE | 2025 | Polyglot | Static cross-language dependencies | Test | No | Empirical (public replication package) | Recent near-neighbor within cutoff window |
| SPIRITuS (Romano, Scanniello, Antoniol, Marchetto) | IST | 2018 | Yes | Method code coverage + lexical similarity (IR) | Test | No | Empirical | Closest published method-level coverage-based RTS predecessor; cite and distinguish in Section 2 |
| DIRTS | ICST | 2023 | Yes | DI-aware static dependencies | Class/method | No | Empirical | Direct baseline |
| BinaryRTS | ICST | 2023 | No (C++) | Binary instrumentation | Test | No | Empirical | Cross-language comparison |
| iJaCoCo | ASE | 2024 | Yes | Ekstazi + JaCoCo | Test subset for coverage update | Yes | Coverage maintenance, not RTS fault inclusiveness | Near-neighbor |
| Regression Test Selection Across JVM Boundaries (Celik, Vasic, Milicevic, Gligoric) | ESEC/FSE | 2017 | Yes | Dynamic, cross-JVM | Test | No | Empirical | Relevant Java RTS; also relevant to out-of-process future work |
| HyRTS (Zhang) | ICSE | 2018 | Yes | Dynamic, hybrid file+method granularity | Test | No (own instrumentation) | Commit-history evaluation | Direct near-neighbor for multi-granularity selection; cite in Section 2.1 |
| RTSCheck (Zhu, Legunsen, Shi, Gligoric) | ICSE | 2019 | Yes | n/a (checks RTS tools) | n/a | No | Rule/behavior checking, not mutation inclusiveness | Relevant validation methodology |
| Skippy | Repository (archived 2025-09-18) | - | Yes | JaCoCo coverage | Test method/case | Yes | No systematic mutation evaluation located | Closest OSS tool |
| Teamscale TIA | Product docs | - | Yes | Execution/coverage data | Proprietary | Supports JaCoCo input | No open artifact located | Industrial comparison |
| Develocity PTS | Product docs | - | Yes | Predictive/history model | Test | Proprietary | Proprietary | Adjacent industrial |
| Parasoft Jtest TIA | Product docs | - | Yes | Correlates test-execution and coverage data with code changes; internal implementation details are proprietary | Unit test | Not established | No open artifact located | Industrial comparison (verification pass 2026-07-16) |

Parasoft note: public documentation confirms selective execution correlating
code changes with impacted unit tests, but implementation details and
reproducible evaluation artifacts are not publicly available; do not claim a
specific internal mechanism in the manuscript.

JCov "test scales": screened during the 2026-07-16 pass via a secondary
source (Wikipedia) only; no primary OpenJDK/JCov confirmation of a relevant
per-test capability was located, so the item is excluded from the candidate
corpus and must not be cited in the manuscript. Re-add only if primary
documentation is found during the full pass.

[TODO: add every additional plausible candidate found during the full pass.]

## 11. Excluded Near-Neighbors

| Work | Reason not treated as directly equivalent |
|---|---|
| iJaCoCo | Uses RTS to update coverage incrementally; regression-test execution reduction is not the final evaluated objective |
| Test prioritization studies | Reorder tests but do not decide which tests may be skipped |
| Test-suite minimization studies | Do not select tests in response to a code change |
| Mutation-test acceleration | Uses RTS to accelerate mutation testing rather than evaluating RTS fault-detection inclusiveness |

## 12. Result (draft - finalize after the full pass)

Primary finding: no prior publication or publicly documented tool was
identified that systematically evaluates mutation-level killing-test
inclusiveness for JaCoCo-based per-test regression test selection and analyzes
the JaCoCo probe-level mechanisms of all observed false negatives. This is the
central gap the manuscript addresses. Note in particular that Shin et al.
(JSS 2022) evaluate the fault-detection ability of selected suites with
mutation scores across four Java RTS tools; their study measures comparative
tool effectiveness across revisions, not mutation-level killing-test
inclusiveness for JaCoCo-based per-test selection, and it does not analyze
probe-level false-negative mechanisms. Any broader phrasing such as
'coverage-based RTS fault detection has never been evaluated with mutation
testing' would be false and must not appear in the manuscript.

The closest coverage-based Java/JVM systems were Skippy, Teamscale, and
iJaCoCo. Skippy provides JaCoCo-based test-impact functionality but no
systematic mutation-based fault-detection evaluation was located. Teamscale is
a commercial system whose implementation and evaluation artifacts are not
openly reproducible. iJaCoCo uses JaCoCo and regression-test selection to
reduce incremental coverage-analysis cost, rather than evaluating RTS as the
final selective-execution objective.

Secondary observation: no reviewed prior system was identified that combines the
complete engineering feature set described in Section 2.5 of the manuscript.
This observation is limited to the sources, queries, screening depth, and
cutoff date documented here and does not carry the primary novelty argument.

This conclusion does not establish the absolute absence of unpublished,
proprietary, or differently indexed work.

## 13. Maintenance

Re-run the queries in Section 5 before camera-ready submission; record the
date and any new findings in Sections 10-12 and the CSV logs.
