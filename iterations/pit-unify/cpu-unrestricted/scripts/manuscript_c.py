"""Recompute A-to-C manuscript comparison using the existing read-only extractor."""
import importlib.util,json
from derive_c import derive
from environment import ROOT,B,OUT
def main():
    spec=importlib.util.spec_from_file_location('existing_manuscript_comparison',B/'scripts/manuscript_compare.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.ITER=OUT
    result=m.generate()
    # Source-location routing only, not a numerical or text-content correction.
    old='iterations/pit-unify/results/';new=str((OUT/'results').relative_to(ROOT))+'/'
    for row in result['claims']:
        if isinstance(row.get('source'),str):row['source']=row['source'].replace(old,new)
    derive.write(OUT/'manuscript_comparison.json',result)
    path=OUT/'MANUSCRIPT_COMPARISON.md';path.write_text(path.read_text().replace(old,new))
    print('Claims',len(result['claims']),'changed',sum(r['changed'] for r in result['claims']),'unmatched',len(result['unmatchedClaimPatterns']))
if __name__=='__main__':main()
