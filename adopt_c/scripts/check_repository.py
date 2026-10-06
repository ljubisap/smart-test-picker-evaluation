"""Two fresh passes, with historical whole-tree assertions scoped explicitly."""
import os,subprocess,time
from common import *
def main():
    rows=[];old=read(C/'verification/current/results.json')['commands']
    for cycle in (1,2):
        commands=[(r['name'],r['command'],ROOT) for r in old if r['name']!='B-unified']
        commands += [('v17',['python3','analysis/v17/verify_v17.py','--verify'],ROOT),('historical-B',['python3','iterations/pit-unify/verify_unified.py','--verify'],WORK/'historical-checks')]
        for name,cmd,cwd in commands:
            log=OUT/'verification'/f'pass-{cycle}-{name}.log';log.parent.mkdir(exist_ok=True);start=time.monotonic()
            with log.open('w') as f:r=subprocess.run(cmd,cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=f,stderr=subprocess.STDOUT)
            lines=[l for l in log.read_text().splitlines() if l.strip()]
            rows.append({'pass':cycle,'name':name,'command':cmd,'cwd':str(cwd),'exitCode':r.returncode,'elapsedSeconds':time.monotonic()-start,'lastLine':lines[-1] if lines else '', 'log':str(log.relative_to(ROOT))})
            write(OUT/'repository_checks.json',{'commands':rows,'completed':False,'allPassed':all(x['exitCode']==0 for x in rows)})
            print(cycle,name,r.returncode,flush=True)
    write(OUT/'repository_checks.json',{'commands':rows,'completed':True,'allPassed':all(x['exitCode']==0 for x in rows)})
if __name__=='__main__':main()
