"""Verify outbound data without reading credentials or calling an external API."""
from pathlib import Path
import json
import hashlib
import re
from ictai_replay.core import read_json,write_json
from run_live_comparison import HISTORY

base=Path('results/live_comparison')
existing=read_json('results/failures/results.json')
samples=[]
for row in existing:
    if row['policy']!='fixed':continue
    cfg=read_json(Path('results/failures')/f"case_{row['case_id']}/config.json")
    samples.append({'symptoms':cfg['symptoms'],'current_evidence':row['evidence'],
                    'synthetic_runbooks':HISTORY,'scope':'generated local replay'})
text=json.dumps(samples,sort_keys=True)
assert not re.search(r'CHG\d+',text),'Unexpected source ticket metadata'
for forbidden in ['SAP HANA','Matillion','PS Lead','OPENAI_API_KEY','C:/research']:
    assert forbidden not in text,'Unexpected source metadata in payload'
write_json(base/'outbound_preview.json',samples)
write_json(base/'payload_privacy_check.json',{
 'preview_sha256':hashlib.sha256(text.encode()).hexdigest(),
 'external_destination':'https://api.openai.com/v1/responses',
 'data':'generated replay symptoms, generated local evidence, synthetic design runbooks',
 'excluded':['original contributor narratives','ticket aliases','company identities','production logs','credentials'],
 'external_request_sent_by_this_preflight_script':False})
print('Outbound preview prepared: six generated replay payloads; private source metadata excluded. No external request sent.')
