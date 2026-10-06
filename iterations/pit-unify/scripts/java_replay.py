"""Reuse the committed harness and hash-verified, unchanged pinned selector."""
import gzip,hashlib,importlib.util,json,os,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ITER=ROOT/'iterations/pit-unify';OUT=ITER/'java'
def read(p):return json.loads(gzip.decompress(p.read_bytes()).decode() if p.suffix=='.gz' else p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def list_sha(xs):return hashlib.sha256(b''.join(x.encode()+b'\0' for x in sorted(xs))).hexdigest()
def prepare():
 data=read(ITER/'results/per_record_outcomes.json.gz');by={p['name']:p for p in read(ITER/'projects_unified.json')['projects']};unique={}
 for row in data['records']:
  key=(row['project'],row['mutatedClass'],row['mutatedMethod']);selected=data['selectedSets'][row['base']['selectedSetId']]
  unique.setdefault(key,{'caseId':hashlib.sha256('\0'.join(key).encode()).hexdigest(),'changedClass':key[1],'changedMethod':key[2],'pythonSelected':selected,'occurrences':0})['occurrences']+=1
 maps=[{'project':n,'path':str(ROOT/p['coverageMap']),'mapSha256':sha(ROOT/p['coverageMap']),'cases':[v for k,v in unique.items() if k[0]==n]} for n,p in by.items()]
 write(OUT/'cases.json',{'maps':maps})
def execute():
 build=read(ROOT/'analysis/v14_4_rederivation/java_build.json');artifacts=[build['jar'],*build['runtimeClasspath']]
 verified=[{**a,'actualSha256':sha(Path(a['path']))} for a in artifacts]
 assert all(x['sha256']==x['actualSha256'] for x in verified),'Pinned runtime artifact hash mismatch'
 java=Path('/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home/bin');classes=OUT/'classes';classes.mkdir(parents=True,exist_ok=True)
 cp=os.pathsep.join(a['path'] for a in artifacts);source=ROOT/'analysis/v14_6/harness/SelectorHarness.java'
 commands=[[str(java/'javac'),'-cp',cp,'-d',str(classes),str(source)],[str(java/'java'),'-XX:ActiveProcessorCount=1','-Xmx3g','-cp',str(classes)+os.pathsep+cp,'SelectorHarness',str(OUT/'cases.json'),str(OUT/'output.json')]]
 for index,cmd in enumerate(commands):
  with (OUT/f'command-{index}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 write(OUT/'runtime.json',{'pinnedBuildSource':'analysis/v14_4_rederivation/java_build.json','commit':build['commit'],'tree':build['tree'],'verifiedArtifacts':verified,'harnessSource':str(source.relative_to(ROOT)),'harnessSha256':sha(source),'commands':commands})
def reuse_identical_inputs():
 """A changed PIT matrix cannot change selection for identical (map,C,M) inputs."""
 archive=ITER/'attempts/implicit-defaults.tar.gz'
 if not archive.exists():return False
 with tarfile.open(archive,'r:gz') as tar:
  old_manifest=json.load(tar.extractfile('java/cases.json'));old_output=json.load(tar.extractfile('java/output.json'));runtime=json.load(tar.extractfile('java/runtime.json'))
 current=read(OUT/'cases.json');old_maps={m['project']:m for m in old_manifest['maps']}
 if any(m['mapSha256']!=old_maps[m['project']]['mapSha256'] or sha(Path(m['path']))!=m['mapSha256'] for m in current['maps']):return False
 if runtime['harnessSha256']!=sha(ROOT/runtime['harnessSource']):return False
 if any(sha(Path(a['path']))!=a['sha256'] for a in runtime['verifiedArtifacts']):return False
 desired={c['caseId']:c for m in current['maps'] for c in m['cases']};previous={c['caseId']:c for m in old_manifest['maps'] for c in m['cases']}
 if not set(desired)<=set(previous):return False
 for key,c in desired.items():
  if any(c[f]!=previous[key][f] for f in ('changedClass','changedMethod','pythonSelected')):return False
 selected=[c for c in old_output['cases'] if c['caseId'] in desired]
 assert len(selected)==len(desired)
 write(OUT/'output.json',{**old_output,'cases':selected})
 runtime['reuse']={'archive':str(archive.relative_to(ROOT)),'archiveSha256':sha(archive),'archivedJavaInputs':'java/cases.json','archivedJavaOutputs':'java/output.json','originalExecutedUniqueInputs':len(old_output['cases']),'identicalInputsReused':len(selected),'additionalInvocations':0,'commandsReferToArchivedInputSnapshot':True,'reason':'All final (map digest, class, method) inputs already executed through the unchanged pinned Java selector; only PIT occurrence weighting changed.'}
 write(OUT/'runtime.json',runtime);return True
def finalize():
 manifest=read(OUT/'cases.json');raw=read(OUT/'output.json');specs={c['caseId']:c for m in manifest['maps'] for c in m['cases']};rows=[]
 assert set(specs)=={c['caseId'] for c in raw['cases']}
 for j in raw['cases']:
  p=specs[j['caseId']];py=sorted(p['pythonSelected']);js=sorted(j['selectedTests'])
  rows.append({'caseId':j['caseId'],'project':j['project'],'changedClass':p['changedClass'],'changedMethod':p['changedMethod'],'occurrences':p['occurrences'],'javaMode':j['mode'],'javaReason':j.get('reason'),'javaSelectedTests':js,'pythonSelectedTests':py,'javaSha256':list_sha(js),'pythonSha256':list_sha(py),'javaOnly':sorted(set(js)-set(py)),'pythonOnly':sorted(set(py)-set(js)),'match':js==py and j['mode']=='SELECTED'})
 comparison={'uniqueInvocations':len(rows),'weightedOccurrences':sum(r['occurrences'] for r in rows),'mismatches':sum(not r['match'] for r in rows),'nonSelectedModes':sum(r['javaMode']!='SELECTED' for r in rows),'cases':rows,'testSelectorCodeSource':raw['testSelectorCodeSource'],'coverageMapReaderCodeSource':raw['coverageMapReaderCodeSource'],'classBaselineVerification':'OFFLINE_ONLY','constructorVariantVerification':'PYTHON_ONLY'}
 comparison['invocationProvenance']=read(OUT/'runtime.json').get('reuse',{'identicalInputsReused':0,'additionalInvocations':len(rows)})
 loader={'maps':raw['loader'],'totalDifferentEntries':sum(m['differentEntryCount'] for m in raw['loader']),'totalRawU':sum(len(m['rawU']) for m in raw['loader']),'totalLoadedU':sum(len(m['loadedU']) for m in raw['loader'])}
 write(ITER/'results/java_comparison.json',comparison);write(ITER/'results/loader_content_equality.json',loader)
 print(json.dumps({k:v for k,v in comparison.items() if k not in ('cases',)}));print('Loader differing entries:',loader['totalDifferentEntries'])
 if comparison['mismatches'] or loader['totalDifferentEntries']:raise SystemExit(1)
if __name__=='__main__':
 prepare()
 if '--reuse-verified' not in sys.argv or not reuse_identical_inputs():execute()
 finalize()
