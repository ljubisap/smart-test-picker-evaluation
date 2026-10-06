"""Stage only evaluation adoption evidence after all publication gates pass."""
import subprocess
from common import *
assert read(OUT/'gates.json')['status']=='ALL_GATES_PASS'
assert git('branch','--show-current')=='adopt-c'
omit={r['source'] for r in read(OUT/'storage_manifest.json')['omittedDuplicateRawFiles']}
paths=[ROOT/'README.md',ROOT/'results/HISTORICAL_SCOPE_NOTES.md',ROOT/'analysis/projects_v17.json',ROOT/'analysis/failure_annotations_v17.json',*(ROOT/'results').glob('v17-*')]
paths.extend(p for directory in (C,OUT,ROOT/'analysis/v17') for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths=[p for p in paths if str(p.relative_to(ROOT)) not in omit]
for p in paths:
    assert p.suffix.lower() not in ('.docx','.pdf','.tex','.zip'),p
    assert p.stat().st_size<100_000_000,p
for i in range(0,len(paths),100):subprocess.run(['git','add','-f','--',*[str(p.relative_to(ROOT)) for p in paths[i:i+100]]],cwd=ROOT,check=True)
staged=git('diff','--cached','--name-only').splitlines()
assert not any(Path(p).suffix.lower() in ('.docx','.pdf','.tex','.zip') for p in staged)
write(OUT/'staging_check.json',{'stagedFileCount':len(staged),'forbiddenManuscriptOrArchiveFiles':[],'omittedLosslessRawDuplicates':sorted(omit),'stagedPaths':staged,'status':'PASS'})
subprocess.run(['git','add','adopt_c/staging_check.json'],cwd=ROOT,check=True)
print('PASS:',len(staged)+1,'evaluation files staged; no paper/PDF/archive')
