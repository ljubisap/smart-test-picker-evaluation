"""Preserve starting state and exact inputs before any adoption edit."""
from common import *
def main():
    assert not (OUT/'preflight.json').exists(),'Do not overwrite preflight'
    s=read(C/'status.json');assert s['numericalVerification']=='PASS'
    a=read(C/'results/summary_tables.json')['aggregate']
    observed=[a['base']['eligible'],*[a[p]['inclusive'] for p in ('base','constructor','class')]]
    assert observed==[3931,3912,3919,3930],observed
    tracked=git('ls-files').splitlines()
    write(OUT/'preflight.json',{'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'main':git('rev-parse','main'),'status':git('status','--porcelain'),'CStatus':s,'CCounts':observed,'packageInput':str(ZIP),'packageSha256':sha(ZIP),'packageDigestMatches':sha(ZIP)==EXPECTED_ZIP,'manuscriptInput':str(PAPER),'manuscriptSha256':sha(PAPER),'trackedHashes':{p:sha(ROOT/p) for p in tracked if (ROOT/p).is_file()},'CFileHashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(C.rglob('*')) if p.is_file()}})
    print('Preflight recorded; package digest matches:',sha(ZIP)==EXPECTED_ZIP)
if __name__=='__main__':main()
