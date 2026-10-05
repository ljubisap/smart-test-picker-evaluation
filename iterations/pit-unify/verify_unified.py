#!/usr/bin/env python3
"""Recompute the separate iteration; never rewrite current or unified results."""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'scripts'));sys.dont_write_bytecode=True
import derive
def read(p):return derive.read(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 failures=[];baseline=read(HERE/'baseline_hashes.json')
 for path,digest in baseline.items():
  p=ROOT/path
  if not p.exists() or sha(p)!=digest:failures.append('Existing input changed: '+path)
 old=read(ROOT/'analysis/projects_v14_6.json');new=read(HERE/'projects_unified.json')
 for before,after in zip(old['projects'],new['projects']):
  expected={**before}
  if before['name'] in ('jgrapht','spring-core'):expected['pitFiles']=['iterations/pit-unify/pit/'+before['name']+'/per-class/*/mutations.xml.gz']
  if expected!=after:failures.append('Unexpected manifest change: '+before['name'])
 with tempfile.TemporaryDirectory(prefix='verify-',dir=HERE) as tmp:
  outputs=derive.generate(Path(tmp))
  for name in outputs:
   if read(Path(tmp)/name)!=read(HERE/'results'/name):failures.append('Re-derivation mismatch: '+name)
  outcome=read(Path(tmp)/'per_record_outcomes.json.gz');summary=outputs['summary_tables.json']
  if summary['status']!='DERIVED':failures.append('Incomplete or unresolved inputs')
  for n in ('jgrapht','spring-core'):
   counts=outputs['matrix_inventory.json'][n]['mutatorCounts']
   if any('NegateConditionalsMutator' in k for k in counts):failures.append(n+': old conditional operator remains')
   if not any('RemoveConditionalMutator_' in k for k in counts):failures.append(n+': no replacement conditional operator found')
  oldout=read(ROOT/'results/v14_6-per-record-outcomes.json');oldrows={r['mutationId']:r for r in oldout['records'] if r['project'] not in ('jgrapht','spring-core')};newrows={r['mutationId']:r for r in outcome['records'] if r['project'] not in ('jgrapht','spring-core')}
  if set(oldrows)!=set(newrows):failures.append('Unchanged six subjects: IDs differ')
  for mid in oldrows.keys()&newrows.keys():
   a=oldrows[mid];b=newrows[mid]
   if a['killingTests']!=b['killingTests']:failures.append('Unchanged killing tests: '+mid)
   for p in derive.POLICIES:
    if a[p]['inclusive']!=b[p]['inclusive'] or oldout['selectedSets'][a[p]['selectedSetId']]!=outcome['selectedSets'][b[p]['selectedSetId']]:failures.append('Unchanged selection: '+mid+' '+p)
  java=read(HERE/'results/java_comparison.json');loader=read(HERE/'results/loader_content_equality.json');raw=read(HERE/'java/output.json')
  cases={(r['project'],r['changedClass'],r['changedMethod']):r for r in java['cases']};groups={}
  for r in outcome['records']:groups.setdefault((r['project'],r['mutatedClass'],r['mutatedMethod']),[]).append(r)
  if set(cases)!=set(groups):failures.append('Java inputs do not cover exactly the unique cases')
  actual={r['caseId']:r for r in raw['cases']}
  for key,records in groups.items():
   if key not in cases:continue
   c=cases[key];j=actual[c['caseId']];wanted=outcome['selectedSets'][records[0]['base']['selectedSetId']]
   if j['mode']!='SELECTED' or sorted(j['selectedTests'])!=wanted or c['pythonSelectedTests']!=wanted or c['javaSelectedTests']!=wanted or c['occurrences']!=len(records):failures.append('Java full-set mismatch: '+repr(key))
  if java['uniqueInvocations']!=len(cases) or java['weightedOccurrences']!=len(outcome['records']) or java['mismatches'] or java['nonSelectedModes']:failures.append('Java summary mismatch')
  if loader['totalDifferentEntries'] or loader['totalRawU']!=loader['totalLoadedU']:failures.append('Loader content mismatch')
  for m in read(HERE/'java/cases.json')['maps']:
   project=next(p for p in new['projects'] if p['name']==m['project'])
   if m['mapSha256']!=sha(ROOT/project['coverageMap']):failures.append('Java map digest mismatch: '+m['project'])
  table=read(HERE/'results/table_i_counts.json')
  for n,t in table.items():
   rows=[r for r in outcome['records'] if r['project']==n]
   sample=read(ROOT/n/'config/sample_classes.json');target_count=len(sample['classes'])
   if n=='petclinic':
    import re
    target_count=int(re.search(r'\*\*(\d+) classes\*\* received mutations',(ROOT/'petclinic/docs/METHODOLOGY.md').read_text()).group(1))
   if t['targetedClasses']!=target_count or t['eligibleKilled']!=len(rows) or t['killedContributingClasses']!=len({r['mutatedClass'] for r in rows}) or t['pitMutations']!=outputs['matrix_inventory.json'][n]['mutations'] or t['logicalTests']!=summary['projects'][n]['logicalTests']:failures.append('Table I mismatch: '+n)
 for f in failures:print('FAIL:',f)
 if failures:return 1
 print('VERIFY PASSED: unified raw-input re-derivation, all policies/statistics/diagnostics, Java full sets, unchanged six subjects and original-file hashes')
 return 0
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true',required=True);parser.parse_args();raise SystemExit(verify())
