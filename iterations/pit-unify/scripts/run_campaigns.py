"""Execute unchanged documented runners; keep every subprocess log and attempt."""
import datetime,importlib.util,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'iterations/pit-unify'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
JDK=Path('/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home')
ENV={**os.environ,'JAVA_HOME':str(JDK),'PATH':str(JDK/'bin')+':/Users/D061177/Programs/apache-maven-3.9.15/bin:'+os.environ['PATH'],
     'JAVA_TOOL_OPTIONS':'-XX:ActiveProcessorCount=1','MAVEN_OPTS':'-XX:ActiveProcessorCount=1 -Xmx2g',
     'PYTHONDONTWRITEBYTECODE':'1','GRADLE_OPTS':'-Dorg.gradle.workers.max=1 -Dorg.gradle.daemon=false'}
os.environ.update(ENV)
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    pre=json.loads((OUT/'preflight.json').read_text());results=[]
    native_run=subprocess.run
    for name in ('jgrapht','spring-core'):
        directory=OUT/'pit'/name;directory.mkdir(parents=True,exist_ok=True)
        checkout=Path(pre['subjects'][name]['checkout']);calls=[]
        if (directory/'campaign.json').exists():raise RuntimeError('Campaign already attempted: '+name)
        logdir=directory/'commands';logdir.mkdir(exist_ok=True)
        def logged_run(cmd,*a,**kw):
            index=len(calls)+1;started=time.monotonic();start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
            row={'command':list(map(str,cmd)) if not isinstance(cmd,str) else cmd,'cwd':str(kw.get('cwd',checkout)),
                 'startedUtc':start_utc,'timeout':kw.get('timeout'),'logPrefix':str((logdir/f'{index:03}').relative_to(ROOT))}
            calls.append(row)
            try:
                r=native_run(cmd,*a,**kw)
                row['exitCode']=r.returncode
                for stream in ('stdout','stderr'):
                    data=getattr(r,stream,None)
                    if data is not None:(logdir/f'{index:03}.{stream}.log').write_bytes(data if isinstance(data,bytes) else data.encode())
                return r
            except subprocess.TimeoutExpired as exc:
                row['status']='TIMEOUT'
                for stream in ('stdout','stderr'):
                    data=getattr(exc,stream,None)
                    if data is not None:(logdir/f'{index:03}.{stream}.log').write_bytes(data if isinstance(data,bytes) else data.encode())
                raise
            finally:
                row['elapsedSeconds']=time.monotonic()-started;dump(directory/'commands.json',calls)
        subprocess.run=logged_run
        spec=importlib.util.spec_from_file_location('documented_'+name,ROOT/name/'scripts/02_run_pit.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        start=time.monotonic();status=0;error=None
        print('START',name,flush=True)
        try:
            if name=='spring-core':
                # Compile only: no Gradle Test task and no new coverage collection.
                with (directory/'build.log').open('w') as stream:
                    r=subprocess.run(['./gradlew','--no-daemon','--max-workers=1',':spring-core:testClasses',':spring-core:pitClasspath'],cwd=checkout,stdout=stream,stderr=subprocess.STDOUT)
                if r.returncode:raise RuntimeError('Documented Spring compile/classpath prerequisite failed; see build.log')
            sys.argv=[str(ROOT/name/'scripts/02_run_pit.py'),'--project-dir',str(checkout),'--results-dir',str(directory)]
            module.main()
        except SystemExit as exc:status=exc.code or 0;error=str(exc)
        except Exception as exc:status=1;error=repr(exc)
        finally:subprocess.run=native_run
        elapsed=time.monotonic()-start
        diff=subprocess.check_output(['git','-C',str(checkout),'diff'],text=True)
        (directory/'checkout-build.diff').write_text(diff)
        record={'subject':name,'sourceRevision':pre['subjects'][name]['revision'],'checkout':str(checkout),
                'originalRunner':str((ROOT/name/'scripts/02_run_pit.py').relative_to(ROOT)),'runnerModified':False,
                'exitCode':status,'error':error,'elapsedSeconds':elapsed,'commands':calls,
                'cpuControl':'One visible CPU per JVM; documented four PIT threads unchanged; sequential subjects.',
                'retryPolicy':'Up to two retries only for evidenced infrastructure failures; no scope/status-driven retries.'}
        dump(directory/'campaign.json',record);results.append(record)
        print('DONE',name,status,elapsed,flush=True)
    dump(OUT/'campaigns.json',results)
if __name__=='__main__':main()
