from dataclasses import dataclass, field
import json
import math

from app.models.macro import MacroBriefing


FX_LABELS = {
    "USDKRW_KR_CLOSE": "원/달러",
    "JPYKRW100_KR_CLOSE": "원/100엔",
    "EURKRW_KR_CLOSE": "원/유로",
}


@dataclass(frozen=True)
class KrCloseFxItem:
    series_code: str
    label: str
    value: float
    change_value: float | None = None
    change_pct: float | None = None


@dataclass(frozen=True)
class KrCloseFxSummary:
    items: list[KrCloseFxItem] = field(default_factory=list)
    missing_labels: list[str] = field(default_factory=list)
    stale_as_of: str | None = None


def _json(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def summarize_kr_close_fx(briefing: MacroBriefing | None) -> KrCloseFxSummary:
    if briefing is None:
        return KrCloseFxSummary()
    market = _json(briefing.market_summary, {})
    quality = _json(briefing.data_quality, [])
    fx = market.get("fx", []) if isinstance(market, dict) else []
    items: list[KrCloseFxItem] = []
    stale_dates: list[str] = []
    for item in fx if isinstance(fx, list) else []:
        if not isinstance(item, dict):
            continue
        series_code = str(item.get("series_code") or "")
        label = FX_LABELS.get(series_code)
        value = _number(item.get("value"))
        if label is None or value is None:
            continue
        items.append(
            KrCloseFxItem(
                series_code=series_code,
                label=label,
                value=value,
                change_value=_number(item.get("change_value")),
                change_pct=_number(item.get("change_pct")),
            )
        )
        if item.get("quality_status") == "stale" and item.get("as_of"):
            stale_dates.append(str(item["as_of"])[:10])
    quality_items = quality if isinstance(quality, list) else []
    unavailable = [
        str(item.get("warning", ""))
        for item in quality_items
        if isinstance(item, dict) and str(item.get("warning", "")).endswith(":unavailable")
    ]
    missing_labels = [
        label
        for series_code, label in FX_LABELS.items()
        if any(warning.startswith(series_code) for warning in unavailable)
    ]
    return KrCloseFxSummary(
        items=items,
        missing_labels=missing_labels,
        stale_as_of=max(stale_dates) if stale_dates else None,
    )


def render_kr_close_fx(summary: KrCloseFxSummary) -> str:
    if not summary.items:
        return "⚠️ 환율 자료를 이번 조회에서 확인하지 못했습니다."
    lines = ["💱 환율"]
    for item in summary.items:
        line = f"• {item.label} {item.value:,.1f}원"
        if item.change_value is not None and item.change_pct is not None:
            line += f" · {item.change_value:+,.1f}원 ({item.change_pct:+.2f}%)"
        lines.append(line)
    if summary.missing_labels:
        lines.append(
            f"⚠️ {', '.join(summary.missing_labels)} 환율은 이번 조회에서 확인하지 못했습니다."
        )
    if summary.stale_as_of:
        lines.append(f"⚠️ 환율 최신 관측은 {summary.stale_as_of} 기준입니다.")
    return "\n".join(lines)
