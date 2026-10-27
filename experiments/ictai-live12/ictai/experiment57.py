"""Paired development pilot: fixed, symptom, mock LLM, mock LLM + knowledge."""
from .experiment55 import investigate_six
from .controller import Investigation
from .confirmation_six import confirm_six
from .reasoning_context import propose_with_symptoms
from .experiment55 import EXTRA_TOOLS
from .controller import LAYER_TOOLS

LAYERS={k:tuple(dict.fromkeys(v+EXTRA_TOOLS.get(k,()))) for k,v in LAYER_TOOLS.items()}
ORDER=('source','validation','pipeline','lineage','impact')
CUES={'source':('missing','file','freshness','late','arrival','delivery'), 'validation':('schema','column','quality','invalid','null'), 'pipeline':('task','dag','failed','dependency','upstream')}
def choose_layer(symptoms,tools,visited,arm,proposal=None,knowledge=()):
    eligible=[k for k in ORDER if k not in visited and any(t in tools for t in LAYERS[k])]
    if not eligible:return None,'none'
    if arm=='B1_fixed':return eligible[0],'fixed'
    if arm=='B4_knowledge' and knowledge:
        for k in knowledge:
            if k in eligible:return k,'knowledge'
    if arm in ('B3_llm','B4_knowledge') and proposal in eligible:return proposal,'llm'
    return sorted(eligible,key=lambda k:(-sum(c in symptoms.lower() for c in CUES.get(k,())),ORDER.index(k)))[0],'symptom'

def run_case(case,arm,model=None,knowledge=(),budget=12):
    if arm not in ('B1_fixed','B2_dynamic','B3_llm','B4_knowledge'):raise ValueError('invalid arm')
    if arm in ('B3_llm','B4_knowledge') and model is None:raise ValueError('model required')
    tools={k:(lambda value=v:dict(value)) for k,v in case['tools'].items()}
    ctx=Investigation(case['id']);attempted=set();llm_calls=0
    while len(attempted)<budget:
        decision=confirm_six(ctx.evidence,available_tools=tools,exhausted=False)
        if decision.status in ('CONFIRMED','REVIEW_REQUIRED'):break
        if decision.status=='PROVISIONAL_RCA':
            pending=[t for t in tools if t not in attempted]
        else:
            if len(ctx.visited)>=5:break
            proposed=None
            if arm in ('B3_llm','B4_knowledge') and llm_calls<4:
                llm_calls+=1
                p=propose_with_symptoms(ctx,tools,model,case['symptoms'])
                proposed=p.layer if p.accepted else None
                ctx.audit.append({'event':'llm_proposal','accepted':p.accepted,'reason':p.reason})
            layer,why=choose_layer(case['symptoms'],tools,ctx.visited,arm,proposed,knowledge)
            if layer is None:break
            ctx.visited.append(layer)
            ctx.audit.append({'event':'layer_selected','layer':layer,'why':why})
            pending=[t for t in LAYERS[layer] if t in tools and t not in attempted]
        if not pending:break
        for t in pending:
            if len(attempted)>=budget:break
            attempted.add(t)
            try:ctx.evidence.append({'tool':t,'layer':ctx.visited[-1],'result':tools[t]()})
            except Exception as e:ctx.audit.append({'event':'tool_error','tool':t,'type':type(e).__name__})
    d=confirm_six(ctx.evidence,available_tools=tools,exhausted=True)
    return {'id':case['id'],'arm':arm,'prediction':d.category,'status':d.status,'tool_calls':len(attempted),'layers':len(ctx.visited),'llm_calls':llm_calls,'audit':ctx.audit}
