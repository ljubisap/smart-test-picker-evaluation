"""Materialize the individually reviewed source/control-flow conclusions.

These explicit case notes are analysis inputs, not a classifier based on footprint.
Unknown cases are deliberately left unclassified. No runtime trace is claimed.
"""
import collections
from derive import ROOT,ITER,read,write,load_coverage_map

NOTES={
 ('ChristofidesThreeHalvesApproxMetricTSP','getTour',97):
  'Both reported killers invoke getTour inside assertThrows(IllegalArgumentException): one supplies a directed graph and the other an incomplete undirected graph. The first operation is checkGraph (javap offset 2), whose requireUndirected/completeness guards throw before getTour reaches its normal body. PIT removes that guard call. The frozen footprints contain only the target constructor. The source path and missing method edge support exceptional-exit probe shadowing; this is not engine-preparation activity.',
 ('TypeDescriptor','upcast',235):
  'upCastNotSuper constructs a Map-valued descriptor, requests Collection as its supertype, and asserts IllegalArgumentException with the assignability message. upcast calls getType and then Assert.isAssignable (javap offset 11), before constructing a result. The pristine guard throws. The killer records the constructor and getType but no upcast edge. PIT removes the assignability check; the exception contract is mutation-sensitive. The disjoint footprint is explained by exit through the callee before downstream attribution, not by lack of entry to upcast.',
 ('GenericConversionService','canConvert',133):
  'Both killers call the Class overload with a null target and assert IllegalArgumentException. Its first statement is Assert.notNull(targetType); the source and bytecode place this before delegation. The removed void call is this guard. The target-class footprint is constructor-only although the test body directly invokes canConvert. This supports early exceptional exit before the method execution is recorded.',
 ('GenericConversionService','canConvert',140):
  'Both killers call the TypeDescriptor overload with a null target and assert IllegalArgumentException. Assert.notNull is the first statement, before getConverter/return. PIT removes that call. The tests instantiate the service and then invoke this overload; constructor-only footprints omit the exceptional call. Source/control-flow evidence supports early exceptional exit rather than a pre-test attribution gap.',
 ('GenericConversionService','convert',164):
  'convertToNullTargetClass invokes convert("3", (Class<?>) null) inside an IllegalArgumentException assertion. Assert.notNull(targetType) precedes delegation and is the void call PIT removes. The constructor is recorded but convert is absent. The exceptional guard path is executed within the test body, supporting probe-shadowed early exit.',
 ('GenericConversionService','convert',171):
  'convertToNullTargetTypeDescriptor invokes the three-argument convert with a null target descriptor. The first Assert.notNull throws before the conversion branches. PIT removes that call and reports this exception-contract test as killer. Its only target-class edge is the constructor; the evidence supports exceptional exit before method attribution.',
 ('SimpleAsyncTaskExecutor','execute',264):
  'The killer calls execute(null) in a try-with-resources block and asserts IllegalArgumentException. The one-argument overload delegates to execute(Runnable,long), whose first call is Assert.notNull(task). PIT removes that call. Other target-class methods (including lifecycle work) are present, but the name-level execute edge is absent. The critical activity is a synchronous guard inside the leaf test, before task submission; this is not evidence of an asynchronous attribution gap.',
 ('Assert','isAssignable',539):
  'isAssignableWithNullSupertype supplies a null superType to the String-message overload and asserts IllegalArgumentException plus the guard message. The first notNull call throws; PIT removes it before the subsequent superType dereference. Assert.notNull is recorded but the isAssignable name-level edge is absent. This is an in-class callee guard with exceptional exit from the caller, not a missing class or session.',
 ('Assert','isAssignable',558):
  'isAssignableWithNullSupertypeAndMessageSupplier supplies null to the Supplier overload and checks IllegalArgumentException and its message. The initial notNull(superType) is the removed void call. The target class has other recorded methods, including the guard, but no isAssignable edge. The caller exits exceptionally before downstream attribution.',
 ('Assert','isInstanceOf',490):
  'isInstanceOfWithNullType passes a null type to the String-message overload and checks IllegalArgumentException plus the guard message. Initial notNull(type) throws before type.isInstance; PIT removes that call. Other Assert edges are present but isInstanceOf is absent, supporting the same caller-probe exceptional-exit mechanism.',
 ('Assert','isInstanceOf',509):
  'isInstanceOfWithNullTypeAndMessageSupplier calls the Supplier overload with null type and asserts the guard exception/message. Initial notNull(type) throws before type.isInstance. Removing that call kills the test. The in-class footprint is nonempty and disjoint from isInstanceOf, consistent with caller attribution lost at the exceptional guard.',
 ('ExponentialBackOff','setMultiplier',141):
  'invalidInterval constructs the backoff and calls setMultiplier(0.9), expecting IllegalArgumentException. setMultiplier first invokes checkMultiplier (javap offset 2), which rejects values below one through Assert.isTrue, before field assignment. PIT removes checkMultiplier. The guard/constructor footprint is present but setMultiplier is absent. This is a test-body exceptional guard path, not pre-test preparation.'
}

def main():
 evidence={r['mutationId']:r for r in read(ITER/'causal_source_evidence.json')}
 outcomes=read(ITER/'results/per_record_outcomes.json.gz');rows={r['mutationId']:r for r in outcomes['records']}
 config={p['name']:p for p in read(ITER/'projects_unified.json')['projects']};maps={};reviews={}
 for annotation in read(ITER/'results/residual_taxonomy.json')['residualMisses']:
  mid=annotation['mutationId'];r=rows[mid];key=(r['mutatedClass'].rsplit('.',1)[-1],r['mutatedMethod'],r['line'])
  if r['project'] not in ('jgrapht','spring-core') or key not in NOTES:continue
  assert r['mutator'].endswith('VoidMethodCallMutator')
  e=evidence[mid];assert e['production'] and e['killingTestExcerpts'] and e['bytecode']['exitCode']==0
  assert set(r['killingTests'])=={t['coverageKey'] for t in e['killingTestExcerpts']}
  mapping=maps.setdefault(r['project'],load_coverage_map(ROOT/config[r['project']]['coverageMap'])['testMappings'])
  H={k for k,v in mapping.items() if r['mutatedClass']+'#'+r['mutatedMethod'] in (v.get('methods') or [])}
  U={k for k,v in mapping.items() if not(v.get('classes') or []) and not(v.get('methods') or [])}
  reviews[mid]={'causalMechanism':'EARLY_EXCEPTION_PROBE_SHADOWING','causalEvidence':NOTES[key],
   'annotationStatus':'SOURCE_CONTROL_FLOW_REVIEWED','annotationSource':'iterations/pit-unify/causal_source_evidence.json',
   'guardSource':'iterations/pit-unify/causal_guard_evidence.json','bytecodeEvidence':e['bytecode']['output'],
   'evidenceBoundary':'Pristine source and bytecode, frozen per-test footprints and newly executed PIT matrix; no new method-entry/probe trace or isolated-mutant experiment.',
   'selectionExplanation':{'nameLevelHits':len(H),'emptyEntries':len(U),'killersInU':sorted(set(r['killingTests'])&U),'classEscalationUsed':not bool(H),'baseSelectedCount':r['base']['selectedCount'],
     'reason':'Nonempty method-hit set prevents class escalation; none of these nonempty-footprint killing tests enters through U.' if H else 'Class escalation inspected; see full selected set.'}}
 write(ITER/'causal_review.json',reviews)
 # Refresh annotation-bearing outputs only. The verifier re-derives all of them
 # independently; numerical policy results and selected sets are not rewritten.
 path=ITER/'results/residual_taxonomy.json';tax=read(path)
 for r in tax['residualMisses']+tax['recoveredByNoCoverage']:
  if r['mutationId'] in reviews:r.update(reviews[r['mutationId']])
 tax['residualCausalMechanismCounts']=dict(collections.Counter(r['causalMechanism'] for r in tax['residualMisses']))
 write(path,tax)
 path=ITER/'results/failure_annotations_unified.json';annotations=read(path)
 for r in annotations:
  if r['mutationId'] in reviews:r.update(reviews[r['mutationId']])
 write(path,annotations)
 print('Recorded source/control-flow reviews:',len(reviews))
if __name__=='__main__':main()
