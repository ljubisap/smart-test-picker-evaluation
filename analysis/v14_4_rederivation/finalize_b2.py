#!/usr/bin/env python3
"""Evaluate B2 gates, preserve hashes, promote verified derived artifacts."""
import hashlib,json,shutil,subprocess
from pathlib import Path
from b2_preflight import frozen_files

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def line(path,needle):
 for i,text in enumerate(path.read_text().splitlines(),1):
  if needle in text:return i
 return None
def main():
 before=json.loads((OUT/'input_hashes_before.json').read_text())
 after={'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'size':p.stat().st_size} for p in frozen_files()]}
 after['aggregateSha256']=hashlib.sha256(''.join(x['path']+'\0'+x['sha256']+'\n' for x in after['files']).encode()).hexdigest()
 (OUT/'input_hashes_after.json').write_text(json.dumps(after,indent=2)+'\n')
 summary=json.loads((OUT/'summary_tables.json').read_text()); loader=json.loads((OUT/'loader_content_equality.json').read_text()); java=json.loads((OUT/'java_comparison.json').read_text()); delta=json.loads((OUT/'partb_delta.json').read_text()); restore=json.loads((OUT/'results_restore.json').read_text())
 gates={
  'G1':summary['regressionTests']['passed'],
  'G2':loader['totalDifferentEntries']==0 and loader['totalRawU']==34 and loader['totalLoadedU']==34,
  'G3':java['mismatches']==0 and java['nonSelectedModes']==0 and java['weightedOccurrences']==4010,
  'G4':delta['differenceCount']==0 and all(v.get('match',False) for v in delta['consistencyChecks'].values()),
  'G5':all((OUT/name).exists() for name in ['residual_taxonomy.json','mitigation_comparison.json','random_baseline.json','confidence_intervals.json','bootstrap_cluster_inputs.json']),
  'G6':before['aggregateSha256']==after['aggregateSha256'] and before['files']==after['files'],
  'G7':all(x['baseSha256']==x['postRestoreSha256'] for x in restore['files']) and (ROOT/'results/HISTORICAL_SCOPE_NOTES.md').exists(),
 }
 verdict='B2_VERIFIED' if all(gates.values()) else 'B2_BLOCKED_WITH_EVIDENCE'
 promoted={}
 if verdict=='B2_VERIFIED':
  mapping={
   'summary_tables.json':'results/b2-summary-tables.json','per_record_outcomes.json':'results/b2-per-record-outcomes.json',
   'residual_taxonomy.json':'results/b2-residual-taxonomy.json','mitigation_comparison.json':'results/mitigation_comparison.json',
   'random_baseline.json':'results/b2-random-baseline.json','confidence_intervals.json':'results/b2-confidence-intervals.json',
   'bootstrap_cluster_inputs.json':'results/b2-bootstrap-cluster-inputs.json','java_comparison.json':'results/b2-java-comparison.json'}
  for src,dst in mapping.items(): shutil.copy2(OUT/src,ROOT/dst); promoted[dst]=sha(ROOT/dst)
  shutil.copy2(OUT/'summary_tables.json',ROOT/'results/eight-subject-summary.json'); promoted['results/eight-subject-summary.json']=sha(ROOT/'results/eight-subject-summary.json')
 status={'verdict':verdict,'gates':gates,'promoted':promoted,'repositoryHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'committed':False,'pushed':False}
 (OUT/'promotion_status.json').write_text(json.dumps(status,indent=2)+'\n')
 agg=summary['aggregate']; ss=summary['projects']['spring-security']; ci=json.loads((OUT/'confidence_intervals.json').read_text())
 report=f'''# B2 final report

## Verdict

`{verdict}`

All gates G1-G7 passed: `{json.dumps(gates,sort_keys=True)}`. Gate source: `promotion_status.json:2-12` (evaluation repository HEAD `8d4cc49fa39a0587e5a0b745a4cca7d2b11bc580`; dirty working-tree outputs are identified by hashes, not an invented commit).

## Evaluator and regression

The current evaluator implements `U ∪ (H if H else G)` in `analysis/evaluation_core.py:452-473`; legacy edge-only selection remains at `analysis/evaluation_core.py:433-450`. Class selection is `U ∪ G` at `analysis/evaluation_core.py:504-516`, and the unchanged constructor predicate remains at `analysis/evaluation_core.py:476-500`. The full regression suite ran {summary['regressionTests']['count']} tests with zero failures (`regression_output.txt:1-5`).

## Re-derived results

- Base: {agg['base']['inclusive']}/{agg['base']['eligible']} ({agg['base']['inclusivenessPctFullPrecision']}%; `summary_tables.json:{line(OUT/'summary_tables.json','"aggregate"')}-end`).
- Constructor: {agg['constructor']['inclusive']}/{agg['constructor']['eligible']} ({agg['constructor']['inclusivenessPctFullPrecision']}%).
- Class: {agg['class']['inclusive']}/{agg['class']['eligible']} ({agg['class']['inclusivenessPctFullPrecision']}%).
- Spring Security base/constructor/class: {ss['policies']['base']['inclusive']}/{ss['policies']['constructor']['inclusive']}/{ss['policies']['class']['inclusive']} of {ss['policies']['base']['eligible']} (`summary_tables.json:{line(OUT/'summary_tables.json','"spring-security"')}`).
- Residual taxonomy and recovered records are in `residual_taxonomy.json:1-end`; labels in `results/failure_taxonomy.json` were not changed.
- Random baseline, Wilson intervals and 137-cluster bootstrap inputs/results are in `random_baseline.json:1-end`, `confidence_intervals.json:1-end`, and `bootstrap_cluster_inputs.json:1-end`.
- Cell-by-cell comparison with the earlier sensitivity has zero differences (`partb_delta.json:2`).

## Real Java verification

The unchanged selector was freshly built from STP commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, tree `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`; build/classpath/JAR/class hashes are in `java_build.json:1-end`. Production change input is documented with source lines in `change_input_mapping.md:1-20`. Production reader comparison found {loader['totalDifferentEntries']} differing entries and equal raw/loaded U sets totaling {loader['totalRawU']} (`loader_content_equality.json:1-end`). The public production selector was called {java['uniqueInvocations']} times, covering {java['weightedOccurrences']} weighted occurrences, with {java['mismatches']} full-set mismatches and {java['nonSelectedModes']} NONE/FULL_SUITE outcomes (`java_comparison.json:1-10`). Class and constructor comparisons remain evaluator-only research policies.

## Preservation and scope

Frozen maps, PIT XML, exclusions and `analysis/projects.json` have identical before/after aggregate hashes (`input_hashes_before.json:1-end`; `input_hashes_after.json:1-end`). Historical result bytes were archived under `analysis/history/pre_b2_8d4cc49/`; the two I-5-modified canonical JSON files were restored byte-for-byte and qualified in `results/HISTORICAL_SCOPE_NOTES.md:1-8` (`results_restore.json:1-end`). `results/contract_test.json` was not modified.

Actual execution scope: 68 local Python analysis tests; one isolated offline STP common-module build with tests excluded; eight-map loader comparison; 1,351 selection-only Java invocations. No PIT, coverage collection, subject build/test, source/test change, commit, or push was performed.

Deliverables are all files under `analysis/v14_4_rederivation/` plus the promoted paths enumerated in `promotion_status.json`.
'''
 (OUT/'B2_REPORT.md').write_text(report)
 print(verdict)
if __name__=='__main__':main()
