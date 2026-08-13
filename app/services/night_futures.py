from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


NIGHT_FUTURES_SERIES = (
    "KRX_KOSPI200_NIGHT_FUT",
    "KRX_KOSDAQ150_NIGHT_FUT",
)

NIGHT_FUTURES_LABELS = {
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 최근월물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 최근월물",
}


@dataclass(frozen=True)
class NightFuturesItem:
    series_code: str
    label: str
    value: float
    change_value: float | None
    change_pct: float | None
    session_date: date


@dataclass(frozen=True)
class NightFuturesSummary:
    items: list[NightFuturesItem] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)

    @property
    def source_date(self) -> date | None:
        dates = {item.session_date for item in self.items}
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
    session_date = _date_value(item.get("trade_date")) or _date_value(
        item.get("observed_at")
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
        items.append(
            NightFuturesItem(
                series_code=series_code,
                label=NIGHT_FUTURES_LABELS[series_code],
                value=value,
                change_value=_number(row.get("change_value")),
                change_pct=_number(row.get("change_pct")),
                session_date=session_date,
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
    date_label = f" · {source_date:%m/%d} 기준" if source_date is not None else ""
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
