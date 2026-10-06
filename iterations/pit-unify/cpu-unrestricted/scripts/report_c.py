"""Render C execution, numeric verification and adoption readiness separately."""
import collections,re,subprocess
from environment import *
def main():
    pre=read(OUT/'preflight.json');inv=read(OUT/'campaign_inventory.json');summary=read(OUT/'results/summary_tables.json');comp=read(OUT/'comparison.json');java=read(OUT/'results/java_comparison.json');env=read(OUT/'worker_environment.json');tax=read(OUT/'results/residual_taxonomy.json');checks=read(OUT/'verification/current/results.json');paper=read(OUT/'manuscript_comparison.json')
    counts={}
    for label,path in [('repository',OUT/'verification/current/unittest.log'),('localHelpers',OUT/'helper-tests.log'),('cpuRemovalSubset',OUT/'environment-tests.log')]:
        match=re.search(r'Ran (\d+) tests?',path.read_text());counts[label]={'tests':int(match.group(1)) if match else None,'source':str(path.relative_to(ROOT))}
    write(OUT/'test_counts.json',counts)
    hashes=read(OUT/'preserved_hashes.json');changed=[p for p,h in hashes.items() if not(ROOT/p).exists() or sha(ROOT/p)!=h]
    write(OUT/'preservation.json',{'startHead':pre['head'],'endHead':git('rev-parse','HEAD'),'main':git('rev-parse','main'),'checkedFiles':len(hashes),'changedFiles':changed,'allCurrentHashes':{p:sha(ROOT/p) for p in hashes},'subjectCheckouts':{n:{'head':git('rev-parse','HEAD',cwd=Path(s['checkout'])),'status':git('status','--porcelain',cwd=Path(s['checkout']))} for n,s in pre['subjects'].items()}})
    verification=OUT/'verification/C.log';last=[l for l in verification.read_text().splitlines() if l.strip()][-1]
    new_checks=read(OUT/'verification/new-checks.json')
    verified=last.startswith('PASS:') and checks['allPassed'] and new_checks['allPassed'] and not changed and not java['mismatches'] and not java['nonSelectedModes']
    status={'execution':'COMPLETED_WITH_RECORDED_JOB_OUTCOMES','numericalVerification':'PASS' if verified else 'NOT_VERIFIED','authorReview':'READY_FOR_REVIEW_NOT_ADOPTED' if verified else 'BLOCKED','historicalEffectiveProcessors':'UNKNOWN','commit':'NONE','push':'NONE'}
    write(OUT/'status.json',status)
    lines=['# CPU-override-free PIT rerun','','## Status','',*['- '+k+': '+v for k,v in status.items()],
       '',f"Starting and ending HEAD: `{pre['head']}`. Canonical baseline: `{pre['main']}`. All new material is confined to `iterations/pit-unify/cpu-unrestricted/`; A and B files are preserved. No manuscript, anonymous package, evaluator, map, scope, oracle exclusion, main or tag was changed.",
       '', '## Environment and actual campaigns','',f"The initial control JVM reports {pre['controlJvmAvailableProcessors']} processors, without ActiveProcessorCount. Additional controls use each subject's configured PIT JVM arguments; they are control JVMs, not direct measurements inside leaf tests. Actual observed coverage/minion command lines and inherited launch settings are retained in worker_environment.json and per-attempt process snapshots.",
       'Primary PIT workers: four. Per-class jobs and subjects are sequential. CPU use is monitored, with a stop-and-retry resource fallback to one PIT worker only if needed; the JVM-visible processor count is never replaced by another explicit value. This guard is not an affinity or duty-cycle limiter. Per-attempt worker modes are reported below.',
       '', '| Subject | Planned classes | Attempted classes | Attempts | Successful matrices | Failed classes | Workers by attempt | Elapsed seconds |','|---|---:|---:|---:|---:|---:|---|---:|']
    for n,d in inv.items():
        jobs=d['campaign']['jobs'];workers=dict(collections.Counter(r['pitWorkers'] for r in jobs))
        lines.append(f"| {n} | {d['sampledClasses']} | {len({r['fqn'] for r in jobs})} | {len(jobs)} | {d['completeClasses']} | {len(d['failedOrTimedOut'])} | {workers} | {d['campaign']['elapsedSeconds']:.3f} |")
    lines+=['','Observed peak aggregate CPU use by subject (one-second process samples): '+str({n:d['peakObservedAggregateCpuPercent'] for n,d in env['subjects'].items()})+'. No claim is made about unsampled instantaneous peaks.',
       '', '### Jobs without usable matrices','']
    for n,d in inv.items():
        for row in d['classes']:
            if row['status']!='OK':lines.append(f"- {n}: `{row['fqn']}` — {row['status']}; attempt logs: `{row['attempts'][-1]['directory']}`.")
    if not any(d['failedOrTimedOut'] for d in inv.values()):lines.append('None.')
    lines+=['','Every attempted job, including failures or resource interruptions, has a separate directory and effective command. Successful matrices are copied only from fresh C output; no B/current matrix fills a gap. XML/gzip identity is verified in matrix_packaging.json. JGraphT receives the same documented Maven profile; Spring reuses native pitClasspath and the proven test-free runtime-JAR preparation. The original Spring runner remains unchanged; its command adapter appends --mutators DEFAULTS. No PIT history input is configured; JGraphT starts with a clean compile and removes stale target XML, while every C attempt output directory starts empty.',
       '', '## A / B / C numerical results','','| State | Eligible | Base inclusive | Base % | Constructor inclusive | Class inclusive |','|---|---:|---:|---:|---:|---:|']
    for k,a in comp['aggregate'].items():lines.append(f"| {k} | {a['base']['eligible']} | {a['base']['inclusive']} | {a['base']['inclusivenessPctFullPrecision']:.8f} | {a['constructor']['inclusive']} | {a['class']['inclusive']} |")
    lines+=['',f"Previously A KILLED → B SURVIVED transit-routing cases found by correspondence: {comp['transitCaseCount']}. Their C status distribution: `{comp['transitSummary']}`. Full A/B/C IDs, statuses, raw/normalized killers and eligible policy outcomes are in comparison_records.json.gz. Different mutators are never paired. Ambiguous multiplicity and missing/fresh-only records remain explicit.",
       '',f"C residual footprint counts: `{tax['residualFootprintCounts']}`; causal annotations: `{tax['residualCausalMechanismCounts']}`. Transfer of annotations requires unique correspondence and identical normalized killers/footprints at unchanged source revisions. Unestablished causes remain UNDETERMINED.",
       '', '## Comparison and verification','',f"Java full-set comparison: {java['uniqueInvocations']} unique inputs, {java['weightedOccurrences']} weighted occurrences, {java['mismatches']} mismatches, {java['nonSelectedModes']} non-SELECTED results. Reuse/fresh: `{java['invocationProvenance']}`. All map content was freshly read through the production loader. No new selector build was performed.",
       f"Manuscript comparison, without manuscript edits: {len(paper['claims'])} claim/cell entries, {sum(r['changed'] for r in paper['claims'])} changed, {len(paper['unmatchedClaimPatterns'])} unmatched. Sources point to C results. See MANUSCRIPT_COMPARISON.md/json.",
       f"Preserved tracked files checked: {len(hashes)}; changed: {len(changed)}. Existing checks below were rerun in this task, not copied from B. Regression test counts from logs: `{counts}`. The CPU-removal tests are a subset of the local helper tests, not additional independent cases.",
       '', '| Check | Exit | Last line |','|---|---:|---|']
    for c in checks['commands']+new_checks['commands']:lines.append(f"| {c['name']} | {c['exitCode']} | {c['lastNonEmptyLine'].replace('|','/')} |")
    lines+=['', 'C verifier: '+last,
       '', '## Related diagnostics','',
       'Succeeding-tests check: `'+str(read(OUT/'results/succeeding_tests_check.json')['summary'])+'`.',
       'Collection-failing killer impact: `'+str(read(OUT/'results/failed_killer_impact.json')['summary'])+'`.',
       'Spring repeat-map selected-set differences: `'+str(read(OUT/'results/springcore_run2_sensitivity.json')['selectedSetDifferences'])+'`; residual-miss correspondence: `'+str(read(OUT/'results/springcore_run2_sensitivity.json')['residualDifference'])+'`. This reuses retained run-2 evidence; no coverage collection was performed.',
       'The worked example, random baseline, Wilson/class-cluster intervals and all full per-record policy sets were regenerated under results/. Cross-run multiplicities are preserved; ambiguous records are not forcibly paired (see BLOCKERS.md for the frozen index-parser boundary).',
       '', '## Interpretation and remaining unknowns','',
       f"The high measured inclusiveness and the observed residual mechanism model remain supported in this sample: C has {summary['aggregate']['base']['eligible']-summary['aggregate']['base']['inclusive']} base misses and {summary['aggregate']['constructor']['inclusive']-summary['aggregate']['base']['inclusive']} constructor-rule recoveries. Its footprint and causal totals equal B: {tax['residualFootprintCounts']==read(B/'results/residual_taxonomy.json')['residualFootprintCounts'] and tax['residualCausalMechanismCounts']==read(B/'results/residual_taxonomy.json')['residualCausalMechanismCounts']}. The denominator and selection statistics change; the canonical paper numbers cannot simply be relabeled as C.",
       'Removing the explicit override establishes a newly measured execution condition, not equivalence with unknown historical CPU/thread settings. B→C is the observed repeat after removing that override (plus any labeled resource fallback). A→C also includes the changed conditional-operator treatment and other potentially unrecorded historical conditions. A single repeat does not establish determinism or prove that every status change has a single CPU cause.',
       'CPU exposure and executor sizing can alter test paths and mutation detection, not just elapsed time. The transit-routing source evidence is preserved in ../cpu_environment_evidence.json. Numerical verifier success is distinct from certification of historical environment equality and from author adoption.',
       '', '## Reproduction','',
       'From the repository root: `PYTHONDONTWRITEBYTECODE=1 python3 iterations/pit-unify/cpu-unrestricted/scripts/verify_c.py --verify`. Per-attempt commands reproduce execution with the recorded checkout/toolchain; do not blindly rerun the guarded campaign launcher into existing attempt directories.',
       'The unchanged final manuscript was only read for claim comparison. No commit, merge, push, tag movement or automatic promotion was performed.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
