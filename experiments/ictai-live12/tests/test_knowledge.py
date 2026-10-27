import json
import tempfile
import unittest
from pathlib import Path
from ictai.knowledge import KnowledgeRepository, investigate_with_knowledge

TODAY = '2026-10-22'
def record(id='r1', signal='schema_drift', kind='incident', **kwargs):
    return dict(id=id, kind=kind, signal=signal, suggested_layer='validation',
                summary='Check schema contract', verified=True,
                reviewed_on='2026-01-01', expires_on='2027-01-01', **kwargs)

class KnowledgeTests(unittest.TestCase):
    def test_match(self):
        repo = KnowledgeRepository([record()], as_of=TODAY)
        self.assertEqual(repo.query('schema_drift')[0].record_id, 'r1')
    def test_cold_start(self):
        self.assertEqual(KnowledgeRepository([], as_of=TODAY).query('missing_file'), [])
    def test_expired_rejected(self):
        r = record(); r['expires_on'] = '2025-01-01'
        repo = KnowledgeRepository([r], as_of=TODAY)
        self.assertEqual(repo.query('schema_drift'), [])
        self.assertEqual(len(repo.rejected), 1)
    def test_unverified_rejected(self):
        r = record(); r['verified'] = False
        self.assertEqual(KnowledgeRepository([r], as_of=TODAY).records, [])
    def test_duplicate_rejected(self):
        repo = KnowledgeRepository([record(), record()], as_of=TODAY)
        self.assertEqual(len(repo.records), 1)
        self.assertEqual(len(repo.rejected), 1)
    def test_excluded_holdout(self):
        repo = KnowledgeRepository([record()], as_of=TODAY, excluded_ids={'r1'})
        self.assertEqual(repo.query('schema_drift'), [])
    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'knowledge.json'
            path.write_text(json.dumps([record()]), encoding='utf-8')
            self.assertEqual(len(KnowledgeRepository.from_json(path, as_of=TODAY).records), 1)
    def test_history_does_not_override_current_evidence(self):
        repo = KnowledgeRepository([record()], as_of=TODAY)
        tools = {'inspect_manifest': lambda: {'expected': True},
                 'check_object_inventory': lambda: {'present': False}}
        ctx, result, matches = investigate_with_knowledge('case', 'schema_drift', tools, repo)
        self.assertEqual(result.category, 'MISSING_FILE')
        self.assertEqual(len(matches), 1)
        self.assertFalse(ctx.audit[0]['applied_to_rca'])
    def test_history_cannot_invent_rca(self):
        repo = KnowledgeRepository([record()], as_of=TODAY)
        ctx, result, _ = investigate_with_knowledge('case', 'schema_drift', {}, repo)
        self.assertEqual(result.category, 'INSUFFICIENT_EVIDENCE')
    def test_cold_start_audit(self):
        repo = KnowledgeRepository([], as_of=TODAY)
        ctx, _, _ = investigate_with_knowledge('case', 'missing_file', {}, repo)
        self.assertEqual(ctx.audit[0]['status'], 'COLD_START')
    def test_invalid_query(self):
        with self.assertRaises(ValueError):
            KnowledgeRepository([], as_of=TODAY).query('unknown')

if __name__ == '__main__': unittest.main()
