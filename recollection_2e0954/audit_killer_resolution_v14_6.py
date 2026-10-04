#!/usr/bin/env python3
"""Audit every frozen PIT killing identity against the v14.6 map keys."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from analysis.evaluation_core import load_coverage_map, load_pit_mutations, discover_pit_files, build_base_to_keys, normalize_pit_test_name

projects=json.loads((ROOT/'analysis/projects_v14_6.json').read_text())['projects']; output={'projects':{},'unresolvedTotal':0}
for project in projects[:4]:
 mappings=load_coverage_map(ROOT/project['coverageMap'])['testMappings']; bases=build_base_to_keys(mappings)
 raw=load_pit_mutations(project['name'],ROOT,discover_pit_files(ROOT,project['pitFiles'])); unresolved=[]
 for mutation in raw:
  for identity in mutation.raw_killing_test_ids:
   normalized=normalize_pit_test_name(identity)
   if normalized not in mappings and normalized not in bases:
    unresolved.append({'mutationId':mutation.mutation_id,'raw':identity,'normalized':normalized})
 output['projects'][project['name']]={'killedRecords':len(raw),'killerOccurrences':sum(len(x.raw_killing_test_ids) for x in raw),'unresolved':unresolved,'unresolvedCount':len(unresolved)}; output['unresolvedTotal']+=len(unresolved)
(ROOT/'recollection_2e0954/killer_resolution_v14_6.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({k:v['unresolvedCount'] for k,v in output['projects'].items()}))
raise SystemExit(bool(output['unresolvedTotal']))
