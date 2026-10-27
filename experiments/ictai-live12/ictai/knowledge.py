"""Read-only, deterministic, advisory knowledge retrieval for ICTAI."""
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

VALID_SIGNALS = frozenset(('missing_file', 'schema_drift', 'pipeline_failure',
                           'dependency_failure', 'data_quality', 'freshness'))
VALID_LAYERS = frozenset(('source', 'validation', 'pipeline', 'lineage', 'impact'))

@dataclass(frozen=True)
class KnowledgeMatch:
    record_id: str
    kind: str
    suggested_layer: str
    score: int
    summary: str

class KnowledgeRepository:
    def __init__(self, records, as_of=None, excluded_ids=()):
        self.as_of = date.fromisoformat(as_of) if isinstance(as_of, str) else (as_of or date.today())
        self.excluded_ids = frozenset(excluded_ids)
        self.records = []
        self.rejected = []
        seen = set()
        for record in records:
            try:
                if not isinstance(record, dict): raise ValueError('not an object')
                rid = record['id']
                if not isinstance(rid, str) or not rid.strip() or rid in seen:
                    raise ValueError('invalid or duplicate id')
                seen.add(rid)
                if rid in self.excluded_ids: continue
                if record['kind'] not in ('incident', 'runbook'): raise ValueError('invalid kind')
                if record['signal'] not in VALID_SIGNALS: raise ValueError('invalid signal')
                if record['suggested_layer'] not in VALID_LAYERS: raise ValueError('invalid layer')
                if not isinstance(record['summary'], str) or not record['summary'].strip():
                    raise ValueError('invalid summary')
                if record.get('verified') is not True: raise ValueError('unverified')
                if date.fromisoformat(record['reviewed_on']) > self.as_of:
                    raise ValueError('future review date')
                if date.fromisoformat(record['expires_on']) < self.as_of:
                    raise ValueError('expired')
                self.records.append(dict(record))
            except (KeyError, TypeError, ValueError) as exc:
                self.rejected.append({'id': record.get('id') if isinstance(record, dict) else None,
                                      'reason': str(exc)})

    @classmethod
    def from_json(cls, path, **kwargs):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data, list): raise ValueError('knowledge file must contain a list')
        return cls(data, **kwargs)

    def query(self, signal, limit=3):
        if signal not in VALID_SIGNALS: raise ValueError('unknown signal')
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError('limit must be a positive integer')
        matches = [KnowledgeMatch(r['id'], r['kind'], r['suggested_layer'],
                                  2 if r['kind'] == 'incident' else 1, r['summary'])
                   for r in self.records if r['signal'] == signal]
        return sorted(matches, key=lambda m: (-m.score, m.record_id))[:limit]


def investigate_with_knowledge(incident_id, signal, available_tools, repository,
                               max_calls=4, max_layers=5):
    """Knowledge is logged as advice; current-evidence RCA is unchanged."""
    from .rca import investigate_and_classify
    matches = repository.query(signal)
    ctx, rca = investigate_and_classify(incident_id, signal, available_tools,
                                        max_calls=max_calls, max_layers=max_layers)
    ctx.audit.insert(0, {'event': 'knowledge_retrieval', 'status': 'MATCHED' if matches else 'COLD_START',
                         'record_ids': [m.record_id for m in matches],
                         'suggested_layers': [m.suggested_layer for m in matches],
                         'applied_to_routing': False, 'applied_to_rca': False})
    return ctx, rca, matches
