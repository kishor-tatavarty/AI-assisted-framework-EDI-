"""Six-category bounded end-to-end investigation; gold labels never enter routing."""
from .controller import Investigation, LAYER_TOOLS, select_next_layer
from .reasoning_context import propose_with_symptoms
from .confirmation_six import confirm_six

EXTRA_TOOLS = {
    'validation': ('inspect_quality_rule','inspect_quality_measurement'),
    'source': ('inspect_freshness_sla','inspect_arrival_timestamps'),
}

def investigate_six(incident_id, symptoms, tools, model_callable=None, *,
                    max_tool_calls=12, max_llm_calls=4, max_layers=5, max_rounds=2):
    if not isinstance(symptoms,str) or not symptoms.strip(): raise ValueError('symptoms required')
    if max_tool_calls<1 or max_layers<1 or max_llm_calls<0 or max_rounds<0: raise ValueError('invalid budgets')
    ctx=Investigation(incident_id)
    attempted=set(); llm_attempts=0; rounds=0
    layers={k:tuple(dict.fromkeys(v+EXTRA_TOOLS.get(k,()))) for k,v in LAYER_TOOLS.items()}
    while len(attempted)<max_tool_calls:
        decision=confirm_six(ctx.evidence, available_tools=tools, exhausted=False)
        if decision.status=='CONFIRMED': break
        if decision.status=='REVIEW_REQUIRED':
            ctx.audit.append({'event':'conflict','reasons':list(decision.reasons)})
            break
        if decision.status=='PROVISIONAL_RCA':
            rounds+=1
            if rounds>max_rounds: break
            pending=[t for t in tools if t not in attempted]
            ctx.audit.append({'event':'confirmation_round','round':rounds,'pending':pending})
        else:
            if len(ctx.visited)>=max_layers: break
            layer=None
            if model_callable is not None and llm_attempts<max_llm_calls:
                llm_attempts+=1
                proposal=propose_with_symptoms(ctx,tools,model_callable,symptoms)
                if proposal.accepted and any(t in tools for t in layers[proposal.layer]):
                    layer=proposal.layer
                ctx.audit.append({'event':'llm_proposal','accepted':layer is not None,
                                  'reason':proposal.reason,'layer':proposal.layer})
            if layer is None:
                # Deterministic symptom routing, not ground-truth labels.
                lower=symptoms.lower()
                cues={'validation':('schema','column','invalid','duplicate','quality','null'),
                      'source':('missing','file','late','freshness','arrival','delivery'),
                      'pipeline':('task','dag','job','orchestration','failed','dependency','upstream')}
                order=sorted(layers,key=lambda k: -sum(cue in lower for cue in cues.get(k,())))
                layer=next((k for k in order if k not in ctx.visited and any(t in tools for t in layers[k])),None)
                ctx.audit.append({'event':'fallback','layer':layer})
            if layer is None or layer in ctx.visited: break
            ctx.visited.append(layer)
            ctx.audit.append({'event':'layer_selected','layer':layer})
            pending=[t for t in layers[layer] if t in tools and t not in attempted]
        if not pending: break
        for t in pending:
            if len(attempted)>=max_tool_calls: break
            attempted.add(t)
            try:
                result=tools[t]()
                ctx.evidence.append({'layer':ctx.visited[-1] if ctx.visited else 'confirmation','tool':t,'result':result})
                ctx.audit.append({'event':'tool_result','tool':t,'outcome':'ok'})
            except Exception as exc:
                ctx.audit.append({'event':'tool_result','tool':t,'outcome':'error','error_type':type(exc).__name__})
    decision=confirm_six(ctx.evidence,available_tools=tools,exhausted=True)
    ctx.status=decision.status
    ctx.audit.append({'event':'final','status':decision.status,'category':decision.category,
                      'evidence_refs':list(decision.evidence_refs),'llm_attempts':llm_attempts,
                      'tool_calls':len(attempted)})
    return ctx,decision
