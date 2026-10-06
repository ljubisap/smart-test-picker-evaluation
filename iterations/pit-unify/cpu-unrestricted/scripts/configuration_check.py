"""Check effective B/C PIT command differences against the permitted changes."""
from pathlib import Path
from environment import *
def canonical(command):
    cmd=command.copy()
    if Path(cmd[0]).name=='mvn':cmd[0]='<PINNED_MAVEN>'
    if '--reportDir' in cmd:cmd[cmd.index('--reportDir')+1]='<FRESH_REPORT_DIR>'
    if '--threads' in cmd:cmd[cmd.index('--threads')+1]='<RECORDED_PIT_WORKERS>'
    cmd=['-Dthreads=<RECORDED_PIT_WORKERS>' if x.startswith('-Dthreads=') else x for x in cmd]
    return cmd
def main():
    old=read(B/'campaign_inventory.json');new=read(OUT/'campaign_inventory.json');rows=[]
    for subject,campaign in new.items():
        base={r['fqn']:r for r in old[subject]['classes']}
        for job in campaign['campaign']['jobs']:
            prior=base[job['fqn']]['attempts'][-1]
            actual=[r for r in job['commands'] if 'org.pitest.mutationtest.commandline.MutationCoverageReport' in r['command'] or any('pitest-maven:' in a for a in r['command'])]
            assert len(actual)==1
            current=actual[0];equal=canonical(prior['command'])==canonical(current['command'])
            rows.append({'subject':subject,'fqn':job['fqn'],'attempt':job['attempt'],'commandsEqualApartFromRecordedAllowedRouting':equal,'timeoutUnchanged':prior.get('timeout')==current.get('timeout'),'pitWorkers':job['pitWorkers'],'BCommand':prior['command'],'CCommand':current['command']})
    d={'allowedCommandNormalization':['mvn executable name versus the absolute path to the same pinned Maven','fresh --reportDir','separately recorded PIT worker fallback only'],'environmentDifference':'Explicit ActiveProcessorCount removed; effective environment in preflight.json','profileSource':'jgrapht/config/pit_profile.xml','profileSha256':sha(ROOT/'jgrapht/config/pit_profile.xml'),'rows':rows,'unexpectedDifferences':[r for r in rows if not r['commandsEqualApartFromRecordedAllowedRouting'] or not r['timeoutUnchanged']]}
    write(OUT/'configuration_comparison.json',d)
    print('PIT command comparisons',len(rows),'unexpected',len(d['unexpectedDifferences']))
    if d['unexpectedDifferences']:raise SystemExit(1)
if __name__=='__main__':main()
