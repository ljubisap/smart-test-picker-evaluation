"""Regenerate neutral-package outputs, then compare scientific values to v17."""
import sys
from common import *
sys.dont_write_bytecode=True
sys.path.insert(0,str(PACKAGE))
from evaluator.derive import derive
from evaluator.evidence_checks import failed_impact,succeeding_check
from evaluator.repeat_collection import sensitivity,worked_example
from update_package_inputs import scrub

def main():
    # Correct the retained Java output filename; this is recorded execution evidence.
    write(PACKAGE/'evidence/java_replay/outputs.json',scrub(read(C/'java/output.json')))
    accidental=PACKAGE/'evidence/java_replay/output.json'
    if accidental.exists():accidental.rename(WORK/'duplicate-java-output.json')
    canonical=read(ROOT/'results/v17-per-record-outcomes.json.gz')
    failure=read(PACKAGE/'evidence/springcore_test_outcomes.json')
    for row in failure['failures']:
        keys=set(row['adoptedMap']['matchingKeys'])
        ids=[r['mutationId'] for r in canonical['records'] if r['project']=='spring-core' and keys.intersection(r['killingTests'])]
        row['eligibleMutationIds']=ids;row['eligiblePitKiller']=bool(ids)
    ids=sorted({i for row in failure['failures'] for i in row['eligibleMutationIds']})
    failure.update(eligibleRecordsWithFailingKiller=ids,eligibleRecordsWithFailingKillerCount=len(ids),noneIsEligiblePitKiller=not ids)
    write(PACKAGE/'evidence/springcore_test_outcomes.json',failure)
    values=derive(PACKAGE)
    fresh=values['per_record'];by={r['mutationId']:r for r in canonical['records']}
    assert set(by)=={r['mutationId'] for r in fresh['records']}
    for row in fresh['records']:
        old=by[row['mutationId']]
        assert row['killingTests']==old['killingTests']
        for p in ('base','constructor','class'):
            assert row[p]==old[p],(row['mutationId'],p)
            assert fresh['selectedSets'][row[p]['selectedSetId']]==canonical['selectedSets'][old[p]['selectedSetId']]
    summary=read(ROOT/'results/v17-summary-tables.json')
    assert values['summary']['projects']==summary['projects']
    assert values['summary']['aggregate']==summary['aggregate']
    assert values['intervals']==read(ROOT/'results/v17-confidence-intervals.json')
    assert values['bootstrap_inputs']==read(ROOT/'results/v17-bootstrap-cluster-inputs.json')
    assert values['random_baseline']==read(ROOT/'results/v17-random-baseline.json')
    tax=read(ROOT/'results/v17-residual-taxonomy.json')
    for cohort in ('residualMisses','recoveredByNoCoverage'):
        ref={r['mutationId']:r for r in tax[cohort]}
        assert set(ref)=={r['mutationId'] for r in values['taxonomy'][cohort]}
        for row in values['taxonomy'][cohort]:
            for k in ('footprintType','causalMechanism','recoveredByConstructorRule'):
                assert row[k]==ref[row['mutationId']][k]
    for name,value in values.items():write(PACKAGE/'results'/f'{name}.json',value)
    evidence={'failed_killer_impact':failed_impact(PACKAGE,fresh,values['taxonomy']),
              'succeeding_tests':succeeding_check(PACKAGE,fresh,values['taxonomy']),
              'springcore_run2/sensitivity':sensitivity(),'worked_example':worked_example()}
    for name,value in evidence.items():write(PACKAGE/'evidence'/f'{name}.json',value)
    ref=read(ROOT/'results/v17-worked-example.json')['eligibleExamples'][0]
    for k in evidence['worked_example']:
        if k in ref:assert evidence['worked_example'][k]==ref[k],k
    run2=read(ROOT/'results/v17-springcore-run2-sensitivity.json')
    assert evidence['springcore_run2/sensitivity']['selectedSetDifferences']==run2['selectedSetDifferences']
    write(OUT/'package_derivation.json',{'status':'PASS','eligible':len(fresh['records']),
      'fullSelectedSetsEqual':True,'allPolicyOutcomesEqual':True,'summaryEquality':True,
      'intervalEquality':True,'bootstrapInputEquality':True,'randomEquality':True,
      'taxonomyEquality':True,'outputs':list(values),'evidence':list(evidence)})
    print('PASS: package derived from inputs; full outcomes, sets, statistics and taxonomy equal v17')
if __name__=='__main__':main()
