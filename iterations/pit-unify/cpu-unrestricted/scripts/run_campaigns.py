"""Run the existing per-class functions with a narrow environment/CLI adapter."""
import datetime,importlib.util,signal,sys,threading,time,shutil
from environment import *
sys.dont_write_bytecode=True
NATIVE_RUN=subprocess.run
ENV=effective_environment()
os.environ.clear();os.environ.update(ENV)
CURRENT={};CALLS=[]

def observe(pid,done,row,directory):
    seen={};samples=[]
    while not done.is_set():
        proc=NATIVE_RUN(['ps','-axo','pid=,ppid=,%cpu=,command='],capture_output=True,text=True)
        if proc.returncode:
            row['monitorError']=proc.stderr;os.killpg(pid,signal.SIGTERM);return
        processes={}
        for line in proc.stdout.splitlines():
            bits=line.strip().split(None,3)
            if len(bits)==4:
                try:processes[int(bits[0])]=(int(bits[1]),float(bits[2]),bits[3])
                except ValueError:pass
        selected={pid}
        while True:
            extra={p for p,v in processes.items() if v[0] in selected}
            if extra<=selected:break
            selected.update(extra)
        scoped={p:processes[p] for p in selected if p in processes}
        for p,v in scoped.items():seen[(p,v[2])]={'pid':p,'ppid':v[0],'command':v[2]}
        cpu=sum(v[1] for v in scoped.values());samples.append({'elapsedSeconds':time.monotonic()-row['_start'],'cpuPercent':cpu,'processes':len(scoped)})
        if any('ActiveProcessorCount=' in v[2] for v in scoped.values()):row['cpuOverrideDetected']=True
        if cpu>700 or row.get('cpuOverrideDetected'):
            row['resourceInterrupted']=cpu>700
            try:os.killpg(pid,signal.SIGTERM)
            except ProcessLookupError:pass
            break
        done.wait(1)
    row['peakObservedCpuPercent']=max((s['cpuPercent'] for s in samples),default=0)
    write(directory/(row['id']+'.processes.json'),{'sampleIntervalSeconds':1,'scope':'Actual launched process and observed descendants only; short-lived processes can fall between samples. Environment inherited from recorded launcher.','commands':list(seen.values()),'samples':samples})

def logged_run(command,*args,**kw):
    original=list(map(str,command));cmd=original.copy();pit='org.pitest.mutationtest.commandline.MutationCoverageReport' in cmd or any('pitest-maven:' in a for a in cmd)
    if 'org.pitest.mutationtest.commandline.MutationCoverageReport' in cmd:
        assert '--mutators' not in cmd;cmd+=['--mutators','DEFAULTS']
    workers=CURRENT.get('workers',4)
    if pit and workers!=4:
        if '--threads' in cmd:cmd[cmd.index('--threads')+1]=str(workers)
        else:cmd=[('-Dthreads='+str(workers)) if a.startswith('-Dthreads=') else a for a in cmd]
    assert not any('ActiveProcessorCount' in a for a in cmd)
    timeout=kw.pop('timeout',None);capture=kw.pop('capture_output',False);check=kw.pop('check',False)
    if capture:kw.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    kw.update(env=ENV,start_new_session=True)
    directory=CURRENT['directory'];logs=directory/'commands';logs.mkdir(exist_ok=True,parents=True)
    row={'id':f'{len(CALLS)+1:03}', 'originalCommand':original,'command':cmd,'cwd':str(kw.get('cwd','')),'timeout':timeout,'pitWorkers':workers if pit else None,'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'_start':time.monotonic()}
    CALLS.append(row);proc=subprocess.Popen(cmd,*args,**kw);row['pid']=proc.pid
    done=threading.Event();monitor=threading.Thread(target=observe,args=(proc.pid,done,row,logs));monitor.start()
    expired=False
    try:stdout,stderr=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired=True
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        stdout,stderr=proc.communicate()
    finally:done.set();monitor.join()
    row['elapsedSeconds']=time.monotonic()-row.pop('_start');row['exitCode']=proc.returncode
    if expired:row['status']='TIMEOUT'
    for name,value in [('stdout',stdout),('stderr',stderr)]:
        if value is not None:(logs/(row['id']+'.'+name+'.log')).write_bytes(value if isinstance(value,bytes) else value.encode())
    # Original Spring runner removes invalid XML; retain its bytes first.
    if pit and (proc.returncode or expired):
        for xml in directory.glob('per-class/**/mutations.xml'):
            dst=directory/'partial-evidence'/xml.parent.name/'mutations.xml';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(xml,dst)
    write(directory/'commands.json',CALLS)
    if expired:raise subprocess.TimeoutExpired(cmd,timeout,output=stdout,stderr=stderr)
    result=subprocess.CompletedProcess(cmd,proc.returncode,stdout,stderr)
    if check:result.check_returncode()
    return result

def load_runner(subject):
    path=ROOT/subject/'scripts/02_run_pit.py';spec=importlib.util.spec_from_file_location('documented_'+subject,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    pre=read(OUT/'preflight.json');plan=read(OUT/'plan.json');campaigns=[]
    subprocess.run=logged_run
    for name in ('jgrapht','spring-core'):
        subject=OUT/'pit'/name
        if subject.exists():raise RuntimeError('Preserve prior attempts; directory already exists: '+str(subject))
        subject.mkdir(parents=True);checkout=Path(pre['subjects'][name]['checkout']);module=load_runner(name);results=[];started=time.monotonic();workers=4
        def context(attempt):
            global CALLS
            d=subject/attempt;d.mkdir(exist_ok=True);CURRENT.clear();CURRENT.update(directory=d,workers=workers);CALLS=[];return d
        setup=context('preparation');print('PREPARE',name,flush=True)
        if name=='jgrapht':module.prepare_pit_build('/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn',checkout)
        else:
            cmd=['./gradlew','--no-daemon','--max-workers=1',':spring-core:jar',':spring-core:testFixturesJar',':spring-jcl:jar',':spring-core:pitClasspath']
            r=logged_run(cmd,cwd=checkout,capture_output=True,text=True,timeout=1800)
            if r.returncode:raise RuntimeError('Spring runtime prerequisites failed; inspect logs')
            classpath=module.get_classpath(checkout);jars=module.find_pitest_jar()
        for index,c in enumerate(read(ROOT/name/'config/sample_classes.json')['classes'],1):
            for attempt in (1,2):
                directory=context(f'job-{index:02}-attempt-{attempt}');t=time.monotonic()
                print('START',name,index,c['fqn'],'PIT workers',workers,flush=True)
                if name=='jgrapht':
                    result=module.run_pit_for_class('/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn',checkout,directory,c['fqn'],c['targetTests'],c['loc'],index,len(plan[name]['classes']),directory/'progress.log')
                else:
                    status,count=module.run_pit_for_class(c['fqn'],c['targetTests'],checkout,classpath,jars,directory,timeout=600);result={'status':status,'mutations':count}
                result.update(fqn=c['fqn'],targetTests=c['targetTests'],attempt=attempt,pitWorkers=workers,elapsedSeconds=time.monotonic()-t,directory=str(directory.relative_to(ROOT)),commands=CALLS)
                results.append(result);write(subject/'campaign.json',{'subject':name,'sourceRevision':pre['subjects'][name]['revision'],'elapsedSeconds':time.monotonic()-started,'jobs':results,'completed':False})
                if any(r.get('resourceInterrupted') for r in CALLS) and workers==4:
                    workers=1;print('RESOURCE FALLBACK: retry this interrupted job with one PIT worker; all later jobs use same documented fallback',flush=True);continue
                break
        record={'subject':name,'sourceRevision':pre['subjects'][name]['revision'],'elapsedSeconds':time.monotonic()-started,'jobs':results,'completed':True}
        write(subject/'campaign.json',record);campaigns.append(record);print('FINISHED',name,flush=True)
    subprocess.run=NATIVE_RUN;write(OUT/'campaigns.json',campaigns)
if __name__=='__main__':main()
