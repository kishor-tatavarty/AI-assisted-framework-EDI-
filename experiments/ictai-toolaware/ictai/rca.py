"""Evidence-only deterministic RCA baseline for ICTAI; no learned confidence."""
from dataclasses import dataclass
from typing import Optional
from .controller import Investigation

@dataclass(frozen=True)
class RCAResult:
    category: str
    status: str
    evidence_refs: tuple[str, ...]
    reasons: tuple[str, ...]


def classify_root_cause(ctx: Investigation) -> RCAResult:
    """Classify using explicit cross-tool agreement, never incident ID/signal/layer.

    Contract: manifest expected=True; inventory present=False or count=0;
    schema contract/observed schema each has a list of column names.
    A schema difference indicates drift in this minimal prototype; production
    deployments need type/nullability/compatibility policies.
    """
    observations = {}
    for i, entry in enumerate(ctx.evidence):
        if not isinstance(entry, dict):
            continue
        tool, value = entry.get('tool'), entry.get('result')
        if tool not in ('inspect_manifest', 'check_object_inventory',
                        'inspect_schema_contract', 'inspect_observed_schema') or not isinstance(value, dict):
            continue
        observations.setdefault(tool, []).append((f'evidence[{i}]/{tool}', value))

    reasons=[]
    refs=[]
    def unanimous(tool, field):
        vals=[(ref, d[field]) for ref,d in observations.get(tool, []) if field in d]
        if not vals: return None, ()
        if any(type(v) is not type(vals[0][1]) or v != vals[0][1] for _,v in vals):
            reasons.append(f'conflicting {tool}.{field}')
            return None, ()
        return vals[0][1], tuple(ref for ref,_ in vals)

    expected, er = unanimous('inspect_manifest','expected')
    present, pr = unanimous('check_object_inventory','present')
    count, cr = unanimous('check_object_inventory','count')
    if present is not None and type(present) is not bool:
        reasons.append('invalid inventory present type'); present=None
    if count is not None and (type(count) is not int or count < 0):
        reasons.append('invalid inventory count'); count=None
    if present is not None and count is not None and present != (count > 0):
        reasons.append('conflicting inventory presence and count')
    missing = expected is True and ((present is False and count is None) or
             (count == 0 and present is None) or (present is False and count == 0))
    if missing: refs.extend(er + pr + cr)

    expected_cols, ecr = unanimous('inspect_schema_contract','columns')
    observed_cols, ocr = unanimous('inspect_observed_schema','columns')
    schema_drift=False
    if expected_cols is not None and observed_cols is not None:
        if (isinstance(expected_cols,list) and isinstance(observed_cols,list) and
            all(isinstance(x,str) for x in expected_cols + observed_cols) and
            len(expected_cols)==len(set(expected_cols)) and len(observed_cols)==len(set(observed_cols))):
            schema_drift = set(expected_cols) != set(observed_cols)
        else:
            reasons.append('invalid schema columns')
    if schema_drift: refs.extend(ecr + ocr)
    if reasons or (missing and schema_drift):
        if missing and schema_drift: reasons.append('multiple supported candidate causes')
        return RCAResult('INSUFFICIENT_EVIDENCE','REVIEW_REQUIRED',tuple(dict.fromkeys(refs)),tuple(reasons))
    if missing:
        return RCAResult('MISSING_FILE','CLASSIFIED',tuple(dict.fromkeys(refs)),('manifest and inventory corroborate missing expected input',))
    if schema_drift:
        return RCAResult('SCHEMA_DRIFT','CLASSIFIED',tuple(dict.fromkeys(refs)),('expected and observed column sets differ',))
    return RCAResult('INSUFFICIENT_EVIDENCE','ABSTAINED',(),('no supported root cause from available evidence',))


def investigate_and_classify(incident_id, signal, available_tools, max_calls=4, max_layers=5):
    from .controller import investigate_dynamic
    ctx=investigate_dynamic(incident_id,signal,available_tools,max_calls,max_layers)
    result=classify_root_cause(ctx)
    ctx.audit.append({'event':'rca_decision','category':result.category,
                      'status':result.status,'evidence_refs':list(result.evidence_refs)})
    return ctx,result
