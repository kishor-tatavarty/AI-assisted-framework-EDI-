"""Shared task logic for direct execution and the optional Airflow DAG.

File values, contracts, deadlines and failures are generated replay parameters.
They are not recovered production artifacts. Every tool returns local evidence.
"""
from pathlib import Path
from datetime import datetime
import csv
import json
import re
import sqlite3
import time
from contextlib import closing
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


class UpstreamUnavailable(RuntimeError):
    pass


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def table_count(database, table, business_date):
    if table not in ('raw', 'fact'):
        raise ValueError('unsupported table')
    with closing(sqlite3.connect(database)) as con:
        return con.execute(f'SELECT COUNT(*) FROM {table} WHERE business_date = ?',
                           (business_date,)).fetchone()[0]


def ingest(root, service_url=None):
    """Execute the replay pipeline. Airflow calls this exact function.

    Success is committed atomically. Exceptions propagate to Airflow; an audit
    artifact is written for both successful and failed task execution.
    """
    root = Path(root)
    cfg = read_json(root / 'config.json')
    con = sqlite3.connect(root / 'data.sqlite')
    log = {'run_id': cfg['run_id'], 'execution_environment': 'local replay task',
           'started_at': datetime.now().astimezone().isoformat(),
           'status': 'RUNNING', 'error_code': None, 'error': None}
    start = time.perf_counter()
    try:
        # A replay runtime flag injects the reported package failure mechanism.
        # It does not establish that the original server had this exact error.
        if not cfg['runtime']['worker_package_ok']:
            raise ImportError('REPLAY_WORKER_PACKAGE_CONFLICT: incompatible worker dependency')
        file = root / cfg['expected_file']
        if not file.is_file():
            raise FileNotFoundError('REPLAY_INPUT_NOT_FOUND: expected business-date CSV absent')
        with file.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            rows = list(reader)
        if columns != cfg['contract']['columns']:
            raise ValueError('REPLAY_COLUMN_MISMATCH: received columns differ from contract')
        for row in rows:
            if row.get('business_date') != cfg['business_date']:
                raise ValueError('REPLAY_BUSINESS_DATE_MISMATCH')
            if not re.fullmatch(r'[+-]?\d+', row['revenue']):
                raise ValueError('REPLAY_NUMERIC_CONVERSION: revenue must be an integer')
        if cfg['dependency']['required']:
            if not service_url:
                raise UpstreamUnavailable('REPLAY_DEPENDENCY_NOT_CONFIGURED')
            # Network use is restricted to the local mock endpoint in the runner.
            if not service_url.startswith('http://127.0.0.1:'):
                raise ValueError('replay endpoint must be localhost')
            log['upstream_id'] = cfg['dependency']['id']
            try:
                with urlopen(service_url, timeout=2) as response:
                    body = json.load(response)
                if body.get('status') != 'ok':
                    raise UpstreamUnavailable('REPLAY_UPSTREAM_INVALID_RESPONSE')
            except (HTTPError, URLError, TimeoutError) as exc:
                raise UpstreamUnavailable('REPLAY_UPSTREAM_UNAVAILABLE: '+type(exc).__name__) from exc
        con.execute('BEGIN')
        con.execute('DELETE FROM raw WHERE business_date = ?', (cfg['business_date'],))
        for row in rows:
            con.execute('INSERT INTO raw VALUES (?,?,?)',
                        (row['business_date'], row['id'], int(row['revenue'])))
        rate = 1.0
        if cfg['rates']['required']:
            # Explicitly synthetic reproduction of a risky latest-rate fallback.
            # The contributor did not provide the actual historical lookup SQL.
            with (root / 'rates.csv').open(newline='', encoding='utf-8') as f:
                rates = list(csv.DictReader(f))
            if not rates:
                raise ValueError('REPLAY_NO_EXCHANGE_RATES')
            current = [r for r in rates if r['month'] == cfg['rates']['required_month']]
            chosen = current[0] if current else sorted(rates, key=lambda r:r['month'])[-1]
            rate = float(chosen['rate'])
            log['selected_rate_month'] = chosen['month']
            log['selected_rate'] = rate
        con.execute('DELETE FROM fact WHERE business_date = ?', (cfg['business_date'],))
        for date, rid, amount in con.execute('SELECT * FROM raw WHERE business_date = ?',
                                            (cfg['business_date'],)).fetchall():
            con.execute('INSERT INTO fact VALUES (?,?,?)', (date, rid, amount * rate))
        con.commit()
        log['status'] = 'SUCCESS'
        return log
    except Exception as exc:
        con.rollback()
        log.update(status='FAILED', error_code=type(exc).__name__, error=str(exc))
        raise
    finally:
        con.close()
        log['elapsed_ms'] = round((time.perf_counter()-start)*1000, 3)
        write_json(root / 'task_run.json', log)


def inspect_source(root):
    root = Path(root); cfg = read_json(root/'config.json')
    file = root/cfg['expected_file']
    return {'expected': cfg['delivery_expected'], 'expected_file': cfg['expected_file'],
            'present': file.is_file(), 'count': int(file.is_file()),
            'delivery_deadline': cfg['delivery_deadline'],
            'inspection_time': cfg['inspection_time'], 'time_basis':'generated replay parameters'}


def inspect_validation(root):
    root=Path(root);cfg=read_json(root/'config.json');file=root/cfg['expected_file']
    if not file.is_file():
        return {'available':False,'reason':'file absent','schema_mismatch':None,'invalid_integer_rows':None}
    with file.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f);columns=r.fieldnames or [];rows=list(r)
    invalid=[{'row':i+2,'value':r.get('revenue')} for i,r in enumerate(rows)
             if not re.fullmatch(r'[+-]?\d+',r.get('revenue',''))]
    return {'available':True,'expected_columns':cfg['contract']['columns'],
            'observed_columns':columns,'schema_mismatch':columns!=cfg['contract']['columns'],
            'revenue_type':'integer','invalid_integer_rows':invalid,
            'note':'column names and sample values generated for replay'}


def inspect_tables(root):
    root=Path(root);cfg=read_json(root/'config.json')
    return {'business_date':cfg['business_date'],
            'raw_count':table_count(root/'data.sqlite','raw',cfg['business_date']),
            'fact_count':table_count(root/'data.sqlite','fact',cfg['business_date']),
            'backend':'local SQLite stand-in, not a Snowflake query'}


def inspect_execution(root):
    return read_json(Path(root)/'task_run.json')


def inspect_rates(root):
    root=Path(root);cfg=read_json(root/'config.json')
    if not cfg['rates']['required']:
        return {'applicable':False}
    with (root/'rates.csv').open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    return {'applicable':True,'required_month':cfg['rates']['required_month'],
            'observed_months':sorted(set(r['month'] for r in rows)),
            'current_month_count':sum(r['month']==cfg['rates']['required_month'] for r in rows),
            'policy':'current-month rates required; generated replay policy'}


def inspect_dependency(root, service_url=None):
    cfg=read_json(Path(root)/'config.json')
    if not cfg['dependency']['required']:
        return {'required':False,'healthy':None}
    result={'required':True,'upstream_id':cfg['dependency']['id'],
            'health_source':'local HTTP reference-service stub'}
    if not service_url or not service_url.startswith('http://127.0.0.1:'):
        return dict(result,healthy=None,reason='local endpoint not configured')
    try:
        with urlopen(service_url,timeout=2) as response:
            body=json.load(response)
        return dict(result,healthy=body.get('status')=='ok',http_status=200)
    except HTTPError as exc:
        return dict(result,healthy=False,http_status=exc.code)
    except (URLError,TimeoutError) as exc:
        return dict(result,healthy=False,error=type(exc).__name__)


TOOLS={'source':inspect_source,'validation':inspect_validation,'tables':inspect_tables,
       'execution':inspect_execution,'rates':inspect_rates,'dependency':inspect_dependency}


def classify(evidence):
    """Fresh replay contracts; not the unchanged published confirmation_six.

    Causes are inferred from inspected evidence, never from an expected label.
    Execution failure can be a symptom of a more specific cause.
    """
    e={x['tool']:x['result'] for x in evidence}
    s=e.get('source',{});v=e.get('validation',{});run=e.get('execution',{})
    rates=e.get('rates',{});dep=e.get('dependency',{})
    candidates=[]
    def add(category,checks,refs):
        if checks:candidates.append((category,refs))
    deadline=s.get('delivery_deadline');checked=s.get('inspection_time')
    overdue=bool(deadline and checked and datetime.fromisoformat(checked)>=datetime.fromisoformat(deadline))
    add('MISSING_FILE',s.get('expected') is True and s.get('present') is False and overdue,['source'])
    add('SCHEMA_DRIFT',v.get('available') is True and v.get('schema_mismatch') is True,['validation'])
    add('DATA_QUALITY_ANOMALY',v.get('available') is True and v.get('schema_mismatch') is False
        and bool(v.get('invalid_integer_rows')),['validation'])
    add('FRESHNESS_VIOLATION',rates.get('applicable') is True and rates.get('current_month_count')==0,['rates'])
    blocked=run.get('error_code')=='UpstreamUnavailable'
    add('DEPENDENCY_FAILURE',dep.get('required') is True and dep.get('healthy') is False
        and blocked and run.get('upstream_id')==dep.get('upstream_id'),['dependency','execution'])
    add('PIPELINE_FAILURE',run.get('status')=='FAILED' and run.get('error_code')=='ImportError',['execution'])
    if len(candidates)>1:
        status='REVIEW_REQUIRED';category='INSUFFICIENT_EVIDENCE'
        refs=sorted(set(r for _,rs in candidates for r in rs))
    elif candidates:
        category,refs=candidates[0];status='SUPPORTED_IN_REPLAY'
    else:
        status='NO_INCIDENT_DETECTED' if run.get('status')=='SUCCESS' else 'ABSTAINED'
        category='NO_INCIDENT' if status=='NO_INCIDENT_DETECTED' else 'INSUFFICIENT_EVIDENCE';refs=[]
    actions={
        'MISSING_FILE':'Confirm the expected path and deadline; request the missing delivery and validate before rerunning.',
        'SCHEMA_DRIFT':'Review the producer change and approved contract; correct the delivery or approve a compatible mapping before rerunning.',
        'DATA_QUALITY_ANOMALY':'Confirm the numeric-value contract; obtain corrected values or approve a conversion rule, then reconcile totals.',
        'FRESHNESS_VIOLATION':'Obtain approved current-month rates, trace the rate used, and reconcile/reprocess affected converted values.',
        'PIPELINE_FAILURE':'Review the worker dependency error with the platform owner, restore the approved environment and rerun safely.',
        'DEPENDENCY_FAILURE':'Confirm the upstream service outage, coordinate recovery, then retry and validate inventory output.',
    }
    return {'category':category,'status':status,'evidence_refs':refs,
            'candidate_categories':[x[0] for x in candidates],
            'recommendation':actions.get(category,'Request human review before remediation.' if category!='NO_INCIDENT' else 'No remediation proposed.'),
            'recommendation_origin':'deterministic category-to-action template, not LLM generation',
            'human_approval_required':category!='NO_INCIDENT'}


def investigate(root, service_url=None, policy='fixed'):
    if policy not in ('fixed','dynamic'):
        raise ValueError('policy must be fixed or dynamic')
    cfg=read_json(Path(root)/'config.json')
    order=['source','validation','tables','execution','rates','dependency']
    if policy=='dynamic':
        symptom=cfg['symptoms'].lower()
        priority='execution' if any(s in symptom for s in ['task','job','all fact']) else 'source'
        order=[priority]+[x for x in order if x!=priority]
    start=time.perf_counter();evidence=[]
    for tool in order:
        value=TOOLS[tool](root,service_url) if tool=='dependency' else TOOLS[tool](root)
        evidence.append({'tool':tool,'result':value,'evidence_origin':'executed local replay adapter'})
    return {'case_id':cfg['id'],'policy':policy,**classify(evidence),'tool_attempts':len(evidence),
            'elapsed_ms':round((time.perf_counter()-start)*1000,3),'evidence':evidence,
            'scope':'generated incident-informed replay; not independently verified production evidence'}
