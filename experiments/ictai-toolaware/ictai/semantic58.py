
"""Paired semantic stress-test runner; gold never enters controller."""
import json, time, re
from .controller import Investigation
from .experiment57 import LAYERS, ORDER, CUES
from .confirmation_six import confirm_six
from .reasoning_context import propose_with_symptoms, _eligible_layers

ARMS=("B1_fixed","B2_dynamic","B3_llm","B4_knowledge")
def retrieve(history, symptoms):
    tokens=lambda s:set(re.findall(r"[a-z]{4,}",s.lower()))-{"that","with","from","this","task","data","pipeline"}
    q=tokens(symptoms)
    hits=[(len(q&tokens(h["description"])),h["id"],h["layer"],h["description"]) for h in history if h.get("verified") and not h.get("stale")]
    return [{"id":i,"score":n,"layer":layer,"description":description,"verified":True,"stale":False} for n,i,layer,description in sorted(hits,key=lambda t:(-t[0],t[1])) if n>0][:2]

def run(case,arm,model=None,history=(),budget=12):
    if arm not in ARMS:raise ValueError("invalid arm")
    if any(k in case for k in ("gold","label","ground_truth","root_cause")):raise ValueError("gold leakage")
    if arm in ARMS[2:] and model is None:raise ValueError("model required")
    tools={k:(lambda v=v:dict(v)) for k,v in case["tools"].items()}
    ctx=Investigation(case["id"]);used=set();llm=0;errors=0;rounds=0
    hits=retrieve(history,case["symptoms"]) if arm=="B4_knowledge" else []
    start=time.perf_counter()
    while len(used)<budget:
        decision=confirm_six(ctx.evidence,available_tools=tools,exhausted=False)
        if decision.status in ("CONFIRMED","REVIEW_REQUIRED"):break
        if decision.status=="PROVISIONAL_RCA":
            rounds+=1
            if rounds>2:break
            pending=[t for t in tools if t not in used]
        else:
            eligible=[layer for layer in ORDER if layer in _eligible_layers(ctx,tools)]
            if not eligible:break
            selected=None;method="fallback"
            if arm in ARMS[2:] and llm<4:
                llm+=1
                # Retrieved records are recommendations only; never authoritative RCA evidence.
                p=propose_with_symptoms(ctx,tools,model,case["symptoms"],retrieved_knowledge=hits)
                if p.accepted and p.layer in eligible:selected=p.layer;method="llm"
                else:errors+=1
                ctx.audit.append({"event":"llm_proposal","accepted":selected is not None,"reason":p.reason,"proposed_layer":p.layer,"knowledge_refs":list(p.knowledge_refs),"normalized_refs":list(p.normalized_refs),"knowledge_influenced_routing":bool(selected is not None and p.knowledge_refs and arm=="B4_knowledge" and selected!=sorted(eligible,key=lambda k:(-sum(c in case["symptoms"].lower() for c in CUES.get(k,())),ORDER.index(k)))[0])})
            if selected is None:
                selected=eligible[0] if arm=="B1_fixed" else sorted(eligible,key=lambda k:(-sum(c in case["symptoms"].lower() for c in CUES.get(k,())),ORDER.index(k)))[0]
            ctx.visited.append(selected)
            ctx.audit.append({"event":"layer_selected","layer":selected,"method":method})
            pending=[t for t in LAYERS[selected] if t in tools and t not in used]
        if not pending:break
        for t in pending:
            if len(used)>=budget:break
            used.add(t)
            try:ctx.evidence.append({"tool":t,"layer":ctx.visited[-1],"result":tools[t]()})
            except Exception as exc:ctx.audit.append({"event":"tool_error","tool":t,"error_type":type(exc).__name__})
    d=confirm_six(ctx.evidence,available_tools=tools,exhausted=True)
    return {"id":case["id"],"arm":arm,"prediction":d.category,"status":d.status,
            "tool_calls":len(used),"layers":len(ctx.visited),"llm_attempts":llm,"llm_failures":errors,
            "knowledge_hits":hits,"elapsed_ms":round((time.perf_counter()-start)*1000,3),
            "evidence_refs":list(d.evidence_refs),"audit":ctx.audit}
def evaluate(row,gold):
    confirmed=row["status"]=="CONFIRMED"
    answerable=gold!="INSUFFICIENT_EVIDENCE"
    return {"correct":confirmed and row["prediction"]==gold if answerable else not confirmed,
            "false_confirmation":confirmed and (not answerable or row["prediction"]!=gold),
            "correct_abstention":not confirmed and not answerable}
def summarize(rows):
    result=[]
    for arm in ARMS:
        a=[r for r in rows if r["arm"]==arm]
        if not a:continue
        n=len(a)
        result.append({"arm":arm,"n":n,"accuracy":round(sum(x["correct"] for x in a)/n,4),
          "false_confirmations":sum(x["false_confirmation"] for x in a),
          "correct_abstentions":sum(x["correct_abstention"] for x in a),
          "mean_tool_calls":round(sum(x["tool_calls"] for x in a)/n,3),
          "mean_layers":round(sum(x["layers"] for x in a)/n,3),
          "llm_attempts":sum(x["llm_attempts"] for x in a),
          "llm_failures":sum(x["llm_failures"] for x in a),
          "mean_elapsed_ms":round(sum(x["elapsed_ms"] for x in a)/n,3)})
    return result
