"""Prepare isolated output copies after checking exact archive identity."""
import shutil,zipfile
from common import *
def main():
    assert sha(ZIP)==EXPECTED_ZIP,'Part 3 aborted: wrong input ZIP'
    WORK.mkdir(exist_ok=True)
    if not (WORK/'input-anon-final.zip').exists():shutil.copyfile(ZIP,WORK/'input-anon-final.zip')
    assert sha(WORK/'input-anon-final.zip')==EXPECTED_ZIP
    assert not PACKAGE.exists(),'Refuse to overwrite isolated package'
    with zipfile.ZipFile(ZIP) as z:
        for i in z.infolist():
            p=Path(i.filename);assert not p.is_absolute() and '..' not in p.parts
        z.extractall(WORK)
    h=WORK/'historical-checks/iterations/pit-unify/cpu-unrestricted'
    assert not h.exists();shutil.copytree(C,h)
    write(OUT/'package_input.json',{'archive':str(ZIP),'sha256':sha(ZIP),'backup':str(WORK/'input-anon-final.zip'),'isolatedOutput':str(PACKAGE),'initialFileHashes':{str(p.relative_to(PACKAGE)):sha(p) for p in PACKAGE.rglob('*') if p.is_file()}})
    print('Isolated package and unchanged C evidence snapshot prepared')
if __name__=='__main__':main()
