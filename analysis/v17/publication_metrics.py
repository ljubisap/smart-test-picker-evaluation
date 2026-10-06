"""Derived manuscript cross-checks; no new selection or annotation policy."""
import collections,gzip,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):
 b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def generate():
 s=read(ROOT/'results/v17-summary-tables.json');r=read(ROOT/'results/v17-per-record-outcomes.json.gz')['records']
 t=read(ROOT/'results/v17-residual-taxonomy.json');random=read(ROOT/'results/v17-random-baseline.json')
 count=collections.Counter(x['mutator'].rsplit('.',1)[-1] for x in r)
 residual=collections.Counter(x['mutator'].rsplit('.',1)[-1] for x in t['residualMisses'])
 fractions=[x['policies']['base']['selectedFractionPctFullPrecision'] for x in s['projects'].values()]
 maximum=max(x['absoluteDifferencePercentagePoints'] for x in random.values())
 return {'sources':['results/v17-summary-tables.json','results/v17-per-record-outcomes.json.gz','results/v17-residual-taxonomy.json','results/v17-random-baseline.json'],
  'selectedFractionRangePct':[min(fractions),max(fractions)],'maxRandomDifferencePp':maximum,'maxRandomDifferenceCeiling3dp':math.ceil(maximum*1000)/1000,
  'eligibleMutatorCounts':dict(count),'residualMutatorCounts':dict(residual),'residualCount':len(t['residualMisses']),
  'methodKindInclusive':{k:sum(x['base']['inclusive'] for x in r if (x['mutatedMethod']=='<init>' if k=='constructor' else x['mutatedMethod'].startswith('lambda$'))) for k in ('constructor','lambda')}}
if __name__=='__main__':(ROOT/'results/v17-publication-metrics.json').write_text(json.dumps(generate(),indent=2)+'\n')
