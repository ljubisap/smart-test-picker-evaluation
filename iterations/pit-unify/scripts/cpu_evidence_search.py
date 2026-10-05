"""Read-only search of retained original campaign evidence; absence is not proof."""
import re
from derive import ROOT,ITER,read,write,digest

def main():
    paths=sorted((ROOT/'jgrapht/results').rglob('*.log'))
    paths += sorted((ROOT/'jgrapht/docs').glob('*.md'))
    paths += sorted((ROOT/'jgrapht/config').glob('*'))
    paths += sorted((ROOT/'jgrapht/scripts').glob('*.py'))
    pattern=re.compile(r'ActiveProcessorCount|availableProcessors|JAVA_TOOL_OPTIONS|JDK_JAVA_OPTIONS|processor|CPU|threads',re.I)
    rows=[]
    for p in paths:
        hits=[{'line':i,'text':s} for i,s in enumerate(p.read_text(errors='replace').splitlines(),1) if pattern.search(s)]
        rows.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p),'hits':hits})
    result={'scope':'Retained original JGraphT campaign logs, documentation, configuration and runner scripts; not unrelated later experiments.',
        'files':rows,'historicalEffectiveProcessorCount':'UNKNOWN',
        'interpretation':'Recommended hardware and the presence of the auto-thread plugin do not establish effective availableProcessors in the historical PIT worker. No matching effective value was recovered from these files.',
        'decision':'No historical CPU value is invented; the CPU=1 replay is not certified as a PIT-version-only comparison. No further outcome-driven retry is performed.'}
    write(ITER/'cpu_evidence_search.json',result)
    prior=read(ITER/'cpu_environment_evidence.json')
    prior['historicalSearchEvidence']='iterations/pit-unify/cpu_evidence_search.json'
    prior['statusComparison']='iterations/pit-unify/results/status_comparison.json.gz'
    write(ITER/'cpu_environment_evidence.json',prior)

if __name__=='__main__':main()
