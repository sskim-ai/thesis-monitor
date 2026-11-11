"""Opt-in model policy and finite call accounting, not source or Stage authority."""
from dataclasses import dataclass
import re

from app.services.vnext_execution_profile import SOL_HIGH_V1, require_profile

CONTRACT_V2 = 'official-codex-production-transport-v2-sol-high'


def sol_high(profile):
    if require_profile(profile) != SOL_HIGH_V1:
        raise ValueError('exact_sol_high_profile_required')
    return profile


@dataclass(frozen=True)
class SolHighWirePolicy:
    contract: str = CONTRACT_V2
    profile: str = SOL_HIGH_V1.contract
    model: str = SOL_HIGH_V1.model
    effort: str = SOL_HIGH_V1.effort
    timeout_seconds: int = 600
    max_calls: int = 1
    retries: int = 0
    purpose: str = 'NO_SEND_RESEARCH'

    def validate(self):
        if self != SolHighWirePolicy() or any(type(v) is not int for v in
                (self.timeout_seconds, self.max_calls, self.retries)):
            raise ValueError('sol_high_wire_policy_drift')


@dataclass(frozen=True)
class ModelCallSlot:
    panel: str
    stage: str
    payload_sha256: str
    kind: str


class SolHighCallBudget:
    """One shared run budget; cycle changes never refill consumed slots."""
    def __init__(self, slots):
        self.slots = tuple(slots)
        if not 1 <= len(self.slots) <= 6 or len(set(self.slots)) != len(self.slots):
            raise ValueError('sol_high_six_context_plan_required')
        panels = {}
        for slot in self.slots:
            if (type(slot) is not ModelCallSlot or not slot.panel
                    or not re.fullmatch('[a-f0-9]{64}', slot.payload_sha256)
                    or slot.kind not in ('market', 'stock')
                    or slot.stage not in ('MARKET', 'CORE', 'A', 'B', 'B2', 'BLIND', 'ADJUDICATION')
                    or (slot.kind == 'market') != (slot.stage == 'MARKET')):
                raise ValueError('sol_high_slot_invalid')
            panels.setdefault(slot.panel, []).append(slot)
        if (sum(rows[0].kind == 'market' for rows in panels.values()) > 2
                or sum(rows[0].kind == 'stock' for rows in panels.values()) > 2):
            raise ValueError('sol_high_four_panel_limit')
        for rows in panels.values():
            if (len({r.kind for r in rows}) != 1 or len({r.stage for r in rows}) != len(rows)
                    or len(rows) > (1 if rows[0].kind == 'market' else 2)):
                raise ValueError('sol_high_panel_context_limit')
        self.used = set()

    def consume(self, panel, stage, payload_sha256):
        matches = [s for s in self.slots if (s.panel, s.stage, s.payload_sha256) ==
                   (panel, stage, payload_sha256)]
        if len(matches) != 1 or matches[0] in self.used or len(self.used) >= 6:
            raise ValueError('sol_high_call_budget_exhausted_or_unplanned')
        self.used.add(matches[0])
        return len(self.used)
