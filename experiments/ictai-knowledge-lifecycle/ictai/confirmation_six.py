"""Six-category conservative confirmation. Evidence schema v1, read-only.
Independent from the v5.4 two-category baseline for paired comparisons.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Decision:
    status: str
    category: str
    evidence_refs: tuple[str, ...]
    reasons: tuple[str, ...]

CONTRACTS = {
    'MISSING_FILE': ('inspect_manifest','check_object_inventory'),
    'SCHEMA_DRIFT': ('inspect_schema_contract','inspect_observed_schema'),
    'DATA_QUALITY_ANOMALY': ('inspect_quality_rule','inspect_quality_measurement'),
    'PIPELINE_FAILURE': ('inspect_task_execution','read_run_events'),
    'FRESHNESS_VIOLATION': ('inspect_freshness_sla','inspect_arrival_timestamps'),
    'DEPENDENCY_FAILURE': ('query_lineage','check_upstream_health','read_run_events'),
}

def confirm_six(evidence, available_tools=None, exhausted=True):
    """Return CONFIRMED only on a single fully supported cause, otherwise review/abstain.

    Observations are trusted only as tool outputs; this is not production source attestation.
    Each supporting tool must return a dict with case-specific fields.
    """
    obs={}; refs={}; conflicts=[]
    for i,e in enumerate(evidence):
        if not isinstance(e,dict) or not isinstance(e.get('result'),dict): continue
        t=e.get('tool'); val=e['result']
        if t in obs and obs[t]!=val: conflicts.append('contradictory observations: '+str(t))
        obs[t]=val;refs[t]=f'evidence[{i}]/{t}'
    def istrue(t,k): return type(obs.get(t,{}).get(k)) is bool and obs[t][k] is True
    def isfalse(t,k): return type(obs.get(t,{}).get(k)) is bool and obs[t][k] is False
    candidates=[]
    def add(category, predicate):
        if predicate: candidates.append(category)
    inventory=obs.get('check_object_inventory',{})
    absent=isfalse('check_object_inventory','present') and (inventory.get('count') in (None,0))
    add('MISSING_FILE', istrue('inspect_manifest','expected') and absent)
    contract=obs.get('inspect_schema_contract',{}).get('columns')
    actual=obs.get('inspect_observed_schema',{}).get('columns')
    add('SCHEMA_DRIFT', isinstance(contract,list) and isinstance(actual,list) and all(isinstance(x,str) for x in contract+actual) and len(contract)==len(set(contract)) and len(actual)==len(set(actual)) and set(contract)!=set(actual))
    rule=obs.get('inspect_quality_rule',{}); measure=obs.get('inspect_quality_measurement',{})
    add('DATA_QUALITY_ANOMALY', istrue('inspect_quality_rule','active') and type(rule.get('threshold')) in (int,float) and type(measure.get('violations')) is int and measure['violations']>rule['threshold'] and measure.get('rule_id')==rule.get('rule_id') and isinstance(rule.get('rule_id'),str))
    add('PIPELINE_FAILURE', istrue('inspect_task_execution','failed') and istrue('read_run_events','execution_error') and obs['inspect_task_execution'].get('run_id')==obs['read_run_events'].get('run_id') and isinstance(obs['inspect_task_execution'].get('run_id'),str))
    sla=obs.get('inspect_freshness_sla',{}); arrival=obs.get('inspect_arrival_timestamps',{})
    add('FRESHNESS_VIOLATION', istrue('inspect_freshness_sla','active') and type(sla.get('deadline_epoch')) in (int,float) and type(arrival.get('arrival_epoch')) in (int,float) and arrival['arrival_epoch']>sla['deadline_epoch'] and arrival.get('dataset_id')==sla.get('dataset_id') and isinstance(sla.get('dataset_id'),str))
    lineage=obs.get('query_lineage',{}); upstream=obs.get('check_upstream_health',{}); run=obs.get('read_run_events',{})
    add('DEPENDENCY_FAILURE', istrue('query_lineage','depends_on_upstream') and isfalse('check_upstream_health','healthy') and istrue('read_run_events','blocked_by_upstream') and lineage.get('upstream_id')==upstream.get('upstream_id')==run.get('upstream_id') and isinstance(lineage.get('upstream_id'),str))
    # An upstream or schema failure may also manifest as a pipeline failure.
    # Multiple positive categories are not collapsed into an invented single cause.
    if conflicts or len(candidates)>1:
        return Decision('REVIEW_REQUIRED','INSUFFICIENT_EVIDENCE',tuple(refs.values()),tuple(conflicts or ['multiple supported candidate causes']))
    if not candidates:
        return Decision('ABSTAINED' if exhausted else 'INVESTIGATING','INSUFFICIENT_EVIDENCE',(),('no sufficiently corroborated category',))
    cat=candidates[0]; required=CONTRACTS[cat]
    # Do not confirm if available evidence from other categories is still pending;
    # this conservative gate can increase tool calls, to be measured experimentally.
    available=set(available_tools or {})
    relevant=set().union(*map(set,CONTRACTS.values()))
    pending=sorted((available & relevant)-set(obs))
    if pending:
        return Decision('REVIEW_REQUIRED' if exhausted else 'PROVISIONAL_RCA',cat,tuple(refs[t] for t in required),('unchecked available corroboration',))
    return Decision('CONFIRMED',cat,tuple(refs[t] for t in required),('corroborated tool evidence',))
