"""Record effective runtime JAR paths/hashes without changing resolution."""
from environment import *
def main():
    pre=read(OUT/'preflight.json');spring=Path(pre['subjects']['spring-core']['checkout']);cp=spring/'spring-core/build/pit-classpath.txt'
    paths=[Path(x) for x in cp.read_text().strip().split(os.pathsep)]
    jars={str(p):{'exists':p.exists(),'sha256':sha(p) if p.is_file() else None} for p in paths if p.suffix=='.jar'}
    maven=Path('/Users/D061177/Programs/apache-maven-3.9.15')
    build={str(p):sha(p) for p in [maven/'bin/mvn',maven/'boot/plexus-classworlds-2.9.0.jar']}
    write(OUT/'runtime_artifacts.json',{'springClasspathFile':str(cp),'springClasspathSha256':sha(cp),'springRuntimeJars':jars,'mavenLauncherArtifacts':build,'pitArtifactsSource':'preflight.json#/binaries','note':'Observed local artifacts; no dependency versions or source files changed.'})
if __name__=='__main__':main()
