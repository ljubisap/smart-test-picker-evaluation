"""Route the existing iteration calculation to C; policy/statistics unchanged."""
import sys
from environment import ROOT,B,OUT,read,write,sha
sys.path.insert(0,str(B/'scripts'))
import derive
derive.ITER=OUT
def prepare():
    config=read(B/'projects_unified.json')
    for p in config['projects']:
        if p['name'] in ('jgrapht','spring-core'):
            p['pitFiles']=[str((OUT/'pit'/p['name']/'per-class/*/mutations.xml.gz').relative_to(ROOT))]
    write(OUT/'projects_unified.json',config)
    write(OUT/'derivation_sources.json',{'importedCalculation':str((B/'scripts/derive.py').relative_to(ROOT)),'sha256':sha(B/'scripts/derive.py'),'evaluator':'analysis/evaluation_core.py','evaluatorSha256':sha(ROOT/'analysis/evaluation_core.py'),'configurationChange':'Only JGraphT and spring-core PIT patterns point to C; all map and remaining subject inputs unchanged.'})
def generate(destination):
    outputs=derive.generate(destination)
    outputs['summary_tables.json']['methodKinds']['source']=str((OUT/'results/per_record_outcomes.json.gz').relative_to(ROOT))
    write(destination/'summary_tables.json',outputs['summary_tables.json'])
    b=derive.read(B/'results/per_record_outcomes.json.gz');c=outputs['per_record_outcomes.json.gz'];invariance={}
    for subject in outputs['summary_tables.json']['projects']:
        if subject in ('jgrapht','spring-core'):continue
        left={r['mutationId']:r for r in b['records'] if r['project']==subject};right={r['mutationId']:r for r in c['records'] if r['project']==subject};errors=[]
        if set(left)!=set(right):errors.append('Mutation ID set changed')
        for mid in left.keys()&right.keys():
            if left[mid]['killingTests']!=right[mid]['killingTests']:errors.append(mid+': killing set changed')
            for policy in derive.ALL_POLICIES:
                x=left[mid][policy];y=right[mid][policy]
                if x['inclusive']!=y['inclusive'] or b['selectedSets'][x['selectedSetId']]!=c['selectedSets'][y['selectedSetId']]:errors.append(mid+': '+policy+' selection/outcome changed')
        invariance[subject]={'eligible':len(right),'fullSelectedSetsAndKillersIdentical':not errors,'differences':errors}
    outputs['six_subject_invariance.json']=invariance
    write(destination/'six_subject_invariance.json',invariance)
    return outputs
if __name__=='__main__':
    prepare();generate(OUT/'results')
