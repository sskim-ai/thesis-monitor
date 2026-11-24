"""C47 excluded-night projection and real renderer boundaries; synthetic inputs only."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.services import production_message_renderer as renderer
from app.services.canonical_market_projection import _project_market_context
from app.services.selected_source_plan import US_NIGHT_EXCLUDED, excluded_night_receipt
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from scripts import m12ds_r4_r4_market as consumer
from tests.night_owner_fixtures import night_fixture
from tests.test_c44_renderer_replay import synthetic_renderer_case
from tests.test_r2b_r5_market_adapter import fixture


def parts(*, excluded=False, night_case='empty', market='us'):
    packet, seed, graph = fixture(market)
    for name, document in packet['publication_context'].items():
        projection = dict(contract='unified-class-c-owner-projection-v1',
            role=name.removeprefix('class-c/').removesuffix('.json'), eligible=False,
            records=[], version=digest([]), values=[], denials=[])
        projection['projection_sha256'] = digest(projection)
        document['projection'] = projection
    seed.update(contract='selected-original-source-run-binding-v1', market=market)
    graph['contract'] = 'selected-original-source-authority-graph-v1'
    night = None if excluded else night_fixture(case=night_case)
    seed['run_acquisitions']['night'] = digest(None) if excluded else night['value_sha256']
    if excluded:
        seed['us_night_policy'] = US_NIGHT_EXCLUDED
        seed['night_publication_receipt_sha256'] = digest(None)
        packet['optional_denials']['night_futures'] = excluded_night_receipt(seed['parent_run_id'])
    graph['night'] = packet['night_and_publication_context'] = night
    reseal(packet, seed, graph)
    return packet, seed, graph


def reseal(packet, seed, graph):
    seed['optional_denial_set_sha256'] = digest(packet['optional_denials'])
    graph['run_seed_sha256'] = packet['run_seed_sha256'] = digest(seed)
    packet['authority_graph_sha256'] = digest(graph)


def project(value):
    packet, seed, graph = value
    return _project_market_context(packet, seed, graph, expected_authority_sha256=digest(graph),
        execution_metadata=dict(runtime_envelope_contract=seed['contract'],
            execution_purpose='MANUAL_SHADOW_UNSENT'))


def decision(context):
    return dict(market='US', regime='MIXED', confidence='LOW',
        breadth_state='확보된 지수 흐름을 관찰합니다.', leadership='업종 주도력은 확인이 필요합니다.',
        flows_or_participation='수급 근거는 제한적입니다.', rates_or_macro_context='확보된 시장 자료만 반영합니다.',
        supporting_refs=context['request_eligible_refs'][:1], contradicting_refs=[])


def test_excluded_source_reaches_model_and_actual_market_renderer_without_night_claims():
    data = parts(excluded=True)
    before = deepcopy(data)
    included = project(parts())
    projected = project(data)
    source, old_source = projected['packet']['market_context'], included['packet']['market_context']
    assert source['fact_catalog'] == old_source['fact_catalog']
    assert source['numeric_registry'] == old_source['numeric_registry']
    assert {k:v for k,v in source['coverage'].items() if k != 'night_futures'} == {
        k:v for k,v in old_source['coverage'].items() if k != 'night_futures'}
    assert not source['night_futures']
    assert source['coverage']['night_futures'] == dict(status='unavailable',
        state=US_NIGHT_EXCLUDED, optional=True, coverage_resolved=True)
    assert all(not f['fact_type'].startswith('night_futures') for f in source['fact_catalog'])
    assert all(not path.startswith('night_and_publication_context/')
        for refs in projected['receipt']['source_refs'].values() for path in refs)
    assert not any(c['claim_type'] == 'OFFICIAL_NIGHT' for c in projected['context']['numeric_catalog']['claims'])
    assert projected['context']['korean_night_futures'] == dict(state=US_NIGHT_EXCLUDED,
        collected=False, economic_use=False, directional_citation_eligible=False)
    output = decision(projected['context'])
    assert consumer.validate_market(output, projected['context'])['status'] == 'PASS'
    session = SimpleNamespace(market='us', gen='C47-synthetic', projected={'us':projected},
        markets={'us':output}, fresh_stocks={})
    message = renderer.market_message(session)
    assert message['message_id'] == 'MARKET_US'
    assert message['text'].count(consumer.NIGHT_EXCLUSION_NOTICE) == 1
    assert '한국 야간선물 · KOSPI200' not in message['text']
    assert '일: 자료 부족\n주: 자료 부족\n월: 자료 부족' not in message['text']
    assert 'SPY' in message['text'] and '시장 판단:' in message['text']
    assert data == before


@pytest.mark.parametrize('change', ['missing_policy', 'wrong_scope', 'wrong_denial', 'old_observation', 'wrong_none_hash'])
def test_no_exclusion_from_none_alone_or_reused_night_observation(change):
    packet, seed, graph = parts(excluded=True)
    if change == 'missing_policy':
        seed.pop('us_night_policy')
    elif change == 'wrong_scope':
        seed['contract'] = 'historical-proof'
    elif change == 'wrong_denial':
        packet['optional_denials']['night_futures']['run_id'] = 'another-run'
    elif change == 'old_observation':
        graph['night'] = packet['night_and_publication_context'] = night_fixture(case='available')
    else:
        seed['night_publication_receipt_sha256'] = digest('not-none')
    reseal(packet, seed, graph)
    with pytest.raises(ValueError, match='night_.*mismatch'):
        project((packet, seed, graph))


@pytest.mark.parametrize('text', ['야간선물 상승이 위험 선호를 뒷받침합니다.',
    '한국 야간 선물 하락은 경계 요인입니다.', 'KRX overnight futures support sentiment.'])
def test_excluded_night_qualitative_inference_is_not_accepted(text):
    projected = project(parts(excluded=True))
    output = decision(projected['context'])
    output['rates_or_macro_context'] = text
    receipt = consumer.validate_market(output, projected['context'])
    assert 'excluded_korean_night_futures_narrative:rates_or_macro_context' in receipt['errors']
    session = SimpleNamespace(market='us', gen='C47-synthetic', projected={'us':projected},
        markets={'us':output}, fresh_stocks={})
    with pytest.raises(ValueError, match='production_market_render_owner_gap'):
        renderer.market_message(session)


def test_night_exclusion_check_does_not_change_named_us_futures_or_legacy_probe_mode():
    projected = project(parts(excluded=True))
    output = decision(projected['context'])
    output['rates_or_macro_context'] = '미국 야간선물과 나스닥 야간선물, 한국 야간 외환은 별도 시장입니다.'
    assert consumer.excluded_night_narrative_errors(output, projected['context']) == []
    available = project(parts(night_case='available'))
    assert available['packet']['market_context']['night_futures']
    assert 'korean_night_futures' not in available['context']
    assert available['packet']['market_context']['night_futures_ownership']['state'] == 'AVAILABLE_FINAL'
    assert any(f['fact_type'] == 'night_futures'
        for f in available['packet']['market_context']['fact_catalog'])
    assert any(path.startswith('night_and_publication_context/')
        for refs in available['receipt']['source_refs'].values() for path in refs)
    included_message = renderer.market_message(SimpleNamespace(market='us', gen='C47-synthetic',
        projected={'us':available}, markets={'us':decision(available['context'])}, fresh_stocks={}))
    assert '한국 야간선물 · KOSPI200' in included_message['text']
    assert consumer.NIGHT_EXCLUSION_NOTICE not in included_message['text']
    assert consumer.excluded_night_narrative_errors(
        {'rates_or_macro_context':'야간선물 상승'}, available['context']) == []
    assert 'korean_night_futures' not in project(parts(market='kr'))['context']


def test_stock_real_renderer_keeps_b2_and_prices_and_rejects_excluded_night_prose(monkeypatch):
    session, ticker, accepted, row, request = synthetic_renderer_case('us', include_support=True)
    monkeypatch.setattr(renderer, 'stock_plan', lambda *args: accepted)
    normal = renderer.stock_message(session, ticker, row, execution_profile=SOL_HIGH_V1)
    session.projected = {'us':project(parts(excluded=True))}
    before = deepcopy((row, request, session.bctx, session.fresh_stocks))
    current = renderer.stock_message(session, ticker, row, execution_profile=SOL_HIGH_V1)
    assert current == normal
    assert consumer.NIGHT_EXCLUSION_NOTICE not in current['text']
    assert (row, request, session.bctx, session.fresh_stocks) == before
    render = renderer.render_detailed_v2
    def invented(*args, **kwargs):
        result = render(*args, **kwargs)
        return dict(result, text=result['text']+'\n한국 야간선물 상승으로 진입을 검토합니다.')
    monkeypatch.setattr(renderer, 'render_detailed_v2', invented)
    with pytest.raises(ValueError, match='production_stock_excluded_night_narrative'):
        renderer.stock_message(session, ticker, row, execution_profile=SOL_HIGH_V1)
