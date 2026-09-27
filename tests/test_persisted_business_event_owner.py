from copy import deepcopy
from datetime import timedelta
import json

import pytest

from app.services.persisted_business_event_owner import FILES, replay_persisted_event
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from test_unified_stock_event_input import wire
from test_unified_stock_owner import source as source_fixture


@pytest.fixture
def event(tmp_path):
    stock = source_fixture.__wrapped__()
    value, cutoff, policy, security = wire(tmp_path, stock)
    raw = {n: (tmp_path / 'wire' / n).read_bytes() for n in FILES if n != 'logical-receipt.json'}
    raw['logical-receipt.json'] = json.dumps(dict(HTTP_attempts=1, logical_attempts=1,
        owner_error=None, provider=value.read.provider, subject=security['ticker'])).encode()
    return dict(artifacts=raw, hashes={n: sha256_bytes(v) for n, v in raw.items()},
        security_records=[security], ticker=security['ticker'], market='us',
        current_run_id='different-current-run', cutoff=cutoff, policy=policy,
        current_news_denial=dict(role='news_and_filing_events', run_id='different-current-run',
            acquisition_class='OPTIONAL_UNAVAILABLE', denial='no_current_acquisition'))


def mutate(event, name, transform):
    row = json.loads(event['artifacts'][name])
    transform(row)
    event['artifacts'][name] = json.dumps(row).encode()
    event['hashes'][name] = sha256_bytes(event['artifacts'][name])


def test_historical_event_is_subordinate_and_deterministic(event):
    _, receipt = replay_persisted_event(**event)
    assert receipt == replay_persisted_event(**event)[1]
    assert receipt['state'] == 'PERSISTED_SOURCE_OWNED_BUSINESS_EVENT'
    assert receipt['original_run_id'] != receipt['current_run_id']
    assert receipt['current_news_denial']['acquisition_class'] == 'OPTIONAL_UNAVAILABLE'
    assert not receipt['new_acquisition_role'] and not receipt['current_class_b_claimed']
    assert receipt['selected'][0]['requires_review']


@pytest.mark.parametrize('mode', ['body_hash', 'response', 'fingerprint', 'publication',
    'ticker', 'company', 'before_publication', 'relevance', 'temporal', 'current_class_b',
    'old_price', 'old_technical', 'old_pass', 'orm_event', 'review_removed', 'provider_upgrade'])
def test_historical_event_fail_closed_controls(event, mode):
    event = deepcopy(event)
    if mode == 'body_hash':
        event['artifacts']['read-0001.body'] += b'changed'
    elif mode == 'response':
        mutate(event, 'read-0001.response.json', lambda r: r.update(acquisition_id='other'))
    elif mode == 'fingerprint':
        def change(r):
            r['normalized'][0]['title'] = 'different fingerprint'
            r['normalized_sha256'] = digest(r['normalized'])
        mutate(event, 'normalization.json', change)
    elif mode == 'publication':
        event['artifacts']['read-0001.body'] = event['artifacts']['read-0001.body'].replace(b'GMT', b'BAD')
    elif mode == 'ticker':
        event['ticker'] = 'OTHER'
    elif mode == 'company':
        event['security_records'][0]['canonical_company_id'] = 'wrong-company'
    elif mode == 'before_publication':
        event['cutoff'] -= timedelta(days=2)
    elif mode == 'relevance':
        mutate(event, 'normalization.json', lambda r: r['candidates'][0]['relevance'].update(accepted=False))
    elif mode == 'temporal':
        mutate(event, 'normalization.json', lambda r: r.update(cutoff='2099-01-01T00:00:00+00:00'))
    elif mode == 'current_class_b':
        event['current_news_denial']['acquisition_class'] = 'RUN_FRESH_ONCE'
    elif mode in {'old_price', 'old_technical', 'old_pass', 'orm_event'}:
        event['artifacts'][mode + '.json'] = b'{}'
        event['hashes'][mode + '.json'] = sha256_bytes(b'{}')
    elif mode == 'review_removed':
        def change(r):
            r['normalized'][0]['requires_review'] = False
            r['normalized_sha256'] = digest(r['normalized'])
        mutate(event, 'normalization.json', change)
    else:
        mutate(event, 'plan.json', lambda r: r.update(provider='sec_edgar'))
    with pytest.raises((ValueError, KeyError)):
        replay_persisted_event(**event)


def test_original_acquisition_cannot_be_renamed_current(event):
    event['current_run_id'] = json.loads(event['artifacts']['plan.json'])['run_id']
    event['current_news_denial']['run_id'] = event['current_run_id']
    with pytest.raises(ValueError, match='historical_source_required'):
        replay_persisted_event(**event)


def test_unknown_current_news_denial_rejected(event):
    event['current_news_denial']['denial'] = ''
    with pytest.raises(ValueError, match='relabel'):
        replay_persisted_event(**event)


def test_source_resolution_preserves_context_only_permissions(event):
    from app.services.unified_stock_owner import assemble_stock
    from test_unified_stock_event_input import bind
    from scripts.m12dk_current_source_authority import freeze_current_source_binding
    from scripts.m12dr_financial_source_authority import build_source_authority
    from scripts.m12cn_policy_contract import build_subject_catalog
    from scripts.m12dr_offline_source_closure import context
    source, _ = replay_persisted_event(**event)
    stock_inputs = source_fixture.__wrapped__()
    bind(stock_inputs, source, event['cutoff'], event['policy'])
    result = assemble_stock(**stock_inputs)
    packet, ep = result['packet'], result['evidence_packet']
    generation = event['current_run_id']
    catalog = build_subject_catalog(context=context(packet, generation), ticker=event['ticker'], atomic_claims=[])
    params = dict(quality_bundles={}, issuer_bindings={}, ticker=event['ticker'],
        source_generation_id=generation, source_packet=packet, evidence_packet=ep,
        catalog=catalog, source_metadata=[r for r in ep['evidence'] if r['ref_id'] in catalog['all_evidence_refs']],
        frozen_binding=freeze_current_source_binding(source_generation_id=generation,
            source_packet=packet, evidence_packet=ep))
    before = build_source_authority(**params)
    after = build_source_authority(**params, persisted_event_inputs=event)
    event_rows = [r for r in after['authority']['authority_records'] if r['ref_id'].startswith('canonical:event:')]
    assert event_rows
    previous = {r['ref_id']:r for r in before['authority']['authority_records']}
    for row in event_rows:
        assert row['allowed_uses'] == previous[row['ref_id']]['allowed_uses'] == ['CONTEXT']
        assert row['prohibited_uses'] == previous[row['ref_id']]['prohibited_uses']
        assert row['authority_state'] == 'RESOLVED'
        assert 'requires_review' in row['source_scope']
