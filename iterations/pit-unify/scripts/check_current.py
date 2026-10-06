"""Run unchanged current verification commands, writing logs only in this iteration."""
import importlib.util,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'iterations/pit-unify/verification/current'
spec=importlib.util.spec_from_file_location('current_checks',ROOT/'analysis/v15/run_verifications.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for name,command in module.COMMANDS:
  started=time.monotonic();log=OUT/(name+'.log');print('START',name,flush=True)
  with log.open('w') as stream:r=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  lines=[s for s in log.read_text().splitlines() if s.strip()];rows.append({'name':name,'command':command,'exitCode':r.returncode,'lastNonEmptyLine':lines[-1] if lines else '', 'elapsedSeconds':time.monotonic()-started,'log':str(log.relative_to(ROOT))})
  (OUT/'results.json').write_text(json.dumps({'allPassed':all(r['exitCode']==0 for r in rows),'commands':rows},indent=2)+'\n');print(rows[-1],flush=True)
 return all(r['exitCode']==0 for r in rows)
if __name__=='__main__':raise SystemExit(0 if main() else 1)
