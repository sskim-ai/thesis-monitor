from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


CONTRACT_VERSION = "ohlcv-completed-bar-finality-v1"
SEMANTICS_KEY = "_source_field_semantics"
CURRENT_QUOTE_KEY = "_current_quote_value"
COMPLETED_CLOSE_KEY = "_completed_bar_close_value"


class BarFinality(StrEnum):
    FINAL = "FINAL"
    PROVISIONAL = "PROVISIONAL"
    UNCONFIRMED = "UNCONFIRMED"
    INVALID = "INVALID"


class PriceSemanticOwner(StrEnum):
    CURRENT_QUOTE = "CURRENT_QUOTE"
    COMPLETED_BAR_CLOSE = "COMPLETED_BAR_CLOSE"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ProviderFieldSemantics(FrozenModel):
    provider: str
    market: str
    endpoints: dict[str, str]
    open_field: str
    high_field: str
    low_field: str
    normalized_close_field: str
    normalized_close_owner: PriceSemanticOwner
    settled_regular_close_field: str | None = None
    current_quote_field: str | None = None
    provider_finality_field: str | None = None
    evidence: tuple[str, ...] = ()


class BarFinalityAssessment(FrozenModel):
    contract: str = CONTRACT_VERSION
    state: BarFinality
    source: str
    quote_field: str | None = None
    completed_close_field: str | None = None
    completed_close_value: Decimal | None = None
    current_quote_silently_owns_completed_close: bool = False


KIWOOM_US_CHART_FIELDS = ProviderFieldSemantics(
    provider="kiwoom",
    market="US",
    endpoints={
        "daily": "usa06012",
        "weekly": "usa06013",
        "monthly": "usa06014",
    },
    open_field="open_pric",
    high_field="high_pric",
    low_field="low_pric",
    normalized_close_field="cur_prc",
    normalized_close_owner=PriceSemanticOwner.CURRENT_QUOTE,
    settled_regular_close_field=None,
    current_quote_field="cur_prc",
    provider_finality_field=None,
    evidence=(
        "official Kiwoom US chart schema labels cur_prc as current price",
        "ohlcv-analyst KiwoomProvider maps cur_prc to normalized close",
        "no distinct settled regular close or finality field is propagated",
    ),
)


def provider_field_semantics(provider: str, market: str) -> ProviderFieldSemantics | None:
    if provider.lower() == "kiwoom" and market.upper() == "US":
        return KIWOOM_US_CHART_FIELDS
    return None


def annotate_normalized_bar(
    row: Mapping[str, object],
    *,
    provider: str,
    market: str,
    timeframe: str,
    has_later_chart_row: bool = False,
) -> dict[str, object]:
    normalized = dict(row)
    semantics = provider_field_semantics(provider, market)
    if semantics is not None:
        normalized[CURRENT_QUOTE_KEY] = row.get("close")
        normalized[SEMANTICS_KEY] = {
            "provider": semantics.provider,
            "market": semantics.market,
            "endpoint": semantics.endpoints.get(timeframe),
            "open_field": semantics.open_field,
            "high_field": semantics.high_field,
            "low_field": semantics.low_field,
            "normalized_close_field": semantics.normalized_close_field,
            "normalized_close_owner": semantics.normalized_close_owner,
            "settled_regular_close_field": semantics.settled_regular_close_field,
            "current_quote_field": semantics.current_quote_field,
            "provider_finality_field": semantics.provider_finality_field,
            "has_later_chart_row": has_later_chart_row,
        }
    return normalized


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _valid_enclosure(
    row: Mapping[str, object], *, completed_close: object | None = None
) -> bool:
    values = (
        _decimal(row.get("open")),
        _decimal(row.get("high")),
        _decimal(row.get("low")),
        _decimal(row.get("close") if completed_close is None else completed_close),
    )
    if any(value is None for value in values):
        return False
    open_value, high, low, close = values
    assert open_value is not None and high is not None and low is not None and close is not None
    return min(values) > 0 and low <= open_value <= high and low <= close <= high


def assess_completed_bar_finality(
    row: Mapping[str, object],
    *,
    cutoff: date,
) -> BarFinalityAssessment:
    state = str(row.get("bar_state") or row.get("completion_state") or "").upper()
    if state in {"PROVISIONAL", "PARTIAL", "OPEN", "LIVE"}:
        return BarFinalityAssessment(state=BarFinality.PROVISIONAL, source="explicit_marker")
    if state in {"UNCONFIRMED", "UNKNOWN"}:
        return BarFinalityAssessment(state=BarFinality.UNCONFIRMED, source="explicit_marker")
    try:
        row_date = date.fromisoformat(str(row.get("date") or "")[:10])
    except ValueError:
        return BarFinalityAssessment(state=BarFinality.INVALID, source="invalid_date")
    if row_date > cutoff:
        return BarFinalityAssessment(state=BarFinality.PROVISIONAL, source="after_completed_cutoff")
    semantics = row.get(SEMANTICS_KEY)
    if not isinstance(semantics, Mapping):
        if not _valid_enclosure(row):
            return BarFinalityAssessment(state=BarFinality.INVALID, source="ohlc_enclosure")
        if state in {"FINAL", "COMPLETE", "COMPLETED", "CLOSED"}:
            return BarFinalityAssessment(
                state=BarFinality.FINAL,
                source="explicit_marker",
                completed_close_value=_decimal(row.get("close")),
            )
        return BarFinalityAssessment(state=BarFinality.UNCONFIRMED, source="field_semantics_missing")
    quote_field = str(semantics.get("current_quote_field") or "") or None
    settled = str(semantics.get("settled_regular_close_field") or "") or None
    settled_value = row.get(COMPLETED_CLOSE_KEY)
    if settled_value is None and settled:
        settled_value = row.get(settled)
    if settled and settled_value is not None:
        if not _valid_enclosure(row, completed_close=settled_value):
            return BarFinalityAssessment(
                state=BarFinality.INVALID,
                source="settled_close_ohlc_enclosure",
                quote_field=quote_field,
                completed_close_field=settled,
            )
        return BarFinalityAssessment(
            state=BarFinality.FINAL,
            source="provider_native_settled_close",
            quote_field=quote_field,
            completed_close_field=settled,
            completed_close_value=_decimal(settled_value),
        )
    endpoint = str(semantics.get("endpoint") or "")
    if endpoint and state in {"FINAL", "COMPLETE", "COMPLETED", "CLOSED"}:
        if not _valid_enclosure(row):
            return BarFinalityAssessment(
                state=BarFinality.INVALID,
                source="explicit_final_ohlc_enclosure",
                quote_field=quote_field,
            )
        return BarFinalityAssessment(
            state=BarFinality.FINAL,
            source="explicit_final_marker",
            quote_field=quote_field,
            completed_close_field=str(semantics.get("normalized_close_field") or "") or None,
            completed_close_value=_decimal(row.get("close")),
        )
    if bool(semantics.get("has_later_chart_row")):
        if not _valid_enclosure(row):
            return BarFinalityAssessment(
                state=BarFinality.INVALID,
                source="historical_chart_row_ohlc_enclosure",
                quote_field=quote_field,
            )
        return BarFinalityAssessment(
            state=BarFinality.FINAL,
            source="later_chart_row_proves_historical_finality",
            quote_field=quote_field,
            completed_close_field=str(semantics.get("normalized_close_field") or "") or None,
            completed_close_value=_decimal(row.get("close")),
        )
    return BarFinalityAssessment(
        state=BarFinality.UNCONFIRMED,
        source="settled_regular_close_unavailable",
        quote_field=quote_field,
        completed_close_field=None,
        current_quote_silently_owns_completed_close=False,
    )
