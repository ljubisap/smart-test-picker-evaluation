"""Separate operator replacement from status changes in comparable records.

This correspondence never replaces evaluator mutation IDs. Ambiguities are kept.
"""
import collections
from derive import ROOT,ITER,read,write,matrix_inventory
def grouped(nodes):
 groups=collections.defaultdict(list)
 for (path,ordinal),n in nodes.items():
  key=tuple(n.findtext(f) or '' for f in ('mutatedClass','mutatedMethod','methodDescription','lineNumber','mutator','description'))
  groups[key].append({'sourceXml':path,'ordinal':ordinal,'status':n.get('status'),'rawKillingTests':sorted((n.findtext('killingTests') or n.findtext('killingTest') or '').split('|'))})
 return groups
def generate():
 old={p['name']:p for p in read(ROOT/'analysis/projects_v14_6.json')['projects']};new={p['name']:p for p in read(ITER/'projects_unified.json')['projects']};out={}
 for name in ('jgrapht','spring-core'):
  oi,on=matrix_inventory(old[name]);ni,nn=matrix_inventory(new[name]);a=grouped(on);b=grouped(nn);transitions=collections.Counter();pairs=[];unmatched=[]
  for key in sorted(set(a)|set(b)):
   before=a.get(key,[]);after=b.get(key,[])
   if len(before)==len(after)==1:
    x,y=before[0],after[0];transitions[x['status']+' -> '+y['status']]+=1
    pairs.append({'comparisonKey':key,'current':x,'unified':y,'statusChanged':x['status']!=y['status'],'rawKillingSetChanged':x['rawKillingTests']!=y['rawKillingTests']})
   else:unmatched.append({'comparisonKey':key,'current':before,'unified':after,'status':'CURRENT_ONLY' if not after else 'UNIFIED_ONLY' if not before else 'AMBIGUOUS_MULTIPLE'})
  def operators(nodes):
   groups=collections.defaultdict(collections.Counter)
   for n in nodes.values():groups[n.findtext('mutator')][n.get('status')]+=1
   return {k:dict(v) for k,v in sorted(groups.items())}
  out[name]={'currentStatusCounts':oi['statusCounts'],'unifiedStatusCounts':ni['statusCounts'],'currentOperatorStatusCounts':operators(on),'unifiedOperatorStatusCounts':operators(nn),'unambiguousComparableRecords':len(pairs),'commonRecordStatusTransitions':dict(transitions),'comparableRecords':pairs,'unmatchedOrAmbiguous':unmatched,'interpretation':'Correspondence includes class, method descriptor, line, exact operator and description; it is not proof of identical bytecode offsets. Changed conditional operators are not equated. Status and killing-set variability is not automatically attributed solely to the operator substitution.'}
 write(ITER/'results/status_comparison.json.gz',out)
 print({n:{'common':d['unambiguousComparableRecords'],'transitions':d['commonRecordStatusTransitions']} for n,d in out.items()})
 return out
if __name__=='__main__':generate()
