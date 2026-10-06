"""Paths and serialization for the adoption, not evaluation policy."""
import gzip,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'adopt_c'
C=ROOT/'iterations/pit-unify/cpu-unrestricted'
WORK=ROOT.parent/'adopt-c-work'
PACKAGE=WORK/'anon-final'
PAPER=Path('/Users/D061177/Downloads/RAD1_v15_final.docx')
MANUSCRIPT=ROOT.parent/'rad1-v16'
ZIP=ROOT.parent/'final-artifact-work/anon-final.zip'
EXPECTED_ZIP='4f67f79ec05262e18b9fcd3cc5a0e8d79077b3535c7f3ec27e2a2706974b8bb0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);b=(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
