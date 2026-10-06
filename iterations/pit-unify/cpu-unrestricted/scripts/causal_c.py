"""Transfer annotations only after unambiguous identity and witness comparison."""
import collections
from derive_c import derive
from environment import ROOT,B,OUT,read,write,sha
from pathlib import Path
def key(r):return (r['project'],r['mutatedClass'],r['mutatedMethod'],r['methodDescription'],r['line'],r['mutator'],r.get('description'),tuple(r.get('indexes') or []),tuple(r.get('blocks') or []))
def main():
    before=derive.read(B/'results/per_record_outcomes.json.gz');after=derive.read(OUT/'results/per_record_outcomes.json.gz')
    br={r['mutationId']:r for r in before['records']};cr={r['mutationId']:r for r in after['records']};groups=collections.defaultdict(list)
    for r in br.values():groups[key(r)].append(r)
    annotations={r['mutationId']:r for r in read(B/'results/failure_annotations_unified.json')};reviews={};evidence=[];currentMultiplicity=collections.Counter(key(r) for r in cr.values())
    source_evidence={r['mutationId']:r for r in read(B/'causal_source_evidence.json')};pre=read(OUT/'preflight.json')
    for a in read(OUT/'results/failure_annotations_unified.json'):
        row=cr[a['mutationId']]
        if row['project'] not in ('jgrapht','spring-core'):continue
        candidates=groups[key(row)];status='NO_UNAMBIGUOUS_CORRESPONDENCE'
        if len(candidates)==1 and currentMultiplicity[key(row)]==1:
            b=candidates[0];old=annotations.get(b['mutationId'])
            proof=source_evidence.get(b['mutationId']);checkout=Path(pre['subjects'][row['project']]['checkout'])
            sources_match=bool(proof) and all((checkout/x['path']).is_file() and sha(checkout/x['path'])==x['sha256'] for x in proof['production']+proof['killingTestExcerpts'])
            if old and sources_match and b['killingTests']==row['killingTests'] and old['killerFootprints']==a['killerFootprints']:
                reviews[a['mutationId']]={'causalMechanism':old['causalMechanism'],'causalEvidence':old['causalEvidence'],'annotationStatus':'VERIFIED_CORRESPONDENCE_UNCHANGED_WITNESSES','annotationSource':'iterations/pit-unify/results/failure_annotations_unified.json','sourceMutationId':b['mutationId'],'evidenceBoundary':'Same class/method/descriptor/line/operator/description/index/block tuple, unique eligible correspondence, identical normalized killers and target footprints, same source revision; not proof of identical timing or a new instrumented trace.'}
                status='TRANSFERRED'
        evidence.append({'mutationId':a['mutationId'],'candidateBIds':[r['mutationId'] for r in candidates],'status':status,'sourceHashVerificationRequired':True})
    write(OUT/'causal_review.json',reviews);write(OUT/'causal_correspondence.json',evidence)
    # Same refresh of annotation-bearing views as the B review, no selection changes.
    tax=read(OUT/'results/residual_taxonomy.json')
    for r in tax['residualMisses']+tax['recoveredByNoCoverage']:
        if r['mutationId'] in reviews:r.update(reviews[r['mutationId']])
    tax['residualCausalMechanismCounts']=dict(collections.Counter(r['causalMechanism'] for r in tax['residualMisses']))
    write(OUT/'results/residual_taxonomy.json',tax)
    annotations=read(OUT/'results/failure_annotations_unified.json')
    for r in annotations:
        if r['mutationId'] in reviews:r.update(reviews[r['mutationId']])
    write(OUT/'results/failure_annotations_unified.json',annotations)
    print('Verified transfers:',len(reviews),'not transferred:',sum(r['status']!='TRANSFERRED' for r in evidence))
if __name__=='__main__':main()
