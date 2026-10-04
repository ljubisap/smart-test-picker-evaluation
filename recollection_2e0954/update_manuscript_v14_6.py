#!/usr/bin/env python3
"""Synchronize the v14.6 Markdown manuscript with derived JSON results."""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MD=ROOT.parent/'rad1-v14-4/RAD1_v14_4.md'
s=json.loads((ROOT/'results/v14_6-summary-tables.json').read_text())
text=MD.read_text()
text=text.replace('Version 14.5','Version 14.6')
text=text.replace('mean selected fractions from 0.36% to 39.42%','mean selected fractions from 0.47% to 39.42%')
old='Collection and selection revisions are separate. The extension collector (2e0954\\...) retains successfully collected zero-production-coverage sessions as empty entries. The earlier collector (70b398...) retained reports containing only non-production coverage and skipped reports without any package. Applying the adopted selector to the older maps does not claim that 70b398... implemented the newer branch. The retained maps contain 34 structural empty entries: JGraphT 1, Flink 1, Spring Security 23, and Quarkus 9. The other four maps have none. An audit of the original subjects resolves all admitted PIT killing identities to map keys; resolution alone does not prove collection completeness.\n\nFor Commons Lang, JGraphT, spring-core, and PetClinic, the retained per-test JaCoCo XML session identities match the frozen map keys exactly: 4,692, 2,308, 3,624, and 52, respectively, with no difference in either direction. Hence the skip condition did not remove any retained report from these maps. The comparison cannot establish whether an executed test failed to produce a report before conversion.'
new='All eight analyzed maps are produced by collector 2e0954\\.... The four original subjects were recollected at their recorded source revisions. Their earlier 70b398... maps omitted tests without production coverage that the recollected maps retain as empty entries: Commons Lang 5, JGraphT 1, spring-core 14, and PetClinic 4. The analyzed maps contain 58 structural empty entries in total: Commons Lang 5, JGraphT 2, spring-core 14, PetClinic 4, Flink 1, Spring Security 23, Hibernate 0, and Quarkus 9. Every admitted PIT killing identity for the four recollected subjects resolves to a recollected-map key.'
assert old in text; text=text.replace(old,new)
start='The original Commons Lang, JGraphT, spring-core, and PetClinic artifacts retain weaker historical sample provenance.'
end='RQ4 remains descriptive; it is not a controlled estimate of project effects or evidence that an unchanged collector generalizes across both groups.'
i=text.index(start); j=text.index(end,i)+len(end)
text=text[:i]+('The original Commons Lang, JGraphT, spring-core, and PetClinic artifacts retain weaker historical sample provenance. The four extension subjects prospectively froze subject metadata, samples, and functional targetTests policies before result inspection. Project-specific PIT scopes can omit cross-scope killers. The original maps were collected with 70b398\\...; all four original subjects were recollected with 2e0954\\..., which also collected the extension maps. RQ4 remains descriptive across projects.')+text[j:]
text=text.replace('The two collector revisions also prevent attributing differences between the original and extension groups to project characteristics alone. ','')
text=text.replace('Collection revisions co-vary with project group even though one selection policy is adopted, and unsupported provenance fields remain explicit.','One collector revision produced all eight analyzed maps, and unsupported provenance fields remain explicit. Between two identically configured spring-core collections with that revision, 262 logical-test identities had different class or method footprints; this measures run-to-run nondeterminism as a threat for any single collected map.')
text=text.replace('Table 2. Historical collection provenance; not the selector-policy pin. The revised analysis adopts selector 2e0954\\... for every row.','Table 2. Collection provenance. Collector and selector use 2e0954\\... for every row.')
text=text.replace('`70b398...`','`2e0954...`')
text=text.replace('Java 21, Maven                       collector run evidence; JaCoCo declared','SapMachine 21, Maven 3.9.15          collector run evidence; JaCoCo declared',1)
text=text.replace('Java 21, Maven                       collector and JaCoCo declared','SapMachine 21, Maven 3.9.15          collector run evidence; JaCoCo declared',1)
text=text.replace('SapMachine 21, Gradle 8.14           collector and JaCoCo declared','SapMachine 21, Gradle 8.14.2         collector run evidence; JaCoCo declared',1)
text=text.replace('JDK unknown, Gradle                  collector and JaCoCo declared','SapMachine 21, Gradle 8.14.3         collector run evidence; JaCoCo declared',1)

# Table 1 logical populations.
for oldv,newv in [('4,692','4,697'),('2,308','2,309'),('3,624','3,638')]: text=text.replace(oldv,newv,1)
text=text.replace('Spring PetClinic                 52           17','Spring PetClinic                 56           17',1)

labels={'commons-lang':'Commons Lang','jgrapht':'JGraphT','spring-core':'`spring-core`','petclinic':'PetClinic','flink':'Flink','spring-security':'Spring Security','hibernate':'Hibernate','quarkus':'Quarkus'}
rows=[]
for name,d in s['projects'].items():
 p=d['policies']['base']; rows.append(f"| {labels[name]} | {p['eligible']:,} | {p['inclusive']:,} | {p['inclusivenessPct2dp']:.2f}% | {p['meanSelected2dp']:.2f} | {p['selectedFractionPct2dp']:.2f}% |")
table='| Project | Eligible KILLED | Inclusive | Inclusiveness | Mean selected | Selected fraction |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(rows)+"\n| **Micro aggregate** | 4,010 | 3,991 | 99.53% | — | — |"
text=re.sub(r'\| Project \| Eligible KILLED.*?\| \*\*Micro aggregate\*\*.*?\|',table,text,count=1,flags=re.S)
rows=[]
for name,d in s['projects'].items():
 cls=d['policies']['class']; rule=d['policies']['constructor']; rnd=d['randomEqualBudget']
 rows.append(f"| {labels[name]} | {rnd['analyticalPct2dp']:.2f}% | {cls['inclusivenessPct2dp']:.2f}% | {cls['meanSelected2dp']:.2f} | {rule['inclusivenessPct2dp']:.2f}% | {rule['meanSelected2dp']:.2f} |")
table='| Project | Random incl. | Class incl. | Class mean | Rule incl. | Rule mean |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(rows)
text=re.sub(r'\| Project \| Random incl\..*?\| Quarkus .*?\|',table,text,count=1,flags=re.S)
text=text.replace('Mean selection grows from 80.63 to 529.18 for base versus class in spring-core','Mean selection grows from 94.61 to 543.18 for base versus class in spring-core')
old='Relative to the historical edge-only evaluator, every selected set grows by one test in JGraphT, one in Flink, twenty-three in Spring Security, and nine in Quarkus.'
new='Relative to edge-only evaluation of the analyzed maps, every selected set grows by five tests in Commons Lang, two in JGraphT, fourteen in spring-core, four in PetClinic, one in Flink, twenty-three in Spring Security, and nine in Quarkus.'
assert old in text; text=text.replace(old,new)
text=text.replace('Results for the 2e0954\\... selection policy on the eight preserved maps.','Results for the 2e0954\\... selection policy on the eight maps collected with that revision.')
MD.write_text(text)
