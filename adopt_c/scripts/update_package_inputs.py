"""Relocate adopted matrices and supporting evidence; keep selector/maps unchanged."""
import collections,datetime,gzip,importlib.util,re,shutil,sys,xml.etree.ElementTree as ET
from common import *
sys.dont_write_bytecode=True
import replay_helpers as privacy
def scrub(obj):return privacy.scrub_object(obj)
def main():
    assert sha(WORK/'input-anon-final.zip')==EXPECTED_ZIP
    config=read(PACKAGE/'config/projects.json');canonical=read(ROOT/'analysis/projects_v17.json')
    records=read(ROOT/'results/v17-per-record-outcomes.json.gz')['records'];summary=read(ROOT/'results/v17-summary-tables.json')
    for subject in config['projects']:
        name=subject['name']
        if name not in ('jgrapht','spring-core'):continue
        target=PACKAGE/'data/pit'/name;backup=WORK/'prior-pit'/name;backup.parent.mkdir(exist_ok=True)
        assert not backup.exists();target.rename(backup);target.mkdir()
        source=next(x for x in canonical['projects'] if x['name']==name)
        paths=sorted(ROOT.glob(source['pitFiles'][0]));subject['pitFiles']=[];subject['sourceAliases']={}
        for path in paths:
            new=target/'per-class'/path.parent.name/path.name;new.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,new)
            rel=str(new.relative_to(PACKAGE));subject['pitFiles'].append(rel);subject['sourceAliases'][rel]=str(path.relative_to(ROOT))
        cfg=read(PACKAGE/'rerun/pit'/name/'config.json');cfg.update(processorCountOverride=None,buildWorkers=1,pitVersion='1.17.4',mutators=['DEFAULTS'])
        cfg['provenance']='Executed replacement campaign: PIT 1.17.4 with explicitly named DEFAULTS; no processor-count override. Replay configuration is not evidence of the installed versions of other campaigns.'
        write(PACKAGE/'rerun/pit'/name/'config.json',cfg)
    write(PACKAGE/'config/projects.json',config)
    annotations=read(ROOT/'results/v17-failure-annotations-unified.json')
    categories={'EARLY_EXCEPTION_PROBE_SHADOWING':'early-exception-before-probe','PRE_TEST_ATTRIBUTION_GAP':'pre-test-custom-engine-enhancement'}
    assert all(a['causalMechanism'] in categories for a in annotations),'Unestablished annotation'
    write(PACKAGE/'config/failure_annotations.json',scrub([{'mutationId':a['mutationId'],'cause':a['causalEvidence'],'category':categories[a['causalMechanism']]} for a in annotations]))
    integrity=read(PACKAGE/'evidence/input_integrity.json')
    integrity['pit']={path:sha(PACKAGE/path) for s in config['projects'] for path in s['pitFiles']};write(PACKAGE/'evidence/input_integrity.json',integrity)
    population=read(PACKAGE/'evidence/subject_population.json');counts=read(ROOT/'results/v17-table-i-counts.json');inventory=read(ROOT/'results/v17-matrix-inventory.json')
    for s in config['projects']:
        n=s['name'];population[n].update(counts[n],rawKilled=inventory[n]['killed']);population[n]['sources']['mutations']=s['pitFiles']
    write(PACKAGE/'evidence/subject_population.json',population)
    # Preserve detailed category definitions, regenerate all counts from records.
    kinds=read(PACKAGE/'evidence/method_kinds.json')
    sys.path.insert(0,str(PACKAGE));from evaluator.statistics import method_kind
    kinds['scope']=f"{len(records):,} eligible leaf-oracle KILLED records"
    for name,entry in kinds['subjects'].items():
        local=[r for r in records if r['project']==name]
        for kind,d in entry['eligibleRecordsByKind'].items():
            rows=[r for r in local if method_kind(r['mutatedMethod'])==kind]
            d.update(eligible=len(rows),inclusiveUnder2ePolicy=sum(r['base']['inclusive'] for r in rows),residualMissesUnder2ePolicy=sum(not r['base']['inclusive'] for r in rows))
    # Other aggregate fields are replaced with an explicit computed summary.
    kinds={'scope':kinds['scope'],'classificationRule':kinds['classificationRule'],'keyDerivationEvidence':kinds['keyDerivationEvidence'],'subjects':kinds['subjects'],'aggregateCounts':summary['methodKinds']['counts']}
    write(PACKAGE/'evidence/method_kinds.json',kinds)
    for name in ('comparison.json','inputs.json','output.json','runtime.json'):
        source={'comparison.json':ROOT/'results/v17-java-comparison.json','inputs.json':C/'java/cases.json','output.json':C/'java/output.json','runtime.json':C/'java/runtime.json'}[name]
        obj=scrub(read(source))
        if name=='inputs.json':
            for m in obj['maps']:m['path']=next(s['coverageMap'] for s in config['projects'] if s['name']==m['project'])
        write(PACKAGE/'evidence/java_replay'/name,obj)
    write(PACKAGE/'evidence/loader_equality.json',scrub(read(ROOT/'results/v17-loader-content-equality.json')))
    prov=read(PACKAGE/'evidence/summary_provenance.json');prov['methodKinds']['counts']=summary['methodKinds']['counts'];java=read(ROOT/'results/v17-java-comparison.json')
    prov['javaVerification'].update({k:java[k] for k in ('uniqueInvocations','weightedOccurrences','mismatches','nonSelectedModes')});write(PACKAGE/'evidence/summary_provenance.json',prov)
    tax=read(ROOT/'results/v17-residual-taxonomy.json');context=read(PACKAGE/'evidence/policy_context.json')
    context.update(inclusiveWithoutEmptyBranchWitness=summary['aggregate']['base']['inclusive']-len(tax['recoveredByNoCoverage']),nonInclusiveWithoutEmptyBranchWitness=len(tax['residualMisses'])+len(tax['recoveredByNoCoverage']));write(PACKAGE/'evidence/policy_context.json',context)
    scope=read(PACKAGE/'evidence/verification_scope.json');old=read(ROOT/'results/eight-subject-summary.json')
    # Retained separate-model evidence supports the explicit manuscript paragraph;
    # these are not the adopted policy's counts.
    scope['recordedModelComparison']['resultSource']='retained separate-model observation described in the paper'
    write(PACKAGE/'evidence/verification_scope.json',scope)
    selection=read(PACKAGE/'evidence/pit_replay/selection.json')
    for row in selection['subjects']:
        if row['subject'] not in ('jgrapht','spring-core'):continue
        s=next(x for x in config['projects'] if x['name']==row['subject']);candidates=[]
        for f in s['pitFiles']:
            path=PACKAGE/f;nodes=ET.fromstring(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()).findall('mutation');counts=collections.Counter(n.get('status') for n in nodes)
            candidates.append({'class':nodes[0].findtext('mutatedClass'),'killed':counts['KILLED'],'total':len(nodes),'statuses':dict(counts)})
        candidates.sort(key=lambda r:(-r['killed'],r['class']));chosen=candidates[0]
        assert chosen['class']==row['targetClass'],(row['subject'],chosen)
        row.update(selectedKilledCount=chosen['killed'],selectedRecordCount=chosen['total'],candidateCounts=candidates)
    selection.update(frozenAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputArchiveSha256=EXPECTED_ZIP)
    write(PACKAGE/'evidence/pit_replay/selection.json',selection)
    write(OUT/'package_input_changes.json',{'changedPitSubjects':['jgrapht','spring-core'],'selectionFrozenBeforeReplay':selection,'canonicalInputs':'analysis/projects_v17.json'})
    print('Package input and replay-selection update completed')
if __name__=='__main__':main()
