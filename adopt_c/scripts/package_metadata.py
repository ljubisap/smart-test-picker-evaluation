"""Update only supporting metadata; do not rewrite identities or footprints."""
import re
from common import *
def neutral(value):
    if isinstance(value,dict):return {k:neutral(v) for k,v in value.items()}
    if isinstance(value,list):return [neutral(v) for v in value]
    if not isinstance(value,str):return value
    value=value.replace('analysis/v14_4_rederivation/java_build.json','recorded isolated selector build (external execution evidence)')
    value=value.replace('/tmp/TOOL-b2-R2/','<BUILD>/')
    value=value.replace('7a61a4933a7f2b6a64aa06e4893ba61c9d26da33','R2-tree')
    value=re.sub(r'analysis/v14_[^/]+/[^\s";]*','evidence/java_replay/',value)
    return value
def main():
    for p in (PACKAGE/'evidence/java_replay').glob('*.json'):write(p,neutral(read(p)))
    scope=read(PACKAGE/'evidence/verification_scope.json');old=read(ROOT/'results/eight-subject-summary.json')['aggregateCompletedSubjectsOnly']
    scope['recordedModelComparison'].update(inclusive=old['stpInclusive'],misses=old['falseNegatives'])
    write(PACKAGE/'evidence/verification_scope.json',scope)
    metrics=read(ROOT/'results/v17-publication-metrics.json');metrics['sources']=['results/summary.json','results/per_record.json','results/taxonomy.json','results/random_baseline.json']
    write(PACKAGE/'evidence/mutator_concentration.json',metrics)
    write(OUT/'provenance_review.json',{
      'replacementRuns':'Established by C execution transcripts, runtime artifact hashes and matrix inventories: PIT 1.17.4, junit5 plugin 1.2.1, explicit named DEFAULTS, no processor override.',
      'implicitVersusNamed':'PIT bytecode disassembly in iterations/pit-unify/pit-default-resolution/ distinguishes no-option internal default (NEGATE_CONDITIONALS) from named DEFAULTS (REMOVE_CONDITIONALS).',
      'springOriginalOmission':'Directly established by spring-core/scripts/02_run_pit.py command list; no --mutators option.',
      'jgraphtOriginalOmission':'UNKNOWN. jgrapht/scripts/02_run_pit.py has no -Dmutators override, but jgrapht/config/pit_profile.xml (including its first retained revision c77bb2f) explicitly declares DEFAULTS. Original effective POM was not retained. Matrices and stdout prove the actual operator set, not why the option was absent/ineffective.',
      'manuscriptResolution':'Do not assert original JGraphT option omission as directly proven. State measured operator set and provenance limitation.',
      'otherSix':'Unchanged matrices and replay evidence. Configuration is not proof of original installed versions. PetClinic original PIT/plugin version remains UNKNOWN.'})
    print('PASS: metadata routed; model observation separated; provenance limitation explicit')
if __name__=='__main__':main()
