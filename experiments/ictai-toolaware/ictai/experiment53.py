"""LLM-assisted bounded investigation with deterministic fallback and RCA gate."""
from .controller import Investigation, LAYER_TOOLS, select_next_layer
from .confirmation import confirm
from .llm_reasoner import propose

def investigate_llm(incident_id, signal, tools, model_callable, max_calls=12, max_llm_calls=4, max_layers=5, max_rounds=2):
    if any(type(v) is not int or v<0 for v in (max_calls,max_llm_calls,max_layers,max_rounds)) or max_calls<1 or max_layers<1:
        raise ValueError('invalid budgets')
    ctx=Investigation(incident_id)
    attempted=set(); llm_calls=0; rounds=0
    while len(attempted)<max_calls:
        decision=confirm(ctx,tools)
        if decision.status in ('CONFIRMED','REVIEW_REQUIRED'): break
        if decision.status=='PROVISIONAL_RCA':
            rounds+=1
            if rounds>max_rounds: break
            candidates=list(decision.next_tools)
        else:
            layer=None
            if llm_calls<max_llm_calls and len(ctx.visited)<max_layers:
                llm_calls+=1
                suggestion=propose(ctx,tools,model_callable)
                ctx.audit.append({'event':'llm_proposal','accepted':suggestion.accepted,'reason':suggestion.reason,'layer':suggestion.layer})
                if suggestion.accepted: layer=suggestion.layer
            if layer is None and len(ctx.visited)<max_layers:
                layer=select_next_layer(signal,ctx.visited,tools,ctx.evidence)
                ctx.audit.append({'event':'fallback','layer':layer})
            if layer is None: break
            ctx.visited.append(layer)
            ctx.audit.append({'event':'layer_selected','layer':layer})
            candidates=[t for t in LAYER_TOOLS[layer] if t in tools]
        pending=[t for t in candidates if t not in attempted]
        if not pending: break
        for tool in pending:
            if len(attempted)>=max_calls: break
            attempted.add(tool)
            try:
                ctx.evidence.append({'tool':tool,'result':tools[tool](),'layer':ctx.visited[-1] if ctx.visited else 'confirmation'})
                ctx.audit.append({'event':'tool_result','tool':tool,'outcome':'ok'})
            except Exception as exc:
                ctx.audit.append({'event':'tool_result','tool':tool,'outcome':'error','error_type':type(exc).__name__})
    decision=confirm(ctx,tools,exhausted=True)
    ctx.status=decision.status
    ctx.audit.append({'event':'confirmation','status':decision.status,'category':decision.category,'evidence_refs':list(decision.evidence_refs),'llm_calls':llm_calls,'tool_calls':len(attempted)})
    return ctx,decision
