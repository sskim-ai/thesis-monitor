"""Synthetic issuance consistency; original Market validation stays unchanged."""
from copy import deepcopy

import pytest

from app.services.unified_snapshot_contract import digest
from tests.test_r2b_r5_market_adapter import fixture, project


@pytest.mark.parametrize('change,reason', [
    ('outer_run', 'night_acquisition_identity_mismatch'),
    ('nested_run', 'night_request_receipt_mismatch'),
    ('acquisition', 'night_request_receipt_mismatch'),
    ('request_date', 'night_request_date_identity_mismatch'),
    ('request_time', 'night_request_time_mismatch'),
    ('attempt', 'market_attempt_mismatch'),
    ('publication', 'publication_version_mismatch'),
])
def test_rehashing_envelope_does_not_reissue_original_owner(change, reason, record_property):
    packet, seed, graph = fixture('us', run='ng17-synthetic-owner')
    night = graph['night']
    if change == 'outer_run':
        graph['markets']['us']['run_id'] = seed['parent_run_id'] = 'another-run'
    elif change == 'nested_run':
        night['original_receipts'][0]['run_id'] = 'another-run'
    elif change == 'acquisition':
        night['original_receipts'][0]['acquisition_id'] = 'another-acquisition'
    elif change == 'request_date':
        night['original_receipts'][0]['request']['params']['basDd'] = '20260101'
    elif change == 'request_time':
        night['original_receipts'][0]['received_at'] = '2026-09-28T08:01:00+00:00'
    elif change == 'attempt':
        graph['markets']['us']['attempt_id'] = 'another-attempt'
    else:
        name = next(iter(graph['publication_context']))
        graph['publication_context'][name]['source_sha256'] = 'c' * 64
    seed['attempt_hashes']['us'] = digest(graph['markets']['us'])
    graph['run_seed_sha256'] = digest(seed)
    packet.update(market_sources=deepcopy(graph['markets']['us']),
        run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph),
        night_and_publication_context=deepcopy(night),
        publication_context=deepcopy(graph['publication_context']))
    with pytest.raises(ValueError, match=reason):
        project((packet, seed, graph))
    record_property('ng17_owner_rejection', dict(change=change, reason=reason,
        provenance='SYNTHETIC_ORIGINAL_MARKET_VALIDATOR', real_source_failure=False))


def test_fresh_issuance_preserves_nested_request_and_clock_bindings(record_property):
    first = fixture('us', run='ng17-first-owner')
    second = fixture('us', run='ng17-second-owner')
    for packet, seed, graph in (first, second):
        run = seed['parent_run_id']
        night = graph['night']
        assert graph['markets']['us']['run_id'] == night['original_run_id'] == run
        assert all(r['run_id'] == run and r['acquisition_id'] == run + ':night'
                   for r in night['original_receipts'])
        assert project((packet, seed, graph))['context']['parity_status'] == 'PASS'
    assert first[2]['night']['original_receipts'] != second[2]['night']['original_receipts']
    assert first[2]['night']['value'] == second[2]['night']['value']
    record_property('ng17_owner_issuance', dict(original_request_receipts=True,
        mutation_after_issuance=False, provenance='SYNTHETIC_NOT_PROVIDER_CAPTURE'))
