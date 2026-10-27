# Incident-informed ingestion replay with Airflow task support

This extension implements six scenarios described by the incident contributor.
At the user's request, an Airflow-compatible Python task replaces Matillion and
a local inventory reference HTTP service replaces inaccessible SAP HANA.

**These are generated, incident-informed local replays, not preserved production
incidents or measurements from production systems.** No production credentials
are required for offline use. The optional live comparison uses the OpenAI API
only when explicitly invoked with the user's credential.

## What is executed

The task reads real generated CSV files, validates columns and integer values,
loads local SQLite raw/fact tables in a transaction, writes execution records,
and contacts a local HTTP endpoint for the dependency case. Evidence adapters
inspect those files, tables, records and endpoint. A deterministic controller
then proposes a category and a rule-based recommendation with human approval.
The separate live runner adds model-selected investigation order and a live
model diagnosis/recommendation, checked against the same replay evidence rules.

| Case | Contributor's account | Implemented replay |
| --- | --- | --- |
| 01 | Supplier file absent; current-date rows missing | Missing local delivery after a configured deadline |
| 02 | Demand file contains extra columns beyond 14 | Generated 14-column contract and 16-column delivered CSV |
| 03 | Dollar sign in integer revenue; load fails | Integer parser rejects generated `$100`; transaction does not publish rows |
| 04 | Current-month FX rates absent; incorrect converted values | Generated old rates and explicit latest-rate fallback; output traces the selected rate |
| 05 | Matillion server/package failure; source exists, facts empty | Airflow-compatible task raises an injected worker dependency ImportError |
| 06 | SAP HANA memory incident blocks inventory | Local inventory reference endpoint returns HTTP 503, linked to the failed task |

Unknown historical details are listed in `ictai_replay/scenarios.py`. Column
names, row values, fixture dates/rates, error strings and runtime flags are
generated parameters. For case 04, the historical lookup SQL was not supplied:
the fallback implemented here is a test hypothesis, not an established fact
about the incident. Case 05 exercises one representative load; it does not
reproduce every historically failed fact table. Case 06 does not reproduce
SAP HANA, its memory behavior, or its logs.

## Run locally

Use Python 3.10 or later. The direct runner uses only the Python standard library.
From this directory:

```text
python -m unittest discover -s tests -v
python run_replays.py --output results/failures
python run_replays.py --output results/recovered --recovered
```

The runner starts and stops a local HTTP service on `127.0.0.1` using an ephemeral
port. Local socket permission is required. It never calls an external reference
endpoint. Run in a writable directory. Re-running the fixture generator replaces
the generated fixture database/content; keep any outputs you need beforehand.

`results/*/summary.json` contains the category/status, tool count and measured
local investigation elapsed time. `results/*/results.json` includes inspected
evidence and recommendations. Per-case `task_run.json` records task execution.
The SQLite databases can be regenerated and are not included in the release.

## Airflow DAG

`dags/ictai_incident_replay.py` defines an optional DAG that runs the same `ingest`
function and schedules the evidence review with `all_done`, including after task
failure. An existing Airflow environment supporting `airflow.decorators` is
required. Airflow is **not installed or scheduler-tested in the authoring
workspace**; direct Python execution is the completed validation.

Install this package into the Airflow worker environment (`pip install .`), put
the DAG in your Airflow DAG folder and provide:

- `ICTAI_REPLAY_ROOT`: absolute path containing generated `case_01` ... `case_06`
  directories, such as the direct runner's `results/failures` directory.
- `ICTAI_REFERENCE_URL`: for case 06, a reachable local test endpoint returning
  JSON and HTTP 200/503. This implementation intentionally accepts only
  `http://127.0.0.1:<port>/...`. In containers, that means the same network
  namespace as the worker. The direct runner's endpoint stops when it exits.
- Trigger parameter `case_id`: one of `01` through `06`.

Do not substitute a production endpoint in this replay. A production adapter
would require separate access, schema, privacy and operational validation.

## Completed live LLM comparison

```text
python run_live_comparison.py --output results/live_comparison
```

Set `OPENAI_API_KEY` locally, or supply `--env-file` with the path to an existing
private credential file. Never commit that file. This command makes billable
requests to `https://api.openai.com/v1/responses`, sending generated replay
symptoms/evidence and optional synthetic runbooks. It does not send the private
credential as model input, contributor narratives, ticket aliases or production
logs. Maximum calls: 48 (six cases, two LLM policies, four calls per case/policy).
No automatic model-request retries are performed.

One completed run is preserved in `results/live_comparison`. Fixed and dynamic
policies each matched six designed categories; LLM and LLM+guidance policies each
matched five, with one controller review required. Both models called the worker
package error a dependency failure rather than the controller's pipeline-failure
category. The prompt listed category names but did not define their boundaries;
this is a taxonomy/prompt limitation, not proof the model missed the error itself.
There was one rejected routing proposal in the knowledge-assisted policy and no
API failures. Both LLM policies use six domains by design. The 48 calls recorded
23,851 input and 5,865 output tokens. Monetary cost is not inferred from usage.

`model_records.json` preserves raw model responses, usage, latency, model IDs,
and generated input payloads. `manifest.json` freezes case/config/runbook hashes
before execution. Final output and source-code hashes are in REPLAY_MANIFEST.json.
`preflight_payload.py` prepares a generated-data preview without an API call.
Do not modify the recorded outputs or rerun this folder without first preserving
the frozen run; use a new output directory for further experiments.

## Evaluation boundaries

The fixed and dynamic controllers here inspect the same six evidence domains.
Dynamic mode changes inspection order only. All four policies collect all six
domains, so no tool-call savings are expected or claimed. Offline recommendations
are deterministic templates; live recommendations are model proposals. The
knowledge-assisted policy retrieves synthetic design guidance, not independent
verified incident history. This does not replace the original published
four-arm experiment or silently extend its confirmation contracts. The new
contracts explicitly support column counts, invalid numeric values, monthly
reference freshness, worker failures and matching upstream failures.

Success on these constructed cases and their recoveries is functional
verification, not an independent accuracy estimate. Generated recovery runs do
not demonstrate how the historical incidents were resolved. Local elapsed time
is neither human investigation time nor Airflow scheduler latency.
Only one live run per case/policy was completed; stochastic variability and human
effectiveness were not measured. Reviewer response forms are unfilled.

## License

MIT, as specified by the repository's root LICENSE file.
