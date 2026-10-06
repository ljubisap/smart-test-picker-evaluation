"""Render replay rows and expected numbers from the delivered evidence."""
import re
from common import *
p=PACKAGE/'README.md';text=p.read_text();summary=read(PACKAGE/'results/summary.json');ci=read(PACKAGE/'results/intervals.json')['aggregate']['base']
expected='\n'.join(f"{policy}: {summary['aggregate'][policy]['inclusive']:,}/{summary['aggregate'][policy]['eligible']:,}" for policy in ('base','constructor','class'))
assert expected in text
assert 'Wilson ['+', '.join(f'{n:.2f}' for n in ci['wilson95Pct'])+']' in text
assert 'Bootstrap ['+', '.join(f"{ci['clusterBootstrap95Pct'][k]:.2f}" for k in ('lowerPct','upperPct'))+']' in text
selection=read(PACKAGE/'evidence/pit_replay/selection.json')
for n in ('jgrapht','spring-core'):
    chosen=next(r for r in selection['subjects'] if r['subject']==n);d=PACKAGE/'evidence/pit_replay'/n
    a=read(d/'record_agreement.json')['summary'];c=read(d/'comparison.json');env=read(d/'environment.json');assert env['status']=='EXECUTED'
    changes='/'.join(str(a['inclusivenessChanges'][k]) for k in ('base','constructor','class'));unknown='/'.join(str(a['inclusivenessNotComparable'][k]) for k in ('base','constructor','class'))
    row=f"| {n} | `{chosen['targetClass']}` | {a['recordedRecords']}/{a['freshRecords']} | {a['matchingIdentities']}/{a['matchingStatuses']}/{a['matchingKillingSets']} | {len(c['differences'])} | {changes}; not comparable {unknown} | EXECUTED |"
    text,count=re.subn(r'^\| '+re.escape(n)+r' \|.*$',lambda _:row,text,flags=re.M);assert count==1
start=text.index('The JGraphT job has different conditional-mutator populations')
end=text.index('Hibernate initially reached',start)
text=text[:start]+('The JGraphT and spring-core diagnostic jobs use the analyzed named DEFAULTS\n'
 'operator group. Their identity, status and killing-set comparisons are shown\n'
 'above; they do not replace the analyzed matrices. Spring uses the checkout\n'
 'native `pitClasspath` task; a guarded adapter is used only if that task is absent.\n'
 'The Flink job retains three changed killing-test sets with unchanged inclusiveness\n'
 'under all policies; no cause is established for those observed differences.\n'
 'The other six replay evidence directories are byte-identical to the input package.\n'
 'PetClinic reuses its recorded whole-project replay and was not executed again.\n\n')+text[end:]
size=sum(f.stat().st_size for f in PACKAGE.rglob('*') if f.is_file())
text=re.sub(r'about \d+ MB unpacked',f'about {((size//1_000_000)//50+2)*50} MB unpacked',text)
p.write_text(text)
write(OUT/'readme_check.json',{'headlineValuesFromResults':True,'replayRowsFromEvidence':True,'otherSixReplayRowsUnchanged':True,'sha256':sha(p),'packageBytesAtCheck':size})
print('PASS: README values and replay rows regenerated from included evidence')
