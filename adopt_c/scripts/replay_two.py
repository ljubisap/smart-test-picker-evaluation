"""Execute only the two predeclared replacement replay jobs, sequentially."""
import importlib.util,os,signal,subprocess,sys,threading,time
from common import *
sys.path.insert(0,str(C/'scripts'))
import run_campaigns as monitored
JDK=Path('/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home')
def main():
    select=read(PACKAGE/'evidence/pit_replay/selection.json');rows=[]
    sources=read(C/'preflight.json')['subjects']
    for name in ('jgrapht','spring-core'):
        target=next(r['targetClass'] for r in select['subjects'] if r['subject']==name)
        runroot=WORK/'replays'/name;runroot.mkdir(parents=True,exist_ok=True);output=runroot/'output'
        assert not output.exists(),'Do not reuse replay output'
        env=monitored.effective_environment();env['JAVA_HOME']=str(JDK);env['PATH']=str(JDK/'bin')+':/Users/D061177/Programs/apache-maven-3.9.15/bin:'+env['PATH']
        if name=='spring-core':env['GRADLE_USER_HOME']=str(ROOT.parent/'final-artifact-work/uniform-replay/spring-core/gradle-home-1')
        command=[sys.executable,str(PACKAGE/'rerun/run_pit.py'),'--subject',name,'--class',target,'--checkout',sources[name]['checkout'],'--output',str(output),'--cpus','4','--mvn','/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn']
        t=time.monotonic();row={'subject':name,'targetClass':target,'command':command,'sourceRevision':sources[name]['revision'],'checkout':sources[name]['checkout'],'id':'replay','_start':t,'pitWorkers':4,'processorCountOverride':None,'environment':{k:env.get(k) for k in ('JAVA_HOME','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','MAVEN_OPTS','GRADLE_OPTS','GRADLE_USER_HOME')}}
        with (runroot/'run.log').open('w') as log:
            proc=subprocess.Popen(command,cwd=PACKAGE,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            done=threading.Event();observer=threading.Thread(target=monitored.observe,args=(proc.pid,done,row,runroot));observer.start()
            code=proc.wait();done.set();observer.join()
        row.pop('_start');row.update(exitCode=code,elapsedSeconds=time.monotonic()-t,output=str(output),log=str(runroot/'run.log'))
        write(runroot/'execution.json',row);rows.append(row);write(OUT/'replays.json',{'completed':False,'jobs':rows});print(name,code,flush=True)
    write(OUT/'replays.json',{'completed':True,'jobs':rows})
if __name__=='__main__':main()
