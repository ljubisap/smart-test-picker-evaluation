"""Numeric claim comparison, without editing or exporting the manuscript itself."""
import collections,csv,hashlib,json,math,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from derive import ROOT,ITER,read,write
PAPER=Path('/Users/D061177/Downloads/RAD1_v15_final.docx')
def generate():
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};doc=ET.fromstring(zipfile.ZipFile(PAPER).read('word/document.xml'))
 text=lambda e:''.join(x.text or '' for x in e.findall('.//w:t',ns))
 tables=[[[text(c) for c in r.findall('w:tc',ns)] for r in t.findall('w:tr',ns)] for t in doc.findall('.//w:body/w:tbl',ns)]
 paras=[text(p) for p in doc.findall('.//w:body/w:p',ns)]
 old=read(ROOT/'results/v14_6-summary-tables.json');new=read(ITER/'results/summary_tables.json');matrix=read(ITER/'results/matrix_inventory.json')
 rec=read(ITER/'results/per_record_outcomes.json.gz')['records'];tax=read(ITER/'results/residual_taxonomy.json');ci=read(ITER/'results/confidence_intervals.json');random=read(ITER/'results/random_baseline.json')
 repeat=read(ITER/'results/springcore_run2_sensitivity.json');worked=read(ITER/'results/worked_example.json');example=worked['eligibleExamples'][0] if len(worked['eligibleExamples'])==1 else {}
 succeed=read(ITER/'results/succeeding_tests_check.json');failed=read(ITER/'results/failed_killer_impact.json');java=read(ITER/'results/java_comparison.json');rows=[]
 def add(location,current,unified,source,meaning=None):
  rows.append({'location':location,'currentValue':current,'unifiedValue':unified,'changed':current!=unified,'source':source,**({'interpretation':meaning} if meaning else {})})
 names=list(old['projects']);sp='iterations/pit-unify/results/summary_tables.json';ip='iterations/pit-unify/results/matrix_inventory.json'
 table1={}
 for i,n in enumerate(names,1):
  p=new['projects'][n];base=p['policies']['base'];cl=p['policies']['class'];co=p['policies']['constructor']
  targets=len(read(ROOT/n/'config/sample_classes.json')['classes'])
  if n=='petclinic':
   # Whole-project population, not the contributing-class sample file.
   methodology=(ROOT/'petclinic/docs/METHODOLOGY.md').read_text();match=re.search(r'\*\*(\d+) classes\*\* received mutations',methodology);assert match
   targets=int(match.group(1))
  counts=[p['logicalTests'],targets,len({r['mutatedClass'] for r in rec if r['project']==n}),matrix[n]['mutations'],base['eligible']]
  table1[n]=dict(zip(('logicalTests','targetedClasses','killedContributingClasses','pitMutations','eligibleKilled'),counts))
  for col,(field,value) in enumerate(table1[n].items(),1):add(f'Table I/{n}/{field}',int(tables[0][i][col].rstrip('*').replace(',','')),value,sp if col in (1,5) else f'{n}/config/sample_classes.json' if col==2 and n!='petclinic' else 'petclinic/docs/METHODOLOGY.md' if col==2 else ip)
  vals=[f"{base['eligible']:,}",f"{base['inclusive']:,}",f"{base['inclusivenessPctFullPrecision']:.2f}%",f"{base['meanSelectedFullPrecision']:.2f}",f"{base['selectedFractionPctFullPrecision']:.2f}%"]
  for col,value in enumerate(vals,1):add(f'Table III/{n}/{tables[2][0][col]}',tables[2][i][col],value,sp+'#/projects/'+n+'/policies/base')
  vals=[f"{random[n]['analyticalPctFullPrecision']:.2f}%",f"{cl['inclusivenessPctFullPrecision']:.2f}%",f"{cl['meanSelectedFullPrecision']:.2f}",f"{co['inclusivenessPctFullPrecision']:.2f}%",f"{co['meanSelectedFullPrecision']:.2f}"]
  for col,value in enumerate(vals,1):add(f'Table IV/{n}/{tables[3][0][col]}',tables[3][i][col],value,'iterations/pit-unify/results/random_baseline.json' if col==1 else sp+'#/projects/'+n+'/policies')
 ag=new['aggregate'];b=ag['base'];c=ag['constructor'];g=ag['class']
 for col,value in enumerate([f"{b['eligible']:,}",f"{b['inclusive']:,}",f"{b['inclusivenessPctFullPrecision']:.2f}%",'—','—'],1):add(f'Table III/micro aggregate/{col}',tables[2][-1][col],value,sp+'#/aggregate/base')
 for i,row in enumerate(tables[1][1:],1):
  for col,value in enumerate(row[1:],1):add(f'Table II/row {i}/column {col}',value,value,'analysis/v14_7/provenance_v14_6.csv','Collection evidence unchanged; no map was recollected.')
 add('Table V/name-level hits',int(re.search(r'\d+',tables[4][5][1]).group()),example.get('nameLevelHitCount'),'iterations/pit-unify/results/worked_example.json')
 add('Table V/selection/H/U',[int(x) for x in re.findall(r'\d+',tables[4][6][1])],[example.get('baseSelectedCount'),example.get('nameLevelHitCount'),example.get('emptyFootprintCount')],'iterations/pit-unify/results/worked_example.json')
 oldexample=read(ROOT/'analysis/v14_7/worked_example_v14_6.json')
 for field in ('killingTests','footprintType','baseInclusive','constructorRecovers'):add('Table V/'+field,oldexample[field],example.get(field),'iterations/pit-unify/results/worked_example.json')
 write(ITER/'results/table_i_counts.json',table1)
 def claim(location,paragraph,pattern,unified,source,convert=float):
  m=re.search(pattern,paras[paragraph],re.I);current=convert(m.group(1).replace(',','')) if m else 'NOT_FOUND'
  add(location,current,unified,source);rows[-1]['paragraphIndex']=paragraph
 def factual(location,current,unified,source):add(location,current,unified,source)
 residual=len(tax['residualMisses']);causes=tax['residualCausalMechanismCounts'];recovered=len(tax['recoveredByNoCoverage']);ctor=c['inclusive']-b['inclusive']
 # Repeated claims are listed by every manuscript location, not just once globally.
 for p,label in ((4,'Abstract'),(108,'X')):
  claim(label+'/eligible',p,r'([\d,]+) eligible KILLED',b['eligible'],sp)
  claim(label+'/inclusive',p,r'(?:for |for|includes a reported killing test for )([\d,]+)(?: records| of)',b['inclusive'],sp)
  claim(label+'/inclusiveness',p,r'\(([\d.]+)%\)',b['inclusivenessPct2dp'],sp)
  for what,pattern,value in [('residual',r'(Nineteen)',residual),('early-exception',r'(eighteen)',causes.get('EARLY_EXCEPTION_PROBE_SHADOWING',0)),('attribution',r'(one) retains',causes.get('PRE_TEST_ATTRIBUTION_GAP',0)),('empty recovered',r'(five) further',recovered)]:
   m=re.search(pattern,paras[p],re.I);add(label+'/'+what,m.group(1).lower() if m else 'NOT_FOUND',value,'iterations/pit-unify/results/residual_taxonomy.json','Spelled quantity compared numerically in numericEquivalent below.')
 fractions=[p['policies']['base']['selectedFractionPctFullPrecision'] for p in new['projects'].values()]
 claim('Abstract/min selected fraction',4,r'fractions from ([\d.]+)%',round(min(fractions),2),sp);claim('Abstract/max selected fraction',4,r'to ([\d.]+)%',round(max(fractions),2),sp)
 claim('III/empty total',40,r'contain ([\d,]+) structural',sum(p['emptyFootprintTests'] for p in new['projects'].values()),sp)
 for n in names:factual('III/empty/'+n,old['projects'][n]['emptyFootprintTests'],new['projects'][n]['emptyFootprintTests'],sp)
 claim('III/random trials',43,r'uses ([\d,]+) Monte Carlo',next(iter(random.values()))['trials'],'iterations/pit-unify/results/random_baseline.json')
 claim('III/random seed',43,r'\(seed (\d+)',next(iter(random.values()))['seed'],'iterations/pit-unify/results/random_baseline.json')
 claim('III/random upper rounding',43,r'at most ([\d.]+) percentage',math.ceil(max(v['absoluteDifferencePercentagePoints'] for v in random.values())*1000)/1000,'iterations/pit-unify/results/random_baseline.json')
 for kind,pattern in [('regular_method',r'identifies ([\d,]+) regular-named'),('constructor',r'([\d,]+) constructor records'),('lambda',r'([\d,]+) lambda-named records'),('class_initializer',r'and (\d+) class-initializer')]:claim('IV/method kinds/'+kind,53,pattern,new['methodKinds']['counts'].get(kind,0),sp+'#/methodKinds')
 for kind in ('constructor','lambda'):factual('IV/IX '+kind+' inclusive',sum(r['base']['inclusive'] for r in read(ROOT/'results/v14_6-per-record-outcomes.json')['records'] if (r['mutatedMethod']=='<init>' if kind=='constructor' else r['mutatedMethod'].startswith('lambda$'))),sum(r['base']['inclusive'] for r in rec if (r['mutatedMethod']=='<init>' if kind=='constructor' else r['mutatedMethod'].startswith('lambda$'))),'iterations/pit-unify/results/per_record_outcomes.json.gz')
 claim('IV/Java inputs',59,r'for ([\d,]+) unique',java['uniqueInvocations'],'iterations/pit-unify/results/java_comparison.json');claim('IV/Java occurrences',59,r'all ([\d,]+) eligible',java['weightedOccurrences'],'iterations/pit-unify/results/java_comparison.json')
 for policy in ('base','constructor','class'):
  for field in ('eligible','inclusive','inclusivenessPct2dp'):factual('V/X '+policy+'/'+field,old['aggregate'][policy][field],ag[policy][field],sp)
 factual('III/V/VII/X constructor recoveries',old['aggregate']['constructor']['inclusive']-old['aggregate']['base']['inclusive'],ctor,sp)
 factual('V class recoveries',old['aggregate']['class']['inclusive']-old['aggregate']['base']['inclusive'],g['inclusive']-b['inclusive'],sp)
 factual('V constructor residual',old['aggregate']['constructor']['eligible']-old['aggregate']['constructor']['inclusive'],c['eligible']-c['inclusive'],sp)
 factual('V class residual',old['aggregate']['class']['eligible']-old['aggregate']['class']['inclusive'],g['eligible']-g['inclusive'],sp)
 for n in ('spring-core','quarkus','spring-security'):
  for policy in ('base','constructor','class'):factual('V mean/'+n+'/'+policy,old['projects'][n]['policies'][policy]['meanSelected2dp'],new['projects'][n]['policies'][policy]['meanSelected2dp'],sp)
 for typ,p in [('A',72),('B',73),('C',74),('MIXED',75)]:claim('VI footprint/'+typ,p,r'\((\d+)',tax['residualFootprintCounts'].get(typ,0),'iterations/pit-unify/results/residual_taxonomy.json')
 oldtax=read(ROOT/'results/v14_6-residual-taxonomy.json')
 for n in names:
  for typ in ('A','B','C','MIXED'):factual('VI subject footprint/'+n+'/'+typ,sum(r['project']==n and r['footprintType']==typ for r in oldtax['residualMisses']),sum(r['project']==n and r['footprintType']==typ for r in tax['residualMisses']),'iterations/pit-unify/results/residual_taxonomy.json')
 for typ in ('A','B','C','MIXED'):factual('VI early-exception footprint/'+typ,sum(r['footprintType']==typ and r['causalMechanism']=='EARLY_EXCEPTION_PROBE_SHADOWING' for r in oldtax['residualMisses']),sum(r['footprintType']==typ and r['causalMechanism']=='EARLY_EXCEPTION_PROBE_SHADOWING' for r in tax['residualMisses']),'iterations/pit-unify/results/residual_taxonomy.json')
 oldfail=read(ROOT/'analysis/v14_9/failed_killer_impact.json');factual('IV/VI collection-failing killer records',oldfail['summary']['affectedRecords'],failed['summary']['affectedRecords'],'iterations/pit-unify/results/failed_killer_impact.json')
 for policy in ('base','constructor','class'):factual('IV/VI records with another selected killer/'+policy,sum(r['policies'][policy]['anotherKillerSelected'] for r in oldfail['records']),sum(r['policies'][policy]['anotherKillerSelected'] for r in failed['records']),'iterations/pit-unify/results/failed_killer_impact.json')
 oldrep=read(ROOT/'analysis/v14_7/springcore_run2_sensitivity.json')
 for policy in ('base','constructor','class'):
  factual('Abstract/VI/IX repeat differing sets/'+policy,oldrep['selectedSetDifferences'][policy],repeat['selectedSetDifferences'].get(policy,0),'iterations/pit-unify/results/springcore_run2_sensitivity.json')
  for field in ('inclusive','meanSelected'):factual('VI repeat run2/'+policy+'/'+field,oldrep['run2']['policies'][policy][field],repeat['policies'][policy][field],'iterations/pit-unify/results/springcore_run2_sensitivity.json')
 factual('VI repeat denominator',oldrep['commonEligibleRecords'],repeat['eligible'],'iterations/pit-unify/results/springcore_run2_sensitivity.json')
 factual('VI/IX repeat residual count',len(oldrep['run2']['residualMisses']),len(repeat['residualMisses']),'iterations/pit-unify/results/springcore_run2_sensitivity.json')
 oldsuc=read(ROOT/'analysis/v15/succeeding_tests_check.json');ms=[r for r in oldsuc['records'] if r['cohort']=='RESIDUAL_MISS'];nsuc=[r for r in succeed['records'] if r['cohort']=='RESIDUAL_MISS']
 for label,field in [('selected total','selectedCount'),('survived','selectedSurvivingTests'),('not observed','selectedNotExecutedByPit')]:factual('IX/'+label,sum(r[field] if isinstance(r[field],int) else len(r[field]) for r in ms),sum(r[field] if isinstance(r[field],int) else len(r[field]) for r in nsuc),'iterations/pit-unify/results/succeeding_tests_check.json')
 oldci=read(ROOT/'results/v14_6-confidence-intervals.json')['aggregate']['base'];nc=ci['aggregate']['base']
 for key in ('wilson95Pct','clusterBootstrap95Pct'):factual('IX/'+key,oldci[key],nc[key],'iterations/pit-unify/results/confidence_intervals.json')
 # Facts unaffected by PIT replay, with their independent retained evidence.
 for loc,pattern,p,source in [('Abstract/VI/IX repeat footprints',r'(262)',4,'recollection_2e0954/spring-core/run_to_run.json'),('VI repeat population',r'of ([\d,]+) logical-test',89,'analysis/projects_v14_6.json'),('IV historical model counts',r'(4,010/4,010)',58,'results/selector_equivalence.json'),('IV historical inclusive',r'(3,986)',58,'results/eight-subject-summary.json'),('IV historical misses',r'(24) misses',58,'results/eight-subject-summary.json'),('IV contract',r'(21/21)',60,'results/contract_test.json'),('VIII Joda results',r'(896/896)',100,'joda-time/results/aggregated/evaluation_summary.json'),('VIII Joda population',r'(4,235)',100,'joda-time/results/aggregated/evaluation_summary.json'),('VIII stream results',r'(419/419)',100,'lightweight-stream-api/results/aggregated/evaluation_summary.json'),('VIII stream scope',r'(1,318)',100,'lightweight-stream-api/results/aggregated/evaluation_summary.json')]:
  m=re.search(pattern,paras[p]);v=m.group(1) if m else 'NOT_FOUND';add(loc,v,v,source,'Unchanged retained evidence; not rerun or pooled into this iteration.')
 # Remaining numerical collection, configuration, diagnostic and repeated claims.
 gates=read(ROOT/'recollection_2e0954/gate_results_v14_6.json')['subjects']
 for n in names[:4]:factual('III omitted empty identities/'+n,len(gates[n]['addedIdentities']),len(gates[n]['addedIdentities']),'recollection_2e0954/gate_results_v14_6.json')
 for policy in ('base','constructor','class'):
  factual('VI repeat run1/'+policy+'/inclusive',old['projects']['spring-core']['policies'][policy]['inclusive'],new['projects']['spring-core']['policies'][policy]['inclusive'],sp)
  factual('VI repeat run1/'+policy+'/mean',old['projects']['spring-core']['policies'][policy]['meanSelected2dp'],new['projects']['spring-core']['policies'][policy]['meanSelected2dp'],sp)
 factual('VI Flink + Quarkus eligible',sum(old['projects'][n]['policies']['base']['eligible'] for n in ('flink','quarkus')),sum(new['projects'][n]['policies']['base']['eligible'] for n in ('flink','quarkus')),sp)
 for n in names:
  oldlocal=[r for r in read(ROOT/'results/v14_6-per-record-outcomes.json')['records'] if r['project']==n];local=[r for r in rec if r['project']==n]
  factual('V policy added tests/'+n,old['projects'][n]['emptyFootprintTests'],new['projects'][n]['emptyFootprintTests'],sp)
  if n=='spring-security':
   factual('V edge-only mean/'+n,round(sum(r['legacy']['selectedCount'] for r in oldlocal)/len(oldlocal),2),round(sum(r['legacy']['selectedCount'] for r in local)/len(local),2),'iterations/pit-unify/results/per_record_outcomes.json.gz')
   factual('V edge-only inclusive/'+n,sum(r['legacy']['inclusive'] for r in oldlocal),sum(r['legacy']['inclusive'] for r in local),'iterations/pit-unify/results/per_record_outcomes.json.gz')
 oldkeys={e['coverageKey'] for r in oldtax['recoveredByNoCoverage'] for k in r['killingTests'] for e in k['resolvedEntries']};newkeys={k for r in tax['recoveredByNoCoverage'] for k in r['killingTests']}
 factual('VI distinct empty killers',len(oldkeys),len(newkeys),'iterations/pit-unify/results/residual_taxonomy.json')
 for field in ('baseSelectedCount','nameLevelHitCount','emptyFootprintCount','footprintType','constructorRecovers'):factual('VI worked example/'+field,oldexample[field],example.get(field),'iterations/pit-unify/results/worked_example.json')
 for p,pattern,source in [(52,r'(1\.17\.4)','jgrapht/scripts/02_run_pit.py; spring-core/scripts/02_run_pit.py'),(52,r'(1\.2\.1)','jgrapht/config/pit_profile.xml; spring-core/scripts/02_run_pit.py'),(54,r'(56)','recollection_2e0954/gate_results_v14_6.json'),(54,r'(52)','recollection_2e0954/gate_results_v14_6.json'),(56,r'(25)','spring-security/results/jdk25-blocked.json'),(56,r'major-version-(69)','spring-security/results/jdk25-blocked.json'),(56,r'(572) exact','quarkus/config/runnable-test-inventory.json'),(56,r'(684) invocations','quarkus/results/pit-resolution.json'),(101,r'(110) affected','lightweight-stream-api/PRODUCTION_FILTER_FIX_VALIDATION.md'),(100,r'(1,428)','lightweight-stream-api/REPORT.md'),(103,r'(262) logical','recollection_2e0954/spring-core/run_to_run.json')]:
  m=re.search(pattern,paras[p]);v=m.group(1) if m else 'NOT_FOUND';add(f'Paragraph {p}/retained fact/{pattern}',v,v,source,'Unchanged configuration or previously retained observation, not a new measurement.')
 tests=(ITER/'verification/current/unittest.log').read_text();match=re.search(r'Ran (\d+) tests',tests)
 claim('IV analysis regression tests',58,r'passes all (\d+) tests',int(match.group(1)) if match else None,'iterations/pit-unify/verification/current/unittest.log')
 factual('IX Java mismatches',read(ROOT/'results/v14_6-java-comparison.json')['mismatches'],java['mismatches'],'iterations/pit-unify/results/java_comparison.json')
 for p,label in ((4,'Abstract'),(109,'X')):
  if p==4:claim(label+'/constructor inclusiveness',p,r'raising inclusiveness to ([\d.]+)%',c['inclusivenessPct2dp'],sp)
 words={'one':1,'five':5,'eighteen':18,'nineteen':19}
 for row in rows:
  val=words.get(str(row['currentValue']).lower(),row['currentValue']);row['numericEquivalent']=val;row['changed']=val!=row['unifiedValue']
 # Full numeric occurrence inventory, without publishing full manuscript paragraphs.
 inventory=[]
 for i,t in enumerate(paras[:110]):
  if i not in (4,) and not 34<=i<=109:continue
  for m in re.finditer(r'(?<![\w])\d[\d,.]*(?:%)?',t):
   token=m.group();inventory.append({'paragraphIndex':i,'token':token,'offset':m.start(),'classification':'CITATION_OR_SECTION_REFERENCE' if (m.start()>0 and t[m.start()-1]=='[') or re.match(r'^\d+(\.\d+)?\.?\s',t) else 'NUMERIC_OCCURRENCE','note':'Quantitative claims are enumerated above; tool versions, source identifiers and retained collection/supplementary facts are unchanged.'})
 out={'manuscriptFilename':PAPER.name,'manuscriptSha256':hashlib.sha256(PAPER.read_bytes()).hexdigest(),'claims':rows,'numericOccurrenceInventory':inventory,'unmatchedClaimPatterns':[r['location'] for r in rows if r['currentValue']=='NOT_FOUND']}
 write(ITER/'manuscript_comparison.json',out)
 lines=['# Manuscript numerical comparison','','The manuscript is read-only. No manuscript file is included in this branch. Current values are extracted from the final DOCX or its cited current artifacts; unified values are derived from iteration outputs. Historical observations are not retroactively relabeled as new runs.','','| Location | Current | Unified | Changed | Source |','|---|---|---|---|---|']
 for r in rows:lines.append('| '+r['location']+' | '+str(r['currentValue']).replace('|','/')+' | '+str(r['unifiedValue']).replace('|','/')+' | '+str(r['changed'])+' | '+r['source']+' |')
 (ITER/'MANUSCRIPT_COMPARISON.md').write_text('\n'.join(lines)+'\n')
 return out
if __name__=='__main__':generate()
