from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping


CONTRACT_VERSION = "market-evidence-utilization-validator-v1"
US_PLAN_CONTRACT = "us-market-digest-plan-v1"

_REQUIRED_SLOT_ERRORS = {
    "CURRENT_MARKET": "CORE_MARKET_SLOT_UNCONSUMED",
    "PARTICIPATION_STYLE": "SELECTED_RSP_SLOT_UNCONSUMED",
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
    if slot == "SECTOR_DISPERSION":
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
