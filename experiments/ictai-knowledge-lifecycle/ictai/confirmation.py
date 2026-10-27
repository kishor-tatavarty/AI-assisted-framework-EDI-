"""Conservative RCA confirmation gate. No probabilistic confidence or LLM decisions."""
from dataclasses import dataclass
from .rca import classify_root_cause

@dataclass(frozen=True)
class Confirmation:
    status: str
    category: str
    evidence_refs: tuple[str, ...]
    reasons: tuple[str, ...]
    next_tools: tuple[str, ...]

# Independent confirmation checks; tools are read-only.
REQUIRED = {
    'MISSING_FILE': ('inspect_manifest', 'check_object_inventory'),
    'SCHEMA_DRIFT': ('inspect_schema_contract', 'inspect_observed_schema'),
}

def confirm(ctx, available_tools=None, exhausted=False):
    """Never promote a candidate if relevant available corroboration is unobserved.

    This v5.2 gate validates the two implemented RCA classes. The other four
    incident classes must abstain until their evidence contracts are implemented.
    """
    available_tools = available_tools or {}
    result = classify_root_cause(ctx)
    observed = {e.get('tool') for e in ctx.evidence if isinstance(e, dict) and isinstance(e.get('result'), dict)}
    if result.status == 'REVIEW_REQUIRED':
        return Confirmation('REVIEW_REQUIRED', 'INSUFFICIENT_EVIDENCE', result.evidence_refs, result.reasons, ())
    if result.status != 'CLASSIFIED':
        return Confirmation('ABSTAINED' if exhausted else 'INVESTIGATING', 'INSUFFICIENT_EVIDENCE', (), result.reasons, ())
    needed = REQUIRED.get(result.category)
    if not needed:
        return Confirmation('REVIEW_REQUIRED', 'INSUFFICIENT_EVIDENCE', result.evidence_refs, ('unsupported RCA category',), ())
    # Check all available RCA evidence tools for potentially contradictory observations.
    check_tools = set(REQUIRED['MISSING_FILE'] + REQUIRED['SCHEMA_DRIFT'])
    pending = tuple(sorted((set(available_tools) & check_tools) - observed))
    if pending:
        if exhausted:
            return Confirmation('REVIEW_REQUIRED', 'INSUFFICIENT_EVIDENCE', result.evidence_refs,
                                ('confirmation budget exhausted before checking available contradictory evidence',), pending)
        return Confirmation('PROVISIONAL_RCA', result.category, result.evidence_refs,
                            ('additional available RCA evidence must be checked',), pending)
    return Confirmation('CONFIRMED', result.category, result.evidence_refs, result.reasons, ())
