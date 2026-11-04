from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.services.canonical_fact_service import canonical_event_fact
from app.services import persisted_business_event_owner as event_owner
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_owner import assemble_stock
from scripts import m12dr_context_authority_discovery as discovery
from scripts import sealed_business_replay as consumer
from scripts.m12cn_policy_contract import batch_output_schema, build_subject_catalog
from scripts.m12cq_two_pass_contract import pass_b_batch_schema
from scripts.m12da_source_use_contract import (
    SourceUse, build_source_use_projection, canonical_sha256, validate_selected_refs,
)
from scripts.m12dk_current_source_authority import (
    build_current_source_authority, freeze_current_source_binding,
)
from scripts.m12dr_offline_source_closure import context
import test_persisted_business_event_owner as recorded_fixture
from test_unified_stock_event_input import bind, wire
from test_unified_stock_owner import source as stock_fixture


def _sample(event):
    source, receipt = event_owner.replay_persisted_event(**event)
    stock_inputs = stock_fixture.__wrapped__()
    bind(stock_inputs, source, event['cutoff'], event['policy'])
    result = assemble_stock(**stock_inputs)
    # Match the existing persisted owner annotation, without adding economic authority.
    for row in result['observed_business_union']:
        if row.get('source_kind') == 'BUSINESS_EVENT':
            row.update(source_kind='PERSISTED_BUSINESS_EVENT',
                       persisted_source_receipt_sha256=digest(receipt))
    result['persisted_event_receipt'] = receipt
    execution = 'context-review-execution'
    packet, ep = result['packet'], result['evidence_packet']
    frozen = dict(ticker=event['ticker'], source_generation_id=event['current_run_id'],
        execution_generation_id=execution, source_packet=packet, evidence_packet=ep,
        catalog=build_subject_catalog(context=context(packet, execution),
                                      ticker=event['ticker'], atomic_claims=[]),
        frozen_binding=freeze_current_source_binding(source_generation_id=event['current_run_id'],
                                                     source_packet=packet, evidence_packet=ep))
    replay = dict(event_inputs=event, observed_business_union=result['observed_business_union'],
                  persisted_event_receipt=receipt)
    return frozen, replay, result, stock_inputs


@pytest.fixture
def sample(tmp_path):
    return _sample(recorded_fixture.event.__wrapped__(tmp_path))


def _resolve(sample):
    frozen, replay, _, _ = sample
    return discovery.resolve_persisted_context_v1(
        discovery.build_context_discovery_v1(**frozen), **replay, **frozen)


def _rehash(view):
    view.pop('view_sha256', None)
    view['view_sha256'] = canonical_sha256(view)


def _legacy_outputs(frozen):
    catalog = frozen['catalog']
    packet = frozen['source_packet']
    kwargs = {k: v for k, v in frozen.items() if k != 'execution_generation_id'}
    kwargs['source_metadata'] = [row for row in frozen['evidence_packet']['evidence']
                                if row['ref_id'] in catalog['all_evidence_refs']]
    identity = dict(generation_id=frozen['execution_generation_id'], packet_id=packet['packet_id'],
        market=packet['market'], assessment_date=packet['assessment_date'],
        subjects=[frozen['ticker']], catalogs={frozen['ticker']: catalog})
    return (build_current_source_authority(**kwargs), batch_output_schema(**identity),
            pass_b_batch_schema(**identity), build_source_use_projection(
                ticker=frozen['ticker'], input_generation_id=frozen['source_generation_id'],
                catalog=catalog))


def test_exact_replay_resolves_only_context_and_preserves_legacy_outputs(sample):
    frozen, replay, _, _ = sample
    inputs_before = deepcopy((frozen, replay))
    legacy_before = _legacy_outputs(frozen)
    before = discovery.build_context_discovery_v1(**frozen)
    after = _resolve(sample)
    assert before['context_records']
    assert before['persisted_event_receipt_sha256'] is None
    assert discovery.validate_context_discovery_v1(after, **replay, **frozen) == after
    assert after == _resolve(sample)
    assert after['source_generation_id'] != after['execution_generation_id']
    assert after['original_run_id'] != after['source_generation_id']
    assert after['original_run_id'] == replay['persisted_event_receipt']['original_run_id']
    for old, new in zip(before['context_records'], after['context_records'], strict=True):
        assert old['authority_state'] == 'UNRESOLVED'
        assert new['authority_state'] == 'RESOLVED'
        assert old['allowed_uses'] == new['allowed_uses'] == ['CONTEXT']
        assert old['prohibited_uses'] == new['prohibited_uses'] == sorted(
            use.value for use in SourceUse if use != SourceUse.CONTEXT)
        assert new['requires_review'] is True
    assert not set(after['context_refs']) & set(frozen['catalog']['all_evidence_refs'])
    assert 'all_evidence_refs' not in after and 'authority_records' not in after
    assert _legacy_outputs(frozen) == legacy_before
    assert (frozen, replay) == inputs_before


@pytest.mark.parametrize('mutation', [
    'contract', 'purpose', 'source_generation_id', 'execution_generation_id', 'cutoff',
    'ticker', 'market', 'original_run_id', 'original_acquisition_id', 'source_binding_sha256',
    'extra_root', 'missing_root', 'duplicate', 'drop', 'unknown_ref', 'permission',
    'prohibition', 'review', 'extra_record', 'unresolved', 'metadata_hash',
])
def test_rehashed_discovery_forgery_is_rejected_against_trusted_inputs(sample, mutation):
    frozen, replay, _, _ = sample
    view = deepcopy(_resolve(sample))
    row = view['context_records'][0]
    if mutation == 'extra_root':
        view['all_evidence_refs'] = list(view['context_refs'])
    elif mutation == 'missing_root':
        del view['decision_catalog_sha256']
    elif mutation == 'duplicate':
        view['context_records'].append(deepcopy(row))
    elif mutation == 'drop':
        view['context_records'] = []
        view['context_refs'] = []
    elif mutation == 'unknown_ref':
        row['ref_id'] = 'canonical:event:unknown:event'
        view['context_refs'] = [row['ref_id']]
    elif mutation == 'permission':
        row['allowed_uses'].append('OVERALL_DIRECTION')
    elif mutation == 'prohibition':
        row['prohibited_uses'].remove('ENTRY')
    elif mutation == 'review':
        row['requires_review'] = 1
    elif mutation == 'extra_record':
        row['core_current_fact'] = True
    elif mutation == 'unresolved':
        row['authority_state'] = 'UNRESOLVED'
    elif mutation == 'metadata_hash':
        row['source_metadata_sha256'] = '0' * 64
    else:
        view[mutation] = 'foreign-or-unsupported'
    _rehash(view)
    with pytest.raises(ValueError, match='context_discovery_trusted_input_mismatch'):
        discovery.validate_context_discovery_v1(view, **replay, **frozen)


@pytest.mark.parametrize('use', [use.value for use in SourceUse if use != SourceUse.CONTEXT])
def test_every_noncontext_use_is_denied_without_fallback(sample, use):
    frozen, replay, _, _ = sample
    unresolved = discovery.build_context_discovery_v1(**frozen)
    with pytest.raises(ValueError, match='purpose_or_use_denied'):
        discovery.validate_context_discovery_v1(unresolved, use=use, **replay, **frozen)
    legacy = build_source_use_projection(ticker=frozen['ticker'],
        input_generation_id=frozen['source_generation_id'], catalog=unresolved)
    assert validate_selected_refs(legacy, refs=unresolved['context_refs'],
                                  use=use, require_any=True)['status'] == 'FAIL'


def test_unresolved_view_is_not_consumable(sample):
    frozen, replay, _, _ = sample
    with pytest.raises(ValueError, match='trusted_input_mismatch'):
        discovery.validate_context_discovery_v1(
            discovery.build_context_discovery_v1(**frozen), **replay, **frozen)
    with pytest.raises(ValueError, match='purpose_or_use_denied'):
        discovery.build_context_discovery_v1(**frozen, purpose='OVERALL_DIRECTION')


@pytest.mark.parametrize('mutation', ['raw_rehashed', 'subject', 'generation', 'cutoff',
    'review_removed', 'receipt', 'union_missing', 'union_duplicate', 'union_forged',
    'union_nondict', 'union_mapping', 'source_relabel'])
def test_replay_and_observed_union_are_recomputed(sample, mutation):
    frozen, replay, _, _ = deepcopy(sample)
    before = discovery.build_context_discovery_v1(**frozen)
    event = replay['event_inputs']
    if mutation == 'raw_rehashed':
        name = 'read-0001.body'
        event['artifacts'][name] += b'changed'
        event['hashes'][name] = sha256_bytes(event['artifacts'][name])
    elif mutation == 'subject':
        event['ticker'] = 'OTHER'
    elif mutation == 'generation':
        event['current_run_id'] = 'other-current'
        event['current_news_denial']['run_id'] = 'other-current'
    elif mutation == 'cutoff':
        from datetime import timedelta
        event['cutoff'] -= timedelta(days=2)
    elif mutation == 'review_removed':
        def change(row):
            row['normalized'][0]['requires_review'] = False
            row['normalized_sha256'] = digest(row['normalized'])
        recorded_fixture.mutate(event, 'normalization.json', change)
    elif mutation == 'receipt':
        replay['persisted_event_receipt']['original_run_id'] = 'borrowed-history'
    elif mutation == 'union_missing':
        replay['observed_business_union'] = []
    elif mutation == 'union_duplicate':
        replay['observed_business_union'] *= 2
    elif mutation == 'union_nondict':
        replay['observed_business_union'] = [None]
    elif mutation == 'union_mapping':
        replay['observed_business_union'] = {}
    elif mutation == 'union_forged':
        row = next(row for row in replay['observed_business_union']
                   if row.get('source_kind') == 'PERSISTED_BUSINESS_EVENT')
        row['event']['requires_review'] = False
    else:
        event['current_news_denial']['acquisition_class'] = 'RUN_FRESH_ONCE'
    with pytest.raises(ValueError):
        discovery.resolve_persisted_context_v1(before, **replay, **frozen)


@pytest.mark.parametrize('mutation', ['metadata', 'catalog_union', 'atomic_parent', 'canonical_source'])
def test_rehashed_packet_or_catalog_cannot_launder_event_authority(sample, mutation):
    frozen, replay, _, _ = deepcopy(sample)
    event_ref = next(row for row in frozen['evidence_packet']['evidence']
                     if row['ref_id'].startswith('canonical:event:'))
    if mutation == 'metadata':
        event_ref['source_use']['security_id'] = 'OTHER'
    elif mutation == 'catalog_union':
        frozen['catalog']['all_evidence_refs'].append(event_ref['ref_id'])
    elif mutation == 'atomic_parent':
        frozen['catalog']['atomic_claims'].append(dict(ticker=frozen['ticker'],
            claim_ref='claim:laundered', parent_source_refs=[event_ref['ref_id']]))
    else:
        stock = frozen['source_packet']['stocks'][0]
        stock['evidence'][0]['title'] = 'Fixture changed source contract'
        stock['fact_catalog'] = [row for row in stock['fact_catalog']
                                 if not row['fact_id'].startswith('event:')]
        stock['fact_catalog'].extend(canonical_event_fact(row) for row in stock['evidence'])
        ctx = context(frozen['source_packet'], frozen['execution_generation_id'])
        frozen['evidence_packet'] = ctx['evidence_packets'][0]
        frozen['catalog'] = build_subject_catalog(context=ctx, ticker=frozen['ticker'], atomic_claims=[])
    frozen['frozen_binding'] = freeze_current_source_binding(
        source_generation_id=frozen['source_generation_id'], source_packet=frozen['source_packet'],
        evidence_packet=frozen['evidence_packet'])
    with pytest.raises(ValueError):
        discovery.resolve_persisted_context_v1(
            discovery.build_context_discovery_v1(**frozen), **replay, **frozen)


@pytest.mark.parametrize('phrase,role', [
    ('data quality restored', 'positive_quality_refs'),
    ('material disclosure failure', 'material_disclosure_failure_refs'),
])
def test_raw_quality_headline_remains_context_only(tmp_path, monkeypatch, phrase, role):
    monkeypatch.setattr(recorded_fixture, 'wire', lambda path, stock: wire(path, stock,
        title='Fixture awarded large order supply contract signed; ' + phrase))
    sample = _sample(recorded_fixture.event.__wrapped__(tmp_path))
    frozen, replay, _, _ = sample
    before = _legacy_outputs(frozen)
    view = _resolve(sample)
    assert set(view['context_refs']) <= set(frozen['catalog'][role])
    assert not set(view['context_refs']) & set(frozen['catalog']['all_evidence_refs'])
    assert discovery.validate_context_discovery_v1(view, **replay, **frozen) == view
    assert all(row['allowed_uses'] == ['CONTEXT'] and 'CONFIDENCE' in row['prohibited_uses']
               for row in view['context_records'])
    assert _legacy_outputs(frozen) == before


def _consumer_run(sample, tmp_path, monkeypatch, *, tamper=False, non_event=False):
    frozen, replay, result, stock_inputs = sample
    corpus, output = tmp_path / 'corpus', tmp_path / 'output'
    ticker = frozen['ticker']
    durable_json(corpus / 'rev8-full-source-acquisition-plan.json', dict(stock_plan={},
        proof_run_id=frozen['execution_generation_id'], market_attempts={'us': 'synthetic-attempt'},
        class_c_versions={}))
    durable_json(corpus / f'class-c/business-versioned-{ticker}.json', {})
    durable_json(corpus / 'class-c/local-us.json', {})
    # Isolate outer cohort I/O and assembly. Discovery, raw replay and its consumer are real.
    monkeypatch.setattr(consumer, 'UNIVERSE', {'us': (ticker,)})
    monkeypatch.setattr(consumer, 'network_guard', lambda: {})
    monkeypatch.setattr(consumer, 'StockPlan', SimpleNamespace(model_validate=lambda _: SimpleNamespace(
        run_id=frozen['source_generation_id'], frozen_at=replay['event_inputs']['cutoff'])))
    monkeypatch.setattr(consumer, 'current_stock_inputs', lambda *args, **kwargs: deepcopy(stock_inputs))
    monkeypatch.setattr(event_owner, 'bind_persisted_event', lambda **kwargs: dict(
        result=deepcopy(result), binding_kind=event_owner.STATE, fresh_price_technical_unchanged=True))
    calls = []

    def stop_action(**kwargs):
        calls.append(kwargs)
        raise ValueError('STOP_AFTER_CONTEXT_REVIEW')

    def stop_legacy(**kwargs):
        raise ValueError('UNCHANGED_NON_EVENT_BRANCH')

    monkeypatch.setattr(consumer, 'build_source_authority', stop_action)
    monkeypatch.setattr(consumer, 'bind_current_stock', stop_legacy)
    if tamper:
        resolve = discovery.resolve_persisted_context_v1

        def forged(*args, **kwargs):
            view = resolve(*args, **kwargs)
            view['context_records'][0]['allowed_uses'].append('HOLDER_STANCE')
            _rehash(view)
            return view

        monkeypatch.setattr(discovery, 'resolve_persisted_context_v1', forged)
    events = None if non_event else {ticker: {
        **replay['event_inputs'], 'policy_provider': replay['persisted_event_receipt']['provider']}}
    matrix = consumer.replay(corpus, output, persisted_events=events)
    path = output / 'context-authority' / (ticker + '.json')
    return matrix, path, calls


def test_actual_consumer_persists_verified_review_before_action_boundary(sample, tmp_path, monkeypatch):
    import json
    expected = _resolve(sample)
    matrix, path, calls = _consumer_run(sample, tmp_path, monkeypatch)
    assert json.loads(path.read_bytes()) == expected
    assert len(calls) == 1
    assert matrix[0]['mandatory_missing'] == ['STOP_AFTER_CONTEXT_REVIEW']


def test_actual_consumer_rejects_rehashed_producer_result(sample, tmp_path, monkeypatch):
    matrix, path, calls = _consumer_run(sample, tmp_path, monkeypatch, tamper=True)
    assert not path.exists() and calls == []
    assert matrix[0]['status'] == 'BLOCKED'
    assert matrix[0]['mandatory_missing'] == ['context_discovery_trusted_input_mismatch']


def test_non_event_consumer_branch_does_not_enter_discovery(sample, tmp_path, monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError('non-event route must not invoke discovery')

    monkeypatch.setattr(discovery, 'build_context_discovery_v1', forbidden)
    matrix, path, calls = _consumer_run(sample, tmp_path, monkeypatch, non_event=True)
    assert not path.exists() and calls == []
    assert matrix[0]['mandatory_missing'] == ['UNCHANGED_NON_EVENT_BRANCH']


def test_empty_selected_event_replay_preserves_empty_context_and_consumer(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(recorded_fixture, 'wire', lambda path, stock: wire(path, stock,
        title='Other company awarded a supply contract', summary='Other corporation signed a contract'))
    sample = _sample(recorded_fixture.event.__wrapped__(tmp_path))
    frozen, replay, result, _ = sample
    assert replay['persisted_event_receipt']['selected'] == []
    before = _legacy_outputs(frozen)
    unresolved = discovery.build_context_discovery_v1(**frozen)
    resolved = _resolve(sample)
    assert unresolved['context_refs'] == unresolved['context_records'] == []
    assert resolved['context_refs'] == resolved['context_records'] == []
    assert discovery.validate_context_discovery_v1(resolved, **replay, **frozen) == resolved
    assert _legacy_outputs(frozen) == before
    matrix, path, calls = _consumer_run(sample, tmp_path, monkeypatch)
    assert json.loads(path.read_bytes()) == resolved
    if result['status'] == 'PASS':
        assert len(calls) == 1
        assert matrix[0]['mandatory_missing'] == ['STOP_AFTER_CONTEXT_REVIEW']
    else:
        assert calls == []
        assert matrix[0]['status'] == result['status']
        assert matrix[0]['mandatory_missing'] == result['mandatory_missing']
