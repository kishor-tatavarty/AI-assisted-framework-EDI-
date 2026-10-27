"""Fail-closed historical knowledge policy. History is advisory, never RCA evidence."""
from datetime import datetime, timezone

def assess_history(record, evidence=(), now=None):
    """Validate provenance and check explicitly declared claims against current evidence.

    Only claims with declared tool/key/expected values are machine-checkable.
    Unspecified claims cannot be declared consistent; they remain unassessed.
    """
    rid=record.get("id") if isinstance(record,dict) else None
    result={"record_id":rid,"status":"REJECTED","reason":"invalid_provenance"}
    if not isinstance(record,dict):return result
    required=("id","source_incident_id","source_system","reviewer_id","verified_at","valid_from","valid_until","layer","description")
    if not all(isinstance(record.get(k),str) and record[k].strip() for k in required):return result
    if record.get("verified") is not True or record.get("stale") is not False:
        return {**result,"reason":"not_verified_or_stale"}
    def parse(s):
        dt=datetime.fromisoformat(s.replace("Z","+00:00"))
        if dt.tzinfo is None:raise ValueError("timezone required")
        return dt.astimezone(timezone.utc)
    try:
        verified_at,start,end=map(parse,(record["verified_at"],record["valid_from"],record["valid_until"]))
        current=now or datetime.now(timezone.utc)
        if not(start<=current<=end and verified_at<=current):return {**result,"reason":"outside_validity_window"}
    except (ValueError,TypeError):return {**result,"reason":"invalid_dates"}
    checks=record.get("expected_current_observations",[])
    if not isinstance(checks,list):return {**result,"reason":"invalid_checks"}
    observations={e.get("tool"):e.get("result") for e in evidence if isinstance(e,dict) and isinstance(e.get("result"),dict)}
    for check in checks:
        if not isinstance(check,dict) or not isinstance(check.get("tool"),str) or not isinstance(check.get("key"),str) or "equals" not in check:
            return {**result,"reason":"invalid_checks"}
        observed=observations.get(check["tool"],{})
        if check["key"] in observed and (type(observed[check["key"]]) is not type(check["equals"]) or observed[check["key"]]!=check["equals"]):
            return {**result,"status":"REJECTED","reason":"contradicted_by_current_evidence","tool":check["tool"],"key":check["key"]}
    pending=[{"tool":c["tool"],"key":c["key"]} for c in checks if c["key"] not in observations.get(c["tool"],{})]
    if pending:
        return {**result,"status":"PENDING","reason":"awaiting_current_evidence","checks_pending":len(pending),"missing_checks":pending}
    return {**result,"status":"ACCEPTED","reason":"current_observations_consistent","checks_pending":0}
