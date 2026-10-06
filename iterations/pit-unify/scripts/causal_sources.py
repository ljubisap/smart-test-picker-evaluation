"""Retain line-numbered source/control-flow excerpts for every replacement-matrix miss.

This prepares evidence, not an automatic causal classification. Manual review is
stored separately in causal_review.json; unexplained records stay UNDETERMINED.
"""
import hashlib,json,re,subprocess
from pathlib import Path
from derive import ROOT,ITER,read,write
def excerpt(path,lo,hi,checkout):
 lines=path.read_text().splitlines();return {'path':str(path.relative_to(checkout)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'startLine':max(1,lo),'endLine':min(len(lines),hi),'lines':[{'line':i,'text':lines[i-1]} for i in range(max(1,lo),min(len(lines),hi)+1)]}
def main():
 pre=read(ITER/'preflight.json');rows=read(ITER/'results/residual_taxonomy.json')['residualMisses'];out=[];disassembly={}
 for n in ('jgrapht','spring-core'):
  checkout=Path(pre['subjects'][n]['checkout']);files=list(checkout.glob(('jgrapht-core' if n=='jgrapht' else 'spring-core')+'/src/**/*.java'))
  for r in rows:
   if r['project']!=n:continue
   cls=r['mutatedClass'].split('$')[0].rsplit('.',1)[-1];prod=[p for p in files if p.name==cls+'.java' and '/main/' in str(p)];test=[]
   for key in r['killingTests']:
    c,m=key.split('#',1);c=c.split('$')[0].rsplit('.',1)[-1];m=re.sub(r'_[a-f0-9]{7,8}$','',m)
    for p in files:
     if p.name!=c+'.java' or '/test/' not in str(p):continue
     lines=p.read_text().splitlines();matches=[i for i,t in enumerate(lines,1) if re.search(r'\b'+re.escape(m)+r'\s*\(',t)]
     test.extend({'coverageKey':key,**excerpt(p,i-6,i+22,checkout)} for i in matches)
   key=(n,r['mutatedClass'])
   if key not in disassembly:
    output=ITER/'causal-bytecode'/n/(r['mutatedClass']+'.txt');output.parent.mkdir(parents=True,exist_ok=True)
    classroot=checkout/('jgrapht-core/target/classes' if n=='jgrapht' else 'spring-core/build/classes/java/main')
    cmd=['/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home/bin/javap','-c','-l','-p','-classpath',str(classroot),r['mutatedClass']]
    done=subprocess.run(cmd,text=True,capture_output=True);output.write_text(done.stdout+done.stderr)
    clsfile=classroot/(r['mutatedClass'].replace('.','/')+'.class')
    disassembly[key]={'command':cmd,'exitCode':done.returncode,'output':str(output.relative_to(ROOT)),'classSha256':hashlib.sha256(clsfile.read_bytes()).hexdigest() if clsfile.exists() else None,'kind':'Pristine compiled bytecode, not a mutated or instrumented execution trace.'}
   out.append({'mutationId':r['mutationId'],'sourceRevision':pre['subjects'][n]['revision'],'production':[excerpt(p,r['line']-15,r['line']+22,checkout) for p in prod],'killingTestExcerpts':test,'footprintEvidence':r['killerFootprints'],'bytecode':disassembly[key],'causalInferenceNotAutomatic':True})
 write(ITER/'causal_source_evidence.json',out)
 helpers=[]
 for subject,path,lo,hi in [('jgrapht','jgrapht-core/src/main/java/org/jgrapht/alg/tour/HamiltonianCycleAlgorithmBase.java',117,151),('jgrapht','jgrapht-core/src/main/java/org/jgrapht/GraphTests.java',780,810),('spring-core','spring-core/src/main/java/org/springframework/util/Assert.java',160,196),('spring-core','spring-core/src/main/java/org/springframework/util/Assert.java',480,565),('spring-core','spring-core/src/main/java/org/springframework/util/backoff/ExponentialBackOff.java',205,222)]:
  checkout=Path(pre['subjects'][subject]['checkout']);helpers.append({'subject':subject,'sourceRevision':pre['subjects'][subject]['revision'],**excerpt(checkout/path,lo,hi,checkout)})
 write(ITER/'causal_guard_evidence.json',helpers)
 print('Source records:',len(out),'missing production:',sum(not r['production'] for r in out),'missing test:',sum(not r['killingTestExcerpts'] for r in out))
if __name__=='__main__':main()
