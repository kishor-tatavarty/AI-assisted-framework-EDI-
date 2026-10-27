import unittest
from ictai.live_openai import OpenAIResponsesAdapter
from ictai.llm_reasoner import propose
from ictai.controller import Investigation

class LiveAdapterOfflineTests(unittest.TestCase):
    def test_parses_responses_and_usage(self):
        def fake(payload):
            self.assertEqual(payload['text']['format']['type'],'json_object')
            return {'id':'resp_test','model':'test-model','usage':{'input_tokens':10,'output_tokens':20},
                    'output':[{'type':'message','content':[{'type':'output_text','text':'{"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":[]}'}]}]}
        adapter=OpenAIResponsesAdapter(model='test-model',transport=fake)
        proposal=propose(Investigation('test'),{'inspect_manifest':lambda:{}},adapter)
        self.assertTrue(proposal.accepted)
        self.assertEqual(adapter.records[0]['usage']['output_tokens'],20)
    def test_missing_output_falls_back(self):
        adapter=OpenAIResponsesAdapter(transport=lambda _: {'output':[]})
        proposal=propose(Investigation('test'),{'inspect_manifest':lambda:{}},adapter)
        self.assertEqual(proposal.reason,'model_error')
    def test_credentials_not_logged(self):
        adapter=OpenAIResponsesAdapter(api_key='secret-value',transport=lambda _:{'output':[{'type':'message','content':[{'type':'output_text','text':'{}'}]}]})
        adapter([])
        self.assertNotIn('secret-value',str(adapter.records))
