#!/usr/bin/env python3
"""Verify adopted outputs from the explicit manifest without rewriting evidence."""
import argparse,tempfile,gzip,hashlib
from pathlib import Path
from derive_v17 import ROOT,C,generate,canonical_name,derive_c,read,sha
def main():
    errors=[];a=read(ROOT/'analysis/projects_v14_6.json');b=read(ROOT/'analysis/projects_v17.json')
    for old,new in zip(a['projects'],b['projects']):
        expected={**old}
        if old['name'] in ('jgrapht','spring-core'):expected['pitFiles']=['iterations/pit-unify/cpu-unrestricted/pit/'+old['name']+'/per-class/*/mutations.xml.gz']
        if expected!=new:errors.append('Unexpected manifest change: '+old['name'])
    pre=read(ROOT/'adopt_c/preflight.json')
    packed={r['source']:r for r in read(C/'matrix_packaging.json')}
    for path,digest in pre['CFileHashes'].items():
        if (ROOT/path).exists():actual=sha(ROOT/path)
        elif path in packed:
            # Raw XML over GitHub's file-size limit is retained losslessly in
            # the already-verified C gzip. No XML byte or canonical input changes.
            actual=hashlib.sha256(gzip.decompress((ROOT/packed[path]['packaged']).read_bytes())).hexdigest()
        else:actual=None
        if actual!=digest:errors.append('Verified C evidence changed: '+path)
    # Only adoption routing/documentation may alter earlier tracked files.
    for path,digest in pre['trackedHashes'].items():
        if path in ('results/HISTORICAL_SCOPE_NOTES.md','README.md'):continue
        if sha(ROOT/path)!=digest:errors.append('Previous tracked file changed: '+path)
    with tempfile.TemporaryDirectory(prefix='verify-v17-',dir=ROOT/'adopt_c') as tmp:
        t=Path(tmp);files=generate(t)
        for name in files:
            fresh=derive_c.derive.read(t/name)
            if fresh!=derive_c.derive.read(ROOT/'results'/canonical_name(name)):errors.append('Canonical re-derivation mismatch: '+name)
            if fresh!=derive_c.derive.read(C/'results'/name):errors.append('C equality mismatch: '+name)
        if files['summary_tables.json']['methodKinds']!=read(ROOT/'results/v17-method-kinds.json'):errors.append('Method-kind mismatch')
    if files['summary_tables.json']['status']!='DERIVED':errors.append('Incomplete result')
    from publication_metrics import generate as publication_metrics
    if publication_metrics()!=read(ROOT/'results/v17-publication-metrics.json'):errors.append('Publication metric mismatch')
    for e in errors:print('FAIL:',e)
    if errors:return 1
    print('PASS: v17 raw-input derivation, all C outputs, Java full sets, input preservation and adopted manifest verified')
    return 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',required=True,action='store_true');p.parse_args();raise SystemExit(main())
