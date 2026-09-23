"""Offline source qualification only; not imported by production collection/delivery."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

import exchange_calendars

from app.macro.providers.market import MARKET_SYMBOLS
from app.macro.publication import CONTRACT as PUBLICATION_CONTRACT, PUBLICATION_SERIES
from app.providers.kiwoom_rest_client import payload_sha256
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, MARKETS
from app.services.kr_market_digest_quality_service import is_kr_sector_return_row
from scripts.m12ds_r6_r2_cutoff_audit import session_at


def number(value):
    try:
        result = Decimal(str(value).replace(',', ''))
        if not result.is_finite():
            raise ValueError('nonfinite_number')
        return result
    except InvalidOperation as exc:
        raise ValueError('invalid_number') from exc


def source_hash(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('invalid_source_hash')
    return value


def daily_pair(rows, target, previous, fields):
    """Validate exact dates and OHLC enclosure without granting finality."""
    if previous >= target or not isinstance(rows, dict):
        raise ValueError('daily_pair_dates_invalid')
    calendar = exchange_calendars.get_calendar('XNYS')
    session = calendar.date_to_session(target, direction='none')
    if calendar.previous_session(session).date() != previous:
        raise ValueError('previous_exchange_session_required')
    for key in rows:
        date.fromisoformat(key)
    if max(rows, default='') != target.isoformat() or previous.isoformat() not in rows:
        raise ValueError('exact_latest_and_previous_session_required')
    selected = []
    for day in (target, previous):
        raw = rows[day.isoformat()]
        values = {name: number(raw[key]) for name, key in fields.items()}
        o, h, low, c, v = (values[k] for k in ('open', 'high', 'low', 'close', 'volume'))
        if not (0 < low <= min(o, c) <= max(o, c) <= h and v >= 0):
            raise ValueError('ohlcv_enclosure_invalid')
        selected.append(dict(date=day.isoformat(), **{k: str(v) for k, v in values.items()}))
    return selected


def kiwoom_daily_inspection(envelope, *, target, previous, interval='daily'):
    if envelope.get('api_id') != 'usa06012' or envelope.get('endpoint') != '/api/us/chart':
        return dict(close_owner='CURRENT_QUOTE', current_direction_eligible=False, pair=None)
    request = envelope['request']
    if (interval != 'daily' or request.get('upd_stkpc_tp') not in {'0', '1'}
            or request.get('exrt_appl_tp') != '0'):
        raise ValueError('daily_interval_and_basis_required')
    payload = envelope['response']
    if envelope['http_status'] != 200 or str(payload.get('return_code')) != '0':
        raise ValueError('provider_response_failed')
    source_hash(envelope['raw_response_sha256'])
    indexed = {}
    for row in payload['result_list']:
        raw_date = row.get('dt', '')
        if len(raw_date) != 8 or not raw_date.isdigit():
            raise ValueError('row_date_missing_or_invalid')
        day = datetime.strptime(raw_date, '%Y%m%d').date().isoformat()
        if day in indexed:
            raise ValueError('duplicate_daily_row')
        # The response field is often blank. It must not contradict the owned request.
        if row.get('upd_stkpc_tp') not in (None, '', request['upd_stkpc_tp']):
            raise ValueError('adjustment_basis_mismatch')
        indexed[day] = row
    pair = daily_pair(indexed, target, previous, dict(open='open_pric', high='high_pric',
        low='low_pric', close='cur_prc', volume='acc_trde_qty'))
    return dict(contract='kiwoom-daily-row-inspection-v1', close_owner='DATED_DAILY_BAR_CLOSE',
        pair=pair, adjustment='ADJUSTED' if request['upd_stkpc_tp'] == '1' else 'RAW',
        raw_response_sha256=envelope['raw_response_sha256'],
        regular_session_finality='UNPROVEN', current_direction_eligible=False,
        denial_reason='AFTER_HOURS_CONTAMINATION_POSSIBLE', lookahead_used=False)


def universe_coverage(symbols):
    actual = list(symbols)
    required = set(MARKET_SYMBOLS)
    missing = sorted(required - set(actual))
    return dict(required_count=len(required), present_count=len(required & set(actual)),
        missing=missing, unexpected=sorted(set(actual)-required),
        status='PASS' if not missing and len(actual) == len(set(actual)) else 'FAIL')


def alpha_daily_inspection(payload, *, function, symbol, target, previous):
    if function != 'TIME_SERIES_DAILY':
        raise ValueError('unqualified_alpha_endpoint')
    if any(key in payload for key in ('Information', 'Note', 'Error Message')):
        return dict(status='RATE_ENTITLEMENT_OR_PROVIDER_DENIED', pair=None,
            current_direction_eligible=False)
    metadata = payload['Meta Data']
    if metadata['2. Symbol'] != symbol or metadata['5. Time Zone'] not in {'US/Eastern', 'America/New_York'}:
        raise ValueError('alpha_identity_or_timezone_mismatch')
    rows = payload['Time Series (Daily)']
    if any('5. adjusted close' in row for row in rows.values()):
        raise ValueError('mixed_raw_adjusted_schema')
    pair = daily_pair(rows, target, previous, dict(open='1. open', high='2. high',
        low='3. low', close='4. close', volume='5. volume'))
    return dict(status='DAILY_SCHEMA_PASS_NOT_ROUTE_QUALIFICATION', pair=pair, adjustment='RAW',
        current_direction_eligible=False, regular_session_finality='UNPROVEN',
        cutoff_availability='UNPROVEN', sustainable_account_limit='UNPROVEN')


def kr_post_close_receipt(market, envelopes):
    spec = MARKETS[market]
    expected = {'ka20001', 'ka20003', 'ka20009'}
    if set(envelopes) != expected:
        raise ValueError('exact_kr_three_actions_required')
    days = set()
    for action, envelope in envelopes.items():
        request = {'inds_cd': spec['code']}
        if action != 'ka20003':
            request['mrkt_tp'] = spec['ka20001_market']
        if (envelope['api_id'] != action or envelope['endpoint'] != '/api/dostk/sect'
                or envelope['request'] != request or envelope['http_status'] != 200
                or type(envelope['continuation']) is not bool
                or action == 'ka20003' and envelope['continuation']
                or str(envelope['response'].get('return_code')) != '0'):
            raise ValueError('venue_request_or_response_identity_mismatch')
        source_hash(envelope['raw_response_sha256'])
        start, end = (datetime.fromisoformat(str(envelope[k])) for k in ('started_at', 'received_at'))
        if start.tzinfo is None or end.tzinfo is None or end < start:
            raise ValueError('aware_collection_times_required')
        for at in (start, end):
            state = session_at(at, 'KR')
            if state['regular_session_state'] != 'POST_CLOSE':
                raise ValueError('same_day_closed_regular_session_required')
            days.add(state['intended_completed_session'])
    if len(days) != 1:
        raise ValueError('cross_session_collection')
    day = date.fromisoformat(days.pop())
    current, sectors, history = (envelopes[a]['response'] for a in ('ka20001', 'ka20003', 'ka20009'))
    at = datetime.fromisoformat(str(envelopes['ka20001']['started_at']))
    KiwoomKrMarketContextService._validate_session_identity(session_date=day, observed_at=at,
        current=current, sectors=sectors, history=history, market=market, code=spec['code'])
    historic = [r for r in history['inds_cur_prc_daly_rept'] if r.get('dt_n') == day.strftime('%Y%m%d')][0]
    composite = [r for r in sectors['all_inds_idex'] if r.get('stk_cd') == spec['code']][0]
    level, change = abs(number(current['cur_prc'])), number(current['flu_rt'])
    if level <= 0 or any(abs(number(r[p])) != level or number(r[c]) != change for r, p, c in (
            (historic, 'cur_prc_n', 'flu_rt_n'), (composite, 'cur_prc', 'flu_rt'))):
        raise ValueError('exact_decimal_parity_required')
    candidates, excluded, identities = [], [], set()
    for row in sectors['all_inds_idex']:
        code, name = row['stk_cd'], row['stk_nm']
        if code in identities:
            raise ValueError('duplicate_sector_identity')
        identities.add(code)
        count = number(row['flo_stk_num'])
        # Reuse existing adapter + digest taxonomy; no model or new ranking score.
        if (code == spec['code'] or count <= 0 or market == 'KOSPI' and code in {'002','003','004'}
                or not is_kr_sector_return_row(market_scope=market, name=name)):
            excluded.append(code)
            continue
        candidates.append(dict(code=code, name=name, return_pct=str(number(row['flu_rt'])),
            fact_id=f'kiwoom:ka20003:{market}:{code}:{day.isoformat()}'))
    if len(candidates) < 3:
        raise ValueError('sector_coverage_incomplete')
    return dict(contract='kr-post-close-sector-session-v1', status='PASS', market=market,
        session_date=day.isoformat(), regular_session_state='CLOSED', level=str(level), return_pct=str(change),
        parity='EXACT_LEVEL_AND_RETURN', tolerance=0, source_actions=sorted(expected),
        source_raw_hashes={a: envelopes[a]['raw_response_sha256'] for a in sorted(expected)},
        source_payload_hashes={a: payload_sha256(envelopes[a]['response']) for a in sorted(expected)},
        continuation={a: envelopes[a]['continuation'] for a in sorted(expected)},
        pagination_scope='complete sector snapshot; scalar current index and exact-date history row only',
        collected_at={a: str(envelopes[a]['received_at']) for a in sorted(expected)},
        ranking_owner='existing adapter size/listed-count rules + is_kr_sector_return_row',
        candidate_count=len(candidates), candidate_sha256=payload_sha256(sorted(candidates, key=lambda x:x['fact_id'])),
        excluded_codes=sorted(excluded), tie_break='canonical fact_id',
        top3=sorted(candidates, key=lambda r: (-number(r['return_pct']),r['fact_id']))[:3],
        bottom3=sorted(candidates, key=lambda r: (number(r['return_pct']),r['fact_id']))[:3])


def latest_available_information(envelope, *, series, as_of):
    """Authenticated collector envelope, never a direction-evidence source."""
    if (series not in PUBLICATION_SERIES or as_of.tzinfo is None
            or envelope['provider'] != 'fred'
            or envelope['source_url'] != f'https://fred.stlouisfed.org/series/{series}'
            or envelope['request']['series_id'] != series or envelope['http_status'] != 200):
        raise ValueError('macro_source_identity_invalid')
    received = datetime.fromisoformat(envelope['received_at'])
    if received.tzinfo is None or received > as_of:
        raise ValueError('macro_availability_unowned')
    body = envelope['raw_body'].encode('utf-8')
    if sha256(body).hexdigest() != source_hash(envelope['raw_response_sha256']):
        raise ValueError('macro_body_hash_mismatch')
    publication = envelope['publication_receipt']
    published = datetime.fromisoformat(publication['published_at'])
    if (publication['contract'] != PUBLICATION_CONTRACT or publication['provider'] != 'fred'
            or publication['series_code'] != series or publication['source_url'] != envelope['source_url']
            or published.tzinfo is None or published > received):
        raise ValueError('macro_publication_provenance_invalid')
    source_hash(publication['source_sha256'])
    rows, seen = [], set()
    for row in json.loads(body)['observations']:
        day = date.fromisoformat(row['date'])
        if day in seen or day > published.date():
            raise ValueError('macro_date_untrusted')
        seen.add(day)
        if row['value'] != '.':
            rows.append((day, number(row['value'])))
    if not rows:
        raise ValueError('macro_value_missing')
    day, value = max(rows)
    if day.isoformat() != publication['expected_observation_date']:
        raise ValueError('not_latest_published_observation')
    return dict(contract='macro-latest-available-information-v1', series=series, value=str(value),
        observation_date=day.isoformat(), label=f'최신 확인값 (기준 {day.isoformat()})',
        source_url=envelope['source_url'], source_sha256=envelope['raw_response_sha256'],
        publication_source_sha256=publication['source_sha256'], display_eligible=True,
        current_direction_eligible=False, direction_fact_refs=[], renderer_scope='INFORMATION_ONLY')
