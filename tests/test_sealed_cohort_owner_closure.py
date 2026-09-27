import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timezone
import json

import httpx
import pytest

from app.services.kiwoom_consumed_page_contract import CONTRACT, dependency_ledger, read_dependencies
from app.services.unified_aggregate_owners import kiwoom_aggregate_owner
from app.services.unified_aggregate_receipt import AggregateReceipt, verify_aggregate
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_composition import A, SourceRole
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_run_artifacts import sha256_bytes
from app.services.versioned_business_stock_owner import replay_version, bind_current_stock, version_document
from scripts.m12dr_financial_source_authority import comparative_facts, source_quality
from test_financial_observation_quality import snapshots
from test_kiwoom_rest_market_context import OBSERVED_AT, SESSION_DATE, _handler
from test_unified_owner_interfaces import kr_service
from test_unified_real_aggregate_owners import aggregate, clock
from test_unified_stock_owner import source, freeze_hashes  # noqa: F401


@pytest.fixture
def continuing_market(tmp_path, monkeypatch):
    clock(monkeypatch, OBSERVED_AT)
    transport = _handler([])
    def handle(request):
        response = transport.handle_request(request)
        if request.headers.get('api-id') in {'ka20001', 'ka20009'}:
            response.headers.update({'cont-yn': 'Y', 'next-key': 'synthetic-tail'})
        return response
    service, observer = kr_service(tmp_path / 'capture', transport=httpx.MockTransport(handle))
    collection = asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    old = json.loads((observer.root / 'normalization.json').read_bytes())
    assert old['mandatory_complete'] is False
    role = SourceRole(key='kr_local_indices_sectors_breadth', owner='kiwoom_pages', market='kr',
        symbol='*', provider='kiwoom_rest', basis='query_time', session=str(SESSION_DATE),
        acquisition_class=A, mandatory=True)
    normalized = {k: collection.cross_section.model_dump(mode='json')[k]
                  for k in ('indices', 'sectors', 'breadth', 'breadth_by_scope')}
    receipt = aggregate(observer.root, role, normalized, OBSERVED_AT)
    raw = receipt.model_dump(mode='json', exclude={'aggregate_sha256'})
    raw['validator_contract'] = CONTRACT
    receipt = AggregateReceipt.model_validate({**raw, 'aggregate_sha256': digest(raw)})
    policy = UnifiedSourcePolicy(frozenset({'kiwoom_rest'}))
    owner = kiwoom_aggregate_owner(role=role, observed_at=OBSERVED_AT, max_pages=5,
        max_requests_per_page=1, policy=policy, consumer_complete=True)
    return observer.root, receipt, policy, owner, normalized


def test_consumer_complete_opt_in_does_not_change_default(continuing_market):
    root, receipt, policy, owner, value = continuing_market
    with pytest.raises(ValueError, match='page_set_incomplete'):
        verify_aggregate(root, receipt, policy=policy, cutoff=OBSERVED_AT)
    graph = verify_aggregate(root, receipt, policy=policy, cutoff=OBSERVED_AT,
                             completion_observed_at=OBSERVED_AT)
    assert owner.project_aggregate_and_validate(graph, OBSERVED_AT).value == value
    ledger = dependency_ledger(graph, value, observed_at=OBSERVED_AT)
    assert len({r['output_field'] for r in ledger}) == len(ledger)
    assert all(r['direct_sources'] or r['constant_or_denial_owner'] for r in ledger)


def test_adversarial_unconsumed_tail_does_not_change_semantic_output(continuing_market):
    root, receipt, policy, owner, value = continuing_market
    graph = verify_aggregate(root, receipt, policy=policy, cutoff=OBSERVED_AT,
                             completion_observed_at=OBSERVED_AT)
    bodies = []
    for raw, child in zip(graph.child_bodies, graph.child_receipts, strict=True):
        payload = json.loads(raw)
        api = child['request']['api_id']
        if api == 'ka20001':
            payload['inds_cur_prc_tm'] = [{'cur_prc': '-999999999', 'rising': '-123'}]
        if api == 'ka20009':
            payload['inds_cur_prc_daly_rept'].append({'dt_n': '19000101', 'cur_prc_n': '-99999999', 'flu_rt_n': '99'})
        bodies.append(encoded(payload))
    changed = replace(graph, child_bodies=tuple(bodies))
    assert owner.project_aggregate_and_validate(changed, OBSERVED_AT).value == value


@pytest.mark.parametrize('api', ['ka20001', 'ka20009'])
def test_additional_unrelated_pages_preserve_declared_dependency(api):
    first = ({k: '2' for k in ('cur_prc', 'flu_rt', 'rising', 'fall', 'stdns', 'upl', 'lst')}
             if api == 'ka20001' else {'inds_cur_prc_daly_rept': [{'dt_n': '20260923', 'cur_prc_n': '2', 'flu_rt_n': '2'}]})
    tail = {'inds_cur_prc_daly_rept': [{'dt_n': '19000101', 'cur_prc_n': '-999'}], 'cur_prc': '-999'}
    a = read_dependencies(api, [first], session=date(2026, 9, 23), continuation=[True])
    b = read_dependencies(api, [first, tail], session=date(2026, 9, 23), continuation=[True, False])
    assert a == b and a['mode'] == 'CONSUMER_COMPLETE'


@pytest.mark.parametrize('case', ['missing', 'wrong_day', 'duplicate', 'moved_to_page2', 'cross_page_duplicate'])
def test_target_session_dependency_negatives(case):
    target = {'dt_n': '20260923', 'cur_prc_n': '2', 'flu_rt_n': '2'}
    rows, tail = [target], []
    if case == 'missing':
        rows = []
    elif case == 'wrong_day':
        rows = [{**target, 'dt_n': '20260922'}]
    elif case == 'duplicate':
        rows.append({**target, 'cur_prc_n': '3'})
    elif case == 'moved_to_page2':
        rows, tail = [], [target]
    else:
        tail = [{**target, 'cur_prc_n': '3'}]
    with pytest.raises(ValueError, match='target_session'):
        read_dependencies('ka20009', [{'inds_cur_prc_daly_rept': rows}, {'inds_cur_prc_daly_rept': tail}],
                          session=date(2026, 9, 23), continuation=[True, False])


def test_top_level_dependency_moved_to_tail_is_not_complete():
    with pytest.raises(ValueError):
        read_dependencies('ka20001', [{}, {'cur_prc': '2'}], session=date(2026, 9, 23), continuation=[True, False])


def test_native_consumer_never_reads_offered_adversarial_continuation_pages(continuing_market, tmp_path):
    from collections import Counter
    _, _, _, _, expected = continuing_market
    calls = Counter()
    fixture_transport = _handler([])
    def handle(request):
        api = request.headers.get('api-id')
        key = (api, request.content)
        calls[key] += 1
        if api in {'ka20001', 'ka20009'} and calls[key] > 1:
            return httpx.Response(200, json={'cur_prc': '-999999', 'flu_rt': '99',
                'inds_cur_prc_daly_rept': [{'dt_n': '19000101', 'cur_prc_n': '-999999'}]})
        response = fixture_transport.handle_request(request)
        if api in {'ka20001', 'ka20009'}:
            response.headers.update({'cont-yn': 'Y', 'next-key': 'adversarial-tail'})
        return response
    service, _ = kr_service(tmp_path / 'with-tail', transport=httpx.MockTransport(handle))
    output = asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    value = output.cross_section.model_dump(mode='json')
    assert digest({k: value[k] for k in expected}) == digest(expected)
    assert all(count == 1 for (api, _), count in calls.items() if api in {'ka20001', 'ka20009'})


@pytest.mark.parametrize('api', ['ka20003', 'ka10051', 'ka10066'])
def test_transport_exhaustion_preserved(api):
    with pytest.raises(ValueError, match='transport_exhaustion'):
        read_dependencies(api, [{}], session=date(2026, 9, 23), continuation=[True])
    assert read_dependencies(api, [{}, {}], session=date(2026, 9, 23), continuation=[True, False])['mode'] == 'TRANSPORT_EXHAUSTED'


def version_inputs():
    formal, _ = snapshots()
    inputs = {'ticker': 'FICTIVE', 'cutoff': '2026-09-21', 'formal': formal.model_dump(mode='json'), 'preliminary': None}
    bundle = {'source_inputs': inputs, 'source_inputs_sha256': digest(inputs), 'source_generation_id': 'original'}
    bundle['quality'] = source_quality(bundle)
    facts = comparative_facts(bundle['quality'], ticker='FICTIVE', issuer_id='DART:12345678')
    doc = {'contract': 'frozen-accepted-reported-comparison-input-v1', 'ticker': 'FICTIVE',
        'frozen_at': '2026-09-27T00:00:00+00:00', 'original_cutoff': '2026-09-21T00:00:00+00:00',
        'source_artifact_sha256': 'a'*64, 'parent_zip_sha256': 'b'*64, 'quality_bundles': [bundle],
        'facts': facts, 'financial_source_graph': {}, 'issuer_business_bridge': None,
        'scope': 'VERSIONED_BUSINESS_ONLY_CURRENT_ELIGIBILITY_REPLAY_REQUIRED',
        'old_class_a_values_consumed': False, 'prior_event_reused_as_class_b': False}
    seed = {'roles': {'security_identity': {'records': [{'table': 'securitymaster', 'record': {
        'ticker': 'FICTIVE', 'corp_code': '12345678', 'canonical_security_id': 'test-security'}}]}}}
    return doc, dict(ticker='FICTIVE', versions={'FICTIVE': encoded(doc)},
        version_hashes={'class-c/business-versioned-FICTIVE.json': sha256_bytes(encoded(doc))},
        local_seeds=[seed], cutoff=datetime(2026, 9, 27, tzinfo=timezone.utc),
        policy=UnifiedSourcePolicy(frozenset({'opendart'})))


def test_version_current_eligibility_preserves_original_period_and_denied_siblings():
    doc, inputs = version_inputs()
    result = replay_version(**inputs)
    assert result['facts'] == doc['facts']
    assert [f['fields']['metric'] for f in result['facts']] == ['revenue']
    assert result['old_class_a_values_consumed'] is False
    assert result == replay_version(**inputs)


@pytest.mark.parametrize('case', ['hash', 'ticker', 'issuer', 'period', 'denied_sibling', 'old_price',
    'class_b_relabel', 'future_version', 'prohibited_provider'])
def test_version_negatives(case):
    doc, inputs = version_inputs()
    if case == 'hash':
        inputs['version_hashes']['class-c/business-versioned-FICTIVE.json'] = '0'*64
    elif case == 'ticker':
        doc['ticker'] = 'OTHER'
    elif case == 'issuer':
        inputs['local_seeds'][0]['roles']['security_identity']['records'][0]['record']['corp_code'] = '11111111'
    elif case == 'period':
        doc['facts'][0]['fields']['period_start'] = '2026-01-01'
    elif case == 'denied_sibling':
        doc['facts'].append({**deepcopy(doc['facts'][0]), 'fact_id': 'forged-operating'})
        doc['facts'][-1]['fields']['metric'] = 'operating_income'
    elif case == 'old_price':
        doc['price_and_positioning'] = {'current_price': 999}
    elif case == 'class_b_relabel':
        doc['prior_event_reused_as_class_b'] = True
    elif case == 'future_version':
        doc['frozen_at'] = '2027-01-01T00:00:00+00:00'
    else:
        doc['quality_bundles'][0]['source_inputs']['formal']['provider'] = 'alpha_vantage'
    inputs['versions']['FICTIVE'] = encoded(doc)
    if case != 'hash':
        inputs['version_hashes']['class-c/business-versioned-FICTIVE.json'] = sha256_bytes(encoded(doc))
    with pytest.raises(ValueError):
        replay_version(**inputs)


def test_existing_base_owner_invariance_and_missing_price_failure(source):  # noqa: F811
    from app.services.unified_stock_owner import assemble_stock
    at = source['plan'].frozen_at.isoformat()
    doc, _ = version_inputs()
    doc.update(ticker='CORZ', frozen_at=at, original_cutoff=at, facts=[], quality_bundles=[])
    args = dict(stock_inputs=source, versions={'CORZ': encoded(doc)},
        version_hashes={'class-c/business-versioned-CORZ.json': sha256_bytes(encoded(doc))},
        local_seeds=[source['local_seed']])
    bound = bind_current_stock(**args)
    assert bound['result'] == assemble_stock(**source)
    assert bound['baseline_invariant']
    source['receipts'].pop('adjusted_daily')
    freeze_hashes(source)
    with pytest.raises(ValueError, match='four_subject_roles'):
        bind_current_stock(**args)


def test_version_document_rejects_unspecified_event_restore():
    doc, args = version_inputs()
    doc['persisted_event'] = {'event_type': 'reported'}
    with pytest.raises(ValueError, match='shape_or_subject'):
        version_document(encoded(doc), sha256_bytes(encoded(doc)), ticker='FICTIVE', cutoff=args['cutoff'])


def test_current_price_attempt_cannot_be_replaced_by_old_generation(source):  # noqa: F811
    at = source['plan'].frozen_at.isoformat()
    doc, _ = version_inputs()
    doc.update(ticker='CORZ', frozen_at=at, original_cutoff=at, facts=[], quality_bundles=[])
    source['receipts']['adjusted_daily']['acquisition_id'] = 'old-generation'
    freeze_hashes(source)
    with pytest.raises(ValueError):
        bind_current_stock(stock_inputs=source, versions={'CORZ': encoded(doc)},
            version_hashes={'class-c/business-versioned-CORZ.json': sha256_bytes(encoded(doc))},
            local_seeds=[source['local_seed']])


def test_partial_cohort_cannot_emit_whole_authority():
    from scripts.sealed_business_replay import cohort_composition_gate
    from app.services.unified_stock_acquisition import UNIVERSE
    matrix = [{'market': m, 'ticker': t, 'status': 'PASS', 'packet_sha256': 'a'*64,
               'authority_sha256': 'b'*64, 'authority_errors': []} for m, ts in UNIVERSE.items() for t in ts]
    assert cohort_composition_gate(matrix)['eligible']
    matrix[0]['authority_errors'] = ['missing_source']
    assert not cohort_composition_gate(matrix)['eligible']
    matrix[0].update(authority_errors=[], status='BLOCKED', packet_sha256=None)
    assert not cohort_composition_gate(matrix)['eligible']
    with pytest.raises(ValueError, match='exact_cohort'):
        cohort_composition_gate(matrix[:-1])


def test_rebound_packet_requires_independent_business_replay(source, monkeypatch):  # noqa: F811
    import app.services.unified_stock_owner as owner
    doc, _ = version_inputs()
    ticker = source['ticker']
    bundle = doc['quality_bundles'][0]
    bundle['source_inputs']['ticker'] = ticker
    bundle['source_inputs']['formal']['ticker'] = ticker
    bundle['source_inputs_sha256'] = digest(bundle['source_inputs'])
    bundle['quality'] = source_quality(bundle)
    facts = comparative_facts(bundle['quality'], ticker=ticker, issuer_id='DART:12345678')
    at = source['plan'].frozen_at.isoformat()
    doc.update(ticker=ticker, frozen_at=at, facts=facts,
               financial_source_graph={f['fact_id']: {'original_source': 'fixture'} for f in facts})
    for role in source['local_seed']['roles'].values():
        for record in role['records']:
            if record['table'] == 'securitymaster':
                record['record']['corp_code'] = '12345678'
        role['version'] = digest(role['records'])
    freeze_hashes(source)
    args = dict(ticker=ticker, versions={ticker: encoded(doc)},
        version_hashes={'class-c/business-versioned-' + ticker + '.json': sha256_bytes(encoded(doc))},
        local_seeds=[source['local_seed']], cutoff=source['plan'].frozen_at, policy=source['policy'])
    def denied(*args, **kwargs):
        raise ValueError('financial_selected_tuple_mismatch')
    monkeypatch.setattr(owner, '_financial', denied)
    bound = bind_current_stock(stock_inputs=source, versions=args['versions'],
        version_hashes=args['version_hashes'], local_seeds=args['local_seeds'])
    result = bound['result']
    assert owner.validate_assembled(result, expected_result_sha256=digest(result), versioned_business_inputs=args)
    with pytest.raises(ValueError, match='source_replay_required'):
        owner.validate_assembled(result, expected_result_sha256=digest(result))
    result['observed_business_cardinality'] += 1
    with pytest.raises(ValueError, match='union_replay'):
        owner.validate_assembled(result, expected_result_sha256=digest(result), versioned_business_inputs=args)


def bridge_versions():
    from test_issuer_business_bridge import fixture
    from app.services.issuer_business_bridge import identity_bridge, bind_comparison
    args = fixture()
    bridge = identity_bridge(**args)
    doc, inputs = version_inputs()
    bundle = doc['quality_bundles'][0]
    bundle['source_inputs']['ticker'] = '123456'
    bundle['source_inputs']['formal']['ticker'] = '123456'
    bundle['source_inputs_sha256'] = digest(bundle['source_inputs'])
    bundle['quality'] = source_quality(bundle)
    doc.update(ticker='123456', facts=comparative_facts(bundle['quality'], ticker='123456', issuer_id=bridge['issuer_id']))
    target = deepcopy(doc)
    target.update(ticker='FICADR', quality_bundles=[], issuer_business_bridge=bridge)
    target['facts'] = []
    for fact in doc['facts']:
        projected = deepcopy(fact)
        projected.update(fact_id=fact['fact_id'].replace(':123456:', ':FICADR:'), issuer_projection=bridge)
        target['facts'].append(bind_comparison(projected, fact, bridge, source_result_sha256='e'*64))
    inputs.update(ticker='FICADR', versions={t: encoded(d) for t, d in [('123456', doc), ('FICADR', target)]},
        local_seeds=[{'roles': {'identity': {'records': [
            {'table': 'securitymaster', 'record': args[k]} for k in ('target', 'source')]}}}])
    inputs['version_hashes'] = {'class-c/business-versioned-' + t + '.json': sha256_bytes(raw)
                               for t, raw in inputs['versions'].items()}
    return target, inputs


def test_accepted_issuer_bridge_rechecks_underlying_without_security_transfer():
    target, args = bridge_versions()
    value = replay_version(**args)
    assert value['facts'] == target['facts']
    assert value['eligibility'][0]['price_technical_transfers'] == 0
    assert not value['eligibility'][0]['security_per_share_eligible']


@pytest.mark.parametrize('field', ['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE', 'SECURITY_VALUATION_BRIDGE_ELIGIBLE',
                                  'security_valuation_transfer'])
def test_issuer_bridge_scope_escalation_denied_even_if_rehashed(field):
    target, args = bridge_versions()
    bridge = target['issuer_business_bridge']
    bridge[field] = True
    bridge['receipt_sha256'] = digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'})
    args['versions']['FICADR'] = encoded(target)
    args['version_hashes']['class-c/business-versioned-FICADR.json'] = sha256_bytes(encoded(target))
    with pytest.raises(ValueError, match='scope_mismatch'):
        replay_version(**args)


def test_existing_authority_owner_replays_version_without_relabelling_generation():
    from app.services.cross_market_decision_engine_service import _compact
    from scripts.m12dr_financial_source_authority import build_source_authority
    from scripts.m12dk_current_source_authority import freeze_current_source_binding
    doc, args = version_inputs()
    packet = {'packet_id': 'new-run:kr', 'market': 'kr', 'assessment_date': '2026-09-27',
        'generated_at': args['cutoff'].isoformat(), 'stocks': [{'ticker': 'FICTIVE', 'fact_catalog': doc['facts']}]}
    rows = [{'ref_id': 'canonical:' + f['fact_id'], 'source_ref': 'stock.fact_catalog.' + f['fact_id'],
             'category': 'earnings', 'label': 'comparison', 'statement': _compact(f['fields']),
             'as_of': f['as_of_date']} for f in doc['facts']]
    ep = {'ticker': 'FICTIVE', 'evidence': rows}
    refs = [r['ref_id'] for r in rows]
    cat = dict(ticker='FICTIVE', all_evidence_refs=refs, core_evidence_refs=refs, timing_evidence_refs=[],
        valuation_evidence_refs=[], positive_quality_refs=[], material_disclosure_failure_refs=[],
        claim_refs=[], atomic_claims=[])
    result = build_source_authority(quality_bundles={}, issuer_bindings={}, versioned_business_inputs=args,
        ticker='FICTIVE', source_generation_id='new-run', source_packet=packet, evidence_packet=ep,
        catalog=cat, source_metadata=rows, frozen_binding=freeze_current_source_binding(
            source_generation_id='new-run', source_packet=packet, evidence_packet=ep))
    assert not any(r['errors'] for r in result['family_receipts'])
    record = result['authority']['authority_records'][0]
    assert record['source_family'] == 'OBSERVED_COMPARATIVE_FINANCIAL_FACT'
    assert 'OVERALL_DIRECTION' in record['allowed_uses']
    assert 'VALUATION' not in record['allowed_uses']
    assert args['versions']['FICTIVE'] == encoded(doc)
