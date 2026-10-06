"""A/B/C raw-record correspondence, full normalized killing sets and policy results.

Correspondence uses the existing comparison tuple, extended with explicit indexes
and blocks when available. Multiplicity never disappears through a dict overwrite.
"""
import collections,dataclasses,importlib.util
from derive_c import derive
from environment import ROOT,B,OUT,read,write
from analysis.evaluation_core import RawMutation,_parse_int_list,_build_mutation_id

def load_state(config_path,outcome_path):
    cfg=read(config_path)['projects'];data=derive.read(outcome_path);outcomes={r['mutationId']:r for r in data['records']};groups={};inventories={};unresolved=[]
    for p in cfg:
        if p['name'] not in ('jgrapht','spring-core'):continue
        name=p['name'];inventory,nodes=derive.matrix_inventory(p);inventories[name]=inventory
        cov=derive.load_coverage_map(ROOT/p['coverageMap']);mapping=cov['testMappings'];base=derive.build_base_to_keys(mapping);classes=derive.build_class_to_keys(mapping,cov.get('executionIdentities',{}));g=collections.defaultdict(list)
        for (path,ordinal),n in nodes.items():
            cls=n.findtext('mutatedClass')or'';method=n.findtext('mutatedMethod')or'';desc=n.findtext('methodDescription')or'(unknown)';line=int(n.findtext('lineNumber')or'0');op=n.findtext('mutator')or'';ix=_parse_int_list(n.findtext('indexes'));bl=_parse_int_list(n.findtext('blocks'))
            mid=_build_mutation_id(name,cls,method,desc,line,op,ix,bl,path,ordinal)
            ids=tuple(x.strip() for x in (n.findtext('killingTests')or'').split('|') if x.strip());keys=[]
            if ids:
                raw=RawMutation(mid,cls,method,desc,line,op,ix,bl,ids,path,ordinal)
                try:keys=sorted(derive.all_coverage_keys(derive.resolve_killing_tests([raw],mapping,base,classes)[0]))
                except ValueError as e:unresolved.append({'mutationId':mid,'error':str(e)})
            elif n.get('status')=='KILLED':unresolved.append({'mutationId':mid,'error':'KILLED with no raw killers'})
            row={'mutationId':mid,'sourceXml':path,'ordinal':ordinal,'status':n.get('status'),'rawKillingTests':list(ids),'normalizedKillingTests':keys,'policies':{policy:outcomes[mid][policy] for policy in derive.POLICIES} if mid in outcomes else None}
            key=(cls,method,desc,str(line),op,n.findtext('description')or'',ix,bl)
            g[key].append(row)
        groups[name]=g
    return groups,inventories,unresolved

def compare_groups(left,right):
    rows=[];counts=collections.Counter()
    for key in sorted(set(left)|set(right),key=repr):
        a=left.get(key,[]);b=right.get(key,[])
        status='ONE_TO_ONE' if len(a)==len(b)==1 else 'MISSING_FROM_RIGHT' if not b else 'FRESH_ONLY' if not a else 'AMBIGUOUS_MULTIPLICITY'
        row={'comparisonKey':key,'leftMultiplicity':len(a),'rightMultiplicity':len(b),'correspondence':status,'left':a,'right':b}
        counts[status]+=1
        if status=='ONE_TO_ONE':
            row.update(statusChanged=a[0]['status']!=b[0]['status'],normalizedKillingSetChanged=a[0]['normalizedKillingTests']!=b[0]['normalizedKillingTests'])
            counts[a[0]['status']+' -> '+b[0]['status']]+=1
            if row['normalizedKillingSetChanged']:counts['killingSetDifferences']+=1
        rows.append(row)
    return {'counts':dict(counts),'leftRecords':sum(map(len,left.values())),'rightRecords':sum(map(len,right.values())),'records':rows}

def generate(destination=None):
    destination=destination or OUT
    specs={'A':(ROOT/'analysis/projects_v14_6.json',ROOT/'results/v14_6-per-record-outcomes.json'),'B':(B/'projects_unified.json',B/'results/per_record_outcomes.json.gz'),'C':(OUT/'projects_unified.json',OUT/'results/per_record_outcomes.json.gz')}
    states={k:load_state(*v) for k,v in specs.items()};comparisons={}
    for label,l in [('A_to_C','A'),('B_to_C','B')]:comparisons[label]={n:compare_groups(states[l][0][n],states['C'][0][n]) for n in ('jgrapht','spring-core')}
    transitions=[]
    A,Bg,C=(states[k][0]['jgrapht'] for k in ('A','B','C'))
    for key in sorted(set(A)&set(Bg),key=repr):
        if len(A[key])==len(Bg[key])==1 and key[0].endswith('.TransitNodeRoutingPrecomputation') and A[key][0]['status']=='KILLED' and Bg[key][0]['status']=='SURVIVED':
            c=C.get(key,[]);transitions.append({'comparisonKey':key,'A':A[key],'B':Bg[key],'C':c,'COutcome':'MISSING' if not c else 'AMBIGUOUS' if len(c)!=1 else c[0]['status']})
    result={'states':{k:{'manifest':str(v[0].relative_to(ROOT)),'outcomes':str(v[1].relative_to(ROOT)),'inventory':states[k][1],'unresolvedKillingIdentities':states[k][2]} for k,v in specs.items()},'comparisons':comparisons,'transitRoutingCases':transitions,'transitSummary':dict(collections.Counter(r['COutcome'] for r in transitions)),
       'scope':'No mutator substitution or path/ordinal rewrite. Unique semantic correspondence is not proof of identical bytecode offsets; ambiguous multiplicities remain lists. Non-KILLED policies are null because they are outside the operational denominator.',
       'interpretation':'B to C changes CPU override and any explicitly recorded worker fallback; A to C also changes the observed operator set and may differ in unrecorded historical environment. Neither comparison proves determinism or a sole cause.'}
    derive.write(destination/'comparison_records.json.gz',result)
    summaries={'A':read(ROOT/'results/v14_6-summary-tables.json'),'B':read(B/'results/summary_tables.json'),'C':read(OUT/'results/summary_tables.json')}
    summary={'sources':{k:result['states'][k]['outcomes'] for k in specs},'aggregate':{k:d['aggregate'] for k,d in summaries.items()},'projects':{k:d['projects'] for k,d in summaries.items()},'recordComparisonCounts':{k:{n:{f:d[f] for f in ('counts','leftRecords','rightRecords')} for n,d in v.items()} for k,v in comparisons.items()},'transitSummary':result['transitSummary'],'transitCaseCount':len(transitions),'unresolved':{k:states[k][2] for k in specs},'rawComparison':'comparison_records.json.gz'}
    write(destination/'comparison.json',summary)
    lines=['# A / B / C comparison','','A: current canonical data. B: preserved unified CPU=1 iteration. C: fresh explicit DEFAULTS jobs without the override. No current result is promoted.','','| State | Eligible | Base inclusive | Constructor inclusive | Class inclusive |','|---|---:|---:|---:|---:|']
    for k,d in summaries.items():
        a=d['aggregate'];lines.append(f"| {k} | {a['base']['eligible']} | {a['base']['inclusive']} | {a['constructor']['inclusive']} | {a['class']['inclusive']} |")
    lines+=['','## Per-subject outcomes','','| Subject | State | Eligible | Base inclusive | Constructor inclusive | Class inclusive | Base mean selected |','|---|---|---:|---:|---:|---:|---:|']
    for subject in summaries['C']['projects']:
        for state,d in summaries.items():
            p=d['projects'][subject]['policies'];lines.append(f"| {subject} | {state} | {p['base']['eligible']} | {p['base']['inclusive']} | {p['constructor']['inclusive']} | {p['class']['inclusive']} | {p['base']['meanSelectedFullPrecision']:.8f} |")
    lines+=['','## Raw correspondence','','| Comparison | Subject | Left records | Right records | Correspondence / status counts |','|---|---|---:|---:|---|']
    for label,subjects in comparisons.items():
        for subject,d in subjects.items():lines.append(f"| {label} | {subject} | {d['leftRecords']} | {d['rightRecords']} | {d['counts']} |")
    lines+=['','## Previously changed transit-routing records','',f"Matched A KILLED → B SURVIVED records: {len(transitions)}. C outcomes: {result['transitSummary']}.",'All identities, raw and normalized killing sets, statuses and eligible policy results are retained in comparison_records.json.gz.','',result['interpretation']]
    lines+=['','| Method / line | Mutator and description | A | B | C |','|---|---|---|---|---|']
    for row in transitions:
        k=row['comparisonKey'];lines.append(f"| {k[1]} / {k[3]} | {k[4].rsplit('.',1)[-1]}: {k[5]} | {row['A'][0]['status']} | {row['B'][0]['status']} | {row['COutcome']} |")
    (destination/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    return summary
if __name__=='__main__':generate()
