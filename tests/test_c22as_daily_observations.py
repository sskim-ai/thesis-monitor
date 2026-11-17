"""Display-only tests: no models, storage reads, or upstream requests."""
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest

from app.services.confirmed_sector_taxonomy import KR_NAMES
from app.services.kr_close_fx import KrCloseFxObservation, retained_ecos_fx_display, retained_fx_display
from app.services.market_display_plan import build_display_plan, render_display_plan
from app.services.unified_source_policy import UnifiedSourcePolicy

DAY = '2026-11-09'


def kr(code, value, venue='KOSPI', **fields):
    return dict(fact_id=f'{venue}:{code}',fact_type='market_cross_section_sector',as_of_date=DAY,source='kiwoom_rest',
        fields=dict(dict(market_scope=venue,sector_code=code,sector=KR_NAMES[venue][code],return_pct=value,
        metric_role='sector_price_proxy',taxonomy='kiwoom-sector-index-v1',today_signal_eligible=False,
        source_ref=f'kiwoom:ka20003:{venue}:{code}:{DAY}'),**fields))


def source(facts, market='kr'):
    return dict(session=dict(market=market,assessment_date=DAY,latest_completed_regular_session_date=DAY),
        fact_catalog=facts,numeric_registry=[dict(fact_id=f['fact_id'],field_path='fields.return_pct',
            unit='pct',value=f['fields']['return_pct'],registered=False,prose_allowed=False) for f in facts])


def plan(s, market='kr', **kw):
    return build_display_plan(s,market=market,assessment_date=DAY,eligible_refs=(),**kw)


@pytest.mark.parametrize('values', [(-3,-2,-1), (3,2,1), (-1,-1,-1), (1,), (1,2,3,4,5), ()])
def test_sector_daily_values_without_direction_or_breadth(values):
    rows = [kr(c,v) for c,v in zip(('005','006','007','008','009'),values)]
    result = plan(source(rows))
    top,bottom = [i for i in result.items if i.block_id=='sectors' and i.proof['venue']=='KOSPI']
    assert [b.value for b in top.bindings]==sorted(values,reverse=True)[:3]
    assert [b.value for b in bottom.bindings]==sorted(values)[:3]
    assert '상대 강세' in top.label and '상대 약세' in bottom.label
    assert ('확보 업종 기준' in top.text) == bool(values)
    assert top.status==('AVAILABLE' if values else 'UNAVAILABLE')
    if values and len(set(values))==1:
        assert top.fact_ids==bottom.fact_ids==tuple(f['fact_id'] for f in rows)
    assert result.eligible_refs==()


def test_one_polluted_row_does_not_hide_other_venues_and_taxonomy():
    rows = [kr('005',1,sector='음식료 · 담배'), kr('006',2), kr('006',3),
        kr('027',9),kr('002',8),kr('009',3,observed_at='2026-11-08T10:00:00+00:00'),
        kr('103',-1,'KOSDAQ'),kr('111',4,'KOSDAQ')]
    s = source(rows)
    s['numeric_registry'][-1]['unit']='KRW'
    result = plan(s,sector_taxonomy_version='sector-universe-user-confirmed-v2')
    rank = [i for i in result.items if i.block_id=='sectors']
    assert [i.fact_ids for i in rank]==[('KOSPI:005',),('KOSPI:005',),('KOSDAQ:103',),('KOSDAQ:103',)]
    assert any(i.block_id=='sector_auxiliary' and i.fact_ids==('KOSPI:002',) for i in result.items)
    reasons = [r['reason'] for r in result.sector_observation_audit]
    assert {'DUPLICATE_OR_CONFLICT','RETURN_VALUE_OR_UNIT_MISMATCH','OBSERVATION_SESSION_MISMATCH','parent_manufacturing_excluded'} <= set(reasons)
    assert all(not r['directional_authority_added'] for r in result.sector_observation_audit)


def test_us_soxx_is_separate_and_keeps_its_observation():
    rows = [dict(fact_id=s,fact_type='market_sector',as_of_date=DAY,source='ohlcv_analyst',
        fields=dict(series_code=s,return_pct=value)) for s,value in (('SOXX',5),('XLK',2))]
    result = plan(source(rows,market='us'),market='us')
    assert all('SOXX' not in i.fact_ids for i in result.items if i.block_id=='sectors')
    assert any(i.fact_ids==('SOXX',) and '반도체' in i.text for i in result.items if i.block_id=='sector_auxiliary')


def quote(currency, day, rate, *, hour=7, provider='ecos', unit=None, scale=None):
    normal = 100 if currency=='JPY' else 1
    at = datetime.fromisoformat(f'{day}T{hour:02d}:00:00+00:00')
    return KrCloseFxObservation(provider=provider,series_code={'USD':'USDKRW_KR_CLOSE','JPY':'JPYKRW100_KR_CLOSE',
        'EUR':'EURKRW_KR_CLOSE'}[currency],market_session='kr_close',unit=unit or ('KRW per 100 JPY' if currency=='JPY' else f'KRW per {currency}'),
        value=rate*normal,observed_at=at,retrieved_at=at,provider_last_refreshed=at.replace(tzinfo=None).isoformat(),
        provider_timezone='UTC',from_currency=currency,to_currency='KRW',raw_rate=rate,scale=normal if scale is None else scale)


def test_fx_friday_to_monday_excludes_same_day_poll_and_wrong_provider():
    rows = [quote('USD','2026-11-06',1300),quote('USD',DAY,1302,hour=6),quote('USD',DAY,1310),
        quote('JPY','2026-11-06',9),quote('JPY',DAY,9.2),quote('EUR',DAY,1500),
        quote('EUR','2026-11-06',1490,provider='alpha_vantage_fx_close')]
    policy = UnifiedSourcePolicy(frozenset({'ecos','alpha_vantage_fx_close'}))
    assert not policy.permits('alpha_vantage_fx_close')
    cutoff = datetime(2026,11,9,8,tzinfo=timezone.utc)
    s = source([])
    result = plan(s,fx_observations=rows,fx_source_policy=policy,fx_cutoff=cutoff)
    text = render_display_plan(result,s,'시장 서술')
    assert '원/달러: 1,310.00원' in text and '+10.00원 (+0.77%, 2026-11-06 대비)' in text
    assert '원/100엔: 920.00원' in text and '+20.00원 (+2.22%, 2026-11-06 대비)' in text
    assert '원/유로: 1,500.00원 (2026-11-09 관측) · 비교 자료 미확보' in text
    assert all(r.provider=='ecos' for r in result.fx_observations)
    with pytest.raises(ValueError,match='explicit_source_policy'):
        plan(s,fx_observations=rows,fx_cutoff=cutoff)


def test_fx_zero_missing_stale_double_scale_and_cutoff_are_local():
    rows = [quote('USD','2026-11-06',0),quote('USD',DAY,1320),quote('JPY',DAY,9.2,scale=1),
        quote('EUR','2026-11-06',1510),quote('EUR',DAY,1520,hour=10)]
    result = retained_fx_display(rows,completed=DAY,cutoff=datetime(2026,11,9,8,tzinfo=timezone.utc),
        source_policy=UnifiedSourcePolicy(frozenset({'ecos'})))
    assert result['USDKRW_KR_CLOSE'][0].change_value is None
    assert 'JPYKRW100_KR_CLOSE' not in result
    assert result['EURKRW_KR_CLOSE'][0].value==1510 and result['EURKRW_KR_CLOSE'][1]['stale']


def test_ecos_retained_exact_body_uses_100_yen_without_scaling():
    from app.services.macro_source_time import publication_context

    body = json.dumps({'KeyStatisticList':{'row':[
        dict(CLASS_NAME='환율',KEYSTAT_NAME=title,DATA_VALUE=str(v),CYCLE='20261109',UNIT_NAME='원')
        for title,v in (('원/달러 환율(종가)',1310),('원/엔(100엔) 환율(매매기준율)',920),('원/유로 환율(매매기준율)',1500))]}},ensure_ascii=False)
    at = datetime(2026,11,9,8,tzinfo=timezone.utc)
    publication = publication_context(provider='ecos',series='USDKRW',period='20261109',
        query_as_of=at,retrieved_at=at,response_bytes=body.encode(),cadence='daily',daily_required=True,latest_verified=True)
    options = dict(publication=publication,source_hashes={sha256(body.encode()).hexdigest()},anchor_value=1310,
        source_policy=UnifiedSourcePolicy(frozenset({'ecos'})))
    items = retained_ecos_fx_display(body,**options)
    assert len(items)==3 and items['JPYKRW100_KR_CLOSE'][0].value==920
    assert all(item[0].comparison_date is None for item in items.values())
    assert items['EURKRW_KR_CLOSE'][1]['series_basis']=='ECOS_REFERENCE_RATE'
    with pytest.raises(ValueError,match='original_response_mismatch'):
        retained_ecos_fx_display(body.replace('920','921'),**options)
