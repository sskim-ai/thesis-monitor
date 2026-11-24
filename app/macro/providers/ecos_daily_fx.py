"""Two dated ECOS KRW quotes; amounts already use the official quote unit."""
from datetime import timedelta
from math import isfinite

import httpx

from app.macro.providers.base import CollectedObservation
from app.services.macro_source_time import publication_context, observed_timestamp, source_period


TABLE = '731Y001'
DAILY_FX = {
    'JPYKRW100_KR_CLOSE': ('0000002', '원/일본엔(100엔)', 'KRW per 100 JPY'),
    'EURKRW_KR_CLOSE': ('0000003', '원/유로', 'KRW per EUR'),
}


def daily_fx_requests(as_of, api_key, series=tuple(DAILY_FX)):
    """One bounded request per currency, including earlier observations."""
    if as_of.utcoffset() is None or len(set(series)) != len(series) or set(series) - set(DAILY_FX):
        raise ValueError('ecos_daily_fx_request_scope')
    end = as_of.date()
    begin = end - timedelta(days=31)
    return [(code, httpx.Request('GET',
        f'https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/'
        f'{TABLE}/D/{begin:%Y%m%d}/{end:%Y%m%d}/{DAILY_FX[code][0]}')) for code in series]


def parse_daily_fx(response, *, series, as_of, retrieved_at):
    """An item-code match alone cannot authorize another currency or scale."""
    item_code, item_name, quote_unit = DAILY_FX[series]
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError('ecos_daily_fx_response_not_object')
    if isinstance(payload.get('RESULT'), dict) and payload['RESULT'].get('CODE') == 'INFO-200':
        return []
    document = payload['StatisticSearch']
    if not isinstance(document, dict):
        raise ValueError('ecos_daily_fx_response_not_object')
    rows = document['row']
    if (not isinstance(rows, list) or len(rows) > 100
            or int(document['list_total_count']) != len(rows)):
        raise ValueError('ecos_daily_fx_incomplete_response')
    dated = {}
    for row in rows:
        if (not isinstance(row, dict)
                or (row.get('STAT_CODE'), row.get('ITEM_CODE1'), row.get('ITEM_NAME1'), row.get('UNIT_NAME'))
                != (TABLE, item_code, item_name, '원')):
            raise ValueError('ecos_daily_fx_series_or_unit_mismatch')
        day, _ = source_period(row['TIME'], daily_required=True)
        if row['TIME'] != day.strftime('%Y%m%d') or not as_of.date()-timedelta(days=31) <= day <= as_of.date():
            raise ValueError('ecos_daily_fx_observation_outside_request')
        value = float(str(row['DATA_VALUE']).replace(',', ''))
        if not isfinite(value) or value <= 0 or day in dated:
            raise ValueError('ecos_daily_fx_invalid_or_duplicate_observation')
        dated[day] = value, row
    latest = max(dated, default=None)
    result = []
    # The immediately preceding observation supports a like-for-like change.
    # Only the latest row is a display candidate; no old quote fills a bad row.
    for day in sorted(dated)[-2:]:
        value, row = dated[day]
        temporal = publication_context(provider='ecos', series=series, period=row['TIME'],
            query_as_of=as_of, retrieved_at=retrieved_at, response_bytes=response.content,
            cadence='daily', latest_verified=day == latest, daily_required=True)
        result.append(CollectedObservation(series_code=series, category='fx',
            observed_at=observed_timestamp(temporal), value=value, unit='원', frequency='daily',
            source_url='https://ecos.bok.or.kr/', raw_payload=dict(source_row=row,
                source_period=row['TIME'], publication_context=temporal,
                fx_quote_unit=quote_unit, fx_series_basis='ECOS_OFFICIAL_DAILY')))
    return result
