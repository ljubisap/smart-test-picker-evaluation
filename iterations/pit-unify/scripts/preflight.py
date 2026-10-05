"""Preserve the baseline and prepare disposable pinned subject checkouts."""
import collections,datetime,gzip,hashlib,json,os,subprocess,tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'iterations/pit-unify'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a],text=True).strip()
def main():
    if (OUT/'preflight.json').exists():raise SystemExit('Preflight already preserved; do not overwrite')
    files=git('ls-files').splitlines()
    baseline={p:sha(ROOT/p) for p in files}
    (OUT/'baseline_hashes.json').write_text(json.dumps(baseline,indent=2)+'\n')
    subjects={};old={}
    for name,pin,source in [('jgrapht','093b0c5ea006ba5b1d8b7a0212676bf8850cac6b','/private/tmp/recollect-jgrapht'),
                            ('spring-core','25838a334c037b68e614f6b571af03a1f6bfec19','/private/tmp/recollect-spring-core')]:
        destination=Path(tempfile.mkdtemp(prefix='pit-unify-'+name+'-',dir='/private/tmp'))/'subject'
        subprocess.run(['git','clone','--shared','--no-checkout',source,str(destination)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(destination),'checkout','--detach',pin],check=True,capture_output=True)
        subjects[name]={'checkout':str(destination),'revision':pin,'initialStatus':subprocess.check_output(['git','-C',str(destination),'status','--porcelain'],text=True)}
        paths=sorted((ROOT/name/'results/per-class').glob('*/mutations.xml*'));counts=collections.Counter();classes=[]
        for p in paths:
            raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
            nodes=ET.fromstring(raw).findall('mutation');cs=collections.Counter(n.findtext('mutator') for n in nodes);counts.update(cs)
            classes.append({'file':str(p.relative_to(ROOT)),'sha256':sha(p),'mutations':len(nodes),'killed':sum(n.get('status')=='KILLED' for n in nodes),'mutators':dict(cs)})
        old[name]={'classes':classes,'mutators':dict(counts),'mutations':sum(x['mutations'] for x in classes),'killed':sum(x['killed'] for x in classes)}
    jdk=Path('/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home')
    env={**os.environ,'JAVA_HOME':str(jdk),'PATH':str(jdk/'bin')+':'+os.environ['PATH']}
    versions={}
    for label,cmd in [('jdk',[str(jdk/'bin/java'),'-version']),('maven',['/Users/D061177/Programs/apache-maven-3.9.15/bin/mvn','-version'])]:
        r=subprocess.run(cmd,env=env,text=True,capture_output=True);versions[label]={'command':cmd,'exitCode':r.returncode,'output':r.stdout+r.stderr}
    versions['springGradleWrapper']=(Path(subjects['spring-core']['checkout'])/'gradle/wrapper/gradle-wrapper.properties').read_text()
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':git('rev-parse','HEAD'),'main':git('rev-parse','main'),'tagCommit':git('rev-parse','rad1-v15^{commit}'),'branch':git('branch','--show-current'),'status':git('status','--porcelain'),'subjects':subjects,'versions':versions,'originalScripts':{p:sha(ROOT/p) for p in ['jgrapht/scripts/02_run_pit.py','spring-core/scripts/02_run_pit.py','analysis/evaluation_core.py']},'runnerVersionObservation':'Both documented original runners already declare PIT 1.17.4 and JUnit plugin 1.2.1. Execute them unchanged; no version-edit copy is necessary.'}
    (OUT/'preflight.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'old_matrix_inventory.json').write_text(json.dumps(old,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
