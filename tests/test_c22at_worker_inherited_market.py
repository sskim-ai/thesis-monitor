"""Verify the worker counts physical slots without trusting an asserted skip."""
from dataclasses import asdict

import pytest

from app.services.model_execution_plan import compile_model_plan
from app.services.model_invocation_journal import ModelInvocationJournal
from app.services.production_model_profile import SolHighWirePolicy
from app.services.production_model_transport import CONTRACT_V3, request_from_frame
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_c22z_dynamic_model_plan import cohort


def test_kr8_worker_accepts_17_only_with_matching_inherited_market_journal(tmp_path, monkeypatch):
    from app.services import production_model_transport as transport

    monkeypatch.setattr(transport, 'binding_from_json', lambda value: value)
    plan = compile_model_plan(cohort(0, 8), topology='CANONICAL_PRODUCTION')
    market, core = plan.slots[:2]
    assert len(plan.slots) == 18 and core.stage == 'CORE'
    policy = SolHighWirePolicy()
    directory = tmp_path / 'context'
    directory.mkdir()

    def scope(slot, deps):
        return dict(plan_sha256=plan.sha256, cohort_sha256=plan.cohort.sha256, slot_id=slot.slot_id,
            market='kr', stage=slot.stage, batch_id=slot.batch_id, subjects=list(slot.subjects),
            security_ids=list(slot.security_ids), source_generation=slot.source_generation,
            execution_profile=slot.execution_profile, payload_sha256=digest(slot.slot_id),
            build_receipt_sha256=digest('build'), dependency_outputs=deps)

    old = scope(market, {})
    output = digest('accepted-market')
    pending = scope(core, {market.slot_id:output})
    frame = dict(contract=CONTRACT_V3, directory=str(directory), binding={}, request_id='context',
        prompt_sha256=digest('prompt'), schema_sha256=digest('schema'), execution_policy=asdict(policy),
        execution_plan=plan.to_dict(), slot_scope=pending)
    authorization = {k:frame[k] for k in ('contract','request_id','prompt_sha256','schema_sha256','execution_policy','slot_scope')}
    authorization.update(model=policy.model, effort=policy.effort, timeout=policy.timeout_seconds, planned_slots=18,
        maximum=17, physical_call=1, execution_plan_sha256=plan.sha256, payload_sha256=pending['payload_sha256'])

    def write(**changes):
        raw = encoded(dict(authorization, **changes))
        (directory / 'production-authorization.json').write_bytes(raw)
        from hashlib import sha256
        frame['authorization_sha256'] = sha256(raw).hexdigest()

    write()
    with pytest.raises(ValueError, match='dynamic_plan_or_budget'):
        request_from_frame(frame)
    write(inherited_market_slot=core.slot_id)
    with pytest.raises(ValueError, match='invalid_inherited_market_slot'):
        request_from_frame(frame)
    journal = ModelInvocationJournal(tmp_path/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',
        plan_sha256=plan.sha256, maximum=17, inherited_market_slot=market.slot_id)
    write(inherited_market_slot=market.slot_id)
    with pytest.raises(ValueError, match='inherited_market_journal_drift'):
        request_from_frame(frame)
    journal.transact('BIND', slot_id=market.slot_id, scope=old)
    journal.transact('INHERIT_MARKET', slot_id=market.slot_id, lineage=dict(payload_sha256=old['payload_sha256'],
        source_generation=market.source_generation, new_model_invocations=0, output_sha256=output))
    journal.transact('BIND', slot_id=core.slot_id, scope=pending)
    journal.transact('CONSUME', slot_id=core.slot_id)
    assert request_from_frame(frame).model_plan_scope == pending
    write(inherited_market_slot=market.slot_id, physical_call=2)
    with pytest.raises(ValueError, match='inherited_market_journal_drift'):
        request_from_frame(frame)
