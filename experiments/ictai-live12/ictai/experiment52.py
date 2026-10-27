"""Bounded confirmation runner; not a publication benchmark."""
from .controller import Investigation, LAYER_TOOLS, select_next_layer
from .confirmation import confirm

def investigate_confirmed(incident_id, signal, tools, max_calls=12, max_rounds=2):
    if not isinstance(max_calls, int) or max_calls < 1 or not isinstance(max_rounds, int) or max_rounds < 0:
        raise ValueError('invalid budget')
    ctx = Investigation(incident_id)
    attempted = set()
    rounds = 0
    while len(attempted) < max_calls:
        decision = confirm(ctx, tools)
        if decision.status in ('CONFIRMED', 'REVIEW_REQUIRED'):
            break
        if decision.status == 'PROVISIONAL_RCA':
            rounds += 1
            if rounds > max_rounds:
                break
            candidates = list(decision.next_tools)
        else:
            layer = select_next_layer(signal, ctx.visited, tools, ctx.evidence)
            if layer is None:
                break
            ctx.visited.append(layer)
            ctx.audit.append({'event':'layer_selected','layer':layer})
            candidates = [t for t in LAYER_TOOLS[layer] if t in tools]
        for tool in candidates:
            if tool in attempted or len(attempted) >= max_calls:
                continue
            attempted.add(tool)
            try:
                value = tools[tool]()
                ctx.evidence.append({'tool':tool, 'result':value, 'layer':'confirmation' if rounds else ctx.visited[-1]})
                ctx.audit.append({'event':'tool_result','tool':tool,'outcome':'ok'})
            except Exception as exc:
                ctx.audit.append({'event':'tool_result','tool':tool,'outcome':'error','error_type':type(exc).__name__})
        if not candidates:
            break
    decision = confirm(ctx, tools, exhausted=True)
    ctx.status = decision.status
    ctx.audit.append({'event':'confirmation','status':decision.status,'category':decision.category,
                      'evidence_refs':list(decision.evidence_refs),'reasons':list(decision.reasons)})
    return ctx, decision
