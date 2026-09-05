from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Mapping

import exchange_calendars as exchange_calendar
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.night_futures_session_mapping_service import KST


CONTRACT_VERSION = "krx-night-futures-session-quote-v1"
INSTRUMENT_ID = "XKRX:KOSPI200:FUTURES"
SESSION_START = time(18, 0)
SESSION_END = time(6, 0)


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NightMarketState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ChangeReferenceType(StrEnum):
    REGULAR_SESSION_CLOSE = "REGULAR_SESSION_CLOSE"
    OFFICIAL_BASE_PRICE = "OFFICIAL_BASE_PRICE"
    PRIOR_NIGHT_CLOSE = "PRIOR_NIGHT_CLOSE"
    PROVIDER_REFERENCE = "PROVIDER_REFERENCE"
    UNKNOWN = "UNKNOWN"


class RollState(StrEnum):
    SAME_CONTRACT = "SAME_CONTRACT"
    ROLL_PENDING = "ROLL_PENDING"
    ROLLED = "ROLLED"
    UNKNOWN = "UNKNOWN"


class NightFuturesReferenceComparison(FrozenModel):
    reference_type: ChangeReferenceType
    reference_price: Decimal
    change: Decimal
    change_pct: Decimal
    source_semantic_explicit: bool
    source_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_reference(self) -> NightFuturesReferenceComparison:
        if self.reference_price <= 0:
            raise ValueError("night_futures_reference_price_must_be_positive")
        if self.reference_type != ChangeReferenceType.UNKNOWN and not self.source_semantic_explicit:
            raise ValueError("night_futures_reference_type_not_source_owned")
        return self


class KrxNightFuturesSessionQuote(FrozenModel):
    contract: Literal["krx-night-futures-session-quote-v1"] = CONTRACT_VERSION
    instrument_id: Literal["XKRX:KOSPI200:FUTURES"] = INSTRUMENT_ID
    instrument_type: Literal["KOSPI200_FUTURES"] = "KOSPI200_FUTURES"
    exchange: Literal["XKRX"] = "XKRX"
    contract_month: str = Field(pattern=r"^20\d{4}$")
    session_type: Literal["NIGHT"] = "NIGHT"
    session_business_date: date
    session_start_kst: datetime
    session_end_kst: datetime
    observed_at: datetime
    market_state: NightMarketState
    open: Decimal
    high: Decimal
    low: Decimal
    last: Decimal
    volume: int
    comparisons: tuple[NightFuturesReferenceComparison, ...] = Field(min_length=1)
    source: str = Field(min_length=1)
    source_quality: Literal["OFFICIAL", "APPROVED_PROVIDER", "HUMAN_FIXTURE"]
    is_delayed: bool | None
    stale_reason: str | None
    last_trading_date: date | None
    days_to_expiry: int | None
    roll_state: RollState

    @model_validator(mode="after")
    def validate_quote(self) -> KrxNightFuturesSessionQuote:
        expected_start, expected_end = krx_night_session_window(self.session_business_date)
        if self.session_start_kst != expected_start or self.session_end_kst != expected_end:
            raise ValueError("night_futures_cross_midnight_window_mismatch")
        if self.observed_at.tzinfo is None:
            raise ValueError("night_futures_observed_at_timezone_required")
        expected_state, _ = krx_night_market_state(self.observed_at)
        if self.market_state != expected_state:
            raise ValueError("night_futures_market_state_mismatch")
        prices = (self.open, self.high, self.low, self.last)
        if any(value <= 0 for value in prices):
            raise ValueError("night_futures_price_must_be_positive")
        if self.high < max(self.open, self.low, self.last):
            raise ValueError("night_futures_high_invalid")
        if self.low > min(self.open, self.high, self.last):
            raise ValueError("night_futures_low_invalid")
        if self.volume < 0:
            raise ValueError("night_futures_volume_invalid")
        if self.last_trading_date is None:
            if self.days_to_expiry is not None:
                raise ValueError("night_futures_days_to_expiry_without_date")
        else:
            expected_days = (self.last_trading_date - self.session_business_date).days
            if self.days_to_expiry != expected_days:
                raise ValueError("night_futures_days_to_expiry_mismatch")
        return self


def krx_night_session_window(session_business_date: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(session_business_date, SESSION_START, tzinfo=KST),
        datetime.combine(session_business_date + timedelta(days=1), SESSION_END, tzinfo=KST),
    )


def _is_krx_business_date(value: date) -> bool:
    try:
        return bool(exchange_calendar.get_calendar("XKRX").is_session(value))
    except (ValueError, IndexError, TypeError):
        return False


def krx_night_market_state(observed_at: datetime) -> tuple[NightMarketState, date | None]:
    if observed_at.tzinfo is None:
        raise ValueError("night_futures_observed_at_timezone_required")
    observed_kst = observed_at.astimezone(KST)
    clock = observed_kst.timetz().replace(tzinfo=None)
    if clock >= SESSION_START:
        business_date = observed_kst.date()
    elif clock < SESSION_END:
        business_date = observed_kst.date() - timedelta(days=1)
    else:
        return NightMarketState.CLOSED, None
    if not _is_krx_business_date(business_date):
        return NightMarketState.CLOSED, None
    start, end = krx_night_session_window(business_date)
    return (
        (NightMarketState.OPEN, business_date)
        if start <= observed_kst < end
        else (NightMarketState.CLOSED, None)
    )


def _decimal(value: object, *, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"night_futures_{field_name}_invalid") from exc
    if not result.is_finite():
        raise ValueError(f"night_futures_{field_name}_invalid")
    return result


def _comparison(
    *,
    last: Decimal,
    reference_price: Decimal,
    reference_type: ChangeReferenceType,
    source_semantic_explicit: bool,
    source_ref: str,
    reported_change: object | None = None,
    reported_pct: object | None = None,
) -> NightFuturesReferenceComparison:
    change = last - reference_price
    pct = change / reference_price * Decimal("100")
    if reported_change is not None and abs(change - _decimal(reported_change, field_name="change")) > Decimal(
        "0.005"
    ):
        raise ValueError("night_futures_change_arithmetic_mismatch")
    if reported_pct is not None and abs(pct - _decimal(reported_pct, field_name="change_pct")) > Decimal(
        "0.01"
    ):
        raise ValueError("night_futures_change_pct_arithmetic_mismatch")
    return NightFuturesReferenceComparison(
        reference_type=reference_type,
        reference_price=reference_price,
        change=change.quantize(Decimal("0.01")),
        change_pct=pct.quantize(Decimal("0.01")),
        source_semantic_explicit=source_semantic_explicit,
        source_ref=source_ref,
    )


def quote_from_human_acceptance_fixture(
    fixture: Mapping[str, object],
    *,
    observed_at: datetime,
) -> KrxNightFuturesSessionQuote:
    ohlcv = fixture.get("ohlcv")
    header = fixture.get("header_change")
    if not isinstance(ohlcv, Mapping) or not isinstance(header, Mapping):
        raise ValueError("night_futures_fixture_shape_invalid")
    session_business_date = date.fromisoformat(str(fixture["session_business_date"]))
    start, end = krx_night_session_window(session_business_date)
    last = _decimal(ohlcv.get("close"), field_name="last")
    header_reference = _decimal(
        header.get("arithmetically_implied_reference"), field_name="reference_price"
    )
    prior_night_close = _decimal(
        fixture.get("prior_night_close"), field_name="prior_night_close"
    )
    state, _ = krx_night_market_state(observed_at)
    return KrxNightFuturesSessionQuote(
        contract_month=str(fixture["contract"]),
        session_business_date=session_business_date,
        session_start_kst=start,
        session_end_kst=end,
        observed_at=observed_at,
        market_state=state,
        open=_decimal(ohlcv.get("open"), field_name="open"),
        high=_decimal(ohlcv.get("high"), field_name="high"),
        low=_decimal(ohlcv.get("low"), field_name="low"),
        last=last,
        volume=int(ohlcv.get("volume") or 0),
        comparisons=(
            _comparison(
                last=last,
                reference_price=header_reference,
                reference_type=ChangeReferenceType.UNKNOWN,
                source_semantic_explicit=False,
                source_ref="fixture.header_change",
                reported_change=header.get("change"),
                reported_pct=header.get("pct"),
            ),
            _comparison(
                last=last,
                reference_price=prior_night_close,
                reference_type=ChangeReferenceType.PRIOR_NIGHT_CLOSE,
                source_semantic_explicit=True,
                source_ref="fixture.prior_night_close",
                reported_pct=fixture.get("night_close_to_night_close_pct"),
            ),
        ),
        source="Kiwoom screenshot acceptance fixture",
        source_quality="HUMAN_FIXTURE",
        is_delayed=None,
        stale_reason="completed_historical_session",
        last_trading_date=None,
        days_to_expiry=None,
        roll_state=RollState.UNKNOWN,
    )


def same_contract_night_return(
    *,
    current: KrxNightFuturesSessionQuote,
    prior: KrxNightFuturesSessionQuote,
) -> NightFuturesReferenceComparison:
    if current.instrument_id != prior.instrument_id:
        raise ValueError("cross_instrument_raw_return_forbidden")
    if current.contract_month != prior.contract_month:
        raise ValueError("cross_contract_raw_return_forbidden")
    return _comparison(
        last=current.last,
        reference_price=prior.last,
        reference_type=ChangeReferenceType.PRIOR_NIGHT_CLOSE,
        source_semantic_explicit=True,
        source_ref=f"same_contract:{prior.session_business_date.isoformat()}",
    )


def reference_comparisons_conflict(
    comparisons: tuple[NightFuturesReferenceComparison, ...],
) -> bool:
    seen: dict[tuple[ChangeReferenceType, Decimal], tuple[Decimal, Decimal]] = {}
    for comparison in comparisons:
        key = (comparison.reference_type, comparison.reference_price)
        value = (comparison.change, comparison.change_pct)
        if key in seen and seen[key] != value:
            return True
        seen[key] = value
    return False


def _signed(value: Decimal, suffix: str = "") -> str:
    return f"{value:+,.2f}{suffix}"


def render_krx_night_futures_shadow(
    quote: KrxNightFuturesSessionQuote,
    *,
    rendered_at: datetime,
) -> str:
    current_state, active_business_date = krx_night_market_state(rendered_at)
    live = bool(
        quote.market_state == NightMarketState.OPEN
        and current_state == NightMarketState.OPEN
        and active_business_date == quote.session_business_date
        and quote.session_start_kst <= quote.observed_at < quote.session_end_kst
    )
    heading = "KOSPI200 야간선물" if live else "최근 KOSPI200 야간선물"
    session_label = (
        f"{quote.session_business_date.month}/{quote.session_business_date.day} 야간 세션"
    )
    price_label = "현재가" if live else "종가"
    lines = [
        f"🌙 {heading}",
        f"{session_label} {price_label} {quote.last:,.2f} | {quote.contract_month} 계약",
    ]
    for comparison in quote.comparisons:
        if comparison.reference_type == ChangeReferenceType.PRIOR_NIGHT_CLOSE:
            lines.append(f"전 야간 종가 대비 {_signed(comparison.change_pct, '%')}")
            break
    return "\n".join(lines)
