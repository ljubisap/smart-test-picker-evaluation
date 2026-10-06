"""Run all existing repository checks anew; write only the C logs."""
import importlib.util,json,subprocess,time,sys
from environment import B,OUT
spec=importlib.util.spec_from_file_location('unchanged_checks',B/'scripts/check_current.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.OUT=OUT/'verification/current'
if __name__=='__main__':
    ok=True if '--b-only' in sys.argv else module.main();cmd=['python3','iterations/pit-unify/verify_unified.py','--verify'];log=module.OUT/'B-unified.log';start=time.monotonic()
    with log.open('w') as stream:r=subprocess.run(cmd,cwd=module.ROOT,stdout=stream,stderr=subprocess.STDOUT,env={**module.os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    path=module.OUT/'results.json';data=json.loads(path.read_text());data['commands'].append({'name':'B-unified','command':cmd,'exitCode':r.returncode,'lastNonEmptyLine':[x for x in log.read_text().splitlines() if x.strip()][-1],'elapsedSeconds':time.monotonic()-start,'log':str(log.relative_to(module.ROOT))});data['allPassed']=all(x['exitCode']==0 for x in data['commands']);path.write_text(json.dumps(data,indent=2)+'\n')
    raise SystemExit(0 if ok and r.returncode==0 else 1)
