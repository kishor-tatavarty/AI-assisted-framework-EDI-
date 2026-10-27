import unittest
from datetime import datetime,timezone
from ictai.knowledge_guard import assess_history
class GuardTests(unittest.TestCase):
 def setUp(self):
  self.r=dict(id='hist-1',source_incident_id='synthetic-1',source_system='fixture',reviewer_id='test',verified_at='2026-01-01T00:00:00Z',valid_from='2026-01-01T00:00:00Z',valid_until='2027-01-01T00:00:00Z',layer='lineage',description='sample',verified=True,stale=False,expected_current_observations=[dict(tool='check_upstream_health',key='healthy',equals=False)])
  self.now=datetime(2026,10,26,tzinfo=timezone.utc)
 def test_pending(self):self.assertEqual(assess_history(self.r,now=self.now)['status'],'PENDING')
 def test_valid(self):self.assertEqual(assess_history(self.r,[dict(tool='check_upstream_health',result={'healthy':False})],now=self.now)['status'],'ACCEPTED')
 def test_contradiction(self):
  e=[dict(tool='check_upstream_health',result={'healthy':True})]
  self.assertEqual(assess_history(self.r,e,now=self.now)['reason'],'contradicted_by_current_evidence')
 def test_missing_provenance(self):
  del self.r['source_system'];self.assertEqual(assess_history(self.r,now=self.now)['reason'],'invalid_provenance')
 def test_expired(self):
  self.r['valid_until']='2026-02-01T00:00:00Z';self.assertEqual(assess_history(self.r,now=self.now)['reason'],'outside_validity_window')
 def test_stale(self):
  self.r['stale']=True;self.assertEqual(assess_history(self.r,now=self.now)['reason'],'not_verified_or_stale')
