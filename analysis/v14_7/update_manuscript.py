#!/usr/bin/env python3
"""Apply evidence-backed v14.7 manuscript changes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT.parent/'rad1-v14-4'; src=HERE/'RAD1_v14_6.md'; dst=HERE/'RAD1_v14_7.md'
s=json.loads((ROOT/'analysis/v14_7/springcore_run2_sensitivity.json').read_text()); e=json.loads((ROOT/'analysis/v14_7/worked_example_v14_6.json').read_text()); seg=json.loads((ROOT/'analysis/v14_7/test_segment_v14_6.json').read_text())
t=src.read_text().replace('Version 14.6','Version 14.7')
t=t.replace('Historical subjects retain the identities and collection behavior of their original frozen maps; later structured-inventory behavior is not retroactively attributed to them.','All eight maps were produced by the same collector revision (Section 3.2).')
t=t.replace('### 3.2 Adopted selector policy and historical map inputs','### 3.2 Adopted selector policy and map inputs')
old='The provenance table shipped with this manuscript separates the STP collection identity from the evaluator identity and leaves unsupported historical fields as `UNKNOWN`. In particular, the post-study production-output ownership fix is not claimed as the implementation that generated the eight main maps. Table 2 summarizes collection identities; full revisions, digest values, status labels, and evidence paths are in `RAD1_v14_REVIEW_READY_PROVENANCE.csv` and `PROVENANCE_EVIDENCE.md`.'
new='The provenance table shipped with this manuscript separates collector, subject, environment, JaCoCo-version, and map-digest evidence. Table 2 summarizes collection identities; full revisions, digest values, status labels, and evidence paths are in `analysis/v14_7/provenance_v14_6.csv`.'
assert old in t; t=t.replace(old,new)
t=t.replace('One hundred other tests carry the name-level `canConvert` key','One hundred tests carry the name-level `canConvert` key')
t=t.replace('One hundred other tests carry the name-level key `GenericConversionService#canConvert`','One hundred tests carry the name-level key `GenericConversionService#canConvert`')
t=t.replace('100 name-level hits selected; the reported killer is absent','100 name-level hits and 14 empty-footprint entries selected; the reported killer is absent')
t=t.replace('The exceptional-contract test is therefore absent from the selected set.','The base selection contains 114 tests (100 name-level hits and 14 empty-footprint entries), but the exceptional-contract test is absent.')
marker='No additional causal mechanism is claimed.\n\n## 7. Discussion'
addition=('No additional causal mechanism is claimed.\n\n### 6.5 Run-to-run variation\n\n'
 'Only spring-core was collected twice. Between two identically configured collections, 262 of 3,638 logical-test identities have different class or method footprints. Six of 454 base selected sets differ, as do six constructor-rule sets and sixty class-baseline sets. Base, constructor, and class inclusiveness remain 443/454, 447/454, and 454/454, respectively; the eleven base residual mutation IDs and their footprint types are unchanged. Mean selected changes from 94.61 to 94.59 for the base policy, from 98.92 to 98.89 for the constructor rule, and from 543.18 to 542.92 for the class baseline.\n\n## 7. Discussion')
assert marker in t; t=t.replace(marker,addition)
old='However, no canonical map of the eight subjects contains a production class whose package has a test segment, and no such class exists in the qualified production source scope of the seven subjects whose recorded source revision was available (spring-core\'s revision was not retained).'
new='No adopted map contains a production class whose package has a literal `test` segment, and inspection at the recorded revisions finds no such class in any of the eight qualified production source scopes, including `spring-core/src/main/java/`.'
assert old in t; t=t.replace(old,new)
t=t.replace('Matching retained XML session identities to map keys excludes losses during conversion but not tests that produced no report.','Recollection recovered the tests without production coverage that the earlier collector had not recorded (Section 3.2).')
old='Between two identically configured spring-core collections with that revision, 262 logical-test identities had different class or method footprints; this measures run-to-run nondeterminism as a threat for any single collected map.'
new='Between two identically configured spring-core collections with that revision, 262 logical-test identities had different class or method footprints and six base selected sets changed, but inclusiveness and the eleven residual misses did not; this measures run-to-run nondeterminism as a threat for any single collected map.'
assert old in t; t=t.replace(old,new)
abstract='These findings distinguish coverage loss from policy-dependent missed selection; they establish neither formal RTS safety nor runtime savings.'
t=t.replace(abstract,'Repeating spring-core collection changed 262 test footprints and six base selected sets, but not inclusiveness or residual misses. '+abstract)
dst.write_text(t)
