from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Iterable, Mapping


CONTRACT_VERSION = "us-market-digest-plan-v1"
SUPPORTED_MACRO_FACT_TYPES = frozenset(
    {
        "market_nominal_yield",
        "market_real_yield",
        "market_breakeven_inflation",
        "market_credit_spread",
        "market_fx",
        "market_oil",
        "market_volatility",
        "market_dollar_index",
    }
)


class UsMarketDigestSlot(StrEnum):
    CURRENT_MARKET = "CURRENT_MARKET"
    PARTICIPATION_STYLE = "PARTICIPATION_STYLE"
    SECTOR_DISPERSION = "SECTOR_DISPERSION"
    BREADTH_STATE = "BREADTH_STATE"
    MACRO_CONTEXT = "MACRO_CONTEXT"


class DigestOmissionReason(StrEnum):
    SELECTED = "SELECTED"
    OMITTED_SAFE_NOT_MATERIAL = "OMITTED_SAFE_NOT_MATERIAL"
    OMITTED_SAFE_LENGTH_BUDGET = "OMITTED_SAFE_LENGTH_BUDGET"
    OMITTED_UNAVAILABLE = "OMITTED_UNAVAILABLE"
    OMITTED_TEMPORAL = "OMITTED_TEMPORAL"


@dataclass(frozen=True)
class UsMarketDigestPlanItem:
    slot: UsMarketDigestSlot
    priority: int
    claim_text: str
    evidence_refs: tuple[str, ...]
    numeric_refs: tuple[str, ...]
    observation_dates: tuple[str, ...]
    temporal_roles: tuple[str, ...]
    materiality: str
    omission_reason: DigestOmissionReason
    required_consumption: bool

    @property
    def selected(self) -> bool:
        return self.omission_reason == DigestOmissionReason.SELECTED


@dataclass(frozen=True)
class UsMarketDigestPlan:
    contract: str
    market: str
    items: tuple[UsMarketDigestPlanItem, ...]

    def selected_items(self) -> tuple[UsMarketDigestPlanItem, ...]:
        return tuple(item for item in self.items if item.selected)

    def required_items(self) -> tuple[UsMarketDigestPlanItem, ...]:
        return tuple(
            item for item in self.items if item.selected and item.required_consumption
        )

    def primary_claims(self) -> tuple[UsMarketDigestPlanItem, ...]:
        return tuple(
            item
            for item in self.required_items()
            if item.slot != UsMarketDigestSlot.MACRO_CONTEXT
        )

    def required_evidence_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                ref for item in self.required_items() for ref in item.evidence_refs
            )
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: object) -> UsMarketDigestPlan | None:
        if not isinstance(value, Mapping) or value.get("contract") != CONTRACT_VERSION:
            return None
        raw_items = value.get("items")
        if not isinstance(raw_items, (list, tuple)):
            return None
        items: list[UsMarketDigestPlanItem] = []
        try:
            for raw in raw_items:
                if not isinstance(raw, Mapping):
                    return None
                items.append(
                    UsMarketDigestPlanItem(
                        slot=UsMarketDigestSlot(str(raw["slot"])),
                        priority=int(raw["priority"]),
                        claim_text=str(raw.get("claim_text") or ""),
                        evidence_refs=_strings(raw.get("evidence_refs")),
                        numeric_refs=_strings(raw.get("numeric_refs")),
                        observation_dates=_strings(raw.get("observation_dates")),
                        temporal_roles=_strings(raw.get("temporal_roles")),
                        materiality=str(raw.get("materiality") or ""),
                        omission_reason=DigestOmissionReason(
                            str(raw["omission_reason"])
                        ),
                        required_consumption=bool(raw.get("required_consumption")),
                    )
                )
        except (KeyError, TypeError, ValueError):
            return None
        return cls(
            contract=CONTRACT_VERSION,
            market=str(value.get("market") or "US"),
            items=tuple(items),
        )


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _facts(value: object) -> list[dict[str, object]]:
    if isinstance(value, Mapping):
        value = value.get("fact_catalog", [])
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _fields(fact: Mapping[str, object]) -> dict[str, object]:
    value = fact.get("fields")
    return dict(value) if isinstance(value, Mapping) else {}


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _series(fact: Mapping[str, object]) -> str:
    fields = _fields(fact)
    return str(fields.get("series_code") or fields.get("symbol") or "")


def _fact_ref(fact: Mapping[str, object]) -> str:
    return str(fact.get("fact_id") or "")


def _date(fact: Mapping[str, object]) -> str:
    return str(fact.get("as_of_date") or "")


def _role(fact: Mapping[str, object]) -> str:
    return str(_fields(fact).get("temporal_role") or "UNKNOWN")


def _current_directional(fact: Mapping[str, object]) -> bool:
    fields = _fields(fact)
    return bool(
        fields.get("today_signal_eligible") is True
        and fields.get("structured_state") == "CURRENT_DIRECTIONAL"
        and _number(fields.get("return_pct")) is not None
    )


def macro_fact_change(
    fact: Mapping[str, object],
) -> tuple[str, float] | None:
    if fact.get("fact_type") not in SUPPORTED_MACRO_FACT_TYPES:
        return None
    fields = _fields(fact)
    for field in ("change_bp", "return_pct", "change_pct"):
        value = _number(fields.get(field))
        if value is not None:
            return field, value
    return None


def render_specific_macro_claim(fact: Mapping[str, object]) -> str:
    """Render one canonical macro Fact without concatenating status labels."""
    change = macro_fact_change(fact)
    fields = _fields(fact)
    label = str(fields.get("label") or "").strip()
    if change is None or not label or label in {"거시 지표", "보조 거시 맥락"}:
        return ""
    _field, value = change
    if value == 0:
        return f"{label}는 전 세션과 큰 변화가 없었습니다."
    direction = "상승했습니다" if value > 0 else "하락했습니다"
    return f"{label}는 {direction}."


def _labels_by_direction(
    facts: Iterable[Mapping[str, object]],
) -> tuple[list[str], list[str], list[str]]:
    positive: list[str] = []
    negative: list[str] = []
    unchanged: list[str] = []
    for fact in facts:
        fields = _fields(fact)
        label = str(fields.get("label") or _series(fact))
        value = _number(fields.get("return_pct"))
        if value is None:
            continue
        if value > 0:
            positive.append(label)
        elif value < 0:
            negative.append(label)
        else:
            unchanged.append(label)
    return positive, negative, unchanged


def _direction_claim(prefix: str, facts: list[dict[str, object]]) -> str:
    positive, negative, unchanged = _labels_by_direction(facts)
    clauses: list[str] = []
    if positive:
        clauses.append(f"상승은 {'·'.join(positive)}")
    if negative:
        clauses.append(f"하락은 {'·'.join(negative)}")
    if unchanged:
        clauses.append(f"보합은 {'·'.join(unchanged)}")
    return f"{prefix} {', '.join(clauses)}이었습니다." if clauses else ""


def _numeric_refs(facts: Iterable[Mapping[str, object]], field: str) -> tuple[str, ...]:
    return tuple(
        f"{ref}#fields.{field}"
        for fact in facts
        if (ref := _fact_ref(fact)) and _number(_fields(fact).get(field)) is not None
    )


def _item(
    slot: UsMarketDigestSlot,
    priority: int,
    *,
    facts: Iterable[Mapping[str, object]] = (),
    claim_text: str = "",
    materiality: str,
    omission_reason: DigestOmissionReason,
    required_consumption: bool,
    numeric_field: str = "return_pct",
) -> UsMarketDigestPlanItem:
    rows = list(facts)
    return UsMarketDigestPlanItem(
        slot=slot,
        priority=priority,
        claim_text=claim_text,
        evidence_refs=tuple(
            dict.fromkeys(ref for fact in rows if (ref := _fact_ref(fact)))
        ),
        numeric_refs=_numeric_refs(rows, numeric_field),
        observation_dates=tuple(
            dict.fromkeys(value for fact in rows if (value := _date(fact)))
        ),
        temporal_roles=tuple(
            dict.fromkeys(value for fact in rows if (value := _role(fact)))
        ),
        materiality=materiality,
        omission_reason=omission_reason,
        required_consumption=required_consumption,
    )


def _current_market_item(facts: list[dict[str, object]]) -> UsMarketDigestPlanItem:
    order = {symbol: index for index, symbol in enumerate(("SPY", "QQQ", "IWM", "SOXX"))}
    current = sorted(
        (
            fact
            for fact in facts
            if _series(fact) in order and _current_directional(fact)
        ),
        key=lambda fact: order[_series(fact)],
    )
    if not current:
        temporal = [fact for fact in facts if _series(fact) in order]
        return _item(
            UsMarketDigestSlot.CURRENT_MARKET,
            1,
            facts=temporal,
            materiality="current-session core ETF cross-section is unavailable",
            omission_reason=(
                DigestOmissionReason.OMITTED_TEMPORAL
                if temporal
                else DigestOmissionReason.OMITTED_UNAVAILABLE
            ),
            required_consumption=False,
        )
    return _item(
        UsMarketDigestSlot.CURRENT_MARKET,
        1,
        facts=current,
        claim_text=_direction_claim("현재 세션에서", current),
        materiality=(
            "current-session cross-section remains primary even when returns are near flat"
        ),
        omission_reason=DigestOmissionReason.SELECTED,
        required_consumption=True,
    )


def _style_item(facts: list[dict[str, object]]) -> UsMarketDigestPlanItem:
    rsp = next(
        (fact for fact in facts if _series(fact) == "RSP" and _current_directional(fact)),
        None,
    )
    if rsp is None:
        candidates = [fact for fact in facts if _series(fact) == "RSP"]
        return _item(
            UsMarketDigestSlot.PARTICIPATION_STYLE,
            2,
            facts=candidates,
            materiality="equal-weight participation proxy is unavailable",
            omission_reason=(
                DigestOmissionReason.OMITTED_TEMPORAL
                if candidates
                else DigestOmissionReason.OMITTED_UNAVAILABLE
            ),
            required_consumption=False,
        )
    spx = next(
        (fact for fact in facts if _series(fact) == "SPY" and _current_directional(fact)),
        None,
    )
    rows = [rsp, *([spx] if spx is not None else [])]
    rsp_value = _number(_fields(rsp).get("return_pct")) or 0.0
    rsp_direction = "상승" if rsp_value > 0 else "하락" if rsp_value < 0 else "보합"
    if spx is None:
        text = f"동일가중 S&P500은 {rsp_direction}했습니다."
    else:
        spx_value = _number(_fields(spx).get("return_pct")) or 0.0
        aligned = (
            (rsp_value > 0) == (spx_value > 0)
            if rsp_value and spx_value
            else rsp_value == spx_value
        )
        relation = "같았습니다" if aligned else "엇갈렸습니다"
        text = (
            f"동일가중 S&P500은 {rsp_direction}해 시가총액가중 S&P500과 "
            f"방향이 {relation}."
        )
    return _item(
        UsMarketDigestSlot.PARTICIPATION_STYLE,
        2,
        facts=rows,
        claim_text=text,
        materiality="RSP is a participation-style proxy, not market breadth",
        omission_reason=DigestOmissionReason.SELECTED,
        required_consumption=True,
    )


def _sector_item(facts: list[dict[str, object]]) -> UsMarketDigestPlanItem:
    sectors = [
        fact
        for fact in facts
        if fact.get("fact_type") == "market_sector"
        and _series(fact) != "SOXX"
        and _current_directional(fact)
    ]
    if len(sectors) < 2:
        candidates = [
            fact
            for fact in facts
            if fact.get("fact_type") == "market_sector" and _series(fact) != "SOXX"
        ]
        return _item(
            UsMarketDigestSlot.SECTOR_DISPERSION,
            3,
            facts=candidates,
            materiality="fewer than two current directional sector proxies are available",
            omission_reason=(
                DigestOmissionReason.OMITTED_TEMPORAL
                if candidates
                else DigestOmissionReason.OMITTED_UNAVAILABLE
            ),
            required_consumption=False,
        )
    leader = max(sectors, key=lambda fact: float(_fields(fact)["return_pct"]))
    laggard = min(sectors, key=lambda fact: float(_fields(fact)["return_pct"]))
    selected = [leader, laggard]
    return _item(
        UsMarketDigestSlot.SECTOR_DISPERSION,
        3,
        facts=selected,
        claim_text=(
            f"업종 프록시에서는 {_fields(leader).get('label')}가 가장 강했고 "
            f"{_fields(laggard).get('label')}가 가장 약했습니다."
        ),
        materiality="bounded current-session leader and laggard preserve sector dispersion",
        omission_reason=DigestOmissionReason.SELECTED,
        required_consumption=True,
    )


def _breadth_item(
    facts: list[dict[str, object]],
    coverage: Mapping[str, object] | None,
) -> UsMarketDigestPlanItem:
    counts = next(
        (fact for fact in facts if fact.get("fact_type") == "market_breadth_counts"),
        None,
    )
    if counts is None:
        status = None
        if isinstance(coverage, Mapping) and isinstance(coverage.get("breadth"), Mapping):
            status = coverage["breadth"].get("status")
        return _item(
            UsMarketDigestSlot.BREADTH_STATE,
            4,
            materiality=f"official breadth state is {status or 'unavailable'}",
            omission_reason=DigestOmissionReason.OMITTED_UNAVAILABLE,
            required_consumption=False,
        )
    fields = _fields(counts)
    advance = _number(fields.get("advance_count"))
    decline = _number(fields.get("decline_count"))
    if advance is None or decline is None:
        return _item(
            UsMarketDigestSlot.BREADTH_STATE,
            4,
            facts=[counts],
            materiality="breadth counts are incomplete",
            omission_reason=DigestOmissionReason.OMITTED_UNAVAILABLE,
            required_consumption=False,
        )
    relation = (
        "많았습니다"
        if advance > decline
        else "적었습니다"
        if advance < decline
        else "같았습니다"
    )
    return _item(
        UsMarketDigestSlot.BREADTH_STATE,
        4,
        facts=[counts],
        claim_text=f"공식 breadth에서 상승 종목 수는 하락 종목 수보다 {relation}.",
        materiality="official issue-level participation is distinct from RSP",
        omission_reason=DigestOmissionReason.SELECTED,
        required_consumption=True,
        numeric_field="advance_count",
    )


def _macro_item(
    facts: list[dict[str, object]],
    key_change_fact_ids: Iterable[str],
) -> UsMarketDigestPlanItem:
    by_id = {_fact_ref(fact): fact for fact in facts}
    selected = next(
        (
            by_id[ref]
            for ref in key_change_fact_ids
            if ref in by_id
            and by_id[ref].get("fact_type") in SUPPORTED_MACRO_FACT_TYPES
        ),
        None,
    )
    if selected is None:
        return _item(
            UsMarketDigestSlot.MACRO_CONTEXT,
            5,
            materiality="no additional macro change passed the existing selection policy",
            omission_reason=DigestOmissionReason.OMITTED_SAFE_NOT_MATERIAL,
            required_consumption=False,
        )
    change = macro_fact_change(selected)
    if change is None or change[1] == 0:
        return _item(
            UsMarketDigestSlot.MACRO_CONTEXT,
            5,
            facts=[selected],
            materiality="generic zero-change macro is not decision-material",
            omission_reason=DigestOmissionReason.OMITTED_SAFE_NOT_MATERIAL,
            required_consumption=False,
            numeric_field=change[0] if change is not None else "return_pct",
        )
    claim_text = render_specific_macro_claim(selected)
    if not claim_text:
        return _item(
            UsMarketDigestSlot.MACRO_CONTEXT,
            5,
            facts=[selected],
            materiality="macro semantic label or change field is not safely renderable",
            omission_reason=DigestOmissionReason.OMITTED_SAFE_NOT_MATERIAL,
            required_consumption=False,
            numeric_field=change[0],
        )
    return _item(
        UsMarketDigestSlot.MACRO_CONTEXT,
        5,
        facts=[selected],
        claim_text=claim_text,
        materiality="macro is retained only after current-session market structure",
        omission_reason=DigestOmissionReason.SELECTED,
        required_consumption=False,
        numeric_field=change[0],
    )


def build_us_market_digest_plan(value: object) -> UsMarketDigestPlan:
    context = value if isinstance(value, Mapping) else {}
    facts = _facts(value)
    key_changes = _strings(context.get("key_change_fact_ids"))
    coverage = (
        context.get("coverage")
        if isinstance(context.get("coverage"), Mapping)
        else None
    )
    items = (
        _current_market_item(facts),
        _style_item(facts),
        _sector_item(facts),
        _breadth_item(facts, coverage),
        _macro_item(facts, key_changes),
    )
    return UsMarketDigestPlan(contract=CONTRACT_VERSION, market="US", items=items)


def market_digest_plan_from_context(value: object) -> UsMarketDigestPlan | None:
    if not isinstance(value, Mapping):
        return None
    stored = UsMarketDigestPlan.from_dict(value.get("us_market_digest_plan"))
    return stored or build_us_market_digest_plan(value)
