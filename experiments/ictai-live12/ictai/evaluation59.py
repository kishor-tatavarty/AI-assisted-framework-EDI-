
"""Phase 5.9 evaluation protocol; no new controller behavior."""
import hashlib, json, statistics
from pathlib import Path
from .semantic58 import ARMS, run, evaluate

CATEGORIES={"MISSING_FILE","SCHEMA_DRIFT","DATA_QUALITY_ANOMALY",
            "PIPELINE_FAILURE","FRESHNESS_VIOLATION","DEPENDENCY_FAILURE",
            "INSUFFICIENT_EVIDENCE"}
def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def validate_dataset(inputs,gold,history):
    if not inputs: raise ValueError("empty inputs")
    ids=[c["id"] for c in inputs]
    if len(set(ids))!=len(ids):raise ValueError("duplicate input IDs")
    if set(ids)!=set(gold):raise ValueError("gold/input ID mismatch")
    if any(v not in CATEGORIES for v in gold.values()):raise ValueError("unknown gold category")
    histids=[h["id"] for h in history]
    if len(set(histids))!=len(histids) or set(ids)&set(histids):raise ValueError("history ID leakage")
    for c in inputs:
        if set(c)&{"gold","label","ground_truth","root_cause","category"}:
            raise ValueError("label leakage in input")
        if not isinstance(c.get("symptoms"),str) or not c["symptoms"].strip():raise ValueError("empty symptoms")
        if not isinstance(c.get("tools"),dict):raise ValueError("invalid tools")
    # Exact description duplication is a clear leakage warning; more subtle
    # semantic overlap requires independent human review.
    histdesc={h["description"].strip().casefold() for h in history if h.get("verified") and not h.get("stale")}
    duplicates=[c["id"] for c in inputs if c["symptoms"].strip().casefold() in histdesc]
    return {"cases":len(ids),"categories":sorted(set(gold.values())),
            "duplicate_history_descriptions":duplicates,
            "inputs_sha256":canonical_hash(inputs),
            "gold_sha256":canonical_hash(gold),
            "history_sha256":canonical_hash(history)}

def run_paired(inputs,gold,history,model=None,budget=3):
    validate_dataset(inputs,gold,history)
    if not isinstance(budget,int) or budget<1:raise ValueError("invalid budget")
    if model is None:arms=ARMS[:2]
    else:arms=ARMS
    rows=[]
    for c in inputs:
        for arm in arms:
            result=run(c,arm,model=model if arm in ARMS[2:] else None,
                       history=history if arm=="B4_knowledge" else (),budget=budget)
            result.update(evaluate(result,gold[c["id"]]))
            result["gold"]=gold[c["id"]]
            result["symptom_type"]=c.get("type","unspecified")
            # Outcome of a bounded search must not be described as full RCA performance.
            result["budget"]=budget
            rows.append(result)
    return rows

def summary(rows):
    output=[]
    for arm in sorted(set(x["arm"] for x in rows)):
        r=[x for x in rows if x["arm"]==arm]
        output.append({"arm":arm,"n":len(r),
            "correct":sum(x["correct"] for x in r),
            "accuracy":sum(x["correct"] for x in r)/len(r),
            "false_confirmations":sum(x["false_confirmation"] for x in r),
            "correct_abstentions":sum(x["correct_abstention"] for x in r),
            "mean_tool_calls":statistics.mean(x["tool_calls"] for x in r),
            "mean_layers":statistics.mean(x["layers"] for x in r),
            "llm_attempts":sum(x["llm_attempts"] for x in r),
            "llm_failures":sum(x["llm_failures"] for x in r)})
    return output
