"""Paired, fixture-based pilot. Synthetic cases, not field observations."""
from dataclasses import dataclass
from time import perf_counter_ns
from .controller import investigate, investigate_dynamic, LAYER_TOOLS, Investigation, select_next_layer
from .rca import classify_root_cause
from .knowledge import KnowledgeRepository

@dataclass(frozen=True)
class Case:
    case_id: str
    signal: str
    truth: str
    observations: dict


def cases():
    # Independent labels and inputs. Signals are initial alert hints, not hidden truth.
    return [
      Case('MF01','missing_file','MISSING_FILE',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0}}),
      Case('MF02','schema_drift','MISSING_FILE',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0},'inspect_schema_contract':{'columns':['id']},'inspect_observed_schema':{'columns':['id']}}),
      Case('MF03','missing_file','MISSING_FILE',{'inspect_manifest':{'expected':True},'check_object_inventory':{'count':0}}),
      Case('SD01','schema_drift','SCHEMA_DRIFT',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':True,'count':1},'inspect_schema_contract':{'columns':['id','price']},'inspect_observed_schema':{'columns':['id','amount']}}),
      Case('SD02','missing_file','SCHEMA_DRIFT',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':True,'count':1},'inspect_schema_contract':{'columns':['id']},'inspect_observed_schema':{'columns':['id','extra']}}),
      Case('SD03','schema_drift','SCHEMA_DRIFT',{'inspect_schema_contract':{'columns':['id','value']},'inspect_observed_schema':{'columns':['id']}}),
      Case('AB01','missing_file','INSUFFICIENT_EVIDENCE',{'inspect_manifest':{'expected':True}}),
      Case('AB02','schema_drift','INSUFFICIENT_EVIDENCE',{'inspect_schema_contract':{'columns':['id']}}),
      Case('AB03','missing_file','INSUFFICIENT_EVIDENCE',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':True,'count':1},'inspect_schema_contract':{'columns':['id']},'inspect_observed_schema':{'columns':['id']}}),
      Case('AB04','schema_drift','INSUFFICIENT_EVIDENCE',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0},'inspect_schema_contract':{'columns':['id']},'inspect_observed_schema':{'columns':['other']}}),
    ]

def _tools(case):
    # Fresh immutable-by-convention fixture results; no external systems.
    return {name:(lambda v=value: dict(v)) for name,value in case.observations.items()}

def _knowledge_order(signal, matches):
    # Knowledge can only prioritize an existing evidence layer; never classify.
    preferred = next((m.suggested_layer for m in matches if m.suggested_layer in LAYER_TOOLS),None)
    return preferred

def knowledge_dynamic(case, repo, max_calls=3):
    matches=repo.query(case.signal)
    preferred=_knowledge_order(case.signal,matches)
    tools=_tools(case)
    ctx=Investigation(case.case_id)
    calls=0
    while len(ctx.visited)<5:
        if not ctx.visited and preferred and any(t in tools for t in LAYER_TOOLS[preferred]):
            layer=preferred
        else:
            layer=select_next_layer(case.signal,ctx.visited,tools,ctx.evidence)
        if layer is None: break
        ctx.visited.append(layer)
        ctx.audit.append({'event':'layer_selected','layer':layer,'knowledge_applied':len(ctx.visited)==1 and layer==preferred})
        for name in LAYER_TOOLS[layer]:
            if name not in tools: continue
            if calls>=max_calls:
                ctx.status='BUDGET_EXHAUSTED';return ctx,matches
            calls+=1
            try:
                ctx.evidence.append({'layer':layer,'tool':name,'result':tools[name]()})
                ctx.audit.append({'step':calls,'layer':layer,'tool':name,'outcome':'ok'})
            except Exception as exc:
                ctx.audit.append({'step':calls,'layer':layer,'tool':name,'outcome':'error','error_type':type(exc).__name__})
    ctx.status='EVIDENCE_COLLECTED' if ctx.evidence else 'INSUFFICIENT_EVIDENCE'
    return ctx,matches

def pilot_repo():
    # Training-only demonstration records; not drawn from evaluation cases.
    return KnowledgeRepository([
       {'id':'TRAIN-RUNBOOK-1','kind':'runbook','signal':'missing_file','suggested_layer':'source','summary':'Check expected delivery and inventory','verified':True,'reviewed_on':'2026-01-01','expires_on':'2027-01-01'},
       {'id':'TRAIN-RUNBOOK-2','kind':'runbook','signal':'schema_drift','suggested_layer':'validation','summary':'Compare schema contract to observed columns','verified':True,'reviewed_on':'2026-01-01','expires_on':'2027-01-01'}
    ],as_of='2026-10-22')

def run_pilot(max_calls=3, repo=None):
    repo=repo or pilot_repo()
    rows=[]
    for case in cases():
        for arm in ('B1_fixed','B2_dynamic','B3_knowledge'):
            tools=_tools(case)
            start=perf_counter_ns()
            if arm=='B1_fixed': ctx=investigate(case.case_id,tools,max_calls=max_calls); matches=[]
            elif arm=='B2_dynamic': ctx=investigate_dynamic(case.case_id,case.signal,tools,max_calls=max_calls); matches=[]
            else: ctx,matches=knowledge_dynamic(case,repo,max_calls=max_calls)
            result=classify_root_cause(ctx)
            elapsed_ns=perf_counter_ns()-start
            rows.append({'case_id':case.case_id,'arm':arm,'signal':case.signal,'truth':case.truth,
                         'predicted':result.category,'rca_status':result.status,'correct':int(result.category==case.truth),
                         'tool_calls':sum('step' in a for a in ctx.audit),'layers_visited':len(ctx.visited),
                         'elapsed_ns':elapsed_ns,'controller_status':ctx.status,'evidence_refs':'|'.join(result.evidence_refs),
                         'visited':'|'.join(ctx.visited),'knowledge_ids':'|'.join(m.record_id for m in matches)})
    return rows

def summarize(rows):
    result=[]
    for arm in ('B1_fixed','B2_dynamic','B3_knowledge'):
        subset=[r for r in rows if r['arm']==arm]
        result.append({'arm':arm,'n':len(subset),'accuracy':sum(r['correct'] for r in subset)/len(subset),
                       'mean_tool_calls':sum(r['tool_calls'] for r in subset)/len(subset),
                       'mean_layers_visited':sum(r['layers_visited'] for r in subset)/len(subset),
                       'abstentions':sum(r['predicted']=='INSUFFICIENT_EVIDENCE' for r in subset),
                       'mean_elapsed_ms':sum(r['elapsed_ns'] for r in subset)/len(subset)/1e6})
    return result
