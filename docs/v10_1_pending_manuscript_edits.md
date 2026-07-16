# Pending RAD1 v10.1 edits (apply AFTER the literature protocol is committed)

## Section 2.1 - add after the Rothermel and Harrold sentence
Harrold et al. developed an early safe regression-test-selection technique
specifically for Java, handling incomplete programs and external libraries
[Harrold et al., OOPSLA 2001]. HyRTS later combined file- and method-level
dependency granularities to balance safety and selection precision
[Zhang, ICSE 2018].

## Section 2.2 - add before the Skippy paragraph
SPIRITuS uses method-level code coverage together with lexical change
information to select regression tests and evaluates the resulting
reduction/fault-detection trade-off on faulty Java program versions
[Romano et al., IST 2018]. It is a close predecessor in method-level
coverage-based selection, but it does not use JaCoCo as the dependency signal
or study probe-level coverage failures. Shin et al. compared four Java RTS
tools, including the coverage-based OpenClover, and evaluated the
fault-detection ability of their selected suites using mutation testing
[Shin, Ghosh, Vijayasarathy, JSS 2022]. Their study compares tool
effectiveness across revisions rather than mutation-level killing-test
inclusiveness or the mechanisms by which coverage-based dependencies are
missed. Parasoft Jtest provides commercial Java test-impact analysis that
correlates test-execution and coverage data with code changes; implementation
details and reproducible evaluation artifacts are not publicly available.

## Section 2.5 - replace the literature TODO with ONE of the following

### Option A - only after LITERATURE_SEARCH.md status is COMPLETED
The literature search covered major software-engineering publication
databases, venue proceedings, open-source tool ecosystems, and public
industrial-tool documentation through July 2026. The complete queries,
eligibility criteria, screening decisions, and backward/forward snowballing
are documented in the replication package (docs/LITERATURE_SEARCH.md).

### Option B - usable immediately, while the pass is still in progress
A structured verification protocol, including the sources, queries,
eligibility criteria, and screening procedure used to assess the novelty
claims, is documented in the replication package (docs/LITERATURE_SEARCH.md).

Do NOT use Option A while the protocol file says STATUS: IN PROGRESS - the
two documents would contradict each other.

## References - add entries for
Harrold et al. (OOPSLA 2001), Zhang HyRTS (ICSE 2018), Romano et al. SPIRITuS
(IST 2018), Shin et al. (JSS 2022), Parasoft Jtest TIA documentation.
