import unittest
from ictai.controller import Investigation
from ictai.llm_reasoner import validate_proposal, eligible_tools_by_layer
from ictai.reasoning_context import propose_with_symptoms

class EligibilityConsistencyTests(unittest.TestCase):
    def _check(self, layer, tool):
        ctx=Investigation('test-case')
        tools={tool:lambda: {}}
        self.assertIn(tool,eligible_tools_by_layer(ctx,tools)[layer])
        def model(messages):
            import json
            payload=json.loads(messages[1]['content'])
            self.assertIn(layer,payload['available_layers'])
            self.assertIn(tool,payload['eligible_tools_by_layer'][layer])
            return {'next_layer':layer,'hypotheses':[],'open_questions':[],'evidence_refs':[],'knowledge_refs':[]}
        proposal=propose_with_symptoms(ctx,tools,model,'A synthetic incident')
        self.assertTrue(proposal.accepted,proposal.reason)
        ctx.visited.append(layer)
        self.assertNotIn(layer,eligible_tools_by_layer(ctx,tools))
        ctx.visited.clear()
        ctx.evidence.append({'tool':tool,'result':{}})
        self.assertNotIn(layer,eligible_tools_by_layer(ctx,tools))
        rejected=validate_proposal({'next_layer':layer,'hypotheses':[],'open_questions':[],'evidence_refs':[]},ctx,tools)
        self.assertEqual(rejected.reason,'no_available_tools')
    def test_data_quality(self): self._check('validation','inspect_quality_rule')
    def test_freshness(self): self._check('source','inspect_freshness_sla')
    def test_schema_drift(self): self._check('validation','inspect_schema_contract')
    def test_dependency(self): self._check('lineage','query_lineage')

if __name__=='__main__': unittest.main()
