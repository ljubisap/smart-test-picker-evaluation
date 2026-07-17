# Literature Search Protocol

This document supports the novelty claims made in the paper "Lightweight Regression Test Selection via Per-Test Runtime Class and Method Coverage in Java":

1. (Section 2.2, revised) "To the best of our knowledge, no prior study has provided a complete probe-level causal analysis of all observed false negatives in a JaCoCo-based per-test selector, together with an explicit failure taxonomy, a measured mitigation, and a characterization of the residual observability boundary."
2. (Section 2.5) "To the best of our knowledge, none of the reviewed approaches combines per-test method-level runtime coverage mapping with dual-granularity selection in a single pass, direct Git-based method-context extraction from committed, staged, and working-tree changes, explicit per-test selection reasoning, and actionable coverage feedback for developers."

Note: The original claim that this is "the first work to quantify the fault-detection inclusiveness of JaCoCo-based per-test selection against mutation testing" was found to be indefensible (see Section 12) and has been replaced with claim 1 above.

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

## 2. Systematic verification search — STATUS: COMPLETED (2026-07-17)

The verification search was completed on 2026-07-17. Coverage was achieved
through cross-index web search (returning results from ACM, IEEE, Springer,
ScienceDirect, DBLP, and arXiv), backward/forward snowballing from seed
papers, venue proceedings checks (ISSTA, ICSE, ASE, ICST, FSE, TSE, JSS,
IST), repository/tool ecosystem search (GitHub, Gradle Plugin Portal, Maven
Central), and primary-source verification of every retained candidate.

Native database UI queries were not individually executed for each source;
this is documented transparently in the search log.

**Critical finding:** Dreier (2017) already combined JaCoCo-based per-test
method coverage with PIT mutation-based fault-detection evaluation on 12 Java
systems. The original broad novelty claim ("first work to quantify...") is
therefore not defensible and has been narrowed to the probe-level causal
analysis, failure taxonomy, mitigation, and observability boundary.

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

- Initial discovery pass: 2026-07-16
- Final verification pass completed: 2026-07-17
- Publications and tool information available through: 2026-07-17
- Language: English
- Primary domain: Java and JVM regression test selection
- Secondary domain: directly comparable RTS approaches in other languages
- Direct venue/proceedings verification window: 2010-2026
- Earlier foundational work (1996-2001): identified through backward snowballing

## 4. Sources

### Completed
- General web search (initial discovery 2026-07-16; final pass 2026-07-17)
- Official tool and product documentation (Teamscale, Develocity, Parasoft,
  Skippy, junit4git, Tia repositories)
- DBLP API (bibliographic verification and DOI resolution, 2026-07-16)
- Cross-index web search covering ACM, IEEE, Springer, ScienceDirect, DBLP,
  and arXiv results (2026-07-17)
- Backward/forward snowballing from seed papers
- Venue proceedings checks (ISSTA, ICSE, ASE, ICST, FSE, TSE, JSS, IST)
- GitHub, Gradle Plugin Portal, Maven Central (tool ecosystem)
- Primary-source verification for every retained candidate

### Note on methodology
Full native-UI database queries were not individually executed for ACM DL,
IEEE Xplore, Google Scholar, and arXiv as separate sessions. Coverage was
achieved through cross-index web search engines that return results from all
these databases, supplemented by backward/forward snowballing and direct
proceedings/venue checks. This is documented transparently.

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
Dreier 2017; Amann and Jürgens 2020; Reflection-Aware Static RTS; DIRTS;
BinaryRTS; iJaCoCo; Skippy; SPIRITuS; Shin et al.

## 10. Included and Near-Neighbor Works

| Work/tool | Source | Year | Java/JVM | Signal | Selection unit | JaCoCo | Fault/mutation evaluation | Classification |
|---|---|---:|---|---|---|---|---|---|
| Rothermel and Harrold safe RTS | TSE | 1996 | General | Program analysis foundations | Tests | No | Formal safety framework | Foundational |
| Harrold et al. Java RTS | OOPSLA | 2001 | Yes | Static/program analysis | Tests | No | Safety/empirical | Foundational Java RTS |
| Ekstazi | ISSTA | 2015 | Yes | Dynamic file dependencies | Test class/method | No | Commit-history evaluation | Direct baseline |
| **Dreier: Obtaining Coverage per Test Case** | **TUM thesis** | **2017** | **Yes** | **JaCoCo per-test method coverage** | **Test method** | **Yes** | **PIT on 12 Java systems; 99.2% fault detection** | **Closest prior work — MUST be discussed** |
| STARTS | ASE | 2017 | Yes | Static bytecode dependencies | Test class | No | Commit-history evaluation | Direct baseline |
| Regression Test Selection Across JVM Boundaries (Celik et al.) | ESEC/FSE | 2017 | Yes | Dynamic, cross-JVM | Test | No | Empirical | Near-neighbor |
| HyRTS (Zhang) | ICSE | 2018 | Yes | Dynamic, hybrid file+method granularity | Test | No (own instrumentation) | Commit-history evaluation | Included; multi-granularity |
| SPIRITuS (Romano, Scanniello, Antoniol, Marchetto) | IST | 2018 | Yes | Method code coverage + lexical similarity | Test | No | 389 mutation-generated faulty versions | Included; method-level predecessor |
| RTSCheck (Zhu et al.) | ICSE | 2019 | Yes | n/a (checks RTS tools) | n/a | No | Rule/behavior checking | Near-neighbor |
| Reflection-Aware Static RTS (Shi et al.) | PACMPL/OOPSLA | 2019 | Yes | Static + reflection handling | Test class | No | Empirical | Near-neighbor |
| **Amann and Juergens: Change-Driven Testing** | **Springer** | **2020** | **Yes** | **Test-wise coverage (Teamscale)** | **Test** | **Yes (Teamscale uses JaCoCo)** | **99.3% fault detection on 12 systems** | **Included -- published Teamscale line** |
| Build-System-Aware RTS (Elsner et al.) | ICSE-SEIP | 2022 | Multi | Build-system + non-code dependencies | Test | No | Industrial CI evaluation | Near-neighbor |
| Shin et al.: Empirical Comparison of Four Java RTS Techniques | JSS | 2022 | Yes | Various incl. coverage-based (OpenClover) | Test | No | PIT mutation scores; 30,354 mutants | Included; closest mutation-based RTS comparison |
| DIRTS (Hundsdorfer et al.) | ICST | 2023 | Yes | DI-aware static dependencies | Class/method | No | Empirical | Direct baseline |
| BinaryRTS (Elsner et al.) | ICST | 2023 | No (C++) | Binary instrumentation | Test | No | Empirical | Cross-language comparison |
| More Precise RTS (Liu et al.) | ISSTA | 2023 | Yes | Static + semantic change reasoning | Test class | No | Empirical | Near-neighbor |
| iJaCoCo (Wang et al.) | ASE | 2024 | Yes | Ekstazi + JaCoCo | Test subset for coverage update | Yes | Coverage maintenance, not RTS fault inclusiveness | Near-neighbor |
| JcgEks (Zhang et al.) | ASE | 2024 | Yes | Dynamic file + static method call graph | Test class | No | 1,000 revisions, 20 projects | Included; multi-granularity |
| BabelRTS (Maurina et al.) | TSE | 2025 | Polyglot | Static cross-language dependencies | Test | No | Empirical | Near-neighbor |
| Skippy | Repository (archived 2025-09-18) | - | Yes | JaCoCo coverage | Test method/case | Yes | No systematic evaluation located | OSS tool |
| junit4git | Repository | - | Yes | Git-change-based test skipping | Test | Unclear | No published evaluation | OSS tool |
| Tia | Repository | - | Yes | JaCoCo method mapping | Test | Yes | No published evaluation | OSS tool |
| Teamscale TIA | Product docs | - | Yes | Test-wise coverage | Proprietary | Yes | See Dreier 2017 and Amann 2020 | Industrial (academic described above) |
| Develocity PTS | Product docs | - | Yes | Predictive/history model | Test | Proprietary | Proprietary | Adjacent industrial |
| Parasoft Jtest TIA | Product docs | - | Yes | Coverage + execution correlation | Unit test | Not established | No open artifact | Industrial comparison |

Parasoft note: public documentation confirms selective execution correlating
code changes with impacted unit tests, but implementation details and
reproducible evaluation artifacts are not publicly available.

JCov "test scales": screened during the 2026-07-16 pass via a secondary
source (Wikipedia) only; no primary OpenJDK/JCov confirmation of a relevant
per-test capability was located; excluded from the candidate corpus.

## 11. Excluded Near-Neighbors

| Work | Reason not treated as directly equivalent |
|---|---|
| iJaCoCo | Uses RTS to update coverage incrementally; regression-test execution reduction is not the final evaluated objective |
| Test prioritization studies | Reorder tests but do not decide which tests may be skipped |
| Test-suite minimization studies | Do not select tests in response to a code change |
| Mutation-test acceleration | Uses RTS to accelerate mutation testing rather than evaluating RTS fault-detection inclusiveness |

## 12. Result

**The original broad novelty claim is not defensible.**

Dreier (2017) already combined JaCoCo-based per-test method coverage with
PIT mutation-based fault-detection evaluation on 12 Java systems, reporting
99.2% aggregate fault detection. Amann and Jürgens (2020) published the same
Teamscale test-wise-coverage line of work with a 99.3% result across twelve
systems. SPIRITuS (2018) evaluated method-level coverage-based RTS fault
detection on 389 mutation-generated faulty versions. Shin et al. (2022)
compared four Java RTS tools using PIT with 30,354 mutants.

Therefore, the manuscript MUST NOT claim:
- "first JaCoCo-based per-test selection evaluated against mutation testing"
- "first coverage-based RTS evaluated with mutation testing"
- any broader variant of these

**What remains novel (narrowed claim):**

No prior study was identified that provides a complete per-mutant
killing-test inclusiveness audit of a JaCoCo-based per-test selector that:
1. traces every observed false negative to JaCoCo probe-level semantics;
2. derives an explicit three-type failure taxonomy (A/B/C);
3. evaluates a targeted conservative mitigation rule with measured cost;
4. characterizes the residual observability boundary, including the
   Type C case that cannot be identified from positive coverage-map entries.

Prior aggregate evaluations (Dreier, Amann/Jürgens) reported overall
detection rates but did not perform per-mutant killing-test analysis,
identify the shared causal probe mechanism, or derive a taxonomy.

This conclusion does not establish the absolute absence of unpublished,
proprietary, or differently indexed work.

## 13. Maintenance

Re-run the queries in Section 5 before camera-ready submission; record the
date and any new findings in Sections 10-12 and the CSV logs.
