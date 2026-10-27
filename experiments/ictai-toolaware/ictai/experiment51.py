"""Phase 5.1 paired experiment with identical per-tool stopping across arms."""
from time import perf_counter_ns
from .controller import Investigation, LAYER_TOOLS, select_next_layer
from .rca import classify_root_cause
from .experiment import cases, _tools, pilot_repo, _knowledge_order

ARMS = ('B1_fixed', 'B2_dynamic', 'B3_knowledge')
FIXED_ORDER = ('source', 'validation', 'pipeline', 'lineage', 'impact')

def run_case(case, arm, max_calls=3, repo=None):
    if arm not in ARMS: raise ValueError('unknown arm')
    if type(max_calls) is not int or max_calls < 1: raise ValueError('positive max_calls required')
    tools = _tools(case)
    ctx = Investigation(case.case_id)
    repo = repo if repo is not None else pilot_repo()
    matches = repo.query(case.signal) if arm == 'B3_knowledge' else []
    preferred = _knowledge_order(case.signal, matches) if matches else None
    calls = 0
    start = perf_counter_ns()
    while len(ctx.visited) < 5 and calls < max_calls:
        if arm == 'B1_fixed':
            layer = next((x for x in FIXED_ORDER if x not in ctx.visited and any(t in tools for t in LAYER_TOOLS[x])), None)
        elif arm == 'B3_knowledge' and not ctx.visited and preferred and any(t in tools for t in LAYER_TOOLS[preferred]):
            layer = preferred
        else:
            layer = select_next_layer(case.signal, ctx.visited, tools, ctx.evidence)
        if layer is None: break
        ctx.visited.append(layer)
        ctx.audit.append({'event':'layer_selected','layer':layer})
        for tool in LAYER_TOOLS[layer]:
            if tool not in tools: continue
            if calls >= max_calls: break
            calls += 1
            try:
                ctx.evidence.append({'layer':layer,'tool':tool,'result':tools[tool]()})
                ctx.audit.append({'step':calls,'tool':tool,'layer':layer,'outcome':'ok'})
            except Exception as exc:
                ctx.audit.append({'step':calls,'tool':tool,'layer':layer,'outcome':'error','error_type':type(exc).__name__})
            rca = classify_root_cause(ctx)
            # Stop only when exactly one supported RCA is established; never stop on abstention.
            if rca.status == 'CLASSIFIED':
                ctx.status = 'EVIDENCE_SUFFICIENT'
                ctx.audit.append({'event':'early_stop','calls':calls,'evidence_refs':list(rca.evidence_refs)})
                return ctx, rca, matches, perf_counter_ns()-start
    rca = classify_root_cause(ctx)
    ctx.status = 'BUDGET_EXHAUSTED' if calls >= max_calls and rca.status != 'CLASSIFIED' else ('EVIDENCE_COLLECTED' if ctx.evidence else 'INSUFFICIENT_EVIDENCE')
    return ctx, rca, matches, perf_counter_ns()-start

def run_experiment(max_calls=3, repo=None):
    rows=[]
    for case in cases():
        for arm in ARMS:
            ctx,rca,matches,elapsed=run_case(case,arm,max_calls,repo)
            rows.append({'case_id':case.case_id,'arm':arm,'signal':case.signal,'truth':case.truth,
                         'predicted':rca.category,'rca_status':rca.status,'correct':int(rca.category==case.truth),
                         'tool_calls':sum('step' in a for a in ctx.audit),'layers_visited':len(ctx.visited),
                         'elapsed_ns':elapsed,'controller_status':ctx.status,'evidence_refs':'|'.join(rca.evidence_refs),
                         'visited':'|'.join(ctx.visited),'knowledge_ids':'|'.join(m.record_id for m in matches),
                         'early_stop':int(ctx.status=='EVIDENCE_SUFFICIENT')})
    return rows

def summarize(rows):
    out=[]
    for arm in ARMS:
        part=[r for r in rows if r['arm']==arm]
        out.append({'arm':arm,'n':len(part),'accuracy':sum(r['correct'] for r in part)/len(part),
                    'mean_tool_calls':sum(r['tool_calls'] for r in part)/len(part),
                    'mean_layers_visited':sum(r['layers_visited'] for r in part)/len(part),
                    'abstentions':sum(r['predicted']=='INSUFFICIENT_EVIDENCE' for r in part),
                    'early_stops':sum(r['early_stop'] for r in part),
                    'mean_elapsed_ms':sum(r['elapsed_ns'] for r in part)/len(part)/1e6})
    return out

def error_analysis(rows):
    return [dict(r, error_type=('CORRECT_ABSTENTION' if r['truth']=='INSUFFICIENT_EVIDENCE' else 'MISSED_SUPPORTED_RCA')
                 if r['predicted']=='INSUFFICIENT_EVIDENCE' else
                 ('FALSE_POSITIVE_RCA' if r['truth']=='INSUFFICIENT_EVIDENCE' else 'WRONG_RCA'))
            for r in rows if not r['correct'] or r['predicted']=='INSUFFICIENT_EVIDENCE']
