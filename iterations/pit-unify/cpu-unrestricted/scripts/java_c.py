"""Recheck all C selected sets; reuse only hash-identical previously executed inputs."""
import importlib.util,os,subprocess
from environment import ROOT,B,OUT,JDK,read,write,sha,effective_environment
def main():
    spec=importlib.util.spec_from_file_location('existing_java_replay',B/'scripts/java_replay.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.ITER=OUT;m.OUT=OUT/'java';m.prepare()
    current=read(m.OUT/'cases.json');old=read(B/'java/cases.json');prior=read(B/'java/output.json');runtime=read(B/'java/runtime.json')
    source=ROOT/runtime['harnessSource'];assert sha(source)==runtime['harnessSha256']
    for a in runtime['verifiedArtifacts']:assert sha(__import__('pathlib').Path(a['path']))==a['sha256']
    old_maps={x['project']:x for x in old['maps']};old_cases={c['caseId']:c for x in old['maps'] for c in x['cases']};old_results={c['caseId']:c for c in prior['cases']}
    reused=[];fresh=[];fresh_maps=[]
    for item in current['maps']:
        assert item['mapSha256']==sha(__import__('pathlib').Path(item['path']))
        todo=[]
        for c in item['cases']:
            p=old_cases.get(c['caseId'])
            if item['mapSha256']==old_maps[item['project']]['mapSha256'] and p and all(c[k]==p[k] for k in ('changedClass','changedMethod','pythonSelected')):
                reused.append(old_results[c['caseId']])
            else:todo.append(c);fresh.append(c)
        fresh_maps.append({**item,'cases':todo})
    write(m.OUT/'fresh-cases.json',{'maps':fresh_maps})
    classes=m.OUT/'classes';classes.mkdir(exist_ok=True)
    cp=os.pathsep.join(a['path'] for a in runtime['verifiedArtifacts'])
    commands=[[str(JDK/'bin/javac'),'-cp',cp,'-d',str(classes),str(source)],
              [str(JDK/'bin/java'),'-Xmx3g','-cp',str(classes)+os.pathsep+cp,'SelectorHarness',str(m.OUT/'fresh-cases.json'),str(m.OUT/'fresh-output.json')]]
    for i,cmd in enumerate(commands):
        with (m.OUT/f'fresh-command-{i}.log').open('w') as log:subprocess.run(cmd,env=effective_environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
    actual=read(m.OUT/'fresh-output.json')
    assert len(actual['cases'])==len(fresh)
    write(m.OUT/'output.json',{**actual,'cases':reused+actual['cases']})
    write(m.OUT/'runtime.json',{**runtime,'commands':commands,'reuse':{'source':'iterations/pit-unify/java/output.json','sourceSha256':sha(B/'java/output.json'),'sourceInputsSha256':sha(B/'java/cases.json'),'identicalInputsReused':len(reused),'additionalInvocations':len(fresh),'freshLoaderRuns':len(actual['loader']),'reason':'Identical map digests, class/method inputs, evaluator sets, selector runtime artifacts and harness. Occurrences recomputed from C matrices; all maps freshly loaded.'}})
    m.finalize()
if __name__=='__main__':main()
