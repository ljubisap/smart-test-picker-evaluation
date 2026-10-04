#!/usr/bin/env python3
"""Apply corrected identity/addition gates and quantify spring-core run-to-run variation."""
import gzip, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
def load(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt') as f:return json.load(f)['testMappings']
def norm(k):return re.sub(r'_[0-9a-f]{7}$','',k)
def fp(v):return set(v.get('classes') or []),set(v.get('methods') or [])
specs={
'commons-lang':('commons-lang/results/test-coverage-map.json.gz','recollection_2e0954/commons-lang/test-coverage-map.json'),
'jgrapht':('jgrapht/results/test-coverage-map.json.gz','recollection_2e0954/jgrapht/test-coverage-map.json'),
'spring-core':('spring-core/results/test-coverage-map.json','recollection_2e0954/spring-core/test-coverage-map.json'),
'petclinic':('petclinic/results/test-coverage-map.json','recollection_2e0954/petclinic/test-coverage-map.json')}
gates={}
for name,(oldp,newp) in specs.items():
 old,new=load(ROOT/oldp),load(ROOT/newp); on={norm(k) for k in old}; nn={norm(k) for k in new}
 removed=sorted(on-nn); added_norm=sorted(nn-on)
 added_keys=sorted(k for k in new if norm(k) in set(added_norm))
 added=[{'key':k,'normalized':norm(k),'classes':new[k].get('classes') or [],'methods':new[k].get('methods') or [],'empty':not any(fp(new[k]))} for k in added_keys]
 gates[name]={'frozenIdentities':len(old),'recollectedIdentities':len(new),'gIdPass':not removed,'removedNormalizedIdentities':removed,'gAddPass':all(x['empty'] for x in added),'addedIdentities':added,'pass':not removed and all(x['empty'] for x in added)}
(OUT/'gate_results_v14_6.json').write_text(json.dumps({'subjects':gates,'allPass':all(x['pass'] for x in gates.values())},indent=2)+'\n')

frozen=load(ROOT/specs['spring-core'][0]); run1=load(ROOT/specs['spring-core'][1]); run2=load(ROOT/'recollection_2e0954/spring-core/test-coverage-map-run2.json')
def difference(a,b):
 rows=[]
 for k in sorted(set(a)|set(b)):
  ac,am=fp(a.get(k,{}));bc,bm=fp(b.get(k,{}))
  if k not in a or k not in b or ac!=bc or am!=bm:
   rows.append({'identity':k,'run1Present':k in a,'run2Present':k in b,'addedClasses':sorted(bc-ac),'removedClasses':sorted(ac-bc),'addedMethods':sorted(bm-am),'removedMethods':sorted(am-bm)})
 return rows
rtr=difference(run1,run2)
(OUT/'spring-core/run_to_run.json').write_text(json.dumps({'run1Identities':len(run1),'run2Identities':len(run2),'differingIdentityCount':len(rtr),'differences':rtr},indent=2)+'\n')
run_diff_keys={x['identity'] for x in rtr}; classes={'added_empty_identity':[],'run_to_run_nondeterministic':[],'stable_footprint_difference':[]}
for row in difference(frozen,run1):
 k=row['identity']
 if k not in frozen and k in run1 and not any(fp(run1[k])): cat='added_empty_identity'
 elif k in run_diff_keys: cat='run_to_run_nondeterministic'
 else: cat='stable_footprint_difference'
 row['classification']=cat;classes[cat].append(row)
payload={'counts':{k:len(v) for k,v in classes.items()},'classes':classes,'runToRunDifferingIdentityCount':len(rtr)}
(OUT/'spring-core/difference_classes.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'gates':{k:v['pass'] for k,v in gates.items()},'added':{k:len(v['addedIdentities']) for k,v in gates.items()},'springRunToRun':len(rtr),'springClasses':payload['counts']},indent=2))
