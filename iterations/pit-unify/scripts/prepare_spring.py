"""Compile the recorded Spring checkout; no Test or collection task is run."""
import json,os,subprocess,time
from pathlib import Path
from derive import ROOT,ITER,read,write
def main():
 out=ITER/'pit/spring-core';out.mkdir(parents=True,exist_ok=True);checkout=Path(read(ITER/'preflight.json')['subjects']['spring-core']['checkout'])
 jdk='/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home'
 env={**os.environ,'JAVA_HOME':jdk,'PATH':jdk+'/bin:/Users/D061177/Programs/apache-maven-3.9.15/bin:'+os.environ['PATH'],'JAVA_TOOL_OPTIONS':'-XX:ActiveProcessorCount=1','GRADLE_OPTS':'-Dorg.gradle.workers.max=1 -Dorg.gradle.daemon=false'}
 cmd=['./gradlew','--no-daemon','--max-workers=1',':spring-core:testClasses',':spring-core:pitClasspath'];start=time.monotonic()
 with (out/'prerequisite.log').open('w') as log:r=subprocess.run(cmd,cwd=checkout,env=env,stdout=log,stderr=subprocess.STDOUT)
 write(out/'prerequisite.json',{'command':cmd,'checkout':str(checkout),'exitCode':r.returncode,'elapsedSeconds':time.monotonic()-start,'javaHome':jdk,'purpose':'Prerequisite only, before the recorded campaign; no Test or coverage collection task.'});return r.returncode
if __name__=='__main__':raise SystemExit(main())
