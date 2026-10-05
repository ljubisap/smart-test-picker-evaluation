"""Read-only comparison of current and iteration evidence (no identity rewriting)."""
import collections,hashlib,json,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import derive
ROOT=derive.ROOT;ITER=derive.ITER
read=derive.read;write=derive.write
def semantic(row):
 # A comparison key only. Never replaces the evaluator's mutation ID.
 return (row['project'],row['mutatedClass'],row['mutatedMethod'],row['line'],row['mutator'].rsplit('.',1)[-1],row['mutationId'].split('|')[3])
def first_example(d):return d['eligibleExamples'][0] if d.get('eligibleExamples') else None
def generate():
 old=read(ROOT/'results/v14_6-per-record-outcomes.json');new=read(ITER/'results/per_record_outcomes.json.gz')
 osum=read(ROOT/'results/v14_6-summary-tables.json');nsum=read(ITER/'results/summary_tables.json');inv=read(ITER/'results/matrix_inventory.json')
 projects={};errors=[];oldinv={}
 for p in read(ROOT/'analysis/projects_v14_6.json')['projects']:
  n=p['name'];oldinv[n]=derive.matrix_inventory(p)[0]
  before=[r for r in old['records'] if r['project']==n];after=[r for r in new['records'] if r['project']==n]
  def concise(rows,spec,i):return {'mutatorCounts':i['mutatorCounts'],'pitMutations':i['mutations'],'rawKilled':i['killed'],'eligible':len(rows),'inclusive':sum(r['base']['inclusive'] for r in rows),'misses':sum(not r['base']['inclusive'] for r in rows),'policies':spec.get('policies'),'randomEqualBudget':spec.get('randomEqualBudget')}
  projects[n]={'current':concise(before,osum['projects'][n],oldinv[n]),'unified':concise(after,nsum['projects'][n],inv[n])}
  if n not in ('jgrapht','spring-core'):
   b={r['mutationId']:r for r in before};a={r['mutationId']:r for r in after};differences=[]
   if set(a)!=set(b):differences.append('mutation ID sets differ')
   for mid in set(a)&set(b):
    if a[mid]['killingTests']!=b[mid]['killingTests']:differences.append(mid+': killing identities differ')
    for policy in ('base','constructor','class','legacy'):
     if a[mid][policy]['inclusive']!=b[mid][policy]['inclusive'] or new['selectedSets'][a[mid][policy]['selectedSetId']]!=old['selectedSets'][b[mid][policy]['selectedSetId']]:differences.append(mid+': '+policy+' differs')
   if projects[n]['current']!=projects[n]['unified']:differences.append('metrics differ')
   projects[n]['unchangedSubjectCheck']={'pass':not differences,'differences':differences}
   errors.extend(n+': '+x for x in differences)
 oldmiss=[r for r in old['records'] if not r['base']['inclusive']];newmiss=[r for r in new['records'] if not r['base']['inclusive']]
 oi={r['mutationId']:r for r in oldmiss};ni={r['mutationId']:r for r in newmiss};groups_old=collections.defaultdict(list);groups_new=collections.defaultdict(list)
 for r in oldmiss:groups_old[semantic(r)].append(r)
 for r in newmiss:groups_new[semantic(r)].append(r)
 correspondences=[]
 for key in sorted(set(groups_old)|set(groups_new)):
  b=groups_old.get(key,[]);a=groups_new.get(key,[])
  correspondences.append({'semanticComparisonKey':key,'currentIds':[r['mutationId'] for r in b],'unifiedIds':[r['mutationId'] for r in a],'status':'ONE_TO_ONE_SEMANTIC_CORRESPONDENCE' if len(a)==len(b)==1 else 'CURRENT_ONLY' if not a else 'UNIFIED_ONLY' if not b else 'AMBIGUOUS','warning':'Class/method/descriptor/line/operator correspondence is not exact bytecode identity or causal proof.'})
 files=[('confidenceIntervals','results/v14_6-confidence-intervals.json','confidence_intervals.json'),('mitigation','results/v14_6-mitigation-comparison.json','mitigation_comparison.json'),('taxonomy','results/v14_6-residual-taxonomy.json','residual_taxonomy.json'),('succeedingTests','analysis/v15/succeeding_tests_check.json','succeeding_tests_check.json'),('failedKillerImpact','analysis/v14_9/failed_killer_impact.json','failed_killer_impact.json'),('run2Sensitivity','analysis/v14_7/springcore_run2_sensitivity.json','springcore_run2_sensitivity.json'),('workedExample','analysis/v14_7/worked_example_v14_6.json','worked_example.json')]
 extras={label:{'currentSource':oldpath,'unifiedSource':'iterations/pit-unify/results/'+newpath,'current':read(ROOT/oldpath),'unified':read(ITER/'results'/newpath)} for label,oldpath,newpath in files}
 result={'sourceBaselineCommit':read(ITER/'preflight.json')['head'],'projects':projects,'aggregate':{'current':osum['aggregate'],'unified':nsum['aggregate']},'unchangedSixSubjectsErrors':errors,
  'residuals':{'exactIdPersisting':sorted(set(oi)&set(ni)),'exactIdDisappeared':sorted(set(oi)-set(ni)),'exactIdNew':sorted(set(ni)-set(oi)),'semanticCorrespondence':correspondences},'details':extras,
  'meaningChanges':[
   'The statement that no PIT campaign was rerun no longer describes this iteration: JGraphT and spring-core were replayed at the recorded revisions.',
   'The two replacement matrices use observed PIT 1.17.4 DEFAULTS rather than the negate-conditional operator found in their stored matrices; the other six matrices are unchanged.',
   'NegateConditionals is not sufficient evidence of an older PIT version: original JGraphT logs already report pitest-maven 1.17.4, and the PIT 1.17.4 CLI implicit default differs from explicit --mutators DEFAULTS. Spring required that explicit named-group adapter. A manuscript must describe operator/configuration unification, not an established version-only cause.',
   'Historical evaluator/model agreement and historical plugin-contract statements remain historical observations, not validation of the replacement matrices.',
   'Residual causal claims must follow failure_annotations_unified.json; an UNDETERMINED annotation cannot be described as a proven early-exception mechanism.',
   'Method-name counts, case-weighted means, intervals, repeat-collection sensitivity and succeedingTests witnesses describe the new eligible records and must be updated together.'
   ,'The CPU control ActiveProcessorCount=1 changes availableProcessors(), which JGraphT TransitNodeRoutingPrecomputationTest uses to size its executor. Consequently this iteration is not established as a PIT-version-only causal experiment; see BLOCKERS.md and results/status_comparison.json.gz.'
   ,'CPU exposure and thread settings should be reported as test-execution conditions, not only speed controls. Distinguish JVM-visible processor count, PIT workers, and subject executor parallelism from OS CPU utilization limits. The observed source mechanism is not a controlled attribution of every changed PIT status.'
  ]}
 write(ITER/'comparison.json',result)
 lines=['# Unified PIT comparison','','This is a separate iteration; current results and manuscript are unchanged. Mutation IDs are not normalized across XML paths. Exact-ID and semantic correspondence are reported separately.','','| Subject | Current mutations / eligible / inclusive / misses | Unified mutations / eligible / inclusive / misses | Six-subject invariance |','|---|---|---|---|']
 for n,d in projects.items():
  fmt=lambda v:' / '.join(str(v[k]) for k in ('pitMutations','eligible','inclusive','misses'))
  lines.append('| '+n+' | '+fmt(d['current'])+' | '+fmt(d['unified'])+' | '+('PASS' if d.get('unchangedSubjectCheck',{}).get('pass') else 'Replacement matrix')+' |')
 lines+=['','Full operator distributions, policies, intervals, random baselines, residual correspondence, repeat-collection, failed-killer and succeedingTests evidence are in `comparison.json`. Every changed claim is listed in `manuscript_comparison.json` / `MANUSCRIPT_COMPARISON.md`.','','## Meaning changes','']+['- '+s for s in result['meaningChanges']]
 (ITER/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
 return result
if __name__=='__main__':generate()
