"""Explain how confirmed incremental evidence relates to frozen close decisions."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.new_buyer_base_contract import number


_MARKET_ZONES = {'kr': ZoneInfo('Asia/Seoul'), 'us': ZoneInfo('America/New_York')}
_PRICE_BASES = {
    'adjusted_close': 'adjusted',
    'unadjusted_close': 'unadjusted',
    'regular_close': 'unadjusted',
}
_VALID_STRUCTURE = {'intact', 'wick_only_review'}
_PRICE_ONLY_WAIT = {
    'CURRENT_PRICE_RISK_REWARD_CONDITIONAL', 'CURRENT_PRICE_RISK_REWARD_POOR_CHASE',
}


@dataclass(frozen=True)
class PriceComparison:
    status: str
    value: Decimal | None = None
    currency: str | None = None
    observed_at: datetime | None = None
    source: str | None = None
    latency_seconds: Decimal | None = None
    close_change_pct: Decimal | None = None
    reference_rr: Decimal | None = None
    scenario: str | None = None
    rr_at_least_two: bool = False
    in_rr2: bool = False
    preference_relation: str = 'UNCONFIRMED'
    preference_conditional: bool = False

    @property
    def confirmed(self) -> bool:
        return self.value is not None

    @property
    def rr_label(self) -> str | None:
        if self.reference_rr is None:
            return None
        display = f'{self.reference_rr:.2f}'
        if display == '2.00' and not self.rr_at_least_two:
            return '2배 미만'
        return f'{display}배'


@dataclass(frozen=True)
class Applicability:
    state: str
    action: str
    price: PriceComparison
    review: str = 'UNCONFIRMED'


def _instant(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return None
    if isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(UTC)
    return None


def _quote_observation(quote, opening_session, cutoff):
    observed = _instant(quote.get('observation_timestamp'))
    maximum_age = number(quote.get('max_age_seconds'))
    latency = number(quote.get('latency_seconds'))
    zone = _MARKET_ZONES.get(quote.get('market'))
    source = quote.get('source')
    value = number(quote.get('value'))
    if (observed is None or cutoff is None or zone is None or not isinstance(source, str)
            or not source.strip() or quote.get('market_session') != 'pre_market'
            or observed > cutoff
            or observed.astimezone(zone).date().isoformat() != str(opening_session)
            or cutoff.astimezone(zone).date().isoformat() != str(opening_session)
            or maximum_age is None or maximum_age <= 0 or latency is None or latency < 0
            or max(latency, number((cutoff - observed).total_seconds())) > maximum_age
            or value is None or value <= 0):
        return None
    return value, observed, source, latency


def _preference(base, price):
    economics = base.get('economics') or {}
    boundary = number(economics.get('price'))
    if (not economics.get('candidate_id') or economics.get('side') not in {'LOW', 'HIGH'}
            or boundary is None or boundary <= 0
            or economics.get('price_basis') != base.get('price_basis')):
        return 'UNCONFIRMED', False
    relation = 'AT_OR_BELOW' if price <= boundary else 'ABOVE'
    return relation, economics.get('status') == 'CONDITIONAL'


def compare_price(summary_row, *, opening_session: date, cutoff: datetime, quote=None):
    """Compare one qualified observation with the accepted close/structure.

    The adapter supplies an actual pre-market observation time, adjustment basis,
    same-share-basis confirmation, latency and provider-specific freshness limit.
    Query-time snapshots do not fulfill this interface.
    """
    if quote is None:
        return PriceComparison('UNAVAILABLE')
    base = summary_row.get('preopen') or {}
    observation = _quote_observation(quote, opening_session, _instant(cutoff))
    if observation is None:
        return PriceComparison('OBSERVATION_UNVERIFIED')
    adjustment = _PRICE_BASES.get(base.get('price_basis'))
    close = number(base.get('close'))
    if (not base.get('security_id') or quote.get('security_id') != base['security_id']
            or quote.get('market') != base['market'] or not base.get('currency')
            or quote.get('currency') != base['currency'] or adjustment is None
            or quote.get('adjustment_basis') != adjustment
            or quote.get('share_basis_comparable') is not True or close is None or close <= 0):
        return PriceComparison('BASIS_UNVERIFIED')

    price, observed, source, latency = observation
    preference, conditional = _preference(base, price)
    values = dict(value=price, currency=base['currency'], observed_at=observed, source=source,
                  latency_seconds=latency, close_change_pct=(price - close) / close * 100,
                  preference_relation=preference, preference_conditional=conditional)
    current = base.get('current_scenario') or {}
    support = base.get('support') or {}
    band = base.get('support_scenario') or {}
    stop = number(current.get('stop')) if current.get('stop_ref') else None
    current_target = number(current.get('target')) if current.get('target_basis') else None
    band_target = number(band.get('target')) if band.get('target_basis') else None
    low, high = number(support.get('low')), number(support.get('high'))
    if stop is not None and 0 < stop and price <= stop:
        return PriceComparison('STOP_REACHED', **values)
    if summary_row.get('entry_quality') == 'BLOCKED' or current.get('status') in {
        'hard_invalid', 'accelerated_invalid',
    }:
        return PriceComparison('STRUCTURE_REVIEW', **values)
    if current_target is not None and price >= current_target:
        return PriceComparison('TARGET_REACHED', **values)
    if (current.get('status') not in _VALID_STRUCTURE or not support.get('candidate_id')
            or None in (stop, low, high) or not 0 < stop < low <= high):
        return PriceComparison('RR_UNVERIFIED', **values)

    target = scenario = None
    # The current target was determined at the old quote. Moving downward can
    # expose a closer barrier, so the original target needs an explicit bound.
    floor = number(current.get('applicable_from'))
    if (current_target is not None and floor is not None and floor <= price < current_target
            and current.get('possible_barrier') is None):
        target, scenario = current_target, 'CURRENT'
    elif (low <= price <= high and band_target is not None and high < band_target
          and band.get('assumption') is None):
        target, scenario = band_target, 'SUPPORT'
    if target is None:
        return PriceComparison('RR_UNVERIFIED', **values)

    upside, downside = target - price, price - stop
    rr_low, rr_high = number(band.get('rr2_low')), number(band.get('rr2_high'))
    in_rr2 = (band.get('intersection') == 'DISPLAYABLE' and rr_low is not None
              and rr_high is not None and low <= rr_low <= price <= rr_high <= high)
    return PriceComparison('RR_AVAILABLE', reference_rr=upside / downside, scenario=scenario,
                           rr_at_least_two=upside >= 2 * downside, in_rr2=in_rr2, **values)


_PRICE_STATES = {
    'UNAVAILABLE': '장전 가격 미확보',
    'OBSERVATION_UNVERIFIED': '장전 시세 관측 시각·지연 미확인',
    'BASIS_UNVERIFIED': '장전 시세의 동일 종목·가격 기준 비교 미확인',
    'STOP_REACHED': '장전 가격이 기존 무효화선 이하',
    'STRUCTURE_REVIEW': '기존 지지 구조 재검토 상태',
    'TARGET_REACHED': '장전 가격이 기존 목표 저항 도달·상회',
    'RR_UNVERIFIED': '장전 가격 확인 · 기존 저항·무효화선 적용 미확인',
    'RR_AVAILABLE': '장전 가격 확인 · 기존 구조의 참고 손익비 비교',
}


def _avoid_entry(row, base):
    return (row.get('overall') == 'SELL' or row.get('economic') == 'AVOID'
            or bool(base.get('active_material_risk')))


def _entry_application(row, base, price):
    if _avoid_entry(row, base):
        return '기존 신규매수 회피·위험 조건 유지', 'NOT_APPLICABLE'
    if (row.get('entry_quality') == 'BLOCKED' or price.status == 'STRUCTURE_REVIEW'
            or price.status == 'STOP_REACHED'):
        return '완료봉 기준으로 기존 지지 구조 재검토', 'NOT_APPLICABLE'
    if price.status == 'TARGET_REACHED':
        return '기존 목표 저항 부근의 추격 진입 유의 · 구조 확인', 'NOT_APPLICABLE'
    if row.get('economic') != 'ATTRACTIVE':
        return '기존 기업·가격 판단의 확인 조건 대기', 'NOT_APPLICABLE'
    if base.get('technical_state') == 'ADVERSE':
        return '기존 기술 약화의 개선 신호 확인 대기', 'NOT_APPLICABLE'
    if base.get('confidence_veto'):
        return '기존 판단을 제한한 근거 확인', 'UNCONFIRMED'
    if not price.confirmed:
        return '개장 후 기존 가격·구조 조건 확인', 'UNCONFIRMED'
    if price.reference_rr is not None and not price.rr_at_least_two:
        return '기존 손익비 관찰 가격과 기술 조건 확인', 'NOT_APPLICABLE'
    if not price.rr_at_least_two or not price.in_rr2 or base.get('technical_state') not in {
        'SUPPORTIVE', 'MIXED', 'INSUFFICIENT',
    }:
        return '장전 가격과 기존 진입 조건의 적용 여부 확인', 'UNCONFIRMED'

    same_price = price.value == number(base.get('close'))
    if not same_price and price.preference_relation != 'AT_OR_BELOW':
        action = ('변경된 가격과 기존 경제적 선호 조건 재확인' if price.preference_relation == 'ABOVE'
                  else '변경된 가격의 경제적 조건 확인')
        return action, 'UNCONFIRMED'
    original_action = row.get('action_class')
    if original_action == 'REVIEW_NOW' and same_price:
        return '기존 신규매수 검토 조건 확인', 'CONFIRMED'
    if original_action in {'REVIEW_NOW', 'CONDITIONAL'} or (
        original_action == 'WAIT' and base.get('entry_reason') in _PRICE_ONLY_WAIT
        and base.get('technical_state') in {'SUPPORTIVE', 'MIXED'}
    ):
        return '기존 경제·기술 조건 유지 전제에서 조건부 검토', 'CONFIRMED_CONDITIONAL'
    return '기존 확인 조건의 충족 여부 점검', 'UNCONFIRMED'


def confirmed_material_event(event, cutoff):
    """Identify a scoped, newly observed official change with a known release time."""
    published = _instant(event.get('published_at'))
    deadline = _instant(cutoff)
    return (event.get('incremental') == 'CONFIRMED'
            and event.get('official') is True and event.get('material') is True
            and event.get('timestamp_uncertain') is not True and published is not None
            and deadline is not None and published <= deadline)


def assess_stock(summary_row, *, opening_session: date, cutoff: datetime, events=(),
                 coverage='UNKNOWN', quote=None, prior_reference=False):
    """Add an applicability explanation while leaving the accepted row untouched."""
    if summary_row.get('status') != 'COMPLETE':
        return Applicability('본 분석 미완료·제한', '분석 자료 확보 후 판단',
                             PriceComparison('UNAVAILABLE'))
    if prior_reference:
        return Applicability('이전 기준일 참고', '이번 개장일 적용 여부 확인 필요',
                             PriceComparison('UNAVAILABLE'))

    price = compare_price(summary_row, opening_session=opening_session, cutoff=cutoff, quote=quote)
    price_state = _PRICE_STATES[price.status]
    base = summary_row.get('preopen') or {}
    if any(confirmed_material_event(event, cutoff) for event in events):
        action = '새 공식 근거로 기존 판단의 적용 여부 재평가'
        if _avoid_entry(summary_row, base):
            action = '기존 신규매수 회피·위험 조건 유지 · ' + action
        return Applicability(f'중요 공식 변경 확인 · {price_state}',
                             action, price)

    action, review = _entry_application(summary_row, base, price)
    if events or coverage != 'CHECKED':
        coverage_state = '신규 자료 내용·시점 확인 필요' if events else '공시·뉴스 변경 범위 미확인'
        if review in {'CONFIRMED', 'CONFIRMED_CONDITIONAL'}:
            action, review = '신규 자료와 기존 가격·구조 조건 확인', 'UNCONFIRMED'
    else:
        coverage_state = '확인 범위 내 중요 변경 미발견'
    return Applicability(f'{coverage_state} · {price_state}', action, price, review)
