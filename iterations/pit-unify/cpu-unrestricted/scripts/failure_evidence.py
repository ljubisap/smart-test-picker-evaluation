"""Extract failed native-baseline descriptions from retained PIT stderr logs."""
import re
from environment import ROOT,B,OUT,read,write,sha

def extract(path):
    if not path.exists():return {'status':'LOG_NOT_AVAILABLE','path':str(path.relative_to(ROOT))}
    lines=path.read_text(errors='replace').splitlines()
    descriptions=[{'line':i+1,'text':s} for i,s in enumerate(lines) if s.startswith('Description [testClass=')]
    errors=[{'line':i+1,'text':s} for i,s in enumerate(lines) if 'tests did not pass without mutation' in s or 'Tests failing without mutation' in s]
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'failingTestDescriptions':descriptions,'errors':errors}

def generate():
    rows=[]
    for name,subject in read(OUT/'campaign_inventory.json').items():
        for job in subject['campaign']['jobs']:
            if job['status']=='OK':continue
            c=extract(ROOT/job['directory']/'per-class'/job['fqn']/'stderr.log')
            b=extract(B/'pit'/name/'per-class'/job['fqn']/'stderr.log')
            left={r['text'] for r in b.get('failingTestDescriptions',[])}
            right={r['text'] for r in c.get('failingTestDescriptions',[])}
            rows.append({'subject':name,'fqn':job['fqn'],'attempt':job['attempt'],'status':job['status'],'B':b,'C':c,'sameFailingDescriptionsAsB':left==right if 'sha256' in b else None})
    return rows

if __name__=='__main__':
    rows=generate();write(OUT/'failed_jobs_evidence.json',rows)
    for r in rows:print(r['fqn'],len(r['C'].get('failingTestDescriptions',[])),'baseline descriptions; identical to B:',r['sameFailingDescriptionsAsB'])
