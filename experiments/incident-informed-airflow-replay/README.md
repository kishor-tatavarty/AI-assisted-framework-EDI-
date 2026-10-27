# Incident-informed ingestion replay with Airflow task support

This extension implements six scenarios described by the incident contributor.
At the user's request, an Airflow-compatible Python task replaces Matillion and
a local inventory reference HTTP service replaces inaccessible SAP HANA.

**These are generated, incident-informed local replays, not preserved production
incidents or measurements from production systems.** No production credentials
are required. No LLM or external API is called by this package.

## What is executed

The task reads real generated CSV files, validates columns and integer values,
loads local SQLite raw/fact tables in a transaction, writes execution records,
and contacts a local HTTP endpoint for the dependency case. Evidence adapters
inspect those files, tables, records and endpoint. A deterministic controller
then proposes a category and a rule-based recommendation with human approval.

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

## Evaluation boundaries

The fixed and dynamic controllers here inspect the same six evidence domains.
Dynamic mode changes inspection order only. Both collect all six domains, so no
tool-call savings are expected or claimed. Recommendations are deterministic
templates; no model-generated RCA, knowledge ablation or LLM performance result
is produced by this extension. This does not replace the original published
four-arm experiment or silently extend its confirmation contracts. The new
contracts explicitly support column counts, invalid numeric values, monthly
reference freshness, worker failures and matching upstream failures.

Success on these constructed cases and their recoveries is functional
verification, not an independent accuracy estimate. Generated recovery runs do
not demonstrate how the historical incidents were resolved. Local elapsed time
is neither human investigation time nor Airflow scheduler latency.

## License

MIT, as specified by the repository's root LICENSE file.
