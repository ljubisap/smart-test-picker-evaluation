"""Re-derive adopted results with unchanged C computation and explicit v17 inputs.

Recorded Java execution is evidence, not a new execution claim. Selected sets,
occurrence weights and loader-comparison summaries are recomputed against it.
"""
import collections,importlib.util,json,re,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
C=ROOT/'iterations/pit-unify/cpu-unrestricted'
sys.path.insert(0,str(C/'scripts'))
import derive_c
from environment import read,write,sha

def generate(destination):
    d=derive_c.derive; original_read=d.read
    def inputs(path):
        if path==C/'projects_unified.json':path=ROOT/'analysis/projects_v17.json'
        if path==C/'causal_review.json':path=ROOT/'analysis/failure_annotations_v17.json'
        return original_read(path)
    d.read=inputs
    try:outputs=derive_c.generate(destination)
    finally:d.read=original_read
    # Recompute the production-Java comparison from new Python sets and retained
    # actual execution outputs. No result JSON is used as the expected selector.
    spec=importlib.util.spec_from_file_location('v17_java_comparison',ROOT/'iterations/pit-unify/scripts/java_replay.py')
    j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
    with tempfile.TemporaryDirectory(prefix='java-',dir=destination.parent) as tmp:
        t=Path(tmp);j.ITER=t;j.OUT=t/'java'
        write(t/'projects_unified.json',read(ROOT/'analysis/projects_v17.json'))
        d.write(t/'results/per_record_outcomes.json.gz',outputs['per_record_outcomes.json.gz'])
        j.prepare()
        fresh_cases=read(j.OUT/'cases.json');recorded_cases=read(C/'java/cases.json')
        # Absolute checkout roots are provenance, not selector inputs. Verify
        # actual map bytes before disregarding only this relocatable path.
        for current,recorded in zip(fresh_cases['maps'],recorded_cases['maps']):
            assert sha(Path(current['path']))==current['mapSha256']==recorded['mapSha256']
            assert {k:v for k,v in current.items() if k!='path'}=={k:v for k,v in recorded.items() if k!='path'},'Java replay inputs differ'
        assert len(fresh_cases['maps'])==len(recorded_cases['maps'])
        for name in ('output.json','runtime.json'):shutil.copyfile(C/'java'/name,j.OUT/name)
        j.finalize()
        for name in ('java_comparison.json','loader_content_equality.json'):
            outputs[name]=read(t/'results'/name);write(destination/name,outputs[name])
    table={}
    for name,metrics in outputs['summary_tables.json']['projects'].items():
        rows=[r for r in outputs['per_record_outcomes.json.gz']['records'] if r['project']==name]
        target=len(read(ROOT/name/'config/sample_classes.json')['classes'])
        if name=='petclinic':target=int(re.search(r'\*\*(\d+) classes\*\* received mutations',(ROOT/name/'docs/METHODOLOGY.md').read_text()).group(1))
        table[name]={'logicalTests':metrics['logicalTests'],'targetedClasses':target,'killedContributingClasses':len({r['mutatedClass'] for r in rows}),'pitMutations':outputs['matrix_inventory.json'][name]['mutations'],'eligibleKilled':len(rows)}
    outputs['table_i_counts.json']=table;write(destination/'table_i_counts.json',table)
    return outputs

def canonical_name(name):return 'v17-'+name.replace('_','-')

def main():
    out=ROOT/'adopt_c';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='derive-',dir=out) as tmp:
        t=Path(tmp);outputs=generate(t);rows=[]
        for name in outputs:
            # Equality includes provenance strings; C evidence is never rewritten.
            assert derive_c.derive.read(t/name)==derive_c.derive.read(C/'results'/name),name
            target=ROOT/'results'/canonical_name(name)
            shutil.copyfile(t/name,target)
            rows.append({'file':str(target.relative_to(ROOT)),'CSource':str((C/'results'/name).relative_to(ROOT)),'equal':True,'sha256':sha(target),'CSourceSha256':sha(C/'results'/name)})
    kinds=outputs['summary_tables.json']['methodKinds'];write(ROOT/'results/v17-method-kinds.json',kinds)
    write(out/'derivation_equality.json',{'allEqual':True,'files':rows,'methodKinds':kinds,'inputs':'analysis/projects_v17.json','computation':'iterations/pit-unify/scripts/derive.py (unchanged), C routing adapter (unchanged)'})
    print('PASS: independently derived',len(rows),'files equal verified C outputs')
if __name__=='__main__':main()
