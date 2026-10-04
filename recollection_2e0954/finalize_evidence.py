#!/usr/bin/env python3
"""Create the immutable evidence manifests for the bounded v14.5 recollection attempt."""
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
STP=Path('/tmp/stp-rad1442-replay')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2)+'\n')

artifacts=[]
for rel in ['smart-test-picker-common/build/libs/smart-test-picker-common-0.2.0.jar','smart-test-picker-core/build/libs/smart-test-picker-core-0.1.0.jar','smart-test-picker/build/libs/smart-test-picker-0.1.0.jar','smart-test-picker-maven/build/libs/smart-test-picker-maven-0.1.0.jar']:
    p=STP/rel; artifacts.append({'path':str(p),'sha256':sha(p)})
write(OUT/'stp_build.json',{
 'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=STP,text=True).strip(),
 'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=STP,text=True).strip(),
 'jdk':'SapMachine 21.0.12.1+1-LTS',
 'commands':['./gradlew :smart-test-picker-common:jar :smart-test-picker-core:jar :smart-test-picker:publishToMavenLocal :smart-test-picker-maven:publishToMavenLocal -x test --offline --no-daemon --max-workers=5 --console=plain','./gradlew :smart-test-picker-common:publishToMavenLocal :smart-test-picker-core:publishToMavenLocal :smart-test-picker:publishToMavenLocal :smart-test-picker-maven:publishToMavenLocal -x test --offline --no-daemon --max-workers=5 --console=plain'],
 'attempts':2,'result':'SUCCESS','artifacts':artifacts,'log':'recollection_2e0954/stp-build.log'})

subjects={
 'commons-lang':{'checkout':'8538458e7aeb1455a5942f60fe0b4930da6c5d68','jdk':'SapMachine 21.0.12.1+1-LTS','buildTool':'Maven 3.9.15 (attempt 2; attempt 1 used 3.8.6 and was rejected)','commands':['Maven test -Psmart-test-picker','STP Maven generate-reports','STP Maven generate-coverage-map'],'attempts':2,'wallClockSeconds':[7,1254],'sessions':4697,'rawInvocations':60294,'failures':0,'errors':1,'skipped':16,'expectedPopulation':4692,'mapPath':None,'mapSha256':None,'status':'NOT_RECOLLECTED','reason':'Attempt 1 used unsupported Maven 3.8.6. Attempt 2 collected 4,697 session files but the native test task failed because ArrayUtilsConcatTest could not initialize the Mockito MockMaker; conversion was not run.'},
 'jgrapht':{'checkout':'093b0c5ea006ba5b1d8b7a0212676bf8850cac6b','jdk':'SapMachine 21.0.12.1+1-LTS','buildTool':'Maven 3.9.15','commands':['Maven verify -Psmart-test-picker -pl jgrapht-core','STP Maven generate-reports','STP Maven generate-coverage-map'],'attempts':2,'wallClockSeconds':[403,42],'sessions':2309,'rawInvocations':6875,'failures':0,'errors':0,'skipped':15,'expectedPopulation':2308,'mapPath':None,'mapSha256':None,'status':'NOT_RECOLLECTED','reason':'Tests passed and 2,309 sessions were collected. Conversion attempt 1 was denied local-Maven-repository write access; attempt 2 exposed an incomplete initial local publication of smart-test-picker-common 0.2.0. The fixed publication occurred only after the subject attempt limit.'},
 'spring-core':{'checkout':'25838a334c037b68e614f6b571af03a1f6bfec19','jdk':'SapMachine 21.0.12.1+1-LTS','buildTool':'Gradle 8.14.2','commands':['./gradlew :spring-core:test --no-daemon --max-workers=5','./gradlew :spring-core:generateTestCoverageJson --no-daemon --max-workers=5'],'attempts':2,'wallClockSeconds':[355,79],'sessions':3638,'rawInvocations':4704,'failures':3,'errors':0,'skipped':28,'expectedPopulation':3624,'mapPath':'recollection_2e0954/spring-core/test-coverage-map.json','status':'RECOLLECTED_POPULATION_MISMATCH','reason':'The documented three instrumentation-sensitive failures occurred. Converter output retained 3,624 covered and 14 empty sessions, yielding 3,638 map identities rather than the frozen 3,624.'},
 'petclinic':{'checkout':'cbb884f01f7fef663fcff256e303d967494a4f8b','jdk':'SapMachine 21.0.12.1+1-LTS','buildTool':'Gradle 8.14.3','commands':['./gradlew clean test generateSmartReports generateTestCoverageJson --no-daemon --max-workers=5 (attempt 1, project Java 17 toolchain)','same command after generic toolchain configuration to Java 21 (attempt 2)'],'attempts':2,'wallClockSeconds':[155,41],'sessions':56,'rawInvocations':60,'failures':0,'errors':0,'skipped':4,'expectedPopulation':52,'mapPath':'recollection_2e0954/petclinic/test-coverage-map.json','status':'RECOLLECTED_POPULATION_MISMATCH','reason':'The JDK 21 run was green. Converter output retained 52 covered and 4 empty sessions, yielding 56 map identities rather than the frozen 52.'}
}
for name,d in subjects.items():
    if d['mapPath']: d['mapSha256']=sha(ROOT/d['mapPath'])
    write(OUT/name/'collection.json',d)

write(OUT/'BLOCKERS.json',{'decisionBranch':'C','blockers':[{'subject':k,'status':v['status'],'reason':v['reason']} for k,v in subjects.items()]})
