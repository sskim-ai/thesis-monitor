"""Recovered public historical identity, not current SKHY business authority.

Main's one frozen final runner owns execution and exact public admission. REV2 raw
discovery is genuine; original prebridge revenue and source plans remain
unadmitted. Synthetic current-path proofs are explicitly separate below.
"""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import stat

import pytest

from app.services.issuer_business_bridge import bind_comparison, identity_bridge
from app.services.unified_snapshot_contract import digest


PUBLIC_ROOT = Path('/Users/sskim/Documents/Codex/Reports/20261019-post-r22-ng17-historical-owner-repair')
PUBLIC_PINS = {
    'skhy-rev6-sec-identity.json': (6163, '58d3c8acd47c20f3aa5852f53599dfd4f09395eb51d1ed257e4565dd3d006221'),
    'skhy-rev6-sec-archive.json': (7914, 'e1b5ec547e2974b75d9b33869172ff136e34105777f3f37476b310afe8ca3064'),
    'skhy-rev6-authority-freeze.json': (501, 'fdc3e18bbf9df2323883b3f7a16f7acb4baf49db1941fb11f110d9f3a83c7db3'),
    'skhy-rev6-bridge.json': (1327, '6aefc099dbaa326d7853e5302a5562ce1d6cf270bcbf815a28944344f5eba61d'),
    'skhy-rev6-added-facts.json': (7150, 'f653be09b82e92c708fcce8a8daca3479c8f6202910129e2653f9b74ce78c05f'),
    'skhy-rev6-field-matrix.json': (17146, '7b50159f70e175eb11da49d32baf4ba39663aed64e9ae698b4a15a03ed10a74b'),
    'skhy-rev2-discovery-plan.json': (354, 'b3d300e86beb6670770d7b7eee8c38b66b49e98afc865adb1eb4347430aa9699'),
    'skhy-rev2-discovery-receipt.json': (653, '8198f834f210d26a8cc93720ad31647a340b6ad1faccf95334bd4b20092c62f7'),
    'skhy-rev2-discovery.body': (1397, 'e86c79e2e84cf4a0bc26d1a9f24d2f01abc05e7042f1e17973b1bb8a50846555'),
}


@pytest.fixture
def public():
    rows = {}
    for name, (size, expected) in PUBLIC_PINS.items():
        path = PUBLIC_ROOT / name
        assert path.resolve() == path
        # Absolute content opens remain visible to the inherited audit. Do not
        # add a basename/dir_fd exception to its allowed-read boundary.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            assert stat.S_ISREG(info.st_mode) and info.st_size == size
            raw = stream.read(size + 1)
        assert (len(raw), sha256(raw).hexdigest()) == (size, expected)
        rows[name] = json.loads(raw)
    return rows


def historical_arguments(public):
    official = public['skhy-rev6-sec-identity.json']
    bridge = public['skhy-rev6-bridge.json']
    # These public identity views are not a Class-C seed or a financial plan.
    target = {k: official['evidence'][k] for k in
              ('ticker', 'cik', 'security_type', 'issuer_type', 'exchange')}
    target.update(canonical_security_id=bridge['monitored_security_id'],
                  canonical_company_id=bridge['target_company_id'])
    source = dict(ticker=bridge['underlying_ticker'], corp_code=bridge['provider_issuer_ids']['opendart'],
                  canonical_security_id=bridge['source_security_id'],
                  canonical_company_id=bridge['source_company_id'], security_type='common_stock', exchange='KRX')
    return dict(target=target, source=source, official=official,
                expected_official_sha256=bridge['official_identity_sha256'],
                dart_rows=public['skhy-rev2-discovery.body']['list'],
                dart_receipt=public['skhy-rev2-discovery-receipt.json'], cutoff=bridge['cutoff'])


def test_recovered_original_discovery_reissues_exact_historical_identity(public, record_property):
    official = public['skhy-rev6-sec-identity.json']
    archived = public['skhy-rev6-sec-archive.json']
    freeze = public['skhy-rev6-authority-freeze.json']
    request = public['skhy-rev2-discovery-plan.json']
    receipt = public['skhy-rev2-discovery-receipt.json']
    old = public['skhy-rev6-bridge.json']
    assert {k: v for k, v in archived.items() if k != 'validation_audit'} == official
    assert digest(official) == freeze['qualified_identity_sha256'] == old['official_identity_sha256']
    assert digest(request) == receipt['request_sha256']
    assert request['plan_sha256'] == receipt['plan_sha256']
    assert request['logical_id'] == receipt['logical_id'] == '000660:request-001'
    assert request['url'] == 'https://opendart.fss.or.kr/api/list.json'
    assert request['params']['corp_code'] == '00164779'
    assert digest(receipt) == old['dart_receipt_sha256']
    assert receipt['raw_sha256'] == old['dart_raw_sha256'] == PUBLIC_PINS['skhy-rev2-discovery.body'][1]
    assert receipt['started_at'] == '2026-09-27T00:34:10.217541+00:00'
    assert receipt['finished_at'] == '2026-09-27T00:34:10.324395+00:00'
    assert old['cutoff'] == '2026-09-27T09:33:34.100483+09:00'
    arguments = historical_arguments(public)
    before = deepcopy(arguments)
    replayed = identity_bridge(**arguments)
    assert replayed == old
    assert replayed['status'] == 'PASS'
    assert arguments == before
    assert not replayed['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']
    assert not replayed['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
    record_property('ng17_skhy_historical_identity', dict(
        original_discovery_raw=receipt['raw_sha256'], original_discovery_receipt=digest(receipt),
        bridge_receipt=replayed['receipt_sha256'], cutoff=old['cutoff'],
        scope='HISTORICAL_IDENTITY_FUNCTION_ONLY', original_revenue_owner='NOT_RUN_INPUT_NOT_ADMITTED',
        current_source_generation='NOT_RUN', private_reads=0))


@pytest.mark.parametrize('change,error', [
    ('wrong_cik', 'official_security_field_unverified:cik'),
    ('wrong_corp', 'official_dart_security_issuer_mapping_unverified'),
    ('common_not_ads', 'instrument_relationship_not_supported'),
    ('wrong_exchange', 'official_security_field_unverified:exchange'),
    ('wrong_underlying', 'official_security_field_unverified:ordinary_share_identifier'),
    ('identity_hash', 'official_identity_frozen_digest_mismatch'),
    ('missing_receipt', 'official_dart_security_issuer_mapping_unverified'),
    ('source_denied', 'official_dart_security_issuer_mapping_unverified'),
])
def test_original_identity_owner_rejects_altered_public_lineage(public, change, error):
    args = deepcopy(historical_arguments(public))
    if change == 'wrong_cik':
        args['target']['cik'] = '0000000999'
    elif change == 'wrong_corp':
        args['source']['corp_code'] = '00999999'
    elif change == 'common_not_ads':
        args['target']['security_type'] = 'common_stock'
    elif change == 'wrong_exchange':
        args['target']['exchange'] = 'NYSE'
    elif change == 'wrong_underlying':
        args['source']['ticker'] = '123456'
    elif change == 'identity_hash':
        args['expected_official_sha256'] = '0' * 64
    elif change == 'missing_receipt':
        args['dart_receipt'] = {}
    elif change == 'source_denied':
        args['dart_receipt']['failure_class'] = 'PROVIDER_DENIAL'
    result = identity_bridge(**args)
    assert result['status'] == 'FAIL'
    assert error in result['errors']
    assert result['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] is False


def test_recovered_identity_does_not_substitute_for_original_revenue_or_financial_inputs(public):
    from app.services.reported_business_projection import _BUILDER_PERMIT, issue

    bridge = identity_bridge(**historical_arguments(public))
    added = public['skhy-rev6-added-facts.json'][0]
    assert added['issuer_business_bridge']['original_fact_sha256'] == (
        'b485d63d59ae5503182e60af2193eb0e87a57f1efb6da9f3a4e8b383b63eec9e')
    with pytest.raises(ValueError, match='^issuer_business_original_fact_mismatch$'):
        bind_comparison(added, {}, bridge,
                        source_result_sha256=added['issuer_business_bridge']['source_result_sha256'])
    with pytest.raises(ValueError, match='^business_issuer_original_inputs_required$'):
        issue(stock={}, packet={}, facts=[added], plan={'ticker': 'SKHY', 'issuer': '0002120882'},
              acquisition={}, projection={}, selected_owner={}, quality={}, bridge=bridge,
              financial_inputs=None, _permit=_BUILDER_PERMIT)


@pytest.mark.parametrize('subject', ['NVDA', '035420'])
def test_original_stock_reader_denies_unenrolled_subject_before_source_reads(tmp_path, subject):
    from app.services.canonical_source_replay import stock_inputs
    from tests.test_unified_stock_acquisition import plan as plan_fixture

    plan = plan_fixture.__wrapped__()
    with pytest.raises(ValueError, match='^stock_subject_view_not_in_original_plan$'):
        stock_inputs(tmp_path, {'stock_plan': plan.model_dump(mode='json')}, None, {}, subjects=[subject])


@pytest.fixture
def synthetic_source(tmp_path):
    from tests.rev9_source_fixtures import bridge_inputs
    from tests.rev10_source_fixtures import wire_clock
    from tests.test_reported_business_native_projection import window
    from tests.test_unified_stock_acquisition import plan as plan_fixture

    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        target, _ = bridge_inputs(tmp_path)
    target.update(reported_comparison_business=True, source_window=window(plan))
    return target


def test_synthetic_original_selected_fresh_projection_authority_chain_retains_scope(synthetic_source, record_property):
    from app.services.bounded_financial_stock_owner import _issuer_business_facts
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from app.services.selected_financial_owner import validate
    from scripts.m12dr_financial_source_authority import build_source_authority

    inputs = synthetic_source
    fin = inputs['financial_inputs']
    bridge, facts, origin = _issuer_business_facts(fin['plan'], fin['issuer_business'])
    result = assemble_fresh_stock(**inputs)
    selected = validate(result['selected_financial_owner'], projection=origin['projection'], facts=facts, bridge=bridge)
    assert result['status'] == 'PASS'
    assert selected['owner_type'] == 'issuer_business_bridge'
    assert selected['selected_acquisition_sha256'] == origin['input_hashes']['acquisition']
    assert result['quality_view']['receipt']['directional_use_allowed'] is False
    authority = build_source_authority(**fresh_authority_inputs(result, inputs))['authority']
    records = {r['ref_id']: r for r in authority['authority_records']}
    original = {f['fact_id']: f for f in origin['packet']['stocks'][0]['fact_catalog']}
    for fact in facts:
        chain = fact['issuer_business_bridge']
        source_fact = original[chain['original_fact_id']]
        assert fact['fields'] == source_fact['fields']
        assert fact['field_dependency_receipts'] == source_fact['field_dependency_receipts']
        assert chain['original_fact_sha256'] == digest(source_fact)
        assert chain['source_provider'] == 'opendart'
        row = records['canonical:' + fact['fact_id']]
        assert row['allowed_uses'] == ['CONTEXT']
        assert 'OVERALL_DIRECTION' in row['prohibited_uses']
    stock = result['packet']['stocks'][0]
    assert stock['current_valuation_denial'] == 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    assert {e['kind'] for e in stock['reported_business_projection']['payload']['entries'].values()} == {'ISSUER_CONTEXT', 'QUALITY'}
    record_property('ng17_skhy_synthetic_owner_chain', dict(
        synthetic_only=True, historical_public_mixed_in=False, current_SKHY_grant=False,
        original_owners=['_issuer_business_facts', 'assemble_fresh_stock', 'selected_financial_owner.validate',
                         'reported_business_projection.issue', 'fresh_authority_inputs', 'build_source_authority'],
        allowed_use='CONTEXT', security_transfer=False))


@pytest.mark.parametrize('change,error', [
    ('cutoff', 'issuer_business_source_scope_or_cutoff_mismatch'),
    ('source_digest', 'issuer_business_source_owner_replay_mismatch'),
])
def test_original_source_owner_rejects_stale_or_rehashed_dependency(synthetic_source, change, error):
    from app.services.bounded_financial_stock_owner import _issuer_business_facts

    fin = synthetic_source['financial_inputs']
    inputs = fin['issuer_business']
    if change == 'cutoff':
        inputs['source_inputs']['plan']['cutoff'] = '2026-09-01T00:00:00+00:00'
    else:
        inputs['source_result_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='^' + error + '$'):
        _issuer_business_facts(fin['plan'], inputs)


def test_current_selected_owner_rejects_rehashed_scope_expansion(synthetic_source):
    from app.services.bounded_financial_stock_owner import _issuer_business_facts
    from app.services.selected_financial_owner import select

    fin = synthetic_source['financial_inputs']
    bridge, facts, origin = _issuer_business_facts(fin['plan'], fin['issuer_business'])
    bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE'] = True
    bridge['receipt_sha256'] = digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'})
    with pytest.raises(ValueError, match='^selected_financial_bridge_incomplete$'):
        select(plan=fin['plan'], acquisition=fin['acquisition'], projection={}, facts=facts,
               bridge=bridge, origin=origin)
