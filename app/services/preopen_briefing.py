"""Trading-session window and deterministic presentation for the NO_SEND job."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.services.market_session import (
    NEW_YORK,
    SEOUL,
    exchange_session_open,
    is_exchange_session_date,
    preceding_exchange_session_date,
)
from app.services.preopen_applicability import assess_stock, confirmed_material_event
from app.services.unified_snapshot_contract import digest


@dataclass(frozen=True)
class PreopenWindow:
    opening_session: date
    base_session: date
    collection_end: datetime
    delivery_end: datetime


def preopen_window(market: str, now: datetime) -> PreopenWindow | None:
    if now.utcoffset() is None:
        raise ValueError('preopen_aware_clock_required')
    zone, calendar = {'kr': (SEOUL, 'XKRX'), 'us': (NEW_YORK, 'XNYS')}[market]
    local = now.astimezone(zone)
    day = local.date()
    start, collection_end, delivery_end = (
        (time(7, 30), time(7, 45), time(7, 50)) if market == 'kr'
        else (time(8, 30), time(8, 55), time(9))
    )
    if not start <= local.time() < delivery_end or not is_exchange_session_date(calendar, day):
        return None
    opened = exchange_session_open(calendar, day)
    base = preceding_exchange_session_date(calendar, day)
    if opened is None or base is None:
        return None
    if market == 'kr':
        opened = min(opened, datetime.combine(day, time(8), zone))
    delivery = min(datetime.combine(day, delivery_end, zone), opened)
    if local >= delivery:
        return None
    cutoff = min(datetime.combine(day, collection_end, zone), delivery - timedelta(minutes=5))
    return PreopenWindow(day, base, cutoff, delivery)


_BASE_STATUS = {
    'COMPLETE': '검증 완료', 'PARTIAL': '일부 종목 미완료', 'FAILED': '실패',
    'MISSING': '결과 없음', 'IN_PROGRESS': '진행 중 또는 종료 미확인',
    'CORRUPT': '저장 결과 확인 실패',
}


def _stock_coverage(coverage, ticker):
    sources = [r for r in coverage if r.get('ticker') == ticker]
    checked = {'NO_SIGNIFICANT_CHANGE'}
    return 'CHECKED' if all(
        any(r['topic'] == topic and r['status'] in checked for r in sources)
        and not any(r['topic'] == topic and r['status'] not in checked for r in sources)
        for topic in ('filings', 'news')
    ) else 'UNKNOWN'


def _event_line(event, cutoff):
    date_text = event.get('published_at') or event.get('published_date')
    source = event.get('provider', '출처 미확인')
    label = '공식 변경' if confirmed_material_event(event, cutoff) else '내용·시각 확인 필요'
    return f"{label} · {event.get('title') or '제목 미확인'} ({source}, {date_text or '시각 미확인'})"


def _market_line(obs):
    label = obs['series']
    if obs['value'] is not None:
        label += f" {obs['value']} {obs['unit']}"
    label += f" ({obs['observed_date']} · {obs['provider']})"
    if obs.get('change_pct') is not None:
        label += f" · {obs['change_pct']:+.2f}%"
    if obs.get('change_bp') is not None:
        label += f" · {obs['change_bp']:+.1f}bp"
    if obs.get('previous_observed_date') and (
        obs.get('change_pct') is not None or obs.get('change_bp') is not None
    ):
        label += f" (비교일 {obs['previous_observed_date']})"
    return label


def _price_line(price, zone, zone_label):
    observed = price.observed_at.astimezone(zone)
    fields = [f'장전 {price.value:f} {price.currency} ({observed:%H:%M:%S} {zone_label} · {price.source}'
              f' · 지연 {price.latency_seconds:f}초)',
              f'기준 종가 대비 {price.close_change_pct:+.2f}%']
    if price.rr_label is not None:
        scenario = '선택 지지 시나리오' if price.scenario == 'SUPPORT' else '기준가 시나리오'
        fields.append(f'{scenario} 참고 RR {price.rr_label}')
    relation = {'AT_OR_BELOW': '경제적 선호가 이내', 'ABOVE': '경제적 선호가 초과'}
    if price.preference_relation in relation:
        fields.append(relation[price.preference_relation] + ('(조건부)' if price.preference_conditional else ''))
    return ' · '.join(fields)


def render_briefing(market, window, base, sources, generated_at):
    country = '한국' if market == 'kr' else '미국'
    zone = SEOUL if market == 'kr' else NEW_YORK
    zone_label = 'KST' if market == 'kr' else 'ET'
    market_id = 'MARKET_' + market.upper()
    summary_id = 'SUMMARY_' + market.upper()
    originals = {m['message_id']: m for m in base.messages}
    coverage = sources['coverage']
    rows = base.rows
    market_lines = [
        f'[{country} 장전 브리핑] 개장일 {window.opening_session} · '
        f'{generated_at.astimezone(zone):%H:%M} {zone_label}',
        f'직전 완료장 {window.base_session} 본 분석 · {_BASE_STATUS[base.status]}',
    ]
    if base.session is not None and not base.is_current:
        market_lines.append(f'아래 본 분석은 {base.session} 기준 이전 참고 자료입니다.')
    if base.cutoff is not None:
        market_lines.append(f'본 분석 자료 기준 {base.cutoff.astimezone(zone):%Y-%m-%d %H:%M} {zone_label}')
    market_lines.extend(_market_line(obs) for obs in sources['market'])
    if not sources['market']:
        market_lines.append('장전 추가 시장 관측 미확보')

    checked_prices = 0
    immediate = conditional = 0
    overlays = {}
    new_review_lines = []
    cutoff = min(window.collection_end, generated_at)
    for row in rows:
        ticker = row['ticker']
        if row['status'] == 'LEGACY':
            overlays[ticker] = (f'{ticker} · 기준 {base.session} 원문 참고\n'
                                '오늘 · 저장된 가격 비교 자료 미확보')
            continue
        events = sources['events'].get(ticker, ())
        result = assess_stock(
            row, opening_session=window.opening_session,
            cutoff=cutoff, events=events,
            coverage=_stock_coverage(coverage, ticker),
            quote=sources.get('quotes', {}).get(ticker), prior_reference=not base.is_current,
        )
        checked_prices += bool(result.price and result.price.confirmed)
        immediate += result.review == 'CONFIRMED'
        conditional += result.review == 'CONFIRMED_CONDITIONAL'
        state = result.state
        if row['status'].endswith('_UNISSUED_TIMEOUT'):
            state = f"{row['status'].split('_')[0]} 타임아웃 · {state}"
        lines = [f'{ticker} · {state}']
        if result.price.confirmed:
            lines.append(_price_line(result.price, zone, zone_label))
        lines.append(f'오늘 · {result.action}')
        lines.extend(_event_line(event, cutoff) for event in events[:3])
        overlays[ticker] = '\n'.join(lines)
        if any(confirmed_material_event(event, cutoff) for event in events):
            new_review_lines.append(f'{ticker} 공식 변경 · 기존 판단 적용 재검토')
    market_lines.extend(new_review_lines)
    incomplete = sum(r['status'] in {'UNAVAILABLE', 'PARTIAL', 'DISABLED', 'TIMEOUT', 'LOCK_BUSY'}
                     for r in coverage if r.get('topic') != 'quotes')
    if incomplete:
        market_lines.append(f'일부 추가 자료 미확인 ({incomplete}개 조회 범위)')
    market_lines.append(f'장전 실제 가격 확인 {checked_prices}종목' if checked_prices else '장전 실제 가격 미확보')

    prior_summary = originals.get(summary_id)
    summary_lines = [f'[{country} 장전 Summary] {window.opening_session}']
    if base.is_current:
        attractive = sum(row.get('economic') == 'ATTRACTIVE' for row in rows)
        if prior_summary:
            summary_lines.append(f'본 분석 기업·가격 매력 {attractive}종목 · 기준 {base.session}')
        if checked_prices:
            summary_lines.append(f'장전 조건 검토 확인 {immediate}종목 · 조건부 {conditional}종목')
        else:
            summary_lines.append('장전 실제 가격 미확보 · 오늘 신규매수 조건 확인 필요')
    else:
        summary_lines.append(f'직전 완료장 본 분석 {_BASE_STATUS[base.status]} · 오늘 적용 조건 미확인')
    if not prior_summary:
        summary_lines.append('저장된 Summary 미확보' if originals else '검증 가능한 본 분석 원문 미확보')
    summary_lines.extend(overlays.values())

    def message(message_id, sections):
        original = originals.get(message_id)
        result = {'message_id': message_id, 'text': '\n\n'.join(sections)}
        if original:
            result['base_content_sha256'] = digest(original['text'])
        return result

    messages = [message(market_id, [
        '\n'.join(market_lines), *([originals[market_id]['text']] if market_id in originals else []),
    ]), message(summary_id, [
        '\n'.join(summary_lines), *([prior_summary['text']] if prior_summary else []),
    ])]
    for original in base.messages:
        ticker = original['message_id']
        if ticker in {market_id, summary_id}:
            continue
        sections = [original['text']]
        if ticker in overlays:
            sections.append('[장전 확인]\n' + overlays[ticker])
        messages.append(message(ticker, sections))
    return messages
