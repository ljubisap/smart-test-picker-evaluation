"""Two clean-extraction, end-to-end passes over the exact delivery ZIP."""
import gzip,hashlib,importlib.util,os,re,shutil,subprocess,sys,time,zipfile
from common import *
PYTHON=WORK/'venv/bin/python'
TOKENS=['punosevac','ljubisa','d061177','sap.com','com.sap','sapmachine','smart test picker','smarttestpicker','smart-test','generateSmart','SmartTestMojo','2e0954b5','70b39846','coveragemapperjaxb','github.com/sap','github.com/ljubisap']
def scan(root):
    hits=[];accepted=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        b=p.read_bytes();b=gzip.decompress(b) if p.suffix=='.gz' else b;text=b.decode('utf8',errors='replace');low=text.lower();rel=str(p.relative_to(root))
        for token in TOKENS:
            if token.lower() in low or token.lower() in rel.lower():hits.append({'file':rel,'token':token,'count':low.count(token.lower())})
        if re.search(r'\bstp\b',text,re.I):hits.append({'file':rel,'token':'STP word'})
        for token in ('ISSTA','legacy','audit'):
            if token.lower() in low:accepted.append({'file':rel,'token':token,'count':low.count(token.lower()),'scope':'Source/test identifiers and schema keys are expressly excepted; no data renaming.'})
    return {'zeroIdentityHits':not hits,'identityHits':hits,'sourceIdentifierHits':accepted}
def manifest(root):
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and p.name!='CHECKSUMS.sha256' and '__pycache__' not in p.parts]
    (root/'CHECKSUMS.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in files))
def run(cmd,cwd,log):
    start=time.monotonic()
    with log.open('w') as stream:result=subprocess.run(cmd,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    lines=[l for l in log.read_text().splitlines() if l.strip()]
    return {'command':[str(x) for x in cmd],'cwd':str(cwd),'exitCode':result.returncode,'elapsedSeconds':time.monotonic()-start,'lastLine':lines[-1] if lines else '', 'log':str(log)}
def main():
    # Confirm prohibited inputs and six recorded replays before packaging.
    initial=read(OUT/'package_input.json')['initialFileHashes'];preserved=[]
    for rel,digest in initial.items():
        if rel.startswith('data/maps/') or rel=='evaluator/evaluation_core.py' or rel.startswith('data/pit/') and rel.split('/')[2] not in ('jgrapht','spring-core') or rel.startswith('evidence/pit_replay/') and len(rel.split('/'))>3 and rel.split('/')[2] not in ('jgrapht','spring-core'):
            assert sha(PACKAGE/rel)==digest,rel;preserved.append(rel)
    privacy=scan(PACKAGE);write(OUT/'package_identity_scan.json',privacy);assert privacy['zeroIdentityHits']
    manifest(PACKAGE);archive=WORK/'anon-final.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(PACKAGE.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,'anon-final/'+str(p.relative_to(PACKAGE)))
    metadata={'path':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'unpackedBytes':sum(p.stat().st_size for p in PACKAGE.rglob('*') if p.is_file())}
    write(OUT/'package_archive.json',metadata);rounds=[]
    for cycle in (1,2):
        target=WORK/f'delivery-check-{cycle}';target.mkdir(exist_ok=False)
        with zipfile.ZipFile(archive) as z:z.extractall(target)
        root=target/'anon-final';logs=target/'logs';logs.mkdir();commands=[]
        def call(args,name):
            row=run([str(PYTHON),*args],root,logs/(name+'.log'));commands.append(row);print(cycle,name,row['exitCode'],flush=True)
            write(OUT/'package_checks.json',{'completed':False,'archive':metadata,'rounds':rounds,'activeRound':cycle,'activeCommands':commands})
        call(['-m','unittest','discover','-s','evaluator/tests'],'evaluator-tests')
        call(['-m','unittest','discover','-s','rerun/tests'],'runner-tests')
        call(['rerun/run_pit.py','--help'],'runner-help')
        for subject in read(root/'config/projects.json')['projects']:
            n=subject['name'];call(['rerun/compare_pit.py','--subject',n,'--pit-dir','data/pit/'+n],'self-'+n)
            call(['rerun/run_pit.py','--subject',n,'--checkout','/not-needed-for-plan','--plan'],'plan-'+n)
        for n in ('jgrapht','spring-core'):
            selection=next(r for r in read(root/'evidence/pit_replay/selection.json')['subjects'] if r['subject']==n)
            output=logs/(n+'-fresh-comparison.json')
            call(['rerun/compare_pit.py','--subject',n,'--class',selection['targetClass'],'--pit-dir','evidence/pit_replay/'+n,'--json-output',str(output)],'fresh-'+n)
            assert read(output)==read(root/'evidence/pit_replay'/n/'comparison.json')
            commands[-1]['expectedExitCode']=0 if read(output)['fullMatch'] else 1
        if cycle==2:call(['reproduce.py','--write'],'regenerate')
        call(['reproduce.py','--verify'],'reproduce')
        # A fresh extraction must fail closed on result corruption. Restore it.
        p=root/'results/summary.json';original=p.read_bytes();d=read(p);d['aggregate']['base']['inclusive']+=1;write(p,d)
        bad=run([str(PYTHON),'reproduce.py','--verify'],root,logs/'negative-result-tamper.log');p.write_bytes(original)
        assert bad['exitCode']!=0
        after=scan(root);assert after['zeroIdentityHits']
        rounds.append({'round':cycle,'commands':commands,'negativeTamperRejected':True,'scan':after,'passed':all(r['exitCode']==r.get('expectedExitCode',0) for r in commands)})
        write(OUT/'package_checks.json',{'completed':cycle==2,'archive':metadata,'rounds':rounds,'preservedFiles':preserved,'allPassed':all(r['passed'] for r in rounds)})
    assert all(r['passed'] for r in rounds)
    print('PASS: exact ZIP verified twice from fresh extractions, including documented write/verify and failure guard')
if __name__=='__main__':main()
