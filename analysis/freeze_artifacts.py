#!/usr/bin/env python3
"""Write or verify deterministic SHA-256 manifests for canonical artifacts."""

import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--write',action='store_true'); p.add_argument('--verify',action='store_true')
a=p.parse_args()
if a.write == a.verify: raise SystemExit('choose exactly one of --write or --verify')
projects=('hibernate','flink','quarkus','spring-security')
for project in projects:
    base=ROOT/project
    files=[]
    for pattern in ('config/*','results/test-coverage-map.json*','results/per-class/*/mutations.xml','results/aggregated/*'):
        files.extend(path for path in base.glob(pattern) if path.is_file())
    entries={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(files))}
    manifest=base/'results/artifact-manifest.json'
    if a.write:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps({'schemaVersion':1,'project':project,'artifacts':entries},indent=2)+'\n')
        print(f'wrote {manifest.relative_to(ROOT)} ({len(entries)} artifacts)')
    else:
        expected=json.loads(manifest.read_text())['artifacts']
        if entries != expected:
            missing=sorted(set(expected)-set(entries)); extra=sorted(set(entries)-set(expected))
            changed=sorted(k for k in set(entries)&set(expected) if entries[k]!=expected[k])
            raise SystemExit(f'{project}: manifest mismatch missing={missing} extra={extra} changed={changed}')
        print(f'verified {project}: {len(entries)} artifacts')
