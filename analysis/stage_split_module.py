#!/usr/bin/env python3
"""Stage compiled production output in a test-only Maven module for PIT."""

import argparse, shutil
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('action',choices=('stage','clean'))
p.add_argument('--production-classes',type=Path,required=True); p.add_argument('--test-module-classes',type=Path,required=True)
a=p.parse_args(); marker=a.test_module_classes.parent/'.stp-evaluation-staged-classes'
if a.action=='stage':
    if not a.production_classes.is_dir(): raise SystemExit(f'missing {a.production_classes}')
    if a.test_module_classes.exists(): raise SystemExit(f'refusing to replace existing {a.test_module_classes}')
    shutil.copytree(a.production_classes,a.test_module_classes); marker.write_text(str(a.production_classes.resolve())+'\n')
else:
    if not marker.exists(): raise SystemExit('staging marker missing')
    shutil.rmtree(a.test_module_classes); marker.unlink()
