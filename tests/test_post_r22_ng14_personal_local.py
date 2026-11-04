"""Offline contract regressions; these names do not enroll real securities."""
from copy import deepcopy
from pathlib import Path

import pytest

from app.services import manual_shadow_source_session as manual
from app.services import prospective_class_c_owner as prospective
from app.services.issuer_business_bridge import identity_bridge
from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.unified_snapshot_contract import digest
from tests.test_issuer_business_bridge import fixture
from tests.test_post_r22_ng09_manual_session import case


def test_source_inventory_rejects_unknown_name_without_stat(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'allowed.json').write_text('{}')
    denied = source / 'unexpected-private-canary.json'
    denied.write_text('synthetic only')
    original = Path.stat

    def checked(path, *args, **kwargs):
        if path == denied:
            pytest.fail('unexpected path metadata accessed')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'stat', checked)
    with pytest.raises(ValueError, match='source_inventory_drift'):
        manual._source_integrity(source, {'allowed.json': '0' * 64})


def test_synthetic_ibm_unknown_limit_is_not_an_economic_judgment():
    from scripts import r2b_r2_contract as contract
    from tests.test_unknown_limit_recovery_r22r2 import _fixture
    from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
    from app.services.direction_timing_ownership_service import build_owned_evidence_packet

    stock, authority = _fixture()
    stock['ticker'] = authority['ticker'] = 'IBM'
    packet = stock['packet']
    source = packet['stocks'][0]
    source['ticker'] = 'IBM'
    evidence = build_decision_evidence_packet(packet=packet, stock=source)
    owned = build_owned_evidence_packet(evidence, stock=source)
    stock.update(evidence_packet=evidence.model_dump(mode='json'), ownership=owned.model_dump(mode='json'))
    assert contract.decision_mode(stock, authority, {}) == 'UNKNOWN_LIMIT'
    recovery = contract.limitation_catalog(stock, authority)
    raw = dict(decision_mode='UNKNOWN_LIMIT', overall_direction='OBSERVE', new_buyer='OBSERVE',
        holder='OBSERVE', directional_buy_score=None, directional_sell_score=None, confidence=None,
        limitation_reason='ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE', unknowns=list(recovery),
        required_next_evidence=list(recovery))
    capability = {key: [] for key in contract.DIRECTION_BUCKETS}
    assert contract.validate_unknown(raw, mode='UNKNOWN_LIMIT', recovery=recovery, capability=capability)['status'] == 'PASS'
    with pytest.raises(ValueError):
        contract.validate_unknown({**raw, 'overall_direction': 'BUY'}, mode='UNKNOWN_LIMIT',
            recovery=recovery, capability=capability)


def test_session_fingerprint_inventory_is_finite_without_tree_walk(monkeypatch):
    monkeypatch.setattr(Path, 'rglob', lambda *a, **k: pytest.fail('unbounded tree enumeration'))
    pins = manual.code_fingerprints()
    assert 'scripts/r9_rev11_replay.py' in pins
    assert 'app/services/manual_shadow_source_session.py' in pins
    assert 30 < len(pins) < 100
    assert all(not name.startswith(('data/', 'private/', '.env')) for name in pins)


def test_unissued_live_handle_rejected_before_path_access(tmp_path, monkeypatch):
    root, kwargs, _, _ = case(tmp_path)
    kwargs['prospective_owners']['us'] = prospective.ProspectiveOwner()
    monkeypatch.setattr(manual, '_plain_path', lambda *a: pytest.fail('path touched before authority'))
    with pytest.raises(ValueError, match='prospective_live_backend_owner_required'):
        manual.ManualShadowSourceSession(root, **kwargs)


def test_default_off_has_no_import_time_inventory():
    assert not hasattr(manual, '_IMPORT_CODE')
    with pytest.raises(ValueError, match='manual_shadow_disabled'):
        manual.ManualShadowSourceSession(object(), output_root=object(), frozen=None, outcome=None,
            policy=None, prospective_owners=None, source_file_sha256=None,
            expected_code_fingerprints=None)


@pytest.mark.parametrize('ticker', ['035420', 'NVDA', 'UNSEEN_ADS'])
def test_equivalent_unseen_listing_template_uses_same_owner(ticker):
    args = fixture()
    original = deepcopy(args)
    args['target']['ticker'] = ticker
    evidence = dict(args['official']['evidence'])
    evidence['ticker'] = ticker
    args['official'] = OfficialSecurityIdentityEvidence(**evidence).to_payload()
    args['expected_official_sha256'] = digest(args['official'])
    result = identity_bridge(**args)
    assert result['status'] == 'PASS'
    assert result['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE']
    assert not result['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
    assert not result['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']
    assert args['target']['adr_ratio'] is original['target']['adr_ratio'] is None
