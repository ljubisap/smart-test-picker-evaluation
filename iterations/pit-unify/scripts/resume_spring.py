"""Resume after the explicit user pause; materialize missing runtime JARs, no Test tasks."""
import datetime, hashlib, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path
from run_campaigns import ROOT, OUT, ENV, dump

def main():
    checkout=Path(json.loads((OUT/'preflight.json').read_text())['subjects']['spring-core']['checkout'])
    directory=OUT/'pit/spring-core'; archive=OUT/'pit/spring-core-initial-interrupted'
    if archive.exists(): raise RuntimeError('Resume already attempted; inspect evidence before another retry')
    shutil.move(str(directory),str(archive)); directory.mkdir()
    cpfile=checkout/'spring-core/build/pit-classpath.txt'
    paths=cpfile.read_text().strip().split(os.pathsep)
    missing=[p for p in paths if not Path(p).exists()]
    cmd=['./gradlew','--no-daemon','--max-workers=1',':spring-core:jar',':spring-core:testFixturesJar',':spring-jcl:jar',':spring-core:pitClasspath']
    started=time.monotonic()
    with (directory/'runtime-prerequisites.log').open('w') as log:
        build=subprocess.run(cmd,cwd=checkout,env=ENV,stdout=log,stderr=subprocess.STDOUT)
    dump(directory/'runtime-prerequisites.json',{'command':cmd,'exitCode':build.returncode,'elapsedSeconds':time.monotonic()-started,
        'missingClasspathEntriesBefore':missing,'missingClasspathEntriesAfter':[p for p in paths if not Path(p).exists()],
        'runtimeJarHashes':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths if p.endswith('.jar') and Path(p).exists()},
        'reason':'testClasses/pitClasspath resolves runtime paths without producing project runtime JARs; materialize required artifacts without running any subject Test task.',
        'previousAttempt':str(archive.relative_to(ROOT)),'resumeAuthorized':True})
    if build.returncode: raise RuntimeError('Runtime prerequisites failed; see log')
    missing_jars=[p for p in paths if p.endswith('.jar') and not Path(p).exists()]
    if missing_jars: raise RuntimeError('Still missing runtime JARs: '+repr(missing_jars))
    spec=importlib.util.spec_from_file_location('spring_runner',ROOT/'spring-core/scripts/02_run_pit.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    native=subprocess.run;calls=[]
    def logged(cmd,*a,**kw):
        t=time.monotonic();row={'command':list(map(str,cmd)),'cwd':str(kw.get('cwd',checkout)),'timeout':kw.get('timeout'),
             'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()};calls.append(row)
        try:
            r=native(cmd,*a,**kw);row['exitCode']=r.returncode;return r
        except subprocess.TimeoutExpired:
            row['status']='TIMEOUT';raise
        finally:
            row['elapsedSeconds']=time.monotonic()-t;dump(directory/'commands.json',calls)
    subprocess.run=logged;start=time.monotonic();status=0
    try:
        sys.argv=[str(ROOT/'spring-core/scripts/02_run_pit.py'),'--project-dir',str(checkout),'--results-dir',str(directory)]
        module.main()
    except SystemExit as exc:status=exc.code or 0
    finally:subprocess.run=native
    record={'subject':'spring-core','checkout':str(checkout),'exitCode':status,'elapsedSeconds':time.monotonic()-start,
        'commands':calls,'originalRunner':'spring-core/scripts/02_run_pit.py','runnerModified':False,
        'infrastructureRetry':1,'reason':'Previously missing project runtime JARs; initial interrupted attempt preserved separately.',
        'cpuControl':'ActiveProcessorCount=1 per JVM; four PIT threads unchanged; sequential per-class jobs.'}
    dump(directory/'campaign.json',record)
    (directory/'checkout-build.diff').write_text(subprocess.check_output(['git','diff'],cwd=checkout,text=True))
    dump(OUT/'campaigns.json',[json.loads((OUT/'pit/jgrapht/campaign.json').read_text()),record])
    print('SPRING CAMPAIGN FINISHED',status,flush=True)

if __name__=='__main__':main()
