"""Retained replay comparison and presentation scrubbing, relocated unchanged.

Function bodies copied from the previously executed package exporter; evaluator
functions are imported from the isolated package, not reimplemented.
"""
import collections,hashlib,importlib.util,json,re,sys
from common import PACKAGE,WORK
ROOT=PACKAGE
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('comparison',ROOT/'rerun/compare_pit.py')
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)
from evaluator.evaluation_core import select_policy,select_constructor_only_rule,select_class_level

def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p, x): p.write_text(json.dumps(x, indent=2)+'\n')

def scrub(text):
    # Execution transcripts are presentation evidence. XML uses path-only scrubbing below.
    text = re.sub(r'/Users/[^/\s]+', '<WORKDIR>', text)
    text = text.replace('/work/issta/', '/work/study/')
    for old,new in [('SapMachine','OpenJDK-vendor'), ('SAP SE','OpenJDK vendor'),
                    ('com.sap.oss.smarttestpicker','anon.tool'),('com.sap','anon.vendor'),
                    ('smart-test-picker','studied-tool'),('SmartTestPicker','StudiedTool'),
                    ('Smart Test Picker','the studied tool'),('CoverageMapperJaxb','CoverageConverter'),
                    ('SmartTestMojo','TestMojo'),('generateSmart','generateTool'),
                    ('github.com/ljubisap','example.invalid/anonymous'),
                    ('github.com/SAP','example.invalid/anonymous'),('sap.com','example.invalid'),
                    ('punosevac','anonymous'),('ljubisa','anonymous'),('D061177','USER')]:
        text = re.sub(re.escape(old), lambda m: new, text, flags=re.I)
    text = re.sub(r'2e0954[0-9a-f]*', 'R2', text, flags=re.I)
    text = re.sub(r'70b398[0-9a-f]*', 'R1', text, flags=re.I)
    text = re.sub(r'\bstp\b', 'TOOL', text, flags=re.I)
    text = re.sub(r'https?://(?:gradle\.com|scans\.gradle\.com)/s/[^\s]+', '<BUILD-SCAN-URL>', text)
    return text

def scrub_object(obj): return json.loads(scrub(json.dumps(obj)))

def record_agreement(subject, target, freshpath):
    p = next(p for p in cmp.projects(ROOT) if p['name']==subject)
    coverage = cmp.load_coverage_map(ROOT/p['coverageMap'])
    maps=coverage['testMappings']; execution=coverage.get('executionIdentities',{})
    paths=[ROOT/x for x in p['pitFiles']]; aliases=[p['sourceAliases'][x] for x in p['pitFiles']]
    baseline=cmp.records(subject, paths, aliases, maps, execution)
    if target: baseline={k:v for k,v in baseline.items() if v['semanticIdentity'][0]==target}
    if p['mutationFormat']=='single-file': alias=aliases[0]
    else: alias=next(a for pth,a in zip(paths,aliases) if pth.parent.name==target)
    fresh=cmp.records(subject,[freshpath],[alias],maps,execution) if freshpath else {}
    fresh,multiplicity=cmp.reconcile(baseline,fresh)
    canonical=json.loads((ROOT/'results/per_record.json').read_text())
    outcomes={x['mutationId']:x for x in canonical['records']}; sets=canonical['selectedSets']
    policies={'base':select_policy,'constructor':select_constructor_only_rule,'class':select_class_level}
    cached={}; rows=[]; changes=collections.Counter(); unknown=collections.Counter()
    for key in sorted(baseline.keys()|fresh.keys()):
        a=baseline.get(key); b=fresh.get(key); eligible=key in outcomes
        row={'mutationId':key, 'recorded':a, 'fresh':b, 'recordedEligible':eligible,
             'identityMatches':a is not None and b is not None,
             'statusMatches':bool(a and b and a['status']==b['status']),
             'killingSetMatches':bool(a and b and a['killingTests']==b['killingTests']
               and a['containerKillingIdentities']==b['containerKillingIdentities']
               and not a['unresolvedKillingTests'] and not b['unresolvedKillingTests']), 'policies':{}}
        for name,selector in policies.items():
            ref=a or b; c,m=ref['semanticIdentity'][:2]
            cachekey=(name,c,m)
            if eligible: selected=set(sets[outcomes[key][name]['selectedSetId']])
            else:
                if cachekey not in cached: cached[cachekey]=selector(maps,c,m)
                selected=cached[cachekey]
            def observation(x):
                if not x or x['status']!='KILLED' or x['unresolvedKillingTests'] or x['containerKillingIdentities']: return None
                return bool(selected & set(x['killingTests']))
            old=outcomes[key][name]['inclusive'] if eligible else observation(a)
            new=observation(b)
            if eligible:
                if new is None: unknown[name]+=1
                elif old!=new: changes[name]+=1
            row['policies'][name]={'recordedInclusive':old, 'freshInclusive':new,
               'selectedCount':len(selected),
               'freshSelectedKillers':sorted(selected & set(b['killingTests'])) if b else [],
               'recordedSelectedKillers':sorted(selected & set(a['killingTests'])) if a else []}
        rows.append(row)
    return {'subject':subject,'classScope':target,
       'scope':'Diagnostic replay only; frozen results and denominator are unchanged. Non-KILLED, unresolved and container-only observations have null leaf inclusiveness.',
       'records':rows,'repeatedSemanticIdentities':multiplicity,
       'summary':{'recordedRecords':len(baseline),'freshRecords':len(fresh),
          'matchingIdentities':sum(x['identityMatches'] for x in rows),
          'matchingStatuses':sum(x['statusMatches'] for x in rows),
          'matchingKillingSets':sum(x['killingSetMatches'] for x in rows),
          'missingRecordedIdentities':sum(x['recorded'] is not None and x['fresh'] is None for x in rows),
          'newFreshIdentities':sum(x['recorded'] is None and x['fresh'] is not None for x in rows),
          'recordedEligible':sum(x['recordedEligible'] for x in rows),
          'inclusivenessChanges':{k:changes[k] for k in policies},
          'inclusivenessNotComparable':{k:unknown[k] for k in policies},
          'recordedStatusCounts':dict(collections.Counter(x['status'] for x in baseline.values())),
          'freshStatusCounts':dict(collections.Counter(x['status'] for x in fresh.values())),
          'recordedMutatorCounts':dict(collections.Counter(x['semanticIdentity'][4] for x in baseline.values())),
          'freshMutatorCounts':dict(collections.Counter(x['semanticIdentity'][4] for x in fresh.values()))}}
