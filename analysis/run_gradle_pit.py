#!/usr/bin/env python3
"""Run frozen per-class PIT jobs for a Gradle subject, sequentially and CPU-bounded."""

from __future__ import annotations

import argparse, json, os, shutil, subprocess, time
import xml.etree.ElementTree as ET
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True); p.add_argument('--task',required=True)
p.add_argument('--init-script',type=Path,required=True); p.add_argument('--config',type=Path,required=True)
p.add_argument('--results',type=Path,required=True); p.add_argument('--gradle-home',type=Path,required=True)
p.add_argument('--timeout',type=int,default=1800); p.add_argument('--class',dest='single'); p.add_argument('--resume',action='store_true'); p.add_argument('--cpus',type=int,default=3)
p.add_argument('--gradle-arg',action='append',default=[],help='additional immutable Gradle argument, repeatable')
p.add_argument('--report-module-dir',help='module directory when it differs from the Gradle project name')
a=p.parse_args(); cfg=json.loads(a.config.read_text()); items=[x for x in cfg['classes'] if not a.single or x['fqn']==a.single]
a.results.mkdir(parents=True,exist_ok=True); records=[]
for i,item in enumerate(items,1):
    out=a.results/'per-class'/item['fqn']
    if a.resume and (out/'mutations.xml').exists():
        mutations=ET.parse(out/'mutations.xml').getroot().findall('mutation')
        records.append({'fqn':item['fqn'],'targetTests':item['targetTests'],'status':'OK','reason':'reused validated per-class output','mutations':len(mutations),'elapsedSeconds':0})
        print(f"[{i}/{len(items)}] {item['fqn']}: REUSED ({len(mutations)})",flush=True); continue
    shutil.rmtree(out,ignore_errors=True); out.mkdir(parents=True)
    module_dir=a.report_module_dir or a.task.split(':')[1]
    report_root=a.root / module_dir / 'build/reports/pitest'
    shutil.rmtree(report_root,ignore_errors=True)
    cmd=['./gradlew','--no-daemon',f'--max-workers={a.cpus}','--console=plain','-I',str(a.init_script.resolve()),a.task,
         f"-PpitestTargetClass={item['fqn']}",f"-PpitestTargetTests={item['targetTests']}",*a.gradle_arg]
    env={**os.environ,'GRADLE_USER_HOME':str(a.gradle_home),'JAVA_TOOL_OPTIONS':f'-XX:ActiveProcessorCount={a.cpus}', 'STP_EVAL_CPUS':str(a.cpus)}; started=time.time()
    try:
        run=subprocess.run(cmd,cwd=a.root,env=env,text=True,capture_output=True,timeout=a.timeout)
        (out/'stdout.log').write_text(run.stdout); (out/'stderr.log').write_text(run.stderr)
        candidates=list(report_root.glob('**/mutations.xml')); status='FAILED'; reason=f'exit {run.returncode}'; count=0
        if run.returncode==0 and len(candidates)==1:
            mutations=ET.parse(candidates[0]).getroot().findall('mutation'); wrong=[m for m in mutations if m.findtext('mutatedClass')!=item['fqn']]
            if wrong: reason=f'{len(wrong)} wrong-class mutations'
            else: shutil.copy2(candidates[0],out/'mutations.xml'); status='OK'; reason=None; count=len(mutations)
        elif run.returncode==0: reason=f'expected one mutations.xml, found {len(candidates)}'
    except subprocess.TimeoutExpired as exc:
        (out/'stdout.log').write_text(exc.stdout or ''); (out/'stderr.log').write_text(exc.stderr or '')
        status='TIMEOUT'; reason=f'{a.timeout}s'; count=0
    records.append({'fqn':item['fqn'],'targetTests':item['targetTests'],'status':status,'reason':reason,'mutations':count,'elapsedSeconds':round(time.time()-started,2)})
    print(f"[{i}/{len(items)}] {item['fqn']}: {status} ({count})",flush=True)
summary={'project':cfg['project'],'classes':records,'ok':sum(x['status']=='OK' for x in records),'failed':sum(x['status']=='FAILED' for x in records),'timeout':sum(x['status']=='TIMEOUT' for x in records),'totalMutations':sum(x['mutations'] for x in records)}
(a.results/'pit-run-summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
