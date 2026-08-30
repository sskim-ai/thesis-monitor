from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable, Mapping


CONTRACT_VERSION = "market-evidence-utilization-validator-v1"
US_PLAN_CONTRACT = "us-market-digest-plan-v1"
KR_PLAN_CONTRACT = "kr-market-digest-quality-v1"

_REQUIRED_SLOT_ERRORS = {
    "CURRENT_MARKET": "CORE_MARKET_SLOT_UNCONSUMED",
    "PARTICIPATION_STYLE": "SELECTED_RSP_SLOT_UNCONSUMED",
    "SMALL_CAP_RELATIVE": "SELECTED_IWM_RELATIVE_SLOT_UNCONSUMED",
    "SEMICONDUCTOR_RELATIVE": "SELECTED_SOXX_RELATIVE_SLOT_UNCONSUMED",
    "SECTOR_DISPERSION": "SELECTED_SECTOR_DISPERSION_UNCONSUMED",
    "BREADTH_STATE": "SELECTED_BREADTH_SLOT_UNCONSUMED",
}
_ALLOWED_OMISSION_REASONS = {
    "SELECTED",
    "OMITTED_SAFE_NOT_MATERIAL",
    "OMITTED_SAFE_LENGTH_BUDGET",
    "OMITTED_UNAVAILABLE",
    "OMITTED_TEMPORAL",
}
_ALLOWED_KR_SELECTION_STATES = {
    "SELECTED_REQUIRED",
    "SOURCE_UNAVAILABLE",
    "WRONG_SESSION",
    "INVALID_SEMANTIC",
    "NO_VALID_ROWS",
}


@dataclass(frozen=True)
class SlotUtilization:
    slot: str
    selected: bool
    required_consumption: bool
    evidence_refs: tuple[str, ...]
    consumed_refs: tuple[str, ...]
    status: str
    omission_reason: str


@dataclass(frozen=True)
class MarketEvidenceUtilizationResult:
    contract: str
    status: str
    errors: tuple[str, ...]
    slot_results: tuple[SlotUtilization, ...]
    counters: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(dict.fromkeys(str(item) for item in value if str(item)))


def _plan_items(plan: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(plan, Mapping) or plan.get("contract") != US_PLAN_CONTRACT:
        return ()
    items = plan.get("items")
    if not isinstance(items, (list, tuple)):
        return ()
    return tuple(item for item in items if isinstance(item, Mapping))


def _slot_consumed(
    slot: str,
    refs: tuple[str, ...],
    interpretation_refs: set[str],
) -> tuple[bool, tuple[str, ...]]:
    consumed = tuple(ref for ref in refs if ref in interpretation_refs)
    if slot == "CURRENT_MARKET":
        return bool(consumed), consumed
    if slot == "PARTICIPATION_STYLE":
        return bool(refs and refs[0] in interpretation_refs), consumed
    if slot in {
        "SMALL_CAP_RELATIVE",
        "SEMICONDUCTOR_RELATIVE",
        "SECTOR_DISPERSION",
    }:
        return bool(refs and set(refs).issubset(interpretation_refs)), consumed
    return bool(consumed), consumed


def validate_us_market_evidence_utilization(
    plan: object,
    *,
    facts_used: Iterable[str],
    interpretation_fact_ids: Iterable[str],
) -> MarketEvidenceUtilizationResult:
    items = _plan_items(plan)
    used = set(_strings(tuple(facts_used)))
    interpreted = set(_strings(tuple(interpretation_fact_ids)))
    errors: list[str] = []
    rows: list[SlotUtilization] = []
    if not items:
        errors.append("US_MARKET_DIGEST_PLAN_MISSING")

    selected_macro_refs: set[str] = set()
    selected_current_refs: set[str] = set()
    for item in items:
        slot = str(item.get("slot") or "")
        omission_reason = str(item.get("omission_reason") or "")
        required = bool(item.get("required_consumption"))
        selected = omission_reason == "SELECTED"
        refs = _strings(item.get("evidence_refs"))
        if omission_reason not in _ALLOWED_OMISSION_REASONS:
            errors.append(f"UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION:{slot}")
        if selected and not refs:
            errors.append(f"UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION:{slot}")
        consumed, consumed_refs = _slot_consumed(slot, refs, interpreted)
        if selected and required and not consumed:
            errors.append(_REQUIRED_SLOT_ERRORS.get(slot, f"SELECTED_{slot}_UNCONSUMED"))
        undeclared = set(consumed_refs) - used
        if undeclared:
            errors.append(
                f"PLAN_EVIDENCE_NOT_DECLARED_USED:{slot}:" + ",".join(sorted(undeclared))
            )
        if slot == "MACRO_CONTEXT" and selected:
            selected_macro_refs.update(refs)
        if slot == "CURRENT_MARKET" and selected:
            selected_current_refs.update(refs)
        rows.append(
            SlotUtilization(
                slot=slot,
                selected=selected,
                required_consumption=required,
                evidence_refs=refs,
                consumed_refs=consumed_refs,
                status=(
                    "PASS"
                    if not selected or not required or consumed
                    else "FAIL"
                ),
                omission_reason=omission_reason,
            )
        )

    if (
        selected_current_refs
        and not (selected_current_refs & interpreted)
        and selected_macro_refs & interpreted
    ):
        errors.append("MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE")

    unique_errors = tuple(dict.fromkeys(errors))
    names = {error.split(":", 1)[0] for error in unique_errors}
    counters = {
        "CORE_MARKET_SLOT_UNCONSUMED": int("CORE_MARKET_SLOT_UNCONSUMED" in names),
        "SELECTED_RSP_SLOT_UNCONSUMED": int(
            "SELECTED_RSP_SLOT_UNCONSUMED" in names
        ),
        "SELECTED_IWM_RELATIVE_SLOT_UNCONSUMED": int(
            "SELECTED_IWM_RELATIVE_SLOT_UNCONSUMED" in names
        ),
        "SELECTED_SOXX_RELATIVE_SLOT_UNCONSUMED": int(
            "SELECTED_SOXX_RELATIVE_SLOT_UNCONSUMED" in names
        ),
        "SELECTED_SECTOR_DISPERSION_UNCONSUMED": int(
            "SELECTED_SECTOR_DISPERSION_UNCONSUMED" in names
        ),
        "SELECTED_BREADTH_SLOT_UNCONSUMED": int(
            "SELECTED_BREADTH_SLOT_UNCONSUMED" in names
        ),
        "MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE": int(
            "MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE" in names
        ),
        "UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION": int(
            "UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION" in names
        ),
        "VALIDATOR_FORCED_NUMERIC_DUMP": 0,
        "US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS": sum(
            row.status == "FAIL" for row in rows
        ),
    }
    return MarketEvidenceUtilizationResult(
        contract=CONTRACT_VERSION,
        status="PASS" if not unique_errors else "FAIL",
        errors=unique_errors,
        slot_results=tuple(rows),
        counters=counters,
    )


def _normalized_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _kr_plan(value: object) -> Mapping[str, object] | None:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping) or value.get("contract") != KR_PLAN_CONTRACT:
        return None
    return value


def validate_kr_market_evidence_utilization(
    plan: object,
    *,
    rendered_text: str,
) -> MarketEvidenceUtilizationResult:
    value = _kr_plan(plan)
    errors: list[str] = []
    rows: list[SlotUtilization] = []
    if value is None:
        errors.append("KR_MARKET_DIGEST_PLAN_MISSING")
        value = {}

    rendered = _normalized_text(rendered_text)
    for slot, claim_key, state_key, missing_error in (
        (
            "SIZE_STYLE",
            "size_context",
            "size_style_state",
            "SIZE_STYLE_AVAILABLE_BUT_OMITTED",
        ),
        (
            "SECTOR_EXTREMES",
            "sector_context",
            "sector_extremes_state",
            "SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED",
        ),
    ):
        state = str(value.get(state_key) or "")
        claim = value.get(claim_key)
        claim_map = claim if isinstance(claim, Mapping) else {}
        claim_text = _normalized_text(claim_map.get("text"))
        refs = _strings(claim_map.get("source_refs"))
        selected = state == "SELECTED_REQUIRED"
        consumed = bool(selected and claim_text and claim_text in rendered)
        if state not in _ALLOWED_KR_SELECTION_STATES:
            errors.append(f"UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION:{slot}")
        if selected and (not claim_text or not refs):
            errors.append(f"UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION:{slot}")
        if selected and not consumed:
            errors.append(missing_error)
        rows.append(
            SlotUtilization(
                slot=slot,
                selected=selected,
                required_consumption=selected,
                evidence_refs=refs,
                consumed_refs=refs if consumed else (),
                status="PASS" if not selected or consumed else "FAIL",
                omission_reason=state,
            )
        )

    if re.search(r"(?<![A-Za-z])(leader|laggard)(?![A-Za-z])", rendered_text, re.I):
        errors.append("USER_FACING_LEADER_LAGGARD_TERM")
    unique_errors = tuple(dict.fromkeys(errors))
    names = {error.split(":", 1)[0] for error in unique_errors}
    counters = {
        "SIZE_STYLE_AVAILABLE_BUT_OMITTED": int(
            "SIZE_STYLE_AVAILABLE_BUT_OMITTED" in names
        ),
        "SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED": int(
            "SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED" in names
        ),
        "GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_SIZE_SECTOR": int(
            bool(
                names
                & {
                    "SIZE_STYLE_AVAILABLE_BUT_OMITTED",
                    "SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED",
                }
                and re.search(r"(?:미국|글로벌|해외)", rendered_text)
            )
        ),
        "USER_FACING_LEADER_LAGGARD_TERM": int(
            "USER_FACING_LEADER_LAGGARD_TERM" in names
        ),
        "KR_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS": sum(
            row.status == "FAIL" for row in rows
        ),
        "VALIDATOR_FORCED_NUMERIC_DUMP": 0,
    }
    return MarketEvidenceUtilizationResult(
        contract=CONTRACT_VERSION,
        status="PASS" if not unique_errors else "FAIL",
        errors=unique_errors,
        slot_results=tuple(rows),
        counters=counters,
    )
