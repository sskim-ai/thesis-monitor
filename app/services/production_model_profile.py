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


class FourPanelSolHighCallBudgetV1:
    """Frozen C22Y four-panel experiment, not the generic runtime budget."""
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


class SolHighCallBudget(FourPanelSolHighCallBudgetV1):
    """Explicit plan cap, shared across markets. The old experiment stays separate."""
    def __init__(self, slots=None, *, plan=None, approved_max_invocations=None, approved_plan_sha256=None,
                 journal_path=None):
        self.plan = plan
        self.journal = None
        if plan is None:
            if approved_max_invocations is not None or approved_plan_sha256 is not None or journal_path is not None:
                raise ValueError('dynamic_model_plan_required')
            super().__init__(slots)
            self.maximum = len(self.slots)
            return
        from app.services.model_execution_plan import ModelExecutionPlan
        if slots is not None or type(plan) is not ModelExecutionPlan:
            raise ValueError('exact_model_execution_plan_required')
        plan.validate()
        if (type(approved_max_invocations) is not int or approved_max_invocations < len(plan.slots)
                or approved_max_invocations < 0 or approved_plan_sha256 != plan.sha256):
            raise ValueError('model_plan_not_within_approved_cap_or_hash')
        self.approved_plan_sha256 = approved_plan_sha256
        self.maximum = approved_max_invocations
        self.slots = plan.slots
        self.used, self.bound, self.accepted = set(), {}, {}
        self.stopped = False
        if journal_path is not None:
            from app.services.model_invocation_journal import ModelInvocationJournal
            self.journal = ModelInvocationJournal(journal_path, plan_sha256=plan.sha256, maximum=self.maximum)
            self._journal_state('OPEN')

    def _journal_state(self, event, **value):
        if self.journal is not None:
            state = self.journal.transact(event, **value)
            self.used, self.bound, self.accepted, self.stopped = (
                state[k] for k in ('used', 'bound', 'accepted', 'stopped'))

    def stop(self):
        self.stopped = True
        self._journal_state('STOP')

    def _verify_plan(self):
        self._journal_state('OPEN')
        if self.stopped:
            raise ValueError('model_failed_cycle_no_more_calls')
        if self.plan.sha256 != self.approved_plan_sha256:
            raise ValueError('model_plan_changed_after_approval')
        self.plan.validate()

    def bind_stage(self, stage, request):
        """One payload binding after original upstream acceptances, never at compile time."""
        from app.services.unified_snapshot_contract import digest
        self._verify_plan()
        batch = request['batch']
        if stage == 'MARKET':
            if batch != 1:
                raise ValueError('model_market_batch_invalid')
            batch = None
        matches = [s for s in self.slots if (s.market, s.stage, s.batch_id, s.subjects) ==
                   (request['market'], stage, batch, tuple(request['subjects']))]
        if len(matches) != 1:
            raise ValueError('model_request_scope_outside_frozen_plan')
        slot = matches[0]
        if (slot.slot_id in self.bound or set(slot.dependencies) - set(self.accepted)
                or request['source_generation_id'] != self.plan.cohort.source_generation
                or request['execution_generation_id'] != self.plan.cohort.run_id
                or digest(request['payload']) != request['payload_sha256']):
            raise ValueError('model_payload_binding_or_upstream_acceptance_gap')
        scope = dict(plan_sha256=self.plan.sha256, cohort_sha256=self.plan.cohort.sha256,
            slot_id=slot.slot_id, market=slot.market, stage=slot.stage, batch_id=slot.batch_id,
            subjects=list(slot.subjects), security_ids=list(slot.security_ids),
            source_generation=slot.source_generation, execution_profile=slot.execution_profile,
            payload_sha256=request['payload_sha256'], build_receipt_sha256=digest(request),
            dependency_outputs={key: self.accepted[key] for key in slot.dependencies})
        if self.journal is not None:
            self._journal_state('BIND', slot_id=slot.slot_id, scope=scope)
        else:
            self.bound[slot.slot_id] = scope
        return dict(scope, dependency_outputs=dict(scope['dependency_outputs']))

    def consume(self, panel, stage, payload_sha256, *, slot_scope=None):
        if self.plan is None:
            if slot_scope is not None:
                raise ValueError('dynamic_slot_on_legacy_four_panel_budget')
            return super().consume(panel, stage, payload_sha256)
        self._verify_plan()
        # B2's original transport signature supplies the exact ticker. Its slot
        # must already have been bound from the canonical B2 request by the Bridge.
        if slot_scope is None and stage == 'B2':
            rows = [s for s in self.bound.values() if s['stage'] == 'B2' and s['subjects'] == [panel]
                    and s['payload_sha256'] == payload_sha256]
            slot_scope = rows[0] if len(rows) == 1 else None
        if not isinstance(slot_scope, dict):
            raise ValueError('frozen_model_slot_scope_required')
        slot_id = slot_scope.get('slot_id')
        if (self.bound.get(slot_id) != slot_scope or slot_scope['stage'] != stage
                or slot_scope['payload_sha256'] != payload_sha256 or slot_id in self.used
                or len(self.used) >= self.maximum):
            raise ValueError('model_slot_scope_drift_used_or_budget_exhausted')
        if self.journal is not None:
            self._journal_state('CONSUME', slot_id=slot_id)
        else:
            self.used.add(slot_id)
        return len(self.used)

    def resolve_scope(self, panel, stage, payload_sha256, slot_scope=None):
        if slot_scope is None and stage == 'B2':
            rows = [s for s in self.bound.values() if s['stage'] == stage and s['subjects'] == [panel]
                    and s['payload_sha256'] == payload_sha256]
            return rows[0] if len(rows) == 1 else None
        return slot_scope

    def record_acceptance(self, slot_id, *, payload_sha256, output_sha256):
        from app.services.model_execution_plan import _sha
        self._verify_plan()
        if (slot_id not in self.used or slot_id in self.accepted
                or self.bound[slot_id]['payload_sha256'] != payload_sha256):
            raise ValueError('model_slot_original_acceptance_binding_gap')
        output_sha256 = _sha(output_sha256)
        if self.journal is not None:
            self._journal_state('ACCEPT', slot_id=slot_id, output_sha256=output_sha256)
        else:
            self.accepted[slot_id] = output_sha256

    def state(self):
        self._journal_state('OPEN')
        return dict(approved_max_invocations=self.maximum, planned_slots=len(self.slots),
                    consumed=len(self.used), remaining=self.maximum-len(self.used),
                    remaining_planned_slots=len(self.slots)-len(self.used),
                    plan_sha256=self.plan.sha256 if self.plan is not None else None)
