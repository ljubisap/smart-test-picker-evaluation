#!/usr/bin/env python3
"""Generate the v14.7 read-only sensitivity, example, and segment audits."""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from analysis.evaluation_core import (load_coverage_map,load_pit_mutations,discover_pit_files,
 build_base_to_keys,build_class_to_keys,resolve_killing_tests,exclude_non_leaf_oracle_records,
 select_policy,select_constructor_only_rule,select_class_level,all_coverage_keys)
from analysis.analyze_failure_modes import classify_entry,footprint_type_for

SPRING={"name":"spring-core","pitFiles":["spring-core/results/per-class/*/mutations.xml"]}
RUN1=ROOT/'recollection_2e0954/spring-core/test-coverage-map.json'
RUN2=ROOT/'recollection_2e0954/spring-core/test-coverage-map-run2.json'

def resolved(path):
 cov=load_coverage_map(path); mappings=cov['testMappings']; raw=load_pit_mutations('spring-core',ROOT,discover_pit_files(ROOT,SPRING['pitFiles']))
 mutations=resolve_killing_tests(raw,mappings,build_base_to_keys(mappings),build_class_to_keys(mappings,cov.get('executionIdentities',{})))
 return mappings,exclude_non_leaf_oracle_records(mutations,ROOT,'spring-core')

def footprint(mappings,mutation):
 types=[]; entries=[]
 for key in sorted(all_coverage_keys(mutation)):
  kind,present,method_present,class_methods=classify_entry(mappings,key,mutation.mutated_class,mutation.mutated_method)
  types.append(kind); entries.append({'coverageKey':key,'type':kind,'targetClassPresent':present,'mutatedMethodPresent':method_present,'targetClassMethods':class_methods})
 return footprint_type_for(types),entries

def sensitivity():
 maps={}; mutations={}
 for label,path in [('run1',RUN1),('run2',RUN2)]: maps[label],mutations[label]=resolved(path)
 by={label:{m.mutation_id:m for m in rows} for label,rows in mutations.items()}; common=sorted(set(by['run1'])&set(by['run2']))
 selectors={'base':select_policy,'constructor':select_constructor_only_rule,'class':select_class_level}; results={}; selections={}
 for label in ('run1','run2'):
  rows=[]; selections[label]={p:{} for p in selectors}
  for mid in common:
   m=by[label][mid]; killers=set(all_coverage_keys(m)); policy={}
   for name,selector in selectors.items():
    selected=set(selector(maps[label],m.mutated_class,m.mutated_method)); selections[label][name][mid]=selected
    policy[name]={'selectedCount':len(selected),'inclusive':bool(selected&killers)}
   if not policy['base']['inclusive']:
    ftype,entries=footprint(maps[label],m); rows.append({'mutationId':mid,'mutatedClass':m.mutated_class,'mutatedMethod':m.mutated_method,'line':m.line_number,'mutator':m.mutator,'footprintType':ftype,'killerFootprints':entries})
  results[label]={'eligible':len(common),'policies':{p:{'inclusive':sum(selections[label][p][mid]&set(all_coverage_keys(by[label][mid]))!=set() for mid in common),'meanSelected':sum(len(selections[label][p][mid]) for mid in common)/len(common)} for p in selectors},'residualMisses':rows}
 diffs={p:sum(selections['run1'][p][mid]!=selections['run2'][p][mid] for mid in common) for p in selectors}
 run1ids={x['mutationId'] for x in results['run1']['residualMisses']}; run2ids={x['mutationId'] for x in results['run2']['residualMisses']}
 out={'schemaVersion':1,'run1Map':str(RUN1.relative_to(ROOT)),'run2Map':str(RUN2.relative_to(ROOT)),'killerResolutionFailures':[],
      'commonEligibleRecords':len(common),'run1':results['run1'],'run2':results['run2'],'selectedSetDifferences':diffs,
      'residualDifference':{'onlyRun1':sorted(run1ids-run2ids),'onlyRun2':sorted(run2ids-run1ids),'sameMutationIds':run1ids==run2ids}}
 (OUT/'springcore_run2_sensitivity.json').write_text(json.dumps(out,indent=2)+'\n'); return out

def worked_example():
 mappings,mutations=resolved(RUN1); matches=[m for m in mutations if m.mutated_class=='org.springframework.core.convert.support.GenericConversionService' and m.mutated_method=='canConvert' and m.line_number==133 and m.mutator.endswith('VoidMethodCallMutator') and 'ordinal=spring-core/results/per-class/org.springframework.core.convert.support.GenericConversionService/mutations.xml:17' in m.mutation_id]
 if len(matches)!=1: raise RuntimeError(f'worked example matches={len(matches)}')
 m=matches[0]; method_key=m.mutated_class+'#'+m.mutated_method
 H=sorted(k for k,v in mappings.items() if method_key in (v.get('methods') or [])); U=sorted(k for k,v in mappings.items() if not (v.get('classes') or []) and not (v.get('methods') or [])); base=set(select_policy(mappings,m.mutated_class,m.mutated_method)); constructor=set(select_constructor_only_rule(mappings,m.mutated_class,m.mutated_method)); killers=sorted(all_coverage_keys(m)); ftype,entries=footprint(mappings,m)
 out={'mutationId':m.mutation_id,'mutatedClass':m.mutated_class,'mutatedMethod':m.mutated_method,'line':m.line_number,'mutator':m.mutator,'pitOrdinal':17,'methodKey':method_key,'nameLevelHitCount':len(H),'emptyFootprintCount':len(U),'baseSelectedCount':len(base),'baseComposition':{'H':len(set(H)&base),'U':len(set(U)&base),'other':len(base-set(H)-set(U))},'killingTests':killers,'killerTargetClassFootprints':entries,'footprintType':ftype,'baseInclusive':bool(base&set(killers)),'constructorInclusive':bool(constructor&set(killers)),'constructorRecovers':not bool(base&set(killers)) and bool(constructor&set(killers))}
 (OUT/'worked_example_v14_6.json').write_text(json.dumps(out,indent=2)+'\n'); return out

SUBJECTS={
 'commons-lang':('8538458e7aeb1455a5942f60fe0b4930da6c5d68','/Users/D061177/work/issta/finerts-feasibility/subjects-full/apache_commons-lang','src/main/java/'),
 'jgrapht':('093b0c5ea006ba5b1d8b7a0212676bf8850cac6b','/Users/D061177/work/issta/finerts-feasibility/subjects-corpus/jgrapht','jgrapht-core/src/main/java/'),
 'spring-core':('25838a334c037b68e614f6b571af03a1f6bfec19','/tmp/recollect-spring-core','spring-core/src/main/java/'),
 'petclinic':('cbb884f01f7fef663fcff256e303d967494a4f8b','/Users/D061177/work/issta/finerts-feasibility/subjects-corpus/spring-petclinic','src/main/java/'),
 'flink':('c0f8d1a1e09f209885a88f9c19ceb9d9e9870283','/Users/D061177/work/issta/flink-stp-qualification/subject','flink-runtime/src/main/java/'),
 'spring-security':('a825937b8175ee85872c49d9c7fc25eea8cff991','/Users/D061177/work/issta/spring-security-stp-qualification/subject','spring-security-core/src/main/java/'),
 'hibernate':('a95dd44cf654131e984682687cf1b2ec5d3e34cd','/Users/D061177/work/issta/hibernate-orm-stp-qualification/subject','hibernate-core/src/main/java/'),
 'quarkus':('6ce99878508d792f3c2a2a7f9520b086a1c32cab','/Users/D061177/work/issta/quarkus-stp-qualification/subject','independent-projects/arc/processor/src/main/java/')}
def segment_scan():
 config={p['name']:p for p in json.loads((ROOT/'analysis/projects_v14_6.json').read_text())['projects']}; projects={}
 for name,(commit,checkout,prefix) in SUBJECTS.items():
  mappings=load_coverage_map(ROOT/config[name]['coverageMap'])['testMappings']; map_classes=sorted({c for v in mappings.values() for c in (v.get('classes') or []) if 'test' in c.split('.')[:-1]})
  root=Path(checkout); listing=subprocess.run(['git','-C',str(root),'ls-tree','-r','--name-only',commit,'--',prefix],check=True,text=True,capture_output=True).stdout.splitlines(); matches=[]
  for path in listing:
   if not path.endswith('.java') or Path(path).name in ('package-info.java','module-info.java'): continue
   content=subprocess.run(['git','-C',str(root),'show',f'{commit}:{path}'],check=True,text=True,errors='replace',capture_output=True).stdout
   m=re.search(r'^\s*package\s+([\w.]+)\s*;',content,re.M)
   if m and 'test' in m.group(1).split('.'): matches.append({'fqn':m.group(1)+'.'+Path(path).stem,'sourcePath':path})
  projects[name]={'mapPath':config[name]['coverageMap'],'mapTestSegmentClasses':map_classes,'mapCount':len(map_classes),'sourceCommit':commit,'qualifiedSourcePrefix':prefix,'sourceStatus':'INSPECTED','sourceTestSegmentClasses':matches,'sourceCount':len(matches)}
 out={'schemaVersion':1,'definition':'literal package segment equal to test; class simple name excluded','projects':projects,'allMapsClear':all(not p['mapCount'] for p in projects.values()),'allQualifiedSourceScopesClear':all(not p['sourceCount'] for p in projects.values()),'remainingGaps':[]}
 (OUT/'test_segment_v14_6.json').write_text(json.dumps(out,indent=2)+'\n'); return out

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True); print(json.dumps({'sensitivity':sensitivity()['selectedSetDifferences'],'example':worked_example()['baseComposition'],'segments':segment_scan()['remainingGaps']},indent=2))
