"""Export only the two completed diagnostic jobs; preserve six other replays."""
import importlib.util,os,re,subprocess,sys
from common import *
sys.dont_write_bytecode=True
sys.path.insert(0,str(PACKAGE))
import evaluator.evaluation_core,evaluator.inputs
import replay_helpers as ex
def main():
    allruns=read(OUT/'replays.json');assert allruns['completed'];rows=[]
    for run in allruns['jobs']:
        assert run['exitCode']==0,run
        name=run['subject'];target=run['targetClass'];d=PACKAGE/'evidence/pit_replay'/name
        cfg=read(PACKAGE/'rerun/pit'/name/'config.json');runroot=WORK/'replays'/name
        fresh=runroot/'output/per-class'/target/'mutations.xml';assert fresh.exists()
        raw=fresh.read_bytes();text=raw.decode();text,n=re.subn(r'/Users/[^/\s<>"\']+','&lt;WORKDIR&gt;',text)
        (d/'mutations.xml').write_bytes(text.encode())
        logs=[runroot/'run.log',*sorted((runroot/'output').rglob('*.log'))]
        transcript='\n'.join('===== '+str(p)+' =====\n'+p.read_text(errors='replace') for p in logs)
        (d/'run.log').write_text(ex.scrub(transcript))
        command=[sys.executable,str(PACKAGE/'rerun/compare_pit.py'),'--subject',name,'--class',target,'--pit-dir',str(d),'--json-output',str(d/'comparison.json')]
        result=subprocess.run(command,cwd=PACKAGE,capture_output=True,text=True)
        (OUT/(name+'-replay-comparison.log')).write_text(result.stdout+result.stderr)
        assert (d/'comparison.json').exists(),result.stderr
        agreement=ex.record_agreement(name,target,d/'mutations.xml');write(d/'record_agreement.json',agreement)
        java=Path(run['environment']['JAVA_HOME'])/'bin/java'
        jdk=subprocess.run([str(java),'-version'],capture_output=True,text=True)
        if name=='jgrapht':
            version=subprocess.run(['/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn','--version'],env={**os.environ,'JAVA_HOME':run['environment']['JAVA_HOME']},capture_output=True,text=True)
            build=version.stdout+version.stderr
        else:
            properties=(Path(run['checkout'])/'gradle/wrapper/gradle-wrapper.properties').read_text()
            match=re.search(r'gradle-([\d.]+)-(?:bin|all)',properties);assert match
            build='Gradle wrapper '+match.group(1)+'; executed wrapper logged in run.log'
        dirty=subprocess.check_output(['git','status','--porcelain'],cwd=run['checkout'],text=True);assert not dirty,dirty
        env={**run,'status':'EXECUTED','jdk':jdk.stdout+jdk.stderr,'buildTool':build,'pitVersion':cfg['pitVersion'],'testPlugin':cfg['testPlugin'],
             'mutators':cfg['mutators'],'fullMutationMatrix':cfg['fullMutationMatrix'],'adapter':cfg.get('buildAdapter','see run.log: temporary build adapter restored'),
             'comparisonCommand':command,'comparisonExitCode':result.returncode,'gitStatusAfter':dirty,
             'xml':{'originalSha256':sha(fresh),'packagedSha256':sha(d/'mutations.xml'),'pathScrubbingCount':n,'otherRewrites':False},
             'logs':{'originalFiles':[{'path':str(p),'sha256':sha(p)} for p in logs],'packagedSha256':sha(d/'run.log')},
             'logScrubbing':'Presentation paths/vendor/tool identifiers only; mutation XML receives path-only scrubbing if present.',
             'operatorEvidence':'Explicit named DEFAULTS in the executed profile/CLI and RemoveConditionalMutator inventory; see run.log and record_agreement.json.'}
        write(d/'environment.json',ex.scrub_object(env))
        comparison=read(d/'comparison.json');rows.append({'subject':name,'status':'EXECUTED','comparisonExitCode':result.returncode,'agreement':agreement['summary'],'comparison':comparison,'elapsedSeconds':run['elapsedSeconds']})
    # Verify every byte of the other six replay directories against input ZIP.
    before=read(OUT/'package_input.json');hashes=before['initialFileHashes']
    six=[]
    for path,digest in hashes.items():
        if path.startswith('evidence/pit_replay/') and len(path.split('/'))>3 and path.split('/')[2] not in ('jgrapht','spring-core'):
            assert sha(PACKAGE/path)==digest,path;six.append(path)
    write(OUT/'replay_comparisons.json',{'status':'PASS','subjects':rows,'otherSixReplayFilesUnchanged':six})
    print('PASS: two replay exports/comparisons and six-subject byte preservation')
if __name__=='__main__':main()
