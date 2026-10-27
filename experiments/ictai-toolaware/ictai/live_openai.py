"""Minimal OpenAI Responses API adapter. No credentials stored in source."""
import json, os, time, urllib.request

class OpenAIResponsesAdapter:
    def __init__(self, model=None, api_key=None, transport=None):
        self.model=model or os.getenv('ICTAI_MODEL', 'gpt-4.1-mini')
        self.api_key=api_key or os.getenv('OPENAI_API_KEY')
        self.transport=transport or self._http
        self.records=[]
        if not self.api_key and transport is None:
            raise RuntimeError('OPENAI_API_KEY not configured; live run not attempted')

    def _http(self, payload):
        req=urllib.request.Request('https://api.openai.com/v1/responses',
            data=json.dumps(payload).encode(),
            headers={'Authorization':'Bearer '+self.api_key,'Content-Type':'application/json'},
            method='POST')
        with urllib.request.urlopen(req,timeout=45) as response:
            return json.load(response)

    def __call__(self,messages):
        payload={'model':self.model,'input':messages,'temperature':0,'max_output_tokens':500,
                 'text':{'format':{'type':'json_object'}}}
        t=time.perf_counter()
        result=self.transport(payload)
        duration=(time.perf_counter()-t)*1000
        chunks=[part.get('text','') for item in result.get('output',[]) if item.get('type')=='message'
                for part in item.get('content',[]) if part.get('type')=='output_text']
        if not chunks: raise ValueError('No output_text returned by model')
        output=''.join(chunks)
        self.records.append({'model':result.get('model',self.model), 'response_id':result.get('id'),
                             'elapsed_ms':round(duration,3),'usage':result.get('usage',{}),
                             'proposal_raw':output})
        return output
