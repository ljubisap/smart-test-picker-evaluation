"""Campaign-local removal of CPU overrides; no global configuration changes."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
B=ROOT/'iterations/pit-unify'; OUT=B/'cpu-unrestricted'
JDK=Path('/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home')
KEYS=('JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','MAVEN_OPTS','GRADLE_OPTS')
PATTERN=re.compile(r'''(?<!\S)(?:["']?-XX:ActiveProcessorCount=[+-]?\d+["']?)(?=\s|$)''')
def strip_cpu(value):
    return PATTERN.sub('',value).strip()
def effective_environment(base=None):
    env=dict(os.environ if base is None else base)
    # Preserve the previous campaign's non-CPU launch settings.
    env.update(JAVA_HOME=str(JDK),PATH=str(JDK/'bin')+':/Users/D061177/Programs/apache-maven-3.9.15/bin:'+env.get('PATH',''),PYTHONDONTWRITEBYTECODE='1')
    env['MAVEN_OPTS']=(env.get('MAVEN_OPTS','')+' -Xmx2g').strip()
    env['GRADLE_OPTS']=(env.get('GRADLE_OPTS','')+' -Dorg.gradle.workers.max=1 -Dorg.gradle.daemon=false').strip()
    for k in KEYS:
        if k in env:
            env[k]=strip_cpu(env[k])
            if 'ActiveProcessorCount' in env[k]:raise ValueError('Unrecognized override syntax in '+k)
            if not env[k]:env.pop(k)
    return env
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
