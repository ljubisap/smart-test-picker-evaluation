"""Deterministic C re-derivation and preservation checks; read-only on A/B/C."""
import argparse,gzip,tempfile
from pathlib import Path
from derive_c import derive,generate
from environment import ROOT,B,OUT,read,sha,git
def main():
    errors=[]
    for path,h in read(OUT/'preserved_hashes.json').items():
        if not(ROOT/path).exists() or sha(ROOT/path)!=h:errors.append('Preserved file changed: '+path)
    pre=read(OUT/'preflight.json')
    if git('rev-parse','HEAD')!=pre['head']:errors.append('HEAD changed: commit forbidden')
    for name,s in pre['subjects'].items():
        if git('rev-parse','HEAD',cwd=Path(s['checkout']))!=s['revision'] or git('status','--porcelain',cwd=Path(s['checkout'])):errors.append('Subject checkout not restored: '+name)
    config=read(OUT/'projects_unified.json');baseline=read(B/'projects_unified.json')
    for a,b in zip(baseline['projects'],config['projects']):
        expected={**a}
        if a['name'] in ('jgrapht','spring-core'):expected['pitFiles']=[str((OUT/'pit'/a['name']/'per-class/*/mutations.xml.gz').relative_to(ROOT))]
        if expected!=b:errors.append('Unexpected input change: '+a['name'])
    with tempfile.TemporaryDirectory(prefix='verify-',dir=OUT) as tmp:
        files=generate(Path(tmp))
        for name in files:
            if derive.read(Path(tmp)/name)!=derive.read(OUT/'results'/name):errors.append('Derived mismatch: '+name)
        import compare_abc
        compare_abc.generate(Path(tmp))
        for name in ('comparison.json','comparison_records.json.gz'):
            if derive.read(Path(tmp)/name)!=derive.read(OUT/name):errors.append('A/B/C comparison mismatch: '+name)
    data=derive.read(OUT/'results/per_record_outcomes.json.gz');base=derive.read(B/'results/per_record_outcomes.json.gz');a={r['mutationId']:r for r in base['records'] if r['project'] not in ('jgrapht','spring-core')};b={r['mutationId']:r for r in data['records'] if r['project'] not in ('jgrapht','spring-core')}
    if set(a)!=set(b):errors.append('Unchanged six mutation IDs differ')
    for mid in a.keys()&b.keys():
        if a[mid]['killingTests']!=b[mid]['killingTests']:errors.append('Killers changed: '+mid)
        for p in derive.ALL_POLICIES:
            x=a[mid][p];y=b[mid][p]
            if x['inclusive']!=y['inclusive'] or base['selectedSets'][x['selectedSetId']]!=data['selectedSets'][y['selectedSetId']]:errors.append('Six-subject selection mismatch: '+mid+' '+p)
    comparison=read(OUT/'results/java_comparison.json');raw=read(OUT/'java/output.json');actual={r['caseId']:r for r in raw['cases']};cases={(r['project'],r['changedClass'],r['changedMethod']):r for r in comparison['cases']};grouped={}
    for r in data['records']:grouped.setdefault((r['project'],r['mutatedClass'],r['mutatedMethod']),[]).append(r)
    if set(cases)!=set(grouped):errors.append('Java case coverage differs')
    for key,rows in grouped.items():
        c=cases[key];j=actual[c['caseId']];wanted=data['selectedSets'][rows[0]['base']['selectedSetId']]
        if sorted(j['selectedTests'])!=wanted or j['mode']!='SELECTED' or c['occurrences']!=len(rows) or c['pythonSelectedTests']!=wanted or c['javaSelectedTests']!=wanted:errors.append('Java mismatch: '+repr(key))
    if comparison['weightedOccurrences']!=len(data['records']) or comparison['mismatches'] or comparison['nonSelectedModes']:errors.append('Java accounting mismatch')
    for m in read(OUT/'java/cases.json')['maps']:
        if sha(Path(m['path']))!=m['mapSha256']:errors.append('Java map digest changed')
    loader=read(OUT/'results/loader_content_equality.json')
    if loader['totalDifferentEntries'] or loader['totalRawU']!=loader['totalLoadedU']:errors.append('Loader mismatch')
    for p in read(OUT/'matrix_packaging.json'):
        source=ROOT/p['source'];packed=ROOT/p['packaged']
        if sha(source)!=p['sourceSha256'] or sha(packed)!=p['packagedSha256'] or gzip.decompress(packed.read_bytes())!=source.read_bytes():errors.append('Packaging mismatch: '+p['packaged'])
    inventory=read(OUT/'results/matrix_inventory.json')
    for n in ('jgrapht','spring-core'):
        if any('NegateConditionalsMutator' in k for k in inventory[n]['mutatorCounts']):errors.append('Negate remains: '+n)
    if read(OUT/'results/summary_tables.json')['status']!='DERIVED':errors.append('Unresolved derivation')
    import failure_evidence
    if failure_evidence.generate()!=read(OUT/'failed_jobs_evidence.json'):errors.append('Failed-job evidence mismatch')
    if read(OUT/'configuration_comparison.json')['unexpectedDifferences']:errors.append('Unexplained effective command changes')
    for e in errors:print('FAIL',e)
    if errors:return 1
    print('PASS: C raw-input re-derivation, Java full sets, loader, six-subject invariance, lossless matrices and all preserved hashes')
    return 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true',required=True);p.parse_args();raise SystemExit(main())
