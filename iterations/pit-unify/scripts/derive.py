"""Derive the separate unified iteration using the unchanged production evaluator.

Statistics are imported from the current derivation, not redefined. Mutation IDs
come directly from the existing loader; source paths/ordinals are never rewritten.
"""
from __future__ import annotations
import collections,dataclasses,gzip,hashlib,importlib.util,json,sys
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ITER=ROOT/'iterations/pit-unify'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from analysis.evaluation_core import (load_coverage_map,discover_pit_files,load_pit_mutations,
    resolve_killing_tests,build_base_to_keys,build_class_to_keys,exclude_non_leaf_oracle_records,
    select_policy,select_constructor_only_rule,select_class_level,select_original_legacy_edge_only,
    all_coverage_keys)
from analysis.analyze_failure_modes import classify_entry,footprint_type_for
spec=importlib.util.spec_from_file_location('frozen_statistics',ROOT/'analysis/v14_4_rederivation/run_b2_derivation.py')
stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
POLICIES={'base':select_policy,'constructor':select_constructor_only_rule,'class':select_class_level}
ALL_POLICIES={'legacy':select_original_legacy_edge_only,**POLICIES}
def read(p):return json.loads(gzip.decompress(p.read_bytes()).decode() if p.suffix=='.gz' else p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(v,indent=2)+'\n').encode()
    p.write_bytes(gzip.compress(raw,mtime=0) if p.suffix=='.gz' else raw)
def tree(p):return ET.fromstring(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def selected_id(values):return hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def footprint(mappings,m):
    entries=[]
    for key in sorted(all_coverage_keys(m)):
        kind,present,method,methods=classify_entry(mappings,key,m.mutated_class,m.mutated_method)
        entries.append({'coverageKey':key,'type':kind,'targetClassPresent':present,'mutatedMethodPresent':method,'targetClassMethods':methods})
    return footprint_type_for(x['type'] for x in entries),entries
def resolve(project,coverage):
    maps=coverage['testMappings'];base=build_base_to_keys(maps);classes=build_class_to_keys(maps,coverage.get('executionIdentities',{}))
    raw=load_pit_mutations(project['name'],ROOT,discover_pit_files(ROOT,project['pitFiles']))
    valid=[];errors=[]
    for m in raw:
        try:valid.extend(resolve_killing_tests([m],maps,base,classes))
        except ValueError as exc:errors.append({'mutationId':m.mutation_id,'rawKillingTests':list(m.raw_killing_test_ids),'error':str(exc)})
    eligible=exclude_non_leaf_oracle_records(valid,ROOT,project['name'])
    excluded=sorted({m.mutation_id for m in valid}-{m.mutation_id for m in eligible})
    return raw,eligible,errors,excluded
def matrix_inventory(project):
    files=discover_pit_files(ROOT,project['pitFiles']);total=collections.Counter();mutators=collections.Counter();classes=[];nodes={};contributing=set()
    for p in files:
        elements=tree(p).findall('mutation');counts=collections.Counter(n.get('status') for n in elements);ops=collections.Counter(n.findtext('mutator') for n in elements)
        total.update(counts);mutators.update(ops);contributing.update(n.findtext('mutatedClass') for n in elements if n.get('status')=='KILLED')
        classes.append({'file':str(p.relative_to(ROOT)),'sha256':digest(p),'mutations':len(elements),'killed':counts['KILLED'],'statusCounts':dict(counts),'mutatorCounts':dict(ops),'targetClasses':sorted({n.findtext('mutatedClass') for n in elements})})
        for i,n in enumerate(elements):nodes[(str(p.relative_to(ROOT)),i)]=n
    return {'files':classes,'mutations':sum(total.values()),'killed':total['KILLED'],'statusCounts':dict(total),'mutatorCounts':dict(mutators),'usableMatrices':len(files),'killedContributingClasses':len(contributing)},nodes
def generate(destination):
    config=read(ITER/'projects_unified.json')['projects'];sets={};rows=[];resolved={};maps={};nodes={};raws={}
    summary={'schemaVersion':1,'sourcePolicy':'STP 2e0954 U union (H if H else G)','projects':{}};intervals={'projects':{},'aggregate':{}};clusters={'projects':{},'aggregate':{}}
    inventories={};resolution={};residual=[];recovered=[];annotations=[];pairs_all={p:[] for p in POLICIES}
    oldtax=read(ROOT/'results/failure_taxonomy.json');known={m['mutationId']:m for d in oldtax['byProject'].values() for m in d.get('mutations',[])}
    reviews=read(ITER/'causal_review.json') if (ITER/'causal_review.json').exists() else {}
    failed_subjects=[];method_counts=collections.Counter()
    for index,p in enumerate(config):
        name=p['name'];coverage=load_coverage_map(ROOT/p['coverageMap']);mapping=coverage['testMappings'];maps[name]=mapping
        raw,mutations,errors,excluded=resolve(p,coverage);raws[name]=raw;resolved[name]=mutations
        resolution[name]={'rawKilled':len(raw),'eligible':len(mutations),'unresolved':errors,'excluded':excluded}
        inventories[name],nodes[name]=matrix_inventory(p)
        if not mutations:failed_subjects.append(name)
        local=[];cache={}
        for m in mutations:
            killers=sorted(all_coverage_keys(m));node=nodes[name][(m.source_xml,m.xml_ordinal)]
            row={'project':name,'mutationId':m.mutation_id,'mutatedClass':m.mutated_class,'mutatedMethod':m.mutated_method,
                 'methodDescription':m.method_description,'line':m.line_number,'mutator':m.mutator,'description':node.findtext('description'),
                 'sourceXml':m.source_xml,'xmlOrdinal':m.xml_ordinal,'indexes':m.indexes,'blocks':m.blocks,
                 'killingTests':killers,'rawKillingTests':[t.raw_pit_id for t in m.killing_tests]}
            for policy,selector in ALL_POLICIES.items():
                key=(policy,m.mutated_class,m.mutated_method)
                if key not in cache:
                    selected=sorted(selector(mapping,m.mutated_class,m.mutated_method));sid=selected_id(selected);sets.setdefault(sid,selected);cache[key]=sid
                sid=cache[key];selected=sets[sid]
                row[policy]={'selectedSetId':sid,'selectedCount':len(selected),'inclusive':bool(set(selected)&set(killers))}
            rows.append(row);local.append(row);method_counts[stats.method_kind(m.mutated_method)]+=1
            if not row['base']['inclusive'] or (not row['legacy']['inclusive'] and row['base']['inclusive']):
                kind,entries=footprint(mapping,m);old=known.get(m.mutation_id);review=reviews.get(m.mutation_id)
                annotation={'mutationId':m.mutation_id,'project':name,'mutatedClass':m.mutated_class,'mutatedMethod':m.mutated_method,
                            'line':m.line_number,'mutator':m.mutator,'footprintType':kind,'killerFootprints':entries,
                            'killingTests':killers,'recoveredByConstructorRule':not row['base']['inclusive'] and row['constructor']['inclusive']}
                if old:annotation.update(causalMechanism=old['causalMechanism'],causalEvidence=old['causalEvidence'],annotationStatus='EXISTING_EXACT_MUTATION_ID',annotationSource='results/failure_taxonomy.json')
                elif review:annotation.update(review)
                else:annotation.update(causalMechanism='UNDETERMINED',causalEvidence='New record identity: source/control-flow evidence has not established a cause. Footprint shape alone is not a causal classification.',annotationStatus='UNDETERMINED')
                annotations.append(annotation)
                if not row['base']['inclusive']:residual.append(annotation)
                else:recovered.append({**annotation,'recoveredBy':'NO_COVERAGE_BRANCH'})
        if not local:
            summary['projects'][name]={'logicalTests':len(mapping),'eligible':0,'status':'NO_USABLE_RECORDS'};continue
        metrics={policy:stats.metric(local,policy,len(mapping)) for policy in POLICIES};random=stats.random_metric(local,mapping)
        summary['projects'][name]={'logicalTests':len(mapping),'emptyFootprintTests':sum(not(v.get('classes') or []) and not(v.get('methods') or []) for v in mapping.values()),'policies':metrics,'randomEqualBudget':random}
        intervals['projects'][name]={};clusters['projects'][name]={}
        for policy in POLICIES:
            grouped=collections.defaultdict(lambda:[0,0])
            for r in local:grouped[r['mutatedClass']][0]+=int(r[policy]['inclusive']);grouped[r['mutatedClass']][1]+=1
            ordered=[{'subjectQualifiedClass':name+':'+c,'successes':v[0],'total':v[1]} for c,v in sorted(grouped.items())]
            pairs=[[r['successes'],r['total']] for r in ordered];pairs_all[policy].extend(pairs);clusters['projects'][name][policy]=ordered
            intervals['projects'][name][policy]={'wilson95Pct':stats.wilson(metrics[policy]['inclusive'],len(local)),'clusterBootstrap95Pct':stats.bootstrap(pairs,20261003+index)}
        print(name,len(local),'eligible',flush=True)
    summary['aggregate']={};mitigation={'projects':{},'aggregate':{}}
    for policy in POLICIES:
        metric=stats.metric(rows,policy,sum(len(m) for m in maps.values()))
        for field in ('meanSelectedFullPrecision','meanSelected2dp','selectedFractionPctFullPrecision','selectedFractionPct2dp','reductionPctFullPrecision','reductionPct2dp'):metric.pop(field)
        summary['aggregate'][policy]=metric;intervals['aggregate'][policy]={'wilson95Pct':stats.wilson(metric['inclusive'],metric['eligible']),'clusterBootstrap95Pct':stats.bootstrap(pairs_all[policy],20261103)}
        clusters['aggregate'][policy]=[{'successes':a,'total':b} for a,b in pairs_all[policy]]
    for name,data in summary['projects'].items():
        if 'policies' not in data:continue
        mitigation['projects'][name]={'base':data['policies']['base'],'constructor':data['policies']['constructor'],'additionalRecovered':data['policies']['constructor']['inclusive']-data['policies']['base']['inclusive']}
    mitigation['aggregate']={'base':summary['aggregate']['base'],'constructor':summary['aggregate']['constructor'],'additionalRecovered':summary['aggregate']['constructor']['inclusive']-summary['aggregate']['base']['inclusive']}
    taxonomy={'residualMisses':residual,'recoveredByNoCoverage':recovered,'residualFootprintCounts':dict(collections.Counter(x['footprintType'] for x in residual)),'residualCausalMechanismCounts':dict(collections.Counter(x['causalMechanism'] for x in residual))}
    for kind in ('regular_method','constructor','lambda','class_initializer'):method_counts.setdefault(kind,0)
    summary['methodKinds']={'source':'iterations/pit-unify/results/per_record_outcomes.json.gz','counts':dict(method_counts)}
    summary['status']='DERIVED' if not failed_subjects and not any(x['unresolved'] for x in resolution.values()) else 'INCOMPLETE'
    summary['missingSubjects']=failed_subjects
    outputs={'per_record_outcomes.json.gz':{'schemaVersion':'unified-deduplicated-v1','records':rows,'selectedSets':sets},'summary_tables.json':summary,
      'confidence_intervals.json':intervals,'bootstrap_cluster_inputs.json':clusters,'random_baseline.json':{n:d['randomEqualBudget'] for n,d in summary['projects'].items() if 'randomEqualBudget' in d},
      'mitigation_comparison.json':mitigation,'residual_taxonomy.json':taxonomy,'failure_annotations_unified.json':annotations,'killer_resolution.json':resolution,'matrix_inventory.json':inventories}
    outputs.update(additional(config,rows,sets,resolved,raws,maps,nodes,taxonomy))
    for name,data in outputs.items():write(destination/name,data)
    return outputs

def additional(config,rows,sets,resolved,raws,maps,nodes,taxonomy):
    byid={r['mutationId']:r for r in rows};cohort={r['mutationId']:'RESIDUAL_MISS' for r in taxonomy['residualMisses']}
    cohort.update({r['mutationId']:'NO_COVERAGE_RECOVERED' for r in taxonomy['recoveredByNoCoverage']});observed=[];unresolved=[];availability={}
    for p in config:
        name=p['name'];mapping=maps[name];base=build_base_to_keys(mapping);coverage=load_coverage_map(ROOT/p['coverageMap']);classes=build_class_to_keys(mapping,coverage.get('executionIdentities',{}))
        availability[name]={'status':'AVAILABLE' if any(n.find('succeedingTests') is not None for n in nodes[name].values()) else 'NOT_AVAILABLE','mutationRecords':len(nodes[name]),'recordsWithElement':sum(n.find('succeedingTests') is not None for n in nodes[name].values())}
        U={k for k,v in mapping.items() if not(v.get('classes') or []) and not(v.get('methods') or [])}
        for raw in raws[name]:
            if raw.mutation_id not in cohort:continue
            row=byid[raw.mutation_id];node=nodes[name][(raw.source_xml,raw.xml_ordinal)];succ=set()
            for rawid in (node.findtext('succeedingTests') or '').split('|'):
                if not rawid:continue
                try:succ.update(all_coverage_keys(resolve_killing_tests([dataclasses.replace(raw,raw_killing_test_ids=(rawid,))],mapping,base,classes)[0]))
                except ValueError as exc:unresolved.append({'mutationId':raw.mutation_id,'rawSucceedingTestId':rawid,'error':str(exc)})
            selected=set(sets[row['base']['selectedSetId']]);kind=cohort[raw.mutation_id]
            if kind=='NO_COVERAGE_RECOVERED':selected-=U
            kill=set(row['killingTests']);survived=sorted(selected&succ);killed=sorted(selected&kill);unknown=sorted(selected-kill-succ)
            observed.append({'project':name,'mutationId':raw.mutation_id,'cohort':kind,'selectedCount':len(selected),'selectedSurvivingTests':survived,'selectedKillingTests':killed,'selectedNotExecutedByPit':unknown,'fullyExecutedAndSurvived':not killed and not unknown})
    miss=[r for r in observed if r['cohort']=='RESIDUAL_MISS'];rec=[r for r in observed if r['cohort']=='NO_COVERAGE_RECOVERED']
    succeeding={'availability':availability,'unresolvedSucceedingTestIds':unresolved,'records':observed,'summary':{'residualMisses':len(miss),'noCoverageRecovered':len(rec),'f':sum(r['fullyExecutedAndSurvived'] for r in miss),'u_tests':sum(len(r['selectedNotExecutedByPit']) for r in miss),'selectedSurvived':sum(len(r['selectedSurvivingTests']) for r in miss),'recoveredRecordsFullyExecutedEdgeOnlySet':sum(r['fullyExecutedAndSurvived'] for r in rec)}}
    failures=read(ROOT/'analysis/v14_8/springcore_test_outcomes.json');failed_keys={k for f in failures['failures'] for k in f['adoptedMap']['matchingKeys']};affected=[]
    for row in rows:
        if row['project']!='spring-core' or not(set(row['killingTests'])&failed_keys):continue
        pol={}
        for name in POLICIES:
            chosen=set(sets[row[name]['selectedSetId']]);killers=chosen&set(row['killingTests'])
            pol[name]={'inclusive':bool(killers),'selectedKillingIdentities':sorted(killers),'failedTestSelected':bool(chosen&failed_keys),'anotherKillerSelected':bool(killers-failed_keys)}
        affected.append({'mutationId':row['mutationId'],'mutatedClass':row['mutatedClass'],'mutatedMethod':row['mutatedMethod'],'killingIdentities':row['killingTests'],'failedKillingIdentities':sorted(set(row['killingTests'])&failed_keys),'amongSpringCoreResidualMisses':not row['base']['inclusive'],'policies':pol})
    failed={'failedKeys':sorted(failed_keys),'records':affected,'summary':{'affectedRecords':len(affected),'k_miss':sum(r['amongSpringCoreResidualMisses'] for r in affected),'k_only':sum(r['policies']['base']['inclusive'] and not r['policies']['base']['anotherKillerSelected'] for r in affected),'k_other':sum(r['policies']['base']['anotherKillerSelected'] for r in affected)}}
    spring=next(p for p in config if p['name']=='spring-core');coverage2=load_coverage_map(ROOT/'recollection_2e0954/spring-core/test-coverage-map-run2.json');_,run2,errors,_=resolve(spring,coverage2);map2=coverage2['testMappings'];run2rows=[];diffs=collections.Counter();cache={}
    for m in run2:
        if m.mutation_id not in byid:continue
        old=byid[m.mutation_id];kill=set(all_coverage_keys(m));pol={}
        for policy,selector in POLICIES.items():
            key=(policy,m.mutated_class,m.mutated_method)
            if key not in cache:cache[key]=set(selector(map2,m.mutated_class,m.mutated_method))
            chosen=cache[key];different=chosen!=set(sets[old[policy]['selectedSetId']]);diffs[policy]+=different
            pol[policy]={'inclusive':bool(chosen&kill),'selectedCount':len(chosen),'selectedSetDiffers':different}
        r={'mutationId':m.mutation_id,'policies':pol}
        if not pol['base']['inclusive']:r['footprintType'],r['killerFootprints']=footprint(map2,m)
        run2rows.append(r)
    sensitivity={'killerResolutionFailures':errors,'records':run2rows,'eligible':len(run2rows),'selectedSetDifferences':dict(diffs),'policies':{p:{'inclusive':sum(r['policies'][p]['inclusive'] for r in run2rows),'meanSelected':sum(r['policies'][p]['selectedCount'] for r in run2rows)/len(run2rows) if run2rows else None} for p in POLICIES},'residualMisses':[r for r in run2rows if not r['policies']['base']['inclusive']]}
    one={m.mutation_id for m in resolved['spring-core'] if not byid[m.mutation_id]['base']['inclusive']};two={r['mutationId'] for r in sensitivity['residualMisses']};sensitivity['residualDifference']={'onlyRun1':sorted(one-two),'onlyRun2':sorted(two-one),'sameMutationIds':one==two}
    examples=[]
    for m in resolved['spring-core']:
        if m.mutated_class!='org.springframework.core.convert.support.GenericConversionService' or m.mutated_method!='canConvert' or m.line_number!=133 or not m.mutator.endswith('VoidMethodCallMutator'):continue
        mapping=maps['spring-core'];H={k for k,v in mapping.items() if m.mutated_class+'#'+m.mutated_method in(v.get('methods')or[])};U={k for k,v in mapping.items() if not(v.get('classes')or[]) and not(v.get('methods')or[])};r=byid[m.mutation_id];chosen=set(sets[r['base']['selectedSetId']]);kind,entries=footprint(mapping,m)
        examples.append({'mutationId':m.mutation_id,'pitOrdinal':m.xml_ordinal,'nameLevelHitCount':len(H),'emptyFootprintCount':len(U),'baseSelectedCount':len(chosen),'baseComposition':{'H':len(H&chosen),'U':len(U&chosen),'other':len(chosen-H-U)},'killingTests':r['killingTests'],'killerTargetClassFootprints':entries,'footprintType':kind,'baseInclusive':r['base']['inclusive'],'constructorInclusive':r['constructor']['inclusive'],'constructorRecovers':not r['base']['inclusive'] and r['constructor']['inclusive']})
    # Presence is inspected across every PIT status, not only eligible KILLED records.
    present=[{'sourceXml':p,'ordinal':i,'status':n.get('status')} for (p,i),n in nodes['spring-core'].items() if n.findtext('mutatedClass')=='org.springframework.core.convert.support.GenericConversionService' and n.findtext('mutatedMethod')=='canConvert' and n.findtext('lineNumber')=='133' and (n.findtext('mutator')or'').endswith('VoidMethodCallMutator')]
    return {'succeeding_tests_check.json':succeeding,'failed_killer_impact.json':failed,'springcore_run2_sensitivity.json':sensitivity,'worked_example.json':{'present':bool(present),'rawMatches':present,'eligibleExamples':examples}}
if __name__=='__main__':generate(ITER/'results')
