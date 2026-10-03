#!/usr/bin/env python3
"""Re-derive the adopted B2 policy from frozen maps and PIT records."""

from __future__ import annotations

import hashlib, json, math, random, statistics, sys
from collections import defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.evaluation_core import (  # noqa: E402
    all_coverage_keys, build_base_to_keys, build_class_to_keys, discover_pit_files,
    exclude_non_leaf_oracle_records, load_coverage_map, load_pit_mutations,
    resolve_killing_tests, select_class_level, select_constructor_only_rule,
    select_original, select_original_legacy_edge_only,
)

POLICIES = {"base": select_original, "constructor": select_constructor_only_rule,
            "class": select_class_level}
RANDOM_TRIALS, RANDOM_SEED = 1000, 42
BOOTSTRAP_TRIALS = 10_000


def wilson(successes, total, z=1.959963984540054):
    p = successes / total; denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return [100*(center-half), 100*(center+half)]


def bootstrap(pairs, seed):
    rng=random.Random(seed); count=len(pairs); values=[]
    for _ in range(BOOTSTRAP_TRIALS):
        sample=[pairs[rng.randrange(count)] for _ in range(count)]
        values.append(100*sum(x[0] for x in sample)/sum(x[1] for x in sample))
    values.sort()
    return {"seed":seed,"trials":BOOTSTRAP_TRIALS,"clusters":count,
            "lowerPct":values[int(.025*BOOTSTRAP_TRIALS)],
            "upperPct":values[int(.975*BOOTSTRAP_TRIALS)-1]}


def metric(rows, policy, population):
    inclusive=sum(row[policy]["inclusive"] for row in rows)
    mean=sum(row[policy]["selectedCount"] for row in rows)/len(rows)
    fraction=100*mean/population
    return {"eligible":len(rows),"inclusive":inclusive,
            "inclusivenessPctFullPrecision":100*inclusive/len(rows),
            "inclusivenessPct2dp":round(100*inclusive/len(rows),2),
            "meanSelectedFullPrecision":mean,"meanSelected2dp":round(mean,2),
            "selectedFractionPctFullPrecision":fraction,"selectedFractionPct2dp":round(fraction,2),
            "reductionPctFullPrecision":100-fraction,"reductionPct2dp":round(100-fraction,2)}


def random_metric(rows, universe):
    universe=sorted(universe); n=len(universe); universe_set=set(universe); expected=0.0
    inputs=[]
    for row in rows:
        budget=row["base"]["selectedCount"]; killers=set(row["killingTests"]) & universe_set
        k=min(budget,n)
        probability = 0.0
        if k and killers:
            probability = 1.0 if n-len(killers)<k else 1-comb(n-len(killers),k)/comb(n,k)
            expected += probability
        inputs.append((budget,killers,probability))
    trial_values=[]
    for trial in range(RANDOM_TRIALS):
        safe=0
        for index,(budget,killers,probability) in enumerate(inputs):
            rng=random.Random(RANDOM_SEED + trial*len(rows) + index)
            # Whether a uniformly sampled subset intersects K is Bernoulli with
            # this exact hypergeometric probability. Drawing that event avoids
            # materializing millions of large subsets while preserving the
            # specified uniform equal-budget experiment.
            safe += rng.random() < probability
        trial_values.append(100*safe/len(rows))
    mc=statistics.mean(trial_values); analytical=100*expected/len(rows)
    return {"trials":RANDOM_TRIALS,"seed":RANDOM_SEED,
            "perRecordSeedFormula":"42 + trial * number_of_records + record_index",
            "monteCarloImplementation":"Bernoulli draw using the exact uniform-subset intersection probability",
            "monteCarloPctFullPrecision":mc,"monteCarloPct2dp":round(mc,2),
            "monteCarloStdPctFullPrecision":statistics.pstdev(trial_values),
            "analyticalPctFullPrecision":analytical,"analyticalPct2dp":round(analytical,2),
            "absoluteDifferencePercentagePoints":abs(mc-analytical)}


def method_kind(name):
    if name=="<init>": return "constructor"
    if name=="<clinit>": return "class_initializer"
    if name.startswith("lambda$"): return "lambda"
    if name.startswith(("access$","$deserializeLambda$","bridge$")): return "other_synthetic_or_bridge_name_detectable"
    return "regular_method"


def main():
    projects=json.loads((ROOT/"analysis/projects.json").read_text())["projects"]
    taxonomy=json.loads((ROOT/"results/failure_taxonomy.json").read_text())
    annotations={m["mutationId"]:m for p in taxonomy["byProject"].values() for m in p.get("mutations",[])}
    all_rows=[]; summary={"schemaVersion":1,"sourcePolicy":"STP 2e0954 U union (H if H else G)","projects":{}}
    intervals={"projects":{},"aggregate":{}}; clusters_out={"projects":{},"aggregate":{}}
    aggregate_pairs={name:[] for name in POLICIES}; recovered=[]; residual=[]
    legacy_ids=[]; current_ids=[]
    for project_index,project in enumerate(projects):
        name=project["name"]; coverage=load_coverage_map(ROOT/project["coverageMap"]); mappings=coverage["testMappings"]
        raw=load_pit_mutations(name,ROOT,discover_pit_files(ROOT,project["pitFiles"]))
        mutations=resolve_killing_tests(raw,mappings,build_base_to_keys(mappings),build_class_to_keys(mappings,coverage.get("executionIdentities",{})))
        mutations=exclude_non_leaf_oracle_records(mutations,ROOT,name)
        rows=[]
        for mutation in mutations:
            killers=sorted(all_coverage_keys(mutation)); policy_data={}
            for policy,selector in POLICIES.items():
                selected=sorted(selector(mappings,mutation.mutated_class,mutation.mutated_method))
                policy_data[policy]={"selectedTests":selected,"selectedCount":len(selected),"inclusive":bool(set(selected)&set(killers))}
            legacy=sorted(select_original_legacy_edge_only(mappings,mutation.mutated_class,mutation.mutated_method))
            row={"project":name,"mutationId":mutation.mutation_id,"mutatedClass":mutation.mutated_class,
                 "mutatedMethod":mutation.mutated_method,"line":mutation.line_number,"mutator":mutation.mutator,
                 "killingTests":killers,"legacy":{"selectedTests":legacy,"selectedCount":len(legacy),"inclusive":bool(set(legacy)&set(killers))},**policy_data}
            rows.append(row); all_rows.append(row); current_ids.append(mutation.mutation_id); legacy_ids.append(mutation.mutation_id)
            annotation=annotations.get(mutation.mutation_id)
            if annotation and not row["base"]["inclusive"]:
                residual.append({**annotation,"project":name})
            if annotation and not row["legacy"]["inclusive"] and row["base"]["inclusive"]:
                recovered.append({**annotation,"project":name,"recoveredBy":"NO_COVERAGE_BRANCH"})
        policy_metrics={policy:metric(rows,policy,len(mappings)) for policy in POLICIES}
        random_data=random_metric(rows,mappings)
        grouped={policy:defaultdict(lambda:[0,0]) for policy in POLICIES}
        for row in rows:
            for policy in POLICIES:
                grouped[policy][row["mutatedClass"]][0]+=int(row[policy]["inclusive"])
                grouped[policy][row["mutatedClass"]][1]+=1
        interval_policies={}; cluster_policies={}
        for policy in POLICIES:
            pairs=[{"subjectQualifiedClass":f"{name}:{cls}","successes":v[0],"total":v[1]} for cls,v in sorted(grouped[policy].items())]
            raw_pairs=[[x["successes"],x["total"]] for x in pairs]
            aggregate_pairs[policy].extend(raw_pairs); cluster_policies[policy]=pairs
            m=policy_metrics[policy]
            interval_policies[policy]={"wilson95Pct":wilson(m["inclusive"],m["eligible"]),
                "clusterBootstrap95Pct":bootstrap(raw_pairs,20261003+project_index)}
        summary["projects"][name]={"logicalTests":len(mappings),"emptyFootprintTests":sum(not (v.get("classes") or []) and not (v.get("methods") or []) for v in mappings.values()),
            "policies":policy_metrics,"randomEqualBudget":random_data}
        intervals["projects"][name]=interval_policies; clusters_out["projects"][name]=cluster_policies
    for policy in POLICIES:
        m=metric(all_rows,policy,sum(x["logicalTests"] for x in summary["projects"].values()))
        # Aggregate selected fraction across heterogeneous populations is intentionally not reported.
        for key in ["meanSelectedFullPrecision","meanSelected2dp","selectedFractionPctFullPrecision","selectedFractionPct2dp","reductionPctFullPrecision","reductionPct2dp"]: m.pop(key,None)
        summary.setdefault("aggregate",{})[policy]=m
        intervals["aggregate"][policy]={"wilson95Pct":wilson(m["inclusive"],m["eligible"]),"clusterBootstrap95Pct":bootstrap(aggregate_pairs[policy],20261103)}
        clusters_out["aggregate"][policy]=[{"successes":x[0],"total":x[1]} for x in aggregate_pairs[policy]]
    method_audit=json.loads((OUT/"method_kind_audit.json").read_text())
    summary["methodKinds"]={"source":"analysis/v14_4_rederivation/method_kind_audit.json","counts":{
        kind:sum(s["eligibleRecordsByKind"][kind]["eligible"] for s in method_audit["subjects"].values())
        for kind in next(iter(method_audit["subjects"].values()))["eligibleRecordsByKind"]}}
    regression=(OUT/"regression_output.txt").read_text(); import re
    match=re.search(r"Ran (\d+) tests",regression); summary["regressionTests"]={"source":"analysis/v14_4_rederivation/regression_output.txt","count":int(match.group(1)),"passed":regression.rstrip().endswith("OK")}
    summary["confidenceIntervalsSource"]="analysis/v14_4_rederivation/confidence_intervals.json"
    residual_counts=defaultdict(int); causal_counts=defaultdict(int)
    for row in residual: residual_counts[row["footprintType"]]+=1; causal_counts[row["causalMechanism"]]+=1
    residual_output={"residualMisses":residual,"recoveredByNoCoverage":recovered,"residualFootprintCounts":dict(residual_counts),"residualCausalMechanismCounts":dict(causal_counts)}
    mitigation={"projects":{},"aggregate":{}}
    for name,data in summary["projects"].items():
        mitigation["projects"][name]={"base":data["policies"]["base"],"constructor":data["policies"]["constructor"],"additionalRecovered":data["policies"]["constructor"]["inclusive"]-data["policies"]["base"]["inclusive"]}
    mitigation["aggregate"]={"base":summary["aggregate"]["base"],"constructor":summary["aggregate"]["constructor"],"additionalRecovered":summary["aggregate"]["constructor"]["inclusive"]-summary["aggregate"]["base"]["inclusive"]}
    expected={"base":[3991,4010],"constructor":[3998,4010],"class":[4009,4010],"springSecurity":[335,337,340],"flips":5,
              "legacySizeIncrement":{"commons-lang":0,"jgrapht":1,"spring-core":0,"petclinic":0,"flink":1,"spring-security":23,"hibernate":0,"quarkus":9}}
    observed={"base":[summary["aggregate"]["base"]["inclusive"],summary["aggregate"]["base"]["eligible"]],
              "constructor":[summary["aggregate"]["constructor"]["inclusive"],summary["aggregate"]["constructor"]["eligible"]],
              "class":[summary["aggregate"]["class"]["inclusive"],summary["aggregate"]["class"]["eligible"]],
              "springSecurity":[summary["projects"]["spring-security"]["policies"][p]["inclusive"] for p in ("base","constructor","class")],
              "flips":len(recovered),"legacySizeIncrement":{name:round(data["policies"]["base"]["meanSelectedFullPrecision"]-sum(r["legacy"]["selectedCount"] for r in all_rows if r["project"]==name)/sum(r["project"]==name for r in all_rows),12) for name,data in summary["projects"].items()}}
    checks={k:{"expected":expected[k],"observed":observed[k],"match":expected[k]==observed[k]} for k in expected}
    checks["eligibleMutationIdsIdentical"]={"match":current_ids==legacy_ids,"count":len(current_ids)}
    partb=json.loads((ROOT/"analysis/v14_4_checks/no_coverage_sensitivity.json").read_text())
    deltas=[]
    mapping={"base":"stpNc","constructor":"constructorOnlyNc","class":"classLevelNc"}
    for name,data in summary["projects"].items():
        for policy,old_name in mapping.items():
            old=partb["projects"][name]["selectors"][old_name]; new=data["policies"][policy]
            for field in ("inclusive","meanSelectedFullPrecision","selectedFractionPctFullPrecision","reductionPctFullPrecision"):
                if new[field]!=old[field]: deltas.append({"project":name,"policy":policy,"field":field,"partB":old[field],"derived":new[field]})
    # Full selected sets repeat heavily across mutation records.  Store each
    # canonical sorted set once and reference it by its content hash.  This is
    # lossless while keeping the replication artifact below hosting limits.
    selected_sets = {}
    compact_rows = []
    for row in all_rows:
        compact = {key: value for key, value in row.items()
                   if key not in {"legacy", "base", "constructor", "class"}}
        for policy in ("legacy", "base", "constructor", "class"):
            outcome = dict(row[policy])
            selected = outcome.pop("selectedTests")
            selected_bytes = json.dumps(selected, ensure_ascii=False,
                                        separators=(",", ":")).encode("utf-8")
            selected_id = hashlib.sha256(selected_bytes).hexdigest()
            selected_sets.setdefault(selected_id, selected)
            outcome["selectedSetId"] = selected_id
            compact[policy] = outcome
        compact_rows.append(compact)
    (OUT/"per_record_outcomes.json").write_text(json.dumps({
        "schemaVersion": "b2-deduplicated-selected-sets-v1",
        "selectedSets": selected_sets,
        "records": compact_rows,
    },indent=2)+"\n")
    (OUT/"summary_tables.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"confidence_intervals.json").write_text(json.dumps(intervals,indent=2)+"\n")
    (OUT/"bootstrap_cluster_inputs.json").write_text(json.dumps(clusters_out,indent=2)+"\n")
    (OUT/"residual_taxonomy.json").write_text(json.dumps(residual_output,indent=2)+"\n")
    (OUT/"mitigation_comparison.json").write_text(json.dumps(mitigation,indent=2)+"\n")
    (OUT/"random_baseline.json").write_text(json.dumps({n:d["randomEqualBudget"] for n,d in summary["projects"].items()},indent=2)+"\n")
    (OUT/"partb_delta.json").write_text(json.dumps({"differences":deltas,"differenceCount":len(deltas),"consistencyChecks":checks},indent=2)+"\n")
    if deltas or not all(v.get("match",False) for v in checks.values()): raise SystemExit("B2 consistency mismatch; inspect partb_delta.json")
    print(json.dumps({"aggregate":summary["aggregate"],"residual":residual_output["residualFootprintCounts"],"clusters":len(aggregate_pairs["base"])},indent=2))

if __name__=="__main__": main()
