
"""Paired semantic stress-test runner; gold never enters controller."""
import json, time, re
from .knowledge_guard import assess_history
from .controller import Investigation
from .experiment57 import LAYERS, ORDER, CUES
from .confirmation_six import confirm_six
from .reasoning_context import propose_with_symptoms, _eligible_layers

ARMS=("B1_fixed","B2_dynamic","B3_llm","B4_knowledge")
def retrieve(history, symptoms, eligible_layers=None, limit=2):
    """Advisory lexical retrieval; abstain on weak/ambiguous matches.

    Corpus records must be explicitly reviewed and not stale. Never use case
    labels, hidden gold, or tool results in retrieval queries.
    """
    import re
    stop={"that","with","from","this","task","data","pipeline","source",
          "issue","failure","failed","incident","check","historical","runbook",
          "inspect","primary","observations","before","after","system"}
    tokens=lambda text: set(re.findall(r"[a-z][a-z0-9_]{3,}",text.lower()))-stop
    q=tokens(symptoms)
    scored=[]
    for h in history:
        if h.get("verified") is not True or h.get("stale") is not False:
            continue
        if not all(isinstance(h.get(k),str) for k in ("id","layer","description")):
            continue
        if eligible_layers is not None and h["layer"] not in eligible_layers:
            continue
        match=q & tokens(h["description"])
        # Require two distinctive shared terms to avoid generic runbook hits.
        if len(match)<2:continue
        scored.append((len(match),h["id"],h,sorted(match)))
    scored.sort(key=lambda x:(-x[0],x[1]))
    return [{"id":h["id"],"score":score,"layer":h["layer"],
             "description":h["description"],"verified":True,"stale":False,
             "matched_terms":matched}
            for score,_,h,matched in scored[:limit]]

def run(case,arm,model=None,history=(),budget=12):
    if arm not in ARMS:raise ValueError("invalid arm")
    if any(k in case for k in ("gold","label","ground_truth","root_cause")):raise ValueError("gold leakage")
    if arm in ARMS[2:] and model is None:raise ValueError("model required")
    tools={k:(lambda v=v:dict(v)) for k,v in case["tools"].items()}
    ctx=Investigation(case["id"]);used=set();llm=0;errors=0;rounds=0
    tool_successes=0;tool_failures=0
    candidates=retrieve(history,case["symptoms"],eligible_layers=set(_eligible_layers(ctx,tools))) if arm=="B4_knowledge" else []
    records={h.get("id"):h for h in history if isinstance(h,dict)}
    hits=[]; knowledge_decisions=[]; last_status={}
    start=time.perf_counter()
    while len(used)<budget:
        # Reassess every candidate, including PENDING records, as evidence arrives.
        # Only ACCEPTED records are passed to the LLM. Pending records are audit-only.
        if arm=="B4_knowledge":
            accepted=[]
            for candidate in candidates:
                verdict=assess_history(records[candidate["id"]],ctx.evidence)
                rid=candidate["id"]
                status=(verdict["status"],verdict.get("reason"),verdict.get("checks_pending",0))
                if last_status.get(rid)!=status:
                    transition={"event":"knowledge_assessment","previous_status":last_status[rid][0] if rid in last_status else None,
                                "evidence_count":len(ctx.evidence),**verdict}
                    ctx.audit.append(transition)
                    knowledge_decisions.append(transition)
                    last_status[rid]=status
                if verdict["status"]=="ACCEPTED":accepted.append(candidate)
            hits=accepted
        decision=confirm_six(ctx.evidence,available_tools=tools,exhausted=False)
        ctx.audit.append({"event":"confirmation_checkpoint","status":decision.status,"category":decision.category,"evidence_count":len(ctx.evidence),"attempted_tool_calls":len(used)})
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
            ctx.audit.append({"event":"tool_attempt","tool":t,"attempt_number":len(used),"layer":ctx.visited[-1] if ctx.visited else None})
            try:
                result=tools[t]()
                ctx.evidence.append({"tool":t,"layer":ctx.visited[-1] if ctx.visited else None,"result":result})
                tool_successes+=1
                ctx.audit.append({"event":"tool_success","tool":t,"evidence_index":len(ctx.evidence)-1})
            except Exception as exc:
                tool_failures+=1
                ctx.audit.append({"event":"tool_error","tool":t,"error_type":type(exc).__name__})
    if arm=="B4_knowledge":
        final_hits=[]
        for candidate in candidates:
            verdict=assess_history(records[candidate["id"]],ctx.evidence)
            rid=candidate["id"]
            status=(verdict["status"],verdict.get("reason"),verdict.get("checks_pending",0))
            if last_status.get(rid)!=status:
                transition={"event":"knowledge_assessment","previous_status":last_status[rid][0] if rid in last_status else None,
                            "evidence_count":len(ctx.evidence),**verdict}
                ctx.audit.append(transition)
                knowledge_decisions.append(transition)
                last_status[rid]=status
            if verdict["status"]=="ACCEPTED":final_hits.append(candidate)
        hits=final_hits
    d=confirm_six(ctx.evidence,available_tools=tools,exhausted=True)
    ctx.audit.append({"event":"confirmation_final","status":d.status,"category":d.category,"evidence_count":len(ctx.evidence),"attempted_tool_calls":len(used)})
    return {"id":case["id"],"arm":arm,"prediction":d.category,"status":d.status,
            "tool_calls":len(used),"attempted_tool_calls":len(used),"successful_observations":tool_successes,"failed_tool_calls":tool_failures,"supporting_evidence_refs":len(d.evidence_refs),"layers":len(ctx.visited),"llm_attempts":llm,"llm_failures":errors,
            "knowledge_hits":hits,"knowledge_assessments":knowledge_decisions,"knowledge_retrieval_status":("MATCHED" if hits else "ABSTAINED") if arm=="B4_knowledge" else "NOT_APPLICABLE","elapsed_ms":round((time.perf_counter()-start)*1000,3),
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
