"""Focused regression tests for observation-only ECOS comparisons."""
from datetime import datetime
from hashlib import sha256
import json

import pytest

from app.services.kr_close_fx import RetainedEcosFxCapture, format_dated_fx, retained_ecos_fx_display
from app.services.macro_source_time import publication_context
from app.services.unified_source_policy import UnifiedSourcePolicy

USD = '원/달러 환율(종가)'
JPY = '원/엔(100엔) 환율(매매기준율)'
EUR = '원/유로 환율(매매기준율)'
POLICY = UnifiedSourcePolicy(frozenset({'ecos'}))


def capture(day, values):
    body = json.dumps({'KeyStatisticList': {'row': [
        dict(CLASS_NAME='환율', KEYSTAT_NAME=title, DATA_VALUE=str(value), CYCLE=period, UNIT_NAME=unit)
        for title, value, period, unit in values]}}, ensure_ascii=False)
    at = datetime.fromisoformat(day + 'T08:00:00+00:00')
    return RetainedEcosFxCapture(body=body, source_hashes=(sha256(body.encode()).hexdigest(),),
        publication=publication_context(provider='ecos', series='USDKRW', period=day, query_as_of=at,
            retrieved_at=at, response_bytes=body.encode(), cadence='daily', daily_required=True, latest_verified=True))


def display(current, *prior):
    return retained_ecos_fx_display(current.body, publication=current.publication, source_hashes=current.source_hashes,
        anchor_value=1320, source_policy=POLICY, prior_captures=prior)


def test_each_ecos_series_uses_its_own_date_and_same_basis_prior():
    current = capture('2026-11-12', [(USD,1320,'20261112','원'),(JPY,838,'20261111','원'),(EUR,1480,'20261112','원')])
    prior = capture('2026-11-10', [(USD,1310,'20261110','원'),(JPY,830,'20261110','원'),(EUR,1470,'20261110','원')])
    rows = display(current, prior)
    yen,proof = rows['JPYKRW100_KR_CLOSE']
    assert (yen.value,yen.observation_date,yen.comparison_date,yen.change_value)==(838,'2026-11-11','2026-11-10',8)
    assert yen.change_pct == pytest.approx(8/830*100)
    assert proof['comparison_response_sha256']==prior.source_hashes[0] and proof['query_as_of']==current.publication['query_as_of']
    assert rows['USDKRW_KR_CLOSE'][0].change_value==10
    assert rows['EURKRW_KR_CLOSE'][0].change_value==10
    assert all(not p['directional_authority_added'] for _,p in rows.values())


def test_wrong_basis_provider_units_and_future_or_unpinned_prior_never_compare():
    current = capture('2026-11-12', [(USD,1320,'20261112','원'),(JPY,838,'20261112','원'),(EUR,1480,'20261112','원')])
    prior = capture('2026-11-11', [(USD,1300,'20261111','원'),(JPY,830,'20261111','달러'),(EUR.replace('매매기준율','종가'),1470,'20261111','원')])
    wrong = prior.model_copy(update={'publication':dict(prior.publication,provider='alpha_vantage_fx_close')})
    unpinned = prior.model_copy(update={'source_hashes':('0'*64,)})
    future = capture('2026-11-13', [(USD,1300,'20261111','원')])
    rows = display(current, prior, wrong, unpinned, future)
    assert rows['USDKRW_KR_CLOSE'][0].change_value==20
    assert all(rows[s][0].comparison_date is None for s in ('JPYKRW100_KR_CLOSE','EURKRW_KR_CLOSE'))
    assert display(current, wrong, unpinned, future)['USDKRW_KR_CLOSE'][0].comparison_date is None


def test_zero_or_conflicting_previous_value_is_not_zero_percent():
    current = capture('2026-11-12', [(USD,1320,'20261112','원'),(JPY,838,'20261112','원')])
    prior = capture('2026-11-11', [(USD,0,'20261111','원'),(JPY,830,'20261111','원'),(JPY,831,'20261111','원')])
    for item,_ in display(current, prior).values():
        assert item.change_value is None and item.change_pct is None
        assert format_dated_fx(item).endswith('비교 자료 미확보')
