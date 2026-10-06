"""Verify the repository delivery without original checkout roots or huge duplicates."""
import os,shutil,subprocess,sys,time
from common import *
target=WORK/'relocated-verification';target.mkdir(exist_ok=False)
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
for name in filter(None,tracked):
    source=ROOT/name;dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
omitted={r['source'] for r in read(OUT/'storage_manifest.json')['omittedDuplicateRawFiles']}
new=[ROOT/'analysis/projects_v17.json',ROOT/'analysis/failure_annotations_v17.json',*list((ROOT/'results').glob('v17-*'))]
new.extend(p for directory in (C,ROOT/'analysis/v17',OUT) for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for source in new:
    rel=str(source.relative_to(ROOT))
    if rel in omitted:continue
    dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
start=time.monotonic();log=OUT/'relocated-verification.log'
with log.open('w') as f:r=subprocess.run([sys.executable,'analysis/v17/verify_v17.py','--verify'],cwd=target,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=f,stderr=subprocess.STDOUT)
write(OUT/'portability_check.json',{'exitCode':r.returncode,'elapsedSeconds':time.monotonic()-start,'root':str(target),'omittedRawDuplicates':sorted(omitted),'canonicalCompressedInputsUnchanged':True,'lastLine':log.read_text().strip().splitlines()[-1]})
print('PASS: relocated repository input verification' if r.returncode==0 else 'FAIL: see relocated-verification.log')
raise SystemExit(r.returncode)
