#!/usr/bin/env python3
"""Prepare and finalize v14.6 production-selector replay artifacts."""
import hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def list_sha(values):
 d=hashlib.sha256()
 for value in sorted(values): d.update(value.encode()); d.update(b'\0')
 return d.hexdigest()
def prepare():
 data=json.loads((OUT/'per_record_outcomes.json').read_text()); sets=data['selectedSets']; rows=data['records']
 config=json.loads((ROOT/'analysis/projects_v14_6.json').read_text())['projects']; by={p['name']:p for p in config}; unique={}
 for row in rows:
  key=(row['project'],row['mutatedClass'],row['mutatedMethod']); selected=sets[row['base']['selectedSetId']]
  unique.setdefault(key,{'caseId':hashlib.sha256('\0'.join(key).encode()).hexdigest(),'changedClass':row['mutatedClass'],'changedMethod':row['mutatedMethod'],'pythonSelected':selected,'occurrences':0})['occurrences']+=1
 maps=[]
 for name in by:
  path=ROOT/by[name]['coverageMap']; cases=[v for k,v in unique.items() if k[0]==name]
  maps.append({'project':name,'path':str(path),'mapSha256':sha(path),'cases':cases})
 (OUT/'java_cases.json').write_text(json.dumps({'maps':maps},indent=2)+'\n')
 print(len(unique),sum(v['occurrences'] for v in unique.values()))
def finalize():
 manifest=json.loads((OUT/'java_cases.json').read_text()); raw=json.loads((OUT/'harness/java_output.json').read_text()); specs={c['caseId']:c for m in manifest['maps'] for c in m['cases']}
 loader={'stpCommit':'2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9','maps':raw['loader']}; loader['totalDifferentEntries']=sum(x['differentEntryCount'] for x in raw['loader']); loader['totalRawU']=sum(len(x['rawU']) for x in raw['loader']); loader['totalLoadedU']=sum(len(x['loadedU']) for x in raw['loader']); (OUT/'loader_content_equality.json').write_text(json.dumps(loader,indent=2)+'\n')
 rows=[]
 for java in raw['cases']:
  spec=specs[java['caseId']]; py=sorted(spec['pythonSelected']); js=sorted(java['selectedTests'])
  rows.append({'caseId':java['caseId'],'project':java['project'],'changedClass':spec['changedClass'],'changedMethod':spec['changedMethod'],'occurrences':spec['occurrences'],'javaMode':java['mode'],'javaReason':java.get('reason'),'javaSelectedTests':js,'pythonSelectedTests':py,'javaSha256':java['selectedSha256'],'pythonSha256':list_sha(py),'javaOnly':sorted(set(js)-set(py)),'pythonOnly':sorted(set(py)-set(js)),'match':js==py and java['mode']=='SELECTED'})
 comparison={'testSelectorCodeSource':raw['testSelectorCodeSource'],'coverageMapReaderCodeSource':raw['coverageMapReaderCodeSource'],'uniqueInvocations':len(rows),'weightedOccurrences':sum(x['occurrences'] for x in rows),'mismatches':sum(not x['match'] for x in rows),'nonSelectedModes':sum(x['javaMode']!='SELECTED' for x in rows),'cases':rows,'classBaselineVerification':'OFFLINE_ONLY','constructorVariantVerification':'PYTHON_ONLY'}; (OUT/'java_comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
 summary=json.loads((OUT/'summary_tables.json').read_text()); summary['javaVerification']={'source':'analysis/v14_6/java_comparison.json','uniqueInvocations':comparison['uniqueInvocations'],'weightedOccurrences':comparison['weightedOccurrences'],'mismatches':comparison['mismatches'],'nonSelectedModes':comparison['nonSelectedModes']}; (OUT/'summary_tables.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({k:comparison[k] for k in ('uniqueInvocations','weightedOccurrences','mismatches','nonSelectedModes')},indent=2))
if __name__=='__main__': (prepare if sys.argv[1]=='prepare' else finalize)()
