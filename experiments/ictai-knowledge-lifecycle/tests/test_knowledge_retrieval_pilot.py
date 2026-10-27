import unittest
from ictai.semantic58 import retrieve

class RetrievalPilotTests(unittest.TestCase):
    def setUp(self):
        self.history=[
          {"id":"schema","layer":"validation","verified":True,"stale":False,
           "description":"Partner deployment renamed customer_key to account_key; parser rejects unexpected attributes. Compare observed schema against contract."},
          {"id":"dependency","layer":"lineage","verified":True,"stale":False,
           "description":"Reference endpoint timeout blocked the enrichment feed; verify upstream dependency and lineage relationship."},
          {"id":"stale","layer":"validation","verified":True,"stale":True,
           "description":"Partner deployment renamed customer_key to account_key; parser rejects unexpected attributes."},
          {"id":"unverified","layer":"lineage","verified":False,"stale":False,
           "description":"Reference endpoint timeout blocked the enrichment feed; verify upstream dependency."}]
    def test_schema_paraphrase(self):
        h=retrieve(self.history,"Partner deployment triggered parser rejects after unexpected attributes",{"validation","lineage"})
        self.assertEqual([x["id"] for x in h],["schema"])
    def test_dependency(self):
        h=retrieve(self.history,"Reference endpoint timeout affecting enrichment feed",{"lineage"})
        self.assertEqual([x["id"] for x in h],["dependency"])
    def test_weak_generic_abstains(self):
        self.assertEqual(retrieve(self.history,"The pipeline has a problem",{"lineage","validation"}),[])
    def test_unavailable_layer_excluded(self):
        self.assertEqual(retrieve(self.history,"Partner deployment triggered parser rejects after unexpected attributes",{"source"}),[])
    def test_stale_and_unverified_excluded(self):
        self.assertTrue(all(x["id"] not in ("stale","unverified") for x in retrieve(self.history,"Reference endpoint timeout blocked enrichment feed",{"lineage"})))
if __name__=="__main__": unittest.main()
