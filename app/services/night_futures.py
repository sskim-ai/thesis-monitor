from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from app.services.market_session import preceding_exchange_session_date


NIGHT_FUTURES_SERIES = (
    "KRX_KOSPI200_NIGHT_FUT",
    "KRX_KOSDAQ150_NIGHT_FUT",
)

NIGHT_FUTURES_LABELS = {
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 최근월물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 최근월물",
}
NIGHT_FUTURES_SESSION_BASIS_CONTRACT = "night-futures-session-basis-v1"
NIGHT_COMPARISON_SEMANTIC = (
    "completed_night_close_minus_immediately_preceding_day_close"
)
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class NightFuturesItem:
    series_code: str
    label: str
    value: float
    change_value: float | None
    change_pct: float | None
    session_date: date
    contract_code: str
    exchange: str
    session_type: str
    reference_session: str
    reference_date: date
    reference_price: float
    comparison_semantic: str
    as_of: str
    source: str
    night_source_record_id: str
    reference_source_record_id: str
    night_source_payload_sha256: str
    reference_source_payload_sha256: str


@dataclass(frozen=True)
class NightFuturesSummary:
    items: list[NightFuturesItem] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)

    @property
    def source_date(self) -> date | None:
        dates = {item.session_date for item in self.items}
        return next(iter(dates)) if len(dates) == 1 else None

    @property
    def reference_date(self) -> date | None:
        dates = {item.reference_date for item in self.items}
        return next(iter(dates)) if len(dates) == 1 else None


def _date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _session_is_fresh(item: dict[str, object]) -> tuple[bool, date | None]:
    session_date = (
        _date_value(item.get("session_date"))
        or _date_value(item.get("trade_date"))
        or _date_value(item.get("observed_at"))
    )
    expected_date = _date_value(item.get("expected_latest_session_date"))
    session_freshness = str(item.get("session_freshness") or "").lower()
    quality_status = str(item.get("quality_status") or "").lower()

    if session_freshness:
        fresh = session_freshness in {"fresh", "revised"}
    elif expected_date is not None and session_date is not None:
        fresh = expected_date == session_date and quality_status in {"fresh", "revised"}
    else:
        # Night-futures timestamps are session-specific. Generic daily freshness is
        # insufficient when the expected completed KRX session is not recorded.
        fresh = False
    if expected_date is not None and session_date != expected_date:
        fresh = False
    return fresh, session_date


def _verified_session_basis(
    item: dict[str, object],
    *,
    session_date: date,
) -> tuple[bool, date | None, float | None]:
    reference_date = _date_value(item.get("reference_date"))
    reference_price = _number(item.get("reference_price"))
    current_price = _number(item.get("current_session_price"))
    value = _number(item.get("value"))
    change_value = _number(item.get("change_value"))
    change_pct = _number(item.get("change_pct"))
    provider_change = _number(item.get("provider_change_point"))
    provider_change_match = item.get("provider_change_match")
    night_sha = str(item.get("night_source_payload_sha256") or "")
    reference_sha = str(item.get("reference_source_payload_sha256") or "")
    expected_change_pct = (
        (current_price - reference_price) / reference_price * 100
        if current_price is not None
        and reference_price is not None
        and reference_price != 0
        else None
    )
    expected_reference_date = preceding_exchange_session_date("XKRX", session_date)
    provider_cross_check_valid = provider_change is None or bool(
        provider_change_match is True
        and change_value is not None
        and math.isclose(
            provider_change,
            change_value,
            rel_tol=0,
            abs_tol=1e-8,
        )
    )
    valid = bool(
        item.get("session_basis_contract")
        == NIGHT_FUTURES_SESSION_BASIS_CONTRACT
        and str(item.get("exchange") or "") == "XKRX"
        and str(item.get("market_session") or "").lower() == "kr_night"
        and str(item.get("session_type") or "").upper() == "NIGHT"
        and str(item.get("reference_session") or "").upper() == "DAY"
        and expected_reference_date is not None
        and reference_date == expected_reference_date
        and str(item.get("contract_code") or "").strip()
        and str(item.get("retrieved_at") or item.get("session_close") or "").strip()
        and str(item.get("source_url") or item.get("provider") or "").strip()
        and str(item.get("night_source_record_id") or "").strip()
        and str(item.get("reference_source_record_id") or "").strip()
        and _SHA256.fullmatch(night_sha)
        and _SHA256.fullmatch(reference_sha)
        and item.get("comparison_semantic") == NIGHT_COMPARISON_SEMANTIC
        and reference_price is not None
        and current_price is not None
        and value is not None
        and math.isclose(value, current_price, rel_tol=0, abs_tol=1e-8)
        and change_value is not None
        and math.isclose(
            change_value,
            current_price - reference_price,
            rel_tol=0,
            abs_tol=1e-8,
        )
        and change_pct is not None
        and expected_change_pct is not None
        and math.isclose(
            change_pct,
            expected_change_pct,
            rel_tol=0,
            abs_tol=1e-6,
        )
        and provider_cross_check_valid
    )
    return valid, reference_date, reference_price


def summarize_night_futures(market: object) -> NightFuturesSummary:
    observations = market.get("observations", []) if isinstance(market, dict) else []
    rows = {
        str(item["series_code"]): item
        for item in observations
        if isinstance(item, dict) and item.get("series_code") in NIGHT_FUTURES_SERIES
    }
    if not rows:
        gate = market.get("night_futures_gate", {}) if isinstance(market, dict) else {}
        if isinstance(gate, dict) and gate.get("query_attempted"):
            return NightFuturesSummary(
                cautions=[
                    "한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해 "
                    "오늘 개장 전 신호에서 제외했습니다."
                ]
            )
        return NightFuturesSummary()

    items: list[NightFuturesItem] = []
    excluded: list[str] = []
    for series_code in NIGHT_FUTURES_SERIES:
        row = rows.get(series_code)
        if row is None:
            excluded.append(series_code)
            continue
        fresh, session_date = _session_is_fresh(row)
        value = _number(row.get("value"))
        if not fresh or session_date is None or value is None:
            excluded.append(series_code)
            continue
        verified, reference_date, reference_price = _verified_session_basis(
            row,
            session_date=session_date,
        )
        if not verified or reference_date is None or reference_price is None:
            excluded.append(series_code)
            continue
        items.append(
            NightFuturesItem(
                series_code=series_code,
                label=NIGHT_FUTURES_LABELS[series_code],
                value=value,
                change_value=_number(row.get("change_value")),
                change_pct=_number(row.get("change_pct")),
                session_date=session_date,
                contract_code=str(row.get("contract_code")),
                exchange=str(row.get("exchange")),
                session_type="NIGHT",
                reference_session="DAY",
                reference_date=reference_date,
                reference_price=reference_price,
                comparison_semantic=str(row.get("comparison_semantic")),
                as_of=str(row.get("retrieved_at") or row.get("session_close") or ""),
                source=str(row.get("source_url") or row.get("provider") or ""),
                night_source_record_id=str(row.get("night_source_record_id")),
                reference_source_record_id=str(
                    row.get("reference_source_record_id")
                ),
                night_source_payload_sha256=str(
                    row.get("night_source_payload_sha256")
                ),
                reference_source_payload_sha256=str(
                    row.get("reference_source_payload_sha256")
                ),
            )
        )

    if not items:
        cautions = [
            "한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해 오늘 개장 전 신호에서 제외했습니다."
        ]
    else:
        cautions = [
            f"{NIGHT_FUTURES_LABELS[series_code].replace(' 최근월물', '')} 야간선물은 "
            "최신 세션 확인이 되지 않아 제외했습니다."
            for series_code in excluded
        ]
    return NightFuturesSummary(items=items, cautions=cautions)


def render_night_futures(summary: NightFuturesSummary) -> str:
    if not summary.items:
        return ""
    source_date = summary.source_date
    reference_date = summary.reference_date
    date_label = (
        f" · {source_date:%m/%d} 새벽 종료 · {reference_date:%m/%d} 주간장 대비"
        if source_date is not None and reference_date is not None
        else ""
    )
    lines: list[str] = []
    for item in summary.items:
        line = f"• {item.label} {item.value:,.2f}"
        if item.change_value is not None:
            line += f" · {item.change_value:+,.2f}pt"
        if item.change_pct is not None:
            line += f" ({item.change_pct:+.2f}%)"
        lines.append(line)
    return f"🌙 한국 야간선물{date_label}\n" + "\n".join(lines)


def is_night_futures_warning(value: object) -> bool:
    text = str(value or "").lower()
    return "krx_night_futures" in text or "night_session" in text
