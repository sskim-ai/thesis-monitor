from copy import deepcopy

import pytest

from app.services.kr_market_numeric_claim_service import local_kr_claims
from app.services.market_numeric_claim_service import numeric_catalog, validate_catalog
from app.services.numeric_semantic_registry import build_numeric_registry


def fixture():
    day = '2026-09-22'
    source = dict(session=dict(market='kr', assessment_date='2026-09-23', latest_completed_regular_session_date=day),
        fact_catalog=[], adapter_context=dict(session_date=day, indices=[], sectors=[], size_context=[], market_flows=[],
            breadth=dict(availability='AVAILABLE', source_refs=['breadth']), breadth_by_scope=[]))
    refs = {'breadth'}

    def add(kind, ref, fields):
        source['fact_catalog'].append(dict(fact_id=ref, fact_type=kind, source='KIWOOM_REST', as_of_date=day, fields=fields))

    for scope in ('KOSPI', 'KOSDAQ'):
        ref = scope + ':index'
        refs.add(ref)
        add('market_cross_section_index', 'canonical:' + ref, dict(symbol=scope, label=scope, close=1000, return_pct=1))
        source['adapter_context']['indices'].append(dict(symbol=scope, name=scope, close=1000, return_pct=1,
            source_ref=ref, as_of_date=day))
        add('market_breadth_counts', scope + ':counts', dict(market_scope=scope, advance_count=4, decline_count=3,
            unchanged_count=1, eligible_count=8))
        source['adapter_context']['breadth_by_scope'].append(dict(scope=scope, breadth=dict(availability='AVAILABLE',
            advancers=4, decliners=3, unchanged=1, eligible_count=8)))
        for name, value, size in [('전기전자', 2, False), ('대형주', 1, True)]:
            if size and scope != 'KOSPI':
                continue
            ref = scope + ':' + name
            refs.add(ref)
            add('market_cross_section_sector', 'canonical:' + ref, dict(market_scope=scope, sector=name,
                taxonomy='kiwoom-sector-index-v1', metric_role='actual_sector_breadth', source_ref=ref, return_pct=value))
            source['adapter_context']['size_context' if size else 'sectors'].append(dict(name=name, market_scope=scope,
                as_of_date=day, source_ref=ref, return_pct=value, state='CURRENT_DIRECTIONAL',
                basis='official_size_index' if size else 'actual_sector_breadth'))
        ref = scope + ':foreign'
        refs.add(ref)
        add('market_flow', 'canonical:' + ref, dict(source_ref=ref, market_scope=scope, actor='foreign',
            net_buy_amount=-12340000000, currency='KRW'))
        source['adapter_context']['market_flows'].append(dict(source_ref=ref, as_of_date=day, scope=scope,
            participant='foreign', net_flow=-12340000000, unit='KRW'))
    source['numeric_registry'] = build_numeric_registry(source['fact_catalog'])
    return source, refs


def test_actual_registry_labels_and_canonical_adapter_parity_render_all_kr_sections():
    source, refs = fixture()
    original = deepcopy(source)
    catalog = numeric_catalog(source, market='kr', assessment_date='2026-09-23', eligible_refs=refs)
    local = [c for c in catalog['claims'] if c['claim_type'] == 'KR_LOCAL_MARKET']
    assert len(local) == 7
    text = '\n'.join(c['rendered_text'] for c in catalog['claims'])
    assert 'KOSPI: 1,000.00 / +1.00%' in text
    assert 'KOSDAQ 등락 종목: 상승 4개 / 하락 3개 / 보합 1개 / 전체 8개' in text
    assert 'KOSPI 대형주: +1.00%' in text
    assert 'KOSDAQ 외국인 순매수: -123.40억원' in text
    ranks = [c for c in catalog['claims'] if c['claim_type'] == 'SECTOR_RANKING']
    assert len(ranks) == 4 and all(c['metadata']['missing_count'] == 2 for c in ranks)
    assert all('대형주' not in c['rendered_text'] for c in ranks)
    assert validate_catalog(catalog, source)['status'] == 'PASS' and source == original


@pytest.mark.parametrize('mutation', ['registry_denial', 'value_mismatch', 'unit_mismatch', 'ref_denial',
    'future_date', 'ambiguous_row', 'provider_mismatch', 'source_session_mismatch'])
def test_local_indices_require_both_source_and_registry_permission(mutation):
    source, refs = fixture()
    fact = source['fact_catalog'][0]
    row = source['adapter_context']['indices'][0]
    entry = next(r for r in source['numeric_registry'] if r['fact_id'] == fact['fact_id'] and r['field_path'] == 'fields.close')
    if mutation == 'registry_denial':
        entry['prose_allowed'] = False
    elif mutation == 'value_mismatch':
        row['close'] = 999
    elif mutation == 'unit_mismatch':
        entry['unit'] = 'USD'
    elif mutation == 'ref_denial':
        refs.remove(row['source_ref'])
    elif mutation == 'future_date':
        fact['as_of_date'] = '2026-09-23'
    elif mutation == 'ambiguous_row':
        source['adapter_context']['indices'].append(deepcopy(row))
    elif mutation == 'provider_mismatch':
        fact['source'] = 'unverified'
    else:
        source['adapter_context']['session_date'] = '2026-09-21'
    assert not any(fact['fact_id'] in c['input_fact_refs'] for c in local_kr_claims(source, '2026-09-22', refs))
