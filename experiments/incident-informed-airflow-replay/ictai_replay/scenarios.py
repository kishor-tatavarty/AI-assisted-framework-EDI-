"""Generate explicit replay fixtures; never describe these as archived logs."""
from pathlib import Path
import csv
import json
import sqlite3
from contextlib import closing
from .core import write_json

ACCOUNT_SUMMARY={
 '01':{'account':'Supplier delivery due 05:00; monitoring at 07:00; raw rows absent at 07:05; file absent at 07:15; final load due 08:30 for 09:00 reporting.',
       'unknown':['original file name/path','supplier explanation','recovery outcome'],
       'adaptations':['local directory replaces S3','local SQLite replaces analytical tables']},
 '02':{'account':'Demand file present; expected 14 columns; extra columns observed; zero target rows; Snowflake load failure reported.',
       'unknown':['actual added columns','exact load error','retained file','recovery outcome'],
       'adaptations':['Airflow task replaces historical load executor','14 generic columns plus two generated extras','local CSV/SQLite']},
 '03':{'account':'Order file expected/arrived at 03:00; revenue requires integer values; dollar signs observed; matching column count; zero target rows; numeric load failure reported.',
       'unknown':['actual sample values','exact numeric error','recovery outcome'],
       'adaptations':['generated revenue sample $100','Airflow-compatible Python task and SQLite']},
 '04':{'account':'Business reported incorrect EU conversion amounts; file exists; current-month rates absent; previous-month rates present.',
       'unknown':['actual lookup SQL','actual selected rate','approved rates','source deadline','recovery outcome'],
       'adaptations':['generated months/rates and transaction','explicit latest-rate fallback demonstrates a possible failure, not verified historical behavior','replay monthly freshness contract']},
 '05':{'account':'All monitored fact loads failed; date-D source rows present; fact rows zero; Matillion task system failure and package issue reported.',
       'unknown':['exact package','retained system error','outage interval','recovery outcome'],
       'adaptations':['Airflow replaces Matillion at user request','injected worker dependency ImportError, not original Matillion error','one representative fact load, not proof all production jobs were reproduced']},
 '06':{'account':'Inventory load alert; upstream SAP HANA job failed; source count zero; server memory issue reported.',
       'unknown':['exact memory error','causal trace','recovery outcome'],
       'adaptations':['local inventory reference HTTP service replaces inaccessible SAP HANA at user request','HTTP 503 outage replaces memory-outage mechanism','does not reproduce or validate SAP HANA behavior']},
}


def save_csv(path, columns, rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)


def build(root, case_id, recovered=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if case_id not in ACCOUNT_SUMMARY:raise ValueError('unknown case')
    columns=['business_date','id','revenue']
    if case_id=='02':columns += [f'field_{i:02}' for i in range(4,15)]
    cfg={'id':case_id,'business_date':'2024-03-01','run_id':'replay-'+case_id,
         'delivery_expected':True,'expected_file':'landing.csv',
         'delivery_deadline':'2024-03-01T05:00:00-05:00',
         'inspection_time':'2024-03-01T07:15:00-05:00',
         'contract':{'columns':columns},'runtime':{'worker_package_ok':True},
         'dependency':{'required':False,'id':None},
         'rates':{'required':False,'required_month':'2024-03'},
         'symptoms':'Morning monitoring reports the expected business-date rows unavailable.',
         'provenance':{'record_type':'generated replay fixture informed by contributor account',
                       'historical_log_export':False,'all_fixture_dates_values_and_names_generated':True,
                       **ACCOUNT_SUMMARY[case_id]}}
    row={c:'sample' for c in columns};row.update(business_date=cfg['business_date'],id='item-1',revenue='100')
    if case_id=='01':cfg['symptoms']='Morning file ingestion alert; current-day raw rows unavailable.'
    if case_id=='03':cfg['delivery_deadline']='2024-03-01T03:00:00-05:00'
    if case_id=='05':
        cfg['runtime']['worker_package_ok']=recovered
        cfg['symptoms']='All fact loads failed; source rows exist and fact tables are empty. Inspect the processing task.'
    if case_id=='06':
        cfg['dependency']={'required':True,'id':'inventory-reference-service'}
        cfg['symptoms']='Inventory ingestion job failed; upstream reference service must supply current inventory.'
    observed=list(columns)
    if case_id=='02' and not recovered:
        observed += ['extra_01','extra_02'];row.update(extra_01='generated',extra_02='generated')
    if case_id=='03' and not recovered:row['revenue']='$100'
    file=root/cfg['expected_file']
    if case_id!='01' or recovered:save_csv(file,observed,[row])
    elif file.exists():file.unlink()
    if case_id=='04':
        cfg['rates']['required']=True
        rates=[{'month':'2024-02','rate':'1.10'}]
        if recovered:rates.append({'month':'2024-03','rate':'1.20'})
        save_csv(root/'rates.csv',['month','rate'],rates)
    db=root/'data.sqlite'
    with closing(sqlite3.connect(db)) as con:
        con.execute('CREATE TABLE IF NOT EXISTS raw (business_date TEXT, id TEXT, revenue INTEGER)')
        con.execute('CREATE TABLE IF NOT EXISTS fact (business_date TEXT, id TEXT, converted_revenue REAL)')
        con.execute('DELETE FROM raw');con.execute('DELETE FROM fact')
        if case_id=='05':con.execute('INSERT INTO raw VALUES (?,?,?)',(cfg['business_date'],'item-1',100))
        con.commit()
    write_json(root/'config.json',cfg)
    return cfg
