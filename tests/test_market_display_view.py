from copy import deepcopy
from datetime import datetime

import pytest

from app.services.market_display_view import build_display_view, verify_display_view, market_views
from app.services.market_display_plan import build_display_plan, render_display_plan, US_MACRO
from app.services.macro_source_time import publication_context
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as directional
from scripts.r9_rev11_market_qualification import check_projection
from tests.test_r2b_r5_market_adapter import fixture, project


def fresh(market='us', *, missing_publications=(), missing_indices=()):
    packet, seed, graph = fixture(market)
    source = graph['markets'][market]
    value = source['component']['value']
    if market == 'us':
        base = dict(value['observations'][0], previous_value=100., value=101., change_value=1., change_pct=1.)
        value['observations'] = [dict(base, series_code=s) for s in ('SPY','QQQ','IWM')]
    else:
        value['indices'].append(dict(value['indices'][0], symbol='KOSDAQ', label='KOSDAQ', source_ref='source:second'))
        value['indices'] = [r for r in value['indices'] if r['symbol'] not in missing_indices]
    source['component']['value_sha256'] = digest(value)
    seed['attempt_hashes'][market] = digest(source)
    now = datetime.fromisoformat(seed['started_at'])
    providers = {}
    for provider, series in (('fred',US_MACRO), ('ecos',('USDKRW',))):
        observations = []
        for name in series:
            if name in missing_publications:
                continue
            temporal = publication_context(provider=provider, series=name, period='2026-09-25',
                query_as_of=now, retrieved_at=now, response_bytes=b'fictional', cadence='daily',
                latest_verified=True, daily_required=True)
            observations.append(dict(series_code=name, value=4., change_pct=1., quality_status='fresh',
                observed_at='2026-09-25T00:00:00Z', raw_payload=dict(publication_context=temporal)))
        doc = dict(observations=observations)
        providers[provider] = dict(value=doc, value_sha256=digest(doc), source_hashes={'synthetic':temporal['response_sha256']})
    pub = dict(contract='fresh-publication-replay-v1', run_id=seed['parent_run_id'],
               providers=providers, value_sha256=digest(providers))
    graph.update(publication_context=pub, run_seed_sha256=digest(seed))
    packet.update(publication_context=pub, market_sources=deepcopy(source), run_seed_sha256=digest(seed),
                  authority_graph_sha256=digest(graph))
    return project((packet,seed,graph))


@pytest.mark.parametrize('market',['us','kr'])
def test_separate_views_exact_original_model_contract_and_display(market):
    result = fresh(market)
    source, ctx = result['packet']['market_context'], result['context']
    before = directional.market_context(result['packet'])
    assert before == ctx and directional.market_schema(ctx) == result['schema']
    receipt = result['views']['receipt']
    assert receipt['directional_context_sha256'] == digest(ctx)
    assert not set(receipt['display_only_refs']) & set(ctx['facts'])
    assert not any(f.get('fields',{}).get('publication_context') for f in ctx['facts'].values())
    qualified = check_projection(result,market)
    assert qualified['status'] == 'PASS' and not qualified['mandatory_missing']
    display = build_display_plan(source,market=market,assessment_date=result['packet']['assessment_date'],
        eligible_refs=ctx['request_eligible_refs'],display_view=result['views']['display'])
    rendered = render_display_plan(display,source,'시장 판단: 방향 혼재')
    assert '2026-09-25 관측' in rendered
    assert 'KOSDAQ150' not in rendered
    if market == 'kr':
        assert 'KOSPI: 100.00 · +1.00%' in rendered and 'KOSDAQ: 100.00 · +1.00%' in rendered
        assert len(display.display_view.identity_bindings) == 4
    else:
        assert all(i.status == 'AVAILABLE' for i in display.items if i.block_id in {'macro','indices'})
        assert display.items[-1].status == 'UNAVAILABLE'
    assert not any('change' in f or 'return' in f for d in display.display_view.decisions
                   if d.basis == 'LATEST_PUBLISHED_LEVEL_ONLY' for f in d.allowed_fields)


@pytest.mark.parametrize('mutation',['not_latest','display_false','bad_freshness','future','query','response',
    'source_generation','hard_quality','source_value','source_hash','observation_date'])
def test_publication_negative_controls(mutation):
    result = fresh()
    source = result['packet']['market_context']
    origin = deepcopy(result['views']['display']['origin'])
    fact = next(f for f in source['fact_catalog'] if f['fields'].get('series_code') == 'DGS10')
    ref = fact['fact_id']
    pub = fact['fields']['publication_context']
    if mutation in {'not_latest','display_false','bad_freshness','future','query','response','observation_date'}:
        key, value = dict(not_latest=('latest_available_at_query_time',False), display_false=('display_eligible',False),
            bad_freshness=('freshness_state','PUBLICATION_CURRENTNESS_UNPROVEN'),
            future=('published_at','2099-01-01T00:00:00Z'), query=('query_as_of','2026-09-26T08:00:00Z'),
            response=('response_sha256','0'*64), observation_date=('observation_date','2026-09-26'))[mutation]
        pub[key] = value
        origin['publication_origins'][ref]['publication_context_sha256'] = digest(pub)
        origin['publication_origins'][ref]['fact_sha256'] = digest(fact)
        origin['source_sha256'] = digest(source)
    elif mutation == 'source_generation':
        origin['publication_origins'][ref]['generation_id'] = 'other-generation'
    elif mutation == 'hard_quality':
        fact['fields']['source_unavailable'] = True
        source['numeric_registry'] = build_numeric_registry(source['fact_catalog'])
        origin['publication_origins'][ref]['fact_sha256'] = digest(fact)
        origin['source_sha256'] = digest(source)
    elif mutation == 'source_value':
        fact['fields']['level_pct'] = 99.
    else:
        origin['source_sha256'] = '0'*64
    if mutation in {'source_value','source_hash'}:
        with pytest.raises(ValueError,match='source_hash'):
            build_display_view(source,market='us',assessment_date=result['packet']['assessment_date'],origin=origin)
    else:
        view = build_display_view(source,market='us',assessment_date=result['packet']['assessment_date'],origin=origin)
        assert ref not in view.eligible_refs


@pytest.mark.parametrize('mutation',['value','unit','semantic','session','canonical','unbound','duplicate',
                                     'other_alias','generation','hash','registry'])
def test_exact_alias_negative_controls(mutation):
    result = fresh('kr')
    source = result['packet']['market_context']
    view = deepcopy(result['views']['display'])
    origin = view['origin']
    row = next(r for r in origin['alias_audit']['rows'] if r['alias_ref'] in origin['alias_payloads'])
    alias = row['alias_ref']
    if mutation in {'value','unit','semantic','canonical'}:
        key, value = dict(value=('value',999.),unit=('unit','USD'),semantic=('semantic_type','fx_level'),
                         canonical=('canonical_ref','market:cross-section:index:KOSDAQ'))[mutation]
        # Select the other index regardless of stable receipt ordering.
        if mutation == 'canonical':
            value = 'market:cross-section:index:' + ('KOSPI' if row[key].endswith('KOSDAQ') else 'KOSDAQ')
        row[key] = value
    elif mutation == 'session':
        origin['alias_payloads'][alias]['as_of_date'] = '2026-09-22'
    elif mutation == 'unbound':
        origin['directional_refs'].remove(alias)
    elif mutation == 'duplicate':
        origin['alias_audit']['rows'].append(deepcopy(row))
    elif mutation == 'other_alias':
        origin['alias_payloads'][alias]['source_ref'] = 'not-this-occurrence'
    elif mutation in {'generation','hash'}:
        view['identity_bindings'][0]['generation_id' if mutation=='generation' else 'source_sha256'] = 'different'
    else:
        source['numeric_registry'][0]['semantic_type'] = 'wrong'
        origin['source_sha256'] = digest(source)
    with pytest.raises(ValueError):
        verify_display_view(view,source)


def test_display_permission_cannot_promote_direction_or_alias():
    result = fresh()
    ctx = deepcopy(result['context'])
    source = result['packet']['market_context']
    fact = next(f for f in source['fact_catalog'] if f['fields'].get('series_code')=='DGS10')
    ctx['facts']['alias:macro'] = fact
    from app.services.market_display_view import MarketDisplayOrigin
    with pytest.raises(ValueError,match='directional_publication_alias_leak'):
        market_views(source,ctx,result['schema'],market='us',assessment_date=result['packet']['assessment_date'],
                     origin=MarketDisplayOrigin.model_validate(result['views']['display']['origin']))


def test_view_roundtrip_cannot_grant_additional_numeric_field():
    result = fresh()
    view = deepcopy(result['views']['display'])
    row = next(d for d in view['decisions'] if d['fact_ref']=='market:nominal_yield:DGS10')
    row['allowed_fields'].append('fields.change_bp')
    with pytest.raises(ValueError,match='view_binding_mismatch'):
        verify_display_view(view,result['packet']['market_context'])
