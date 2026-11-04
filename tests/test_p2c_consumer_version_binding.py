"""Prompt revisions retain their exact provenance and V3 output contract."""
from copy import deepcopy
import pytest
from app.services import vnext_balanced_stage_review as stage
from app.services import vnext_unified_judgment as engine
from app.services.vnext_daily_bridge import DailyResearchBridge
from app.services.vnext_unified_dispatch import consume
from test_vnext_axis_evidence_roles import AxisHarness


@pytest.mark.parametrize('version', [stage.UNIFIED_AI_V3, stage.UNIFIED_AI_V3_CITATION])
def test_original_owner_dated_and_actual_daily_bridge(monkeypatch, tmp_path, version):
    h = AxisHarness(monkeypatch, tmp_path / 'research.sqlite3')
    h.version = version
    b = h.run()
    blind = h.restore(*b)
    a = h.run('ADJUDICATION', blind)
    adj = h.restore(*a, name='ADJUDICATION', prior=blind)
    owner = stage.StageReviewOwner(blind, adj, enabled=True)
    context = dict(observed_as_of=h.packet['base']['as_of'], completed_market_session=None,
        freshness_by_source={}, required_market_fields={'state': 'NOT_CHECKED'},
        current_price_denials=['NOT_CURRENT'], source_revisions={})
    dated = consume(h.ctrl, packet=h.packet, owner=owner, mode='DATED_REPLAY',
        output_context=context, enabled=True)
    bridge = DailyResearchBridge(registration={'security': h.packet['base']['public_security']},
        session='2026-10-28', prior_session='2026-10-27', as_of=h.packet['base']['as_of'],
        plan_sha256='1' * 64, recover_source=lambda: None, registry=h.registry)
    daily = bridge.consume_unified(h.ctrl, packet=h.economic, review=owner, enabled=True)
    assert dated['decision_sha256'] == daily['decision_sha256']
    assert dated['contract'] == daily['contract'] == engine.AI_OWNED_V3
    assert daily['reused'] and not daily['send'] and not daily['strict_ready']
    assert daily['decision']['model_output'] == h.value
    assert daily['decision']['model_receipt']['adjudication_execution']['prompt_version'] == version
    with pytest.raises(ValueError, match='default_off'):
        consume(h.ctrl, packet=h.packet, owner=owner, mode='DATED_REPLAY', output_context=context)
    bad_packet = deepcopy(h.packet)
    bad_packet['contract'] = stage.UNIFIED_AI
    with pytest.raises(ValueError, match='two_stage_owner'):
        consume(h.ctrl, packet=bad_packet, owner=owner, mode='DATED_REPLAY', output_context=context, enabled=True)
    with pytest.raises(ValueError, match='two_stage_owner'):
        consume(h.ctrl, packet=h.packet, owner=owner.issue(), mode='DATED_REPLAY', output_context=context, enabled=True)
    adj.version = stage.UNIFIED_AI if version == stage.UNIFIED_AI_V3 else stage.UNIFIED_AI_V3
    with pytest.raises(ValueError, match='two_stage_owner'):
        consume(h.ctrl, packet=h.packet, owner=owner, mode='DATED_REPLAY', output_context=context, enabled=True)
    adj.version = version
    owner.revoke()
    with pytest.raises(ValueError):
        bridge.consume_unified(h.ctrl, packet=h.economic, review=owner, enabled=True)
