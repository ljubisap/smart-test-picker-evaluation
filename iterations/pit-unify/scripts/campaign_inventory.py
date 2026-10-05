"""Account for every sampled class, including failed and empty jobs."""
import collections,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from derive import ROOT,ITER,read,write,tree
def generate():
 out={}
 for n in ('jgrapht','spring-core'):
  directory=ITER/'pit'/n;commands=read(directory/'commands.json');sample=read(ROOT/n/'config/sample_classes.json');rows=[]
  earlier=ITER/'pit/spring-core-initial-interrupted/commands.json'
  initial=read(earlier) if n=='spring-core' and earlier.exists() else []
  implicit_path=ITER/'pit/spring-core-implicit-defaults/commands.json'
  implicit=read(implicit_path) if n=='spring-core' and implicit_path.exists() else []
  for spec in sample['classes']:
   fqn=spec['fqn'];p=directory/'per-class'/fqn/'mutations.xml.gz'
   jobs=[c for c in commands if any(fqn==a or a=='-DtargetClasses='+fqn for a in c['command'])]
   previous=[c for c in initial if any(fqn==a for a in c['command'])]
   row={'fqn':fqn,'targetTests':spec['targetTests'],'sourceConfiguration':n+'/config/sample_classes.json','attempts':jobs,'initialAttemptBeforeRuntimePrerequisites':previous,'matrix':str(p.relative_to(ROOT)) if p.exists() else None}
   row['rejectedImplicitDefaultsAttempt']=[c for c in implicit if any(fqn==a for a in c['command'])]
   if n=='spring-core' and (ITER/'pit/spring-core-initial-interrupted/per-class'/fqn).exists() and not previous:
    row['initialAttemptBeforeRuntimePrerequisites']=[{'status':'USER_INTERRUPTED','evidence':'iterations/pit-unify/campaigns.log','reason':'Active subprocess had not returned, so its logging wrapper did not persist a completed command record.'}]
   if p.exists():
    nodes=tree(p).findall('mutation');counts=collections.Counter(x.get('status') for x in nodes);ops=collections.Counter(x.findtext('mutator') for x in nodes)
    row.update(status='COMPLETE',mutations=len(nodes),killed=counts['KILLED'],statusCounts=dict(counts),mutatorCounts=dict(ops),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),containsNegateConditionals=any('NegateConditionalsMutator' in k for k in ops),containsRemoveConditionals=any('RemoveConditionalMutator_' in k for k in ops))
    row['conditionalCheck']='FAIL_NEGATE_REMAINS' if row['containsNegateConditionals'] else 'PASS_REMOVE_PRESENT' if row['containsRemoveConditionals'] else 'NO_CONDITIONAL_OPERATOR_IN_THIS_CLASS'
   else:
    logs='\n'.join(p.read_text(errors='replace') for p in (directory/'per-class'/fqn).glob('*.log'))
    row.update(status='TIMEOUT' if any(c.get('status')=='TIMEOUT' for c in jobs) else 'FAILED' if jobs else 'NOT_EXECUTED',mutations=None,killed=None)
    row['errorEvidence']=[line for line in logs.splitlines() if any(t in line for t in ('ERROR','Exception','did not pass','FAILURE','No mutations','timed out','could not','Could not','FAILED'))][-30:]
   rows.append(row)
  out[n]={'sampledClasses':len(rows),'completeClasses':sum(r['status']=='COMPLETE' for r in rows),'failedOrTimedOut':[r['fqn'] for r in rows if r['status']!='COMPLETE'],'classes':rows,'campaign':read(directory/'campaign.json')}
 jars={}
 for artifact,version in (('pitest','1.17.4'),('pitest-entry','1.17.4'),('pitest-command-line','1.17.4'),('pitest-maven','1.17.4'),('pitest-junit5-plugin','1.2.1')):
  p=Path.home()/'.m2/repository/org/pitest'/artifact/version/(artifact+'-'+version+'.jar')
  jars[artifact]={'version':version,'path':str(p),'present':p.is_file(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
 write(ITER/'pit_tool_artifacts.json',jars)
 write(ITER/'campaign_inventory.json',out);return out
if __name__=='__main__':generate()
