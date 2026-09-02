from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from app.services.krx_night_history_service import (
    KRX_NIGHT_DWM_CONTRACT,
    KrxNightAggregateBar,
    KrxNightTimeframes,
)
from app.services.night_futures import NIGHT_FUTURES_FACT_IDS
from app.services.us_market_digest_plan_service import (
    DigestOmissionReason,
    SUPPORTED_MACRO_FACT_TYPES,
    UsMarketDigestPlan,
    UsMarketDigestSlot,
    market_digest_plan_from_context,
    render_specific_macro_claim,
)


CONTRACT_VERSION = "us-morning-full-message-v1"
INDEX_SYMBOLS = ("SPY", "QQQ", "IWM", "SOXX", "RSP")
NIGHT_LABELS = {
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 야간선물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 야간선물",
}
DWM_LABELS = {
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 최근월물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 최근월물",
}


@dataclass(frozen=True)
class UsFullMessageRender:
    contract: str
    text: str
    index_fact_ids: tuple[str, ...]
    sector_fact_ids: tuple[str, ...]
    night_fact_ids: tuple[str, ...]
    section_order: tuple[str, ...]
    validation_errors: tuple[str, ...]

    @property
    def status(self) -> str:
        return "PASS" if not self.validation_errors else "FAIL"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _facts(value: object) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(value).get("fact_catalog", [])
    if not isinstance(rows, list):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _fields(fact: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(fact.get("fields"))


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _series(fact: Mapping[str, object]) -> str:
    fields = _fields(fact)
    return str(fields.get("series_code") or fields.get("symbol") or "")


def _fact_id(fact: Mapping[str, object]) -> str:
    return str(fact.get("fact_id") or "")


def _current_return(fact: Mapping[str, object]) -> float | None:
    fields = _fields(fact)
    value = _number(fields.get("return_pct"))
    if (
        fields.get("today_signal_eligible") is not True
        or fields.get("structured_state") != "CURRENT_DIRECTIONAL"
    ):
        return None
    return value


def _format_pct(value: float) -> str:
    return f"{value:+.2f}%"


def _night_return(frame: KrxNightAggregateBar) -> str:
    if frame.return_pct is None:
        return " · 수익률 산출 불가"
    label = {
        "DAILY": "주간장 대비",
        "WEEKLY": "주간",
        "MONTHLY": "월간",
    }[frame.timeframe]
    return f" · {label} {frame.return_pct:+.2f}%"


def _night_timeframe_line(frame: KrxNightAggregateBar, label: str) -> str:
    status = {
        "IN_PROGRESS": "진행중",
        "SAME_CONTRACT_PARTIAL_PERIOD": "동일만기 일부",
    }.get(frame.status)
    heading = f"{label}({status})" if status else label
    return (
        f"  - {heading}: O {frame.open:,.2f} · H {frame.high:,.2f} · "
        f"L {frame.low:,.2f} · C {frame.close:,.2f}{_night_return(frame)}"
    )


def _night_timeframe_block(
    row: Mapping[str, object],
    *,
    series: str,
) -> tuple[str, tuple[str, ...]] | None:
    raw = row.get("night_timeframes")
    if not isinstance(raw, Mapping):
        return None
    try:
        frames = KrxNightTimeframes.model_validate(raw)
    except ValueError:
        return None
    if (
        frames.contract != KRX_NIGHT_DWM_CONTRACT
        or frames.series_code != series
        or frames.contract_code != row.get("contract_code")
        or frames.reference_date.isoformat() != str(row.get("session_date"))
        or any(
            frame.series_code != series
            or frame.contract_code != frames.contract_code
            or frame.reference_date != frames.reference_date
            for frame in (frames.daily, frames.weekly, frames.monthly)
        )
    ):
        return None
    maturity = frames.contract_maturity.replace("-", "")
    lines = [f"• {DWM_LABELS[series]} ({maturity})"]
    lines.extend(
        (
            _night_timeframe_line(frames.daily, "일봉"),
            _night_timeframe_line(frames.weekly, "주봉"),
            _night_timeframe_line(frames.monthly, "월봉"),
        )
    )
    return "\n".join(lines), (
        frames.daily.fact_id,
        frames.weekly.fact_id,
        frames.monthly.fact_id,
    )


def _plan(value: object) -> UsMarketDigestPlan | None:
    return market_digest_plan_from_context(value)


def _plan_item(
    plan: UsMarketDigestPlan | None,
    slot: UsMarketDigestSlot,
):
    if plan is None:
        return None
    return next((item for item in plan.items if item.slot == slot), None)


def _safe_next_checks(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))[:2]


def _safe_macro_fact(
    item: object,
    facts_by_id: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object] | None:
    refs = getattr(item, "evidence_refs", ())
    if len(refs) != 1:
        return None
    fact = facts_by_id.get(str(refs[0]))
    if fact is None or fact.get("fact_type") not in SUPPORTED_MACRO_FACT_TYPES:
        return None
    fields = _fields(fact)
    role = str(fields.get("temporal_role") or "")
    date = str(fact.get("as_of_date") or "")
    if role not in {
        "CURRENT_OBSERVATION",
        "PRIOR_MARKET_SESSION",
        "REFERENCE_LAGGING",
    }:
        return None
    if role == "CURRENT_OBSERVATION" and fields.get("today_signal_eligible") is not True:
        return None
    if not date or date not in getattr(item, "observation_dates", ()):
        return None
    if role not in getattr(item, "temporal_roles", ()):
        return None
    if not render_specific_macro_claim(fact):
        return None
    return fact


def render_us_full_market_message(
    context: object,
    *,
    next_checks: Iterable[str] = (),
) -> UsFullMessageRender:
    facts = _facts(context)
    by_series = {_series(fact): fact for fact in facts if _series(fact)}
    by_id = {_fact_id(fact): fact for fact in facts if _fact_id(fact)}
    plan = _plan(context)
    errors: list[str] = []

    index_lines: list[str] = []
    index_fact_ids: list[str] = []
    index_dates: set[str] = set()
    for symbol in INDEX_SYMBOLS:
        fact = by_series.get(symbol)
        value = _current_return(fact) if fact is not None else None
        if fact is None or value is None:
            errors.append(f"missing_current_index_return:{symbol}")
            continue
        index_lines.append(f"• {symbol} {_format_pct(value)}")
        index_fact_ids.append(_fact_id(fact))
        if fact.get("as_of_date"):
            index_dates.add(str(fact["as_of_date"]))
    if len(index_dates) > 1:
        errors.append("index_session_mismatch")

    internal_lines: list[str] = []
    style = _plan_item(plan, UsMarketDigestSlot.PARTICIPATION_STYLE)
    small_cap = _plan_item(plan, UsMarketDigestSlot.SMALL_CAP_RELATIVE)
    breadth = _plan_item(plan, UsMarketDigestSlot.BREADTH_STATE)
    style_claim = (
        style.claim_text if style is not None and style.selected and style.claim_text else ""
    )
    small_cap_claim = (
        small_cap.claim_text
        if small_cap is not None and small_cap.selected and small_cap.claim_text
        else ""
    )
    breadth_claim = (
        breadth.claim_text
        if breadth is not None and breadth.selected and breadth.claim_text
        else ""
    )
    if style_claim and small_cap_claim and breadth_claim:
        internal_lines.append(f"• {style_claim} {small_cap_claim}")
    else:
        internal_lines.extend(f"• {claim}" for claim in (style_claim, small_cap_claim) if claim)
    if breadth is not None and breadth.selected and breadth.claim_text:
        internal_lines.append(f"• {breadth.claim_text}")

    semiconductor = _plan_item(plan, UsMarketDigestSlot.SEMICONDUCTOR_RELATIVE)
    if semiconductor is not None and semiconductor.selected and semiconductor.claim_text:
        internal_lines.append(f"• {semiconductor.claim_text}")

    sector_fact_ids: list[str] = []
    sector = _plan_item(plan, UsMarketDigestSlot.SECTOR_DISPERSION)
    if sector is not None and sector.selected:
        sector_facts = [
            fact
            for ref in sector.evidence_refs
            if (fact := next((row for row in facts if _fact_id(row) == ref), None)) is not None
        ]
        sector_values = [
            (fact, _current_return(fact))
            for fact in sector_facts
            if _current_return(fact) is not None
        ]
        if len(sector_values) == 2:
            leader, laggard = sector_values
            leader_label = str(_fields(leader[0]).get("label") or _series(leader[0]))
            laggard_label = str(_fields(laggard[0]).get("label") or _series(laggard[0]))
            internal_lines.extend(
                (
                    f"• 업종 강세: {leader_label} {_format_pct(leader[1])}",
                    f"• 업종 약세: {laggard_label} {_format_pct(laggard[1])}",
                )
            )
            sector_fact_ids.extend(_fact_id(fact) for fact, _value in sector_values)
        else:
            errors.append("selected_sector_numeric_incomplete")
    if not internal_lines:
        errors.append("market_internal_empty")

    night_lines: list[str] = []
    night_fact_ids: list[str] = []
    night_rows = _mapping(context).get("night_futures", [])
    if isinstance(night_rows, list):
        for row in night_rows:
            if not isinstance(row, Mapping):
                continue
            series = str(row.get("series_code") or "")
            value = _number(row.get("change_pct"))
            label = NIGHT_LABELS.get(series)
            expected_fact_id = NIGHT_FUTURES_FACT_IDS.get(series)
            if (
                label is None
                or value is None
                or row.get("fact_id") != expected_fact_id
                or row.get("field_path") != "fields.change_pct"
                or row.get("state") != "CURRENT_DIRECTIONAL"
            ):
                continue
            timeframe_block = _night_timeframe_block(row, series=series)
            if timeframe_block is not None:
                text, fact_ids = timeframe_block
                night_lines.append(text)
                night_fact_ids.extend(fact_ids)
                continue
            night_lines.append(f"• {label} {_format_pct(value)}")
            night_fact_ids.append(str(row["fact_id"]))

    macro_lines: list[str] = []
    real_yield_fact = by_series.get("DFII10")
    real_yield_claim = (
        render_specific_macro_claim(real_yield_fact) if real_yield_fact is not None else ""
    )
    if "직전" in real_yield_claim and "%p" in real_yield_claim:
        macro_lines.append(f"• {real_yield_claim}")
    macro = _plan_item(plan, UsMarketDigestSlot.MACRO_CONTEXT)
    macro_fact = _safe_macro_fact(macro, by_id) if macro is not None else None
    if (
        macro is not None
        and macro.omission_reason == DigestOmissionReason.SELECTED
        and macro_fact is not None
        and _fact_id(macro_fact) != _fact_id(real_yield_fact or {})
    ):
        macro_claim = render_specific_macro_claim(macro_fact)
        macro_role = str(_fields(macro_fact).get("temporal_role") or "")
        macro_date = str(macro_fact.get("as_of_date") or "")
        date_prefix = ""
        if macro_role != "CURRENT_OBSERVATION":
            date_prefix = f"공식 관측({macro_date}) 기준, "
        macro_lines.append(f"• {date_prefix}{macro_claim}")

    checks = _safe_next_checks(next_checks)
    if not checks:
        checks = ("다음 완료 세션의 주요 지수·동일가중·업종 분산이 이어지는지 확인합니다.",)

    blocks = ["🇺🇸 미국시장 마감", "📈 주요 지수\n" + "\n".join(index_lines)]
    section_order = ["HEADER", "INDEX_BLOCK"]
    blocks.append("🔎 시장 내부\n" + "\n".join(internal_lines))
    section_order.append("MARKET_INTERNAL")
    if night_lines:
        blocks.append("🌙 한국 야간선물\n" + "\n".join(night_lines))
        section_order.append("NIGHT_FUTURES")
    if macro_lines:
        blocks.append("🌐 보조 시장환경\n" + "\n".join(macro_lines))
        section_order.append("MACRO_CONTEXT")
    blocks.append("📌 다음 확인\n" + "\n".join(f"• {item}" for item in checks))
    section_order.append("NEXT_CHECK")
    text = "\n\n".join(blocks)

    for symbol in index_fact_ids:
        if not symbol:
            errors.append("index_fact_id_missing")
    if text.count("📈 주요 지수") != 1 or text.count("🔎 시장 내부") != 1:
        errors.append("required_section_count_invalid")
    if text.count("📌 다음 확인") != 1:
        errors.append("next_check_section_count_invalid")
    return UsFullMessageRender(
        contract=CONTRACT_VERSION,
        text=text,
        index_fact_ids=tuple(index_fact_ids),
        sector_fact_ids=tuple(sector_fact_ids),
        night_fact_ids=tuple(night_fact_ids),
        section_order=tuple(section_order),
        validation_errors=tuple(dict.fromkeys(errors)),
    )


def preserve_us_full_message_layout(
    candidate_text: str,
    *,
    deterministic_text: str,
) -> str:
    """Keep deterministic market sections while retaining a bounded AI next check."""
    if not all(
        heading in deterministic_text
        for heading in ("📈 주요 지수", "🔎 시장 내부", "📌 다음 확인")
    ):
        return candidate_text
    marker = "📌 다음 확인\n"
    candidate_index = candidate_text.find(marker)
    deterministic_index = deterministic_text.find(marker)
    if candidate_index < 0 or deterministic_index < 0:
        return deterministic_text
    candidate_next = candidate_text[candidate_index:].strip()
    if not candidate_next or len(candidate_next) > 700:
        return deterministic_text
    return deterministic_text[:deterministic_index].rstrip() + "\n\n" + candidate_next
