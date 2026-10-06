"""Install the twice-verified archive, retaining the previous directory intact."""
import shutil
from common import *
gates=read(OUT/'gates.json');assert gates['status']=='ALL_GATES_PASS'
checks=read(OUT/'package_checks.json');assert checks['completed'] and checks['allPassed']
archive=read(OUT/'package_archive.json');assert sha(Path(archive['path']))==archive['sha256']
assert sha(ZIP)==EXPECTED_ZIP,'Input archive changed during work; do not overwrite'
original=ZIP.parent/'anon-final';backup=ZIP.parent/'anon-final-before-adopt-c';assert not backup.exists()
initial=read(OUT/'package_input.json')['initialFileHashes']
differences=[p for p,digest in initial.items() if not(original/p).exists() or sha(original/p)!=digest]
# No prior bytes are discarded even if the unpacked directory had additional files.
original.rename(backup);shutil.copytree(PACKAGE,original);shutil.copyfile(Path(archive['path']),ZIP)
assert sha(ZIP)==archive['sha256']
assert sha(PAPER)==read(OUT/'preflight.json')['manuscriptSha256']
write(OUT/'delivery.json',{'archive':str(ZIP),'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'package':str(original),'previousDirectoryPreserved':str(backup),'inputArchiveBackup':str(WORK/'input-anon-final.zip'),'previousDirectoryDifferencesFromInputArchive':differences,'manuscript':str(MANUSCRIPT/'RAD1_v16.docx'),'paperNotInRepository':True,'archiveNotInRepository':True})
print('PASS: twice-verified package installed; previous package and input ZIP preserved')
