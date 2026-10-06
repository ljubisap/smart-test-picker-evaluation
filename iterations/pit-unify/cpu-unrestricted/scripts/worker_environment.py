"""Summarize actual child commands and controlled JVM processor visibility."""
import collections,subprocess,xml.etree.ElementTree as ET
from environment import *
def main():
    profile=ET.fromstring((ROOT/'jgrapht/config/pit_profile.xml').read_text())
    args=[x.text for x in profile.findall('.//jvmArg')]
    controls=[]
    for name,opts in [('jgrapht',args),('spring-core',['--add-opens=java.base/java.lang=ALL-UNNAMED','--add-opens=java.base/java.util=ALL-UNNAMED'])]:
        cmd=[str(JDK/'bin/java'),*opts,str(OUT/'scripts/CpuProbe.java')]
        r=subprocess.run(cmd,env=effective_environment(),text=True,capture_output=True)
        assert r.returncode==0,(name,r.stderr)
        controls.append({'subject':name,'command':cmd,'stdout':r.stdout,'stderr':r.stderr,'exitCode':r.returncode,'kind':'CONTROL_JVM: same JDK, launch environment and configured PIT JVM arguments; not a subject-test measurement and no PIT agent/minion is attached.'})
    subjects={}
    for name in ('jgrapht','spring-core'):
        commands=[];maxcpu=0;hits=[];files=[]
        for p in sorted((OUT/'pit'/name).glob('*/commands/*.processes.json')):
            d=read(p);files.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
            maxcpu=max(maxcpu,max((s['cpuPercent'] for s in d['samples']),default=0))
            for c in d['commands']:
                if '/bin/java ' in c['command'] or c['command'].startswith('java '):commands.append(c)
                if 'ActiveProcessorCount=' in c['command']:hits.append(c)
        subjects[name]={'processSnapshots':files,'actualObservedJavaCommands':commands,'overrideHits':hits,'peakObservedAggregateCpuPercent':maxcpu,
          'mutationMinionCommands':sum('org.pitest.mutationtest.execute.MutationTestMinion' in c['command'] for c in commands),'coverageMinionCommands':sum('org.pitest.coverage.execute.CoverageMinion' in c['command'] for c in commands)}
    write(OUT/'worker_environment.json',{'controls':controls,'subjects':subjects,'sampleCaveat':'Process snapshots sample once per second; no claim that every very short-lived child was sampled. All launched commands share the sanitized environment.'})
    assert not any(v['overrideHits'] for v in subjects.values())
    print('Worker environment: no observed CPU override; control JVM probes retained')
if __name__=='__main__':main()
