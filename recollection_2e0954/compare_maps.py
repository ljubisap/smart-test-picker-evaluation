#!/usr/bin/env python3
"""Compare preserved recollection maps with frozen inputs without mutating either."""
import gzip, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

def load(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt') as stream:
        return json.load(stream)

def normalized(key):
    return re.sub(r'_[0-9a-f]{7}$', '', key)

def footprint(entry):
    return set(entry.get('classes') or []), set(entry.get('methods') or [])

specs = {
    'commons-lang': ('commons-lang/results/test-coverage-map.json.gz', 'recollection_2e0954/commons-lang/test-coverage-map.json'),
    'jgrapht': ('jgrapht/results/test-coverage-map.json.gz', 'recollection_2e0954/jgrapht/test-coverage-map.json'),
    'spring-core': ('spring-core/results/test-coverage-map.json', 'recollection_2e0954/spring-core/test-coverage-map.json'),
    'petclinic': ('petclinic/results/test-coverage-map.json', 'recollection_2e0954/petclinic/test-coverage-map.json'),
}
result = {'subjects': {}}
for name, (old_rel, new_rel) in specs.items():
    row = {'frozenMap': old_rel, 'recollectedMap': new_rel}
    if new_rel is None:
        row.update({'status': 'NOT_RECOLLECTED', 'classification': None})
        result['subjects'][name] = row
        continue
    old_path, new_path = ROOT / old_rel, ROOT / new_rel
    old = load(old_path)['testMappings']; new = load(new_path)['testMappings']
    row['frozenSha256'] = hashlib.sha256(old_path.read_bytes()).hexdigest()
    row['recollectedSha256'] = hashlib.sha256(new_path.read_bytes()).hexdigest()
    old_keys, new_keys = set(old), set(new)
    old_norm = {normalized(k): k for k in old_keys}; new_norm = {normalized(k): k for k in new_keys}
    details=[]
    for logical in sorted(set(old_norm) | set(new_norm)):
        ok, nk = old_norm.get(logical), new_norm.get(logical)
        oc, om = footprint(old[ok]) if ok else (set(),set())
        nc, nm = footprint(new[nk]) if nk else (set(),set())
        if ok is None or nk is None or oc != nc or om != nm:
            details.append({'logicalIdentity': logical, 'frozenKey': ok, 'recollectedKey': nk,
                'addedClasses': sorted(nc-oc), 'removedClasses': sorted(oc-nc),
                'addedMethods': sorted(nm-om), 'removedMethods': sorted(om-nm)})
    old_u=sorted(k for k,v in old.items() if not (v.get('classes') or []) and not (v.get('methods') or []))
    new_u=sorted(k for k,v in new.items() if not (v.get('classes') or []) and not (v.get('methods') or []))
    normalized_removed=sorted(set(old_norm)-set(new_norm))
    normalized_added=sorted(set(new_norm)-set(old_norm))
    added_nonempty=[new_norm[x] for x in normalized_added if any(footprint(new[new_norm[x]]))]
    row.update({'status':'RECOLLECTED_GATE_PASS' if not normalized_removed and not added_nonempty else 'RECOLLECTED_GATE_FAIL',
        'classification':'IDENTICAL' if not details and old_keys==new_keys else 'DIFFERENT',
        'frozenIdentityCount':len(old), 'recollectedIdentityCount':len(new),
        'exactAddedIdentities':sorted(new_keys-old_keys), 'exactRemovedIdentities':sorted(old_keys-new_keys),
        'normalizedAddedIdentities':normalized_added,
        'normalizedRemovedIdentities':normalized_removed,
        'G-ID':not normalized_removed, 'G-ADD':not added_nonempty,
        'addedNonEmptyIdentities':added_nonempty,
        'frozenU':old_u, 'recollectedU':new_u, 'differingIdentityCount':len(details),
        'differences':details})
    result['subjects'][name]=row
result['decisionBranch']='ADOPT' if all(x.get('G-ID') and x.get('G-ADD') for x in result['subjects'].values()) else 'KEEP'
(OUT/'map_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{x:v for x,v in r.items() if x in ('status','classification','frozenIdentityCount','recollectedIdentityCount','differingIdentityCount')} for k,r in result['subjects'].items()},indent=2))
