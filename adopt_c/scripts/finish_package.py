"""Finish after the two already-running jobs; never starts additional PIT."""
import os,subprocess,sys,time
from common import *
while not (OUT/'replays.json').exists() or not read(OUT/'replays.json')['completed']:
    time.sleep(5)
for name in ('export_replays.py','finish_readme.py','check_package.py'):
    result=subprocess.run([sys.executable,str(OUT/'scripts'/name)],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if result.returncode:raise SystemExit(result.returncode)
