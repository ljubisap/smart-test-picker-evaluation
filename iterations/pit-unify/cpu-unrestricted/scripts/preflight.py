"""Preserve A/B and inspect every relevant argument source before execution."""
import datetime,re,subprocess
from environment import *
def main():
    if (OUT/'preflight.json').exists():raise RuntimeError('Preflight exists; preserve it')
    env=effective_environment();old=read(B/'preflight.json');files=git('ls-files').splitlines()
    write(OUT/'preserved_hashes.json',{p:sha(ROOT/p) for p in files})
    scans=[]
    for name,s in old['subjects'].items():
        checkout=Path(s['checkout'])
        assert git('rev-parse','HEAD',cwd=checkout)==s['revision']
        assert not git('status','--porcelain',cwd=checkout)
        candidates=[checkout/p for p in git('ls-files',cwd=checkout).splitlines() if p.endswith(('.gradle','.gradle.kts','gradle.properties','pom.xml','.mvn/jvm.config','.mvn/maven.config'))]
        for p in candidates:
            hits=[{'line':i,'text':t} for i,t in enumerate(p.read_text(errors='replace').splitlines(),1) if re.search('ActiveProcessorCount|jvmargs|jvmArgs|jvmArguments|argLine|pitClasspath|historyInput|historyOutput',t)]
            if hits:scans.append({'subject':name,'path':str(p),'sha256':sha(p),'hits':hits})
    for p in [Path.home()/'.gradle/gradle.properties',Path.home()/'.mavenrc',Path('/etc/mavenrc')]:
        if p.exists():
            hits=[{'line':i,'text':t} for i,t in enumerate(p.read_text().splitlines(),1) if re.search('ActiveProcessorCount|jvmargs|MAVEN_OPTS|JAVA.*OPTIONS|GRADLE_OPTS',t)]
            scans.append({'path':str(p),'sha256':sha(p),'hits':hits})
    write(OUT/'argument_sources.json',scans)
    overrides=[h for r in scans for h in r['hits'] if 'ActiveProcessorCount' in h['text'] and not h['text'].lstrip().startswith('#')]
    assert not overrides,overrides
    record={'head':git('rev-parse','HEAD'),'main':git('rev-parse','main'),'branch':git('branch','--show-current'),'status':git('status','--porcelain'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subjects':old['subjects'],
      'inheritedEnvironment':{k:os.environ.get(k) for k in KEYS},'effectiveEnvironment':{k:env.get(k) for k in (*KEYS,'JAVA_HOME','PATH')},
      'BEnvironmentSource':'iterations/pit-unify/scripts/run_campaigns.py','removedSetting':'-XX:ActiveProcessorCount only; other previous launch settings preserved','primaryPitWorkers':4,
      'resourceGuard':'Sequential jobs. Monitor campaign child CPU; stop an attempt above 7 aggregate CPU cores (reserve one for analysis), then documented worker=1 fallback. No affinity, processor override or SIGSTOP duty cycling.',
      'probes':[],'binaries':{str(p):sha(p) for p in [JDK/'bin/java',JDK/'bin/javac',JDK/'release']}}
    for k,a in read(B/'pit_tool_artifacts.json').items():
        p=Path(a['path']);assert sha(p)==a['sha256'];record['binaries'][str(p)]=sha(p)
    commands=[[str(JDK/'bin/java'),'-version'],['/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn','-version'],[str(JDK/'bin/java'),str(OUT/'scripts/CpuProbe.java')],['sysctl','-n','hw.logicalcpu','hw.physicalcpu']]
    for cmd in commands:
        r=subprocess.run(cmd,env=env,capture_output=True,text=True);record['probes'].append({'command':cmd,'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if 'CpuProbe.java' in ' '.join(cmd):
            assert r.returncode==0,(r.stdout,r.stderr)
            record['controlJvmAvailableProcessors']=int(re.search(r'availableProcessors=(\d+)',r.stdout).group(1))
    assert record['controlJvmAvailableProcessors']>1,'Investigate native processor visibility before running'
    write(OUT/'preflight.json',record)
    inventory=read(B/'campaign_inventory.json')
    write(OUT/'plan.json',{n:{'classes':[{'fqn':c['fqn'],'targetTests':c['targetTests']} for c in d['classes']],'BCompleteClasses':d['completeClasses'],'BFailedClasses':d['failedOrTimedOut']} for n,d in inventory.items()})
    print('PREFLIGHT PASS: control JVM processors',record['controlJvmAvailableProcessors'],'tracked preserved files',len(files))
if __name__=='__main__':main()
