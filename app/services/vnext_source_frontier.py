"""Read-only per-security source planning; never an Owner or use grant."""
from dataclasses import dataclass
from datetime import date

CONTRACT = 'per-security-role-source-frontier-v1'


@dataclass(frozen=True)
class SourceKey:
    security: str
    exchange: str
    role: str
    basis: str
    provider: str

    def __post_init__(self):
        if any(not isinstance(v, str) or not v.strip() for v in
               (self.security, self.exchange, self.role, self.basis, self.provider)):
            raise ValueError('exact_source_key_required')


def plan_frontier(key, *, completed, qualified, stored, checked=False,
                  registered=True, disposition=None, market_last_seen=None):
    """Inputs are backend inventory, NOT accepted source ownership capabilities.

    Mapping keys prevent an unrelated security or adjusted-price role from
    advancing this watermark. A stored later date alone never grants use.
    """
    if not isinstance(key, SourceKey):
        raise ValueError('typed_source_key_required')
    date.fromisoformat(completed)
    last = qualified.get(key)
    persisted = stored.get(key)
    for value in (last, persisted, market_last_seen):
        if value is not None:
            date.fromisoformat(value)
            if value > completed:
                raise ValueError('future_frontier_requires_review')
    if disposition not in (None, 'DENIED', 'REVOKED', 'QUALITY_DENIED'):
        raise ValueError('unknown_source_disposition')
    state = (disposition if disposition else 'NOT_CHECKED' if not checked else
             'ALREADY_CONSUMED' if last == completed else
             'EMPTY_HISTORY_BOOTSTRAP' if last is None and persisted is None else
             'NOT_CHECKED' if last is None else
             'UNCONSUMED_EXISTING_COMPLETED_SESSION' if persisted == completed or market_last_seen == completed else
             'NEW_COMPLETED_SESSION')
    return dict(contract=CONTRACT, state=state, registered=registered,
        lineage='EXISTING_SUBJECT_SUCCESSOR' if registered else 'NEW_SUBJECT_BOOTSTRAP',
        market_last_completed=completed, per_role_last_qualified=last,
        market_previously_seen=market_last_seen,
        newest_stored=persisted, candidate_session=completed,
        source_owner_granted=False, model_admitted=False, strict_ready=False,
        required_next='Original source Owner + exact current use + explicit execution scope')
