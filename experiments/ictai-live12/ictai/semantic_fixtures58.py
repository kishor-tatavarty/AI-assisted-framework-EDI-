
"""Transparent, controlled synthetic stress fixtures. Not independently collected."""
import json
from pathlib import Path
SPECS={
"MISSING_FILE":("source",{"inspect_manifest":{"expected":True},"check_object_inventory":{"present":False,"count":0}},[
"Partner reconciliation placed the overnight export on hold; downstream cannot resolve input.",
"Vendor shipment is pending approval, although the scheduler reports an artifact lookup problem."]),
"SCHEMA_DRIFT":("validation",{"inspect_schema_contract":{"columns":["id","customer_ref"]},"inspect_observed_schema":{"columns":["id","account_reference"]}},[
"Spark cannot resolve customer_ref after release notes renamed it account_reference.",
"The projection fails after the supplier's field-standardization rollout."]),
"DATA_QUALITY_ANOMALY":("validation",{"inspect_quality_rule":{"active":True,"rule_id":"nulls","threshold":2},"inspect_quality_measurement":{"rule_id":"nulls","violations":9}},[
"Reporting completed but analysts noticed many blank customer identifiers.",
"Dashboard figures contain unexpected gaps despite successful execution."]),
"PIPELINE_FAILURE":("pipeline",{"inspect_task_execution":{"failed":True,"run_id":"r1"},"read_run_events":{"execution_error":True,"run_id":"r1"}},[
"Worker process exited unexpectedly after the scheduler launched the transformation.",
"Orchestration worker stopped mid-run with an execution exception."]),
"FRESHNESS_VIOLATION":("source",{"inspect_freshness_sla":{"active":True,"dataset_id":"d1","deadline_epoch":100},"inspect_arrival_timestamps":{"dataset_id":"d1","arrival_epoch":130}},[
"Morning dashboard still displays yesterday's figures after reporting deadline.",
"Analysts complain the feed looks old even though job status is green."]),
"DEPENDENCY_FAILURE":("lineage",{"query_lineage":{"depends_on_upstream":True,"upstream_id":"u1"},"check_upstream_health":{"healthy":False,"upstream_id":"u1"},"read_run_events":{"blocked_by_upstream":True,"upstream_id":"u1"}},[
"Upstream reference service was unavailable and downstream processing is waiting.",
"Nightly task stalled because a prerequisite service did not respond."])
}
DECOY={
"source":{"inspect_manifest":{"expected":False},"check_object_inventory":{"present":True,"count":1}},
"validation":{"inspect_schema_contract":{"columns":["id"]},"inspect_observed_schema":{"columns":["id"]}},
"pipeline":{"inspect_task_execution":{"failed":False,"run_id":"other"},"read_run_events":{"execution_error":False,"run_id":"other"}},
"lineage":{"query_lineage":{"depends_on_upstream":False,"upstream_id":"other"},"check_upstream_health":{"healthy":True,"upstream_id":"other"}}
}
def build(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    cases=[];gold={};history=[]
    for category,(layer,truth,phrases) in SPECS.items():
        for j in range(4):
            id=f"sem58-{category.lower()}-{j+1:02}"
            symptom=phrases[j%2]
            if j>=2:symptom="Operational ticket: "+symptom+" Do not assume the alert category."
            decoy="pipeline" if layer!="pipeline" else "source"
            tools={**DECOY[decoy],**truth}
            if j==3:
                tools.pop(list(truth)[-1])
                gold[id]="INSUFFICIENT_EVIDENCE"
            else:gold[id]=category
            cases.append({"id":id,"symptoms":symptom,"tools":tools,"type":"semantic" if j%2==0 else "cross_source"})
        for j,phrase in enumerate(phrases):
            history.append({"id":f"train-{category.lower()}-{j}","description":phrase,
                            "layer":layer,"verified":True,"stale":False})
    for filename,data in [("semantic_inputs_DEV.json",cases),("semantic_gold_DEV_ONLY.json",gold),("historical_train_only.json",history)]:
        (folder/filename).write_text(json.dumps(data,indent=2))
    return cases,gold,history
