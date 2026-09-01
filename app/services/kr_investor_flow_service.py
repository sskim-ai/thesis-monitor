from __future__ import annotations

import math
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, Field


class InvestorFlowParticipant(BaseModel):
    participant_id: str
    canonical_label: str
    provider_field: str
    provider_label: str
    aggregation_role: str
    display_role: str
    source_ref: str


class InvestorFlowWindowReconciliation(BaseModel):
    window: str
    as_of_date: str | None = None
    constituent_count: int = 0
    participant_flows: dict[str, int] = Field(default_factory=dict)
    displayed_participants: list[str] = Field(default_factory=list)
    omitted_participants: list[str] = Field(default_factory=list)
    missing_participants: list[str] = Field(default_factory=list)
    displayed_net: int | None = None
    omitted_net: int | None = None
    all_participant_net: int | None = None
    provider_total: int | None = None
    reconciliation_status: str = "unavailable"
    reconciliation_difference: int | None = None
    display_coverage_ratio: float | None = None
    material_omitted_flow: bool = False
    attribution_safe: bool = False
    signal: str = "unavailable"
    signal_participants: list[str] = Field(default_factory=list)


PARTICIPANT_CONTRACT = "kr-investor-flow-participants-v1"
RECONCILIATION_CONTRACT = "kr-investor-flow-reconciliation-v1"


@dataclass(frozen=True)
class ParticipantDefinition:
    participant_id: str
    canonical_label: str
    provider_field: str
    provider_label: str
    aggregation_role: str
    display_role: str


TOP_LEVEL_PARTICIPANTS = (
    ParticipantDefinition(
        "foreign",
        "외국인",
        "foreign_net_buy_qty",
        "외국인투자자",
        "top_level",
        "displayed",
    ),
    ParticipantDefinition(
        "institution",
        "기관",
        "institution_net_buy_qty",
        "기관계",
        "top_level",
        "displayed",
    ),
    ParticipantDefinition(
        "individual",
        "개인",
        "individual_net_buy_qty",
        "개인투자자",
        "top_level",
        "displayed",
    ),
    ParticipantDefinition(
        "other_corporation",
        "기타법인",
        "other_corp_net_buy_qty",
        "기타법인",
        "top_level",
        "omitted",
    ),
    ParticipantDefinition(
        "domestic_foreign",
        "내외국인",
        "domestic_foreign_net_buy_qty",
        "내외국인",
        "top_level",
        "omitted",
    ),
)

INSTITUTION_DIAGNOSTIC_PARTICIPANTS = (
    ParticipantDefinition(
        "financial_investment",
        "금융투자",
        "financial_investment_net_buy_qty",
        "금융투자",
        "institution_subclass",
        "diagnostic",
    ),
    ParticipantDefinition(
        "insurance", "보험", "insurance_net_buy_qty", "보험", "institution_subclass", "diagnostic"
    ),
    ParticipantDefinition(
        "investment_trust",
        "투신",
        "investment_trust_net_buy_qty",
        "투신",
        "institution_subclass",
        "diagnostic",
    ),
    ParticipantDefinition(
        "other_finance",
        "기타금융",
        "other_finance_net_buy_qty",
        "기타금융",
        "institution_subclass",
        "diagnostic",
    ),
    ParticipantDefinition(
        "bank", "은행", "bank_net_buy_qty", "은행", "institution_subclass", "diagnostic"
    ),
    ParticipantDefinition(
        "pension_fund",
        "연기금 등",
        "pension_fund_net_buy_qty",
        "연기금 등",
        "institution_subclass",
        "diagnostic",
    ),
    ParticipantDefinition(
        "private_fund",
        "사모펀드",
        "private_fund_net_buy_qty",
        "사모펀드",
        "institution_subclass",
        "diagnostic",
    ),
    ParticipantDefinition(
        "government", "국가", "government_net_buy_qty", "국가", "institution_subclass", "diagnostic"
    ),
)

DISPLAYED_PARTICIPANTS = tuple(
    item.participant_id for item in TOP_LEVEL_PARTICIPANTS if item.display_role == "displayed"
)
OMITTED_PARTICIPANTS = tuple(
    item.participant_id for item in TOP_LEVEL_PARTICIPANTS if item.display_role == "omitted"
)
WINDOWS = (("1d", 1, ""), ("5d", 5, "_5"), ("20d", 20, "_20"))
PROVIDER_TOTAL_FIELD = "investor_net_buy_total_qty"


def participant_taxonomy() -> list[InvestorFlowParticipant]:
    return [
        InvestorFlowParticipant(
            participant_id=item.participant_id,
            canonical_label=item.canonical_label,
            provider_field=item.provider_field,
            provider_label=item.provider_label,
            aggregation_role=item.aggregation_role,
            display_role=item.display_role,
            source_ref=f"ohlcv_analyst.investor_flow.{item.provider_field}",
        )
        for item in (*TOP_LEVEL_PARTICIPANTS, *INSTITUTION_DIAGNOSTIC_PARTICIPANTS)
    ]


def serialized_reconciliation_payload(result: Mapping[str, object]) -> dict[str, object]:
    return json.loads(
        json.dumps(
            result,
            default=lambda value: (
                value.model_dump(mode="json") if isinstance(value, BaseModel) else value
            ),
        )
    )


def serialize_price_context_with_reconciliation(price_context: object) -> str:
    payload = price_context.model_dump(mode="json")
    supply = getattr(price_context, "supply", None)
    internal = supply.reconciliation_payload() if supply is not None else {}
    if internal and isinstance(payload.get("supply"), dict):
        payload["supply"].update(internal)
    technical_context = price_context.technical_context_payload()
    if technical_context:
        payload["technical_context"] = technical_context
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_investor_flow_reconciliation(
    bars: Sequence[Mapping[str, object]],
    *,
    provider_primary_signal: str | None = None,
) -> dict[str, object]:
    dated_rows = _dated_investor_rows(bars)
    if not dated_rows:
        return {
            "participant_contract": PARTICIPANT_CONTRACT,
            "reconciliation_contract": RECONCILIATION_CONTRACT,
            "display_scope": "major_three_participants",
            "participant_taxonomy": participant_taxonomy(),
            "reconciliations": {},
            "primary_signal": "unavailable",
            "signal_basis_window": None,
            "signal_participants": [],
            "attribution_safe": False,
            "attribution_confidence": "unavailable",
            "omitted_participant_materiality": False,
        }

    latest_date, latest = dated_rows[-1]
    reconciliations: dict[str, InvestorFlowWindowReconciliation] = {}
    diagnostic_subcomponents: dict[str, dict[str, int]] = {}
    institution_subclass_difference: dict[str, int | None] = {}
    for window, size, suffix in WINDOWS:
        participant_flows: dict[str, int] = {}
        constituent_count = min(len(dated_rows), size)
        for item in TOP_LEVEL_PARTICIPANTS:
            value = _window_value(
                dated_rows,
                latest,
                item.provider_field,
                size=size,
                suffix=suffix,
            )
            if value is not None:
                participant_flows[item.participant_id] = value
        reconciliations[window] = _reconcile_window(
            window=window,
            as_of_date=latest_date.isoformat(),
            constituent_count=constituent_count,
            participant_flows=participant_flows,
            provider_total=_integer(latest.get(f"{PROVIDER_TOTAL_FIELD}{suffix}")),
        )
        diagnostics = {}
        for item in INSTITUTION_DIAGNOSTIC_PARTICIPANTS:
            value = _window_value(
                dated_rows,
                latest,
                item.provider_field,
                size=size,
                suffix=suffix,
            )
            if value is not None:
                diagnostics[item.participant_id] = value
        diagnostic_subcomponents[window] = diagnostics
        institution = participant_flows.get("institution")
        institution_subclass_difference[window] = (
            institution - sum(diagnostics.values())
            if institution is not None
            and len(diagnostics) == len(INSTITUTION_DIAGNOSTIC_PARTICIPANTS)
            else None
        )

    primary = _select_primary_signal(
        reconciliations,
        provider_primary_signal=provider_primary_signal,
    )
    latest_values = {
        f"{item.provider_field}{suffix}": reconciliation.participant_flows.get(item.participant_id)
        for window, _size, suffix in WINDOWS
        for item in TOP_LEVEL_PARTICIPANTS
        if (reconciliation := reconciliations[window])
    }
    return {
        "participant_contract": PARTICIPANT_CONTRACT,
        "reconciliation_contract": RECONCILIATION_CONTRACT,
        "display_scope": "major_three_participants",
        "participant_taxonomy": participant_taxonomy(),
        "reconciliations": reconciliations,
        "diagnostic_subcomponents": diagnostic_subcomponents,
        "institution_subclass_difference": institution_subclass_difference,
        "primary_signal": primary["signal"],
        "signal_basis_window": primary["basis_window"],
        "signal_participants": primary["participants"],
        "attribution_safe": primary["attribution_safe"],
        "attribution_confidence": primary["confidence"],
        "omitted_participant_materiality": any(
            item.material_omitted_flow for item in reconciliations.values()
        ),
        **latest_values,
    }


def _dated_investor_rows(
    bars: Sequence[Mapping[str, object]],
) -> list[tuple[date, dict[str, object]]]:
    rows: dict[date, dict[str, object]] = {}
    for bar in bars:
        raw_date = bar.get("date")
        try:
            observed = date.fromisoformat(str(raw_date)[:10])
        except (TypeError, ValueError):
            continue
        values = dict(bar)
        nested = bar.get("investor_flow")
        if isinstance(nested, Mapping):
            values.update(nested)
        if any(
            _integer(values.get(item.provider_field)) is not None for item in TOP_LEVEL_PARTICIPANTS
        ):
            rows[observed] = values
    return sorted(rows.items())


def _window_value(
    dated_rows: Sequence[tuple[date, Mapping[str, object]]],
    latest: Mapping[str, object],
    field: str,
    *,
    size: int,
    suffix: str,
) -> int | None:
    if suffix:
        supplied = _integer(latest.get(f"{field}{suffix}"))
        if supplied is not None:
            return supplied
    selected = dated_rows[-size:]
    if len(selected) != size:
        return None
    values = [_integer(row.get(field)) for _observed, row in selected]
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def _reconcile_window(
    *,
    window: str,
    as_of_date: str,
    constituent_count: int,
    participant_flows: Mapping[str, int],
    provider_total: int | None = None,
) -> InvestorFlowWindowReconciliation:
    missing = [
        item.participant_id
        for item in TOP_LEVEL_PARTICIPANTS
        if item.participant_id not in participant_flows
    ]
    displayed_complete = all(item in participant_flows for item in DISPLAYED_PARTICIPANTS)
    omitted_complete = all(item in participant_flows for item in OMITTED_PARTICIPANTS)
    displayed_net = (
        sum(participant_flows[item] for item in DISPLAYED_PARTICIPANTS)
        if displayed_complete
        else None
    )
    omitted_net = (
        sum(participant_flows[item] for item in OMITTED_PARTICIPANTS) if omitted_complete else None
    )
    complete = displayed_complete and omitted_complete
    all_net = sum(participant_flows.values()) if complete else None
    gross = sum(abs(value) for value in participant_flows.values()) if complete else 0
    displayed_gross = (
        sum(abs(participant_flows[item]) for item in DISPLAYED_PARTICIPANTS) if complete else 0
    )
    coverage = round(displayed_gross / gross, 6) if gross else (1.0 if complete else None)
    material_omitted = _omitted_is_material(participant_flows, displayed_net, omitted_net, complete)
    signal, signal_participants = _window_signal(participant_flows, complete, material_omitted)
    difference = (
        all_net - provider_total if all_net is not None and provider_total is not None else None
    )
    if not complete:
        status = "partial_participant_coverage"
    elif provider_total is None:
        status = "complete_without_provider_total"
    elif difference == 0:
        status = "reconciled_to_provider_total"
    else:
        status = "provider_total_conflict"
    return InvestorFlowWindowReconciliation(
        window=window,
        as_of_date=as_of_date,
        constituent_count=constituent_count,
        participant_flows=dict(participant_flows),
        displayed_participants=list(DISPLAYED_PARTICIPANTS),
        omitted_participants=list(OMITTED_PARTICIPANTS),
        missing_participants=missing,
        displayed_net=displayed_net,
        omitted_net=omitted_net,
        all_participant_net=all_net,
        provider_total=provider_total,
        reconciliation_status=status,
        reconciliation_difference=difference,
        display_coverage_ratio=coverage,
        material_omitted_flow=material_omitted,
        attribution_safe=complete and not material_omitted and difference in {None, 0},
        signal=signal,
        signal_participants=signal_participants,
    )


def _omitted_is_material(
    participant_flows: Mapping[str, int],
    displayed_net: int | None,
    omitted_net: int | None,
    complete: bool,
) -> bool:
    if not complete or omitted_net in {None, 0}:
        return False
    displayed_nonzero = [
        abs(participant_flows[item])
        for item in DISPLAYED_PARTICIPANTS
        if participant_flows[item] != 0
    ]
    if not displayed_nonzero:
        return True
    changes_side_balance = displayed_net == 0 or displayed_net * omitted_net < 0
    matches_or_exceeds_displayed_actor = abs(omitted_net) >= min(displayed_nonzero)
    return changes_side_balance or matches_or_exceeds_displayed_actor


def _window_signal(
    participant_flows: Mapping[str, int],
    complete: bool,
    material_omitted: bool,
) -> tuple[str, list[str]]:
    foreign = participant_flows.get("foreign")
    institution = participant_flows.get("institution")
    individual = participant_flows.get("individual")
    if foreign is None or institution is None or individual is None:
        return "unavailable", []
    if not complete:
        return "participant_attribution_unavailable", []
    if foreign < 0 and institution > 0 and individual > 0:
        if material_omitted:
            return "foreign_exit_broad_absorption", ["foreign"]
        return "foreign_exit_institution_retail_absorption", [
            "foreign",
            "institution",
            "individual",
        ]
    if foreign < 0 and individual > 0 and institution <= 0:
        if material_omitted:
            return "foreign_exit_broad_absorption", ["foreign"]
        return "foreign_exit_retail_absorption", ["foreign", "individual"]
    if material_omitted:
        return "material_other_participant_flow", []
    if foreign > 0 and institution > 0:
        return "foreign_institution_joint_accumulation", ["foreign", "institution"]
    if foreign > 0:
        return "foreign_led", ["foreign"]
    if institution > 0:
        return "institution_led", ["institution"]
    if individual > 0:
        return "retail_led", ["individual"]
    if foreign < 0 and institution < 0:
        return "distribution", ["foreign", "institution"]
    return "mixed", []


def _select_primary_signal(
    reconciliations: Mapping[str, InvestorFlowWindowReconciliation],
    *,
    provider_primary_signal: str | None = None,
) -> dict[str, object]:
    five = reconciliations.get("5d")
    twenty = reconciliations.get("20d")
    if five and twenty and _opposing_displayed_directions(five, twenty):
        return {
            "signal": "mixed_window_flow",
            "basis_window": "mixed",
            "participants": list(DISPLAYED_PARTICIPANTS),
            "attribution_safe": False,
            "confidence": "qualified",
        }
    if (
        provider_primary_signal
        in {
            "foreign_reentry",
            "foreign_reentry_signal",
            "distribution",
            "retail_chasing_warning",
            "institutional_distribution_warning",
        }
        and twenty
    ):
        return {
            "signal": provider_primary_signal,
            "basis_window": "20d",
            "participants": twenty.signal_participants,
            "attribution_safe": twenty.attribution_safe,
            "confidence": "high" if twenty.attribution_safe else "qualified",
        }
    for window in ("20d", "5d", "1d"):
        reconciliation = reconciliations.get(window)
        if reconciliation and reconciliation.signal != "unavailable":
            return {
                "signal": reconciliation.signal,
                "basis_window": window,
                "participants": reconciliation.signal_participants,
                "attribution_safe": reconciliation.attribution_safe,
                "confidence": ("high" if reconciliation.attribution_safe else "qualified"),
            }
    return {
        "signal": "unavailable",
        "basis_window": None,
        "participants": [],
        "attribution_safe": False,
        "confidence": "unavailable",
    }


def _opposing_displayed_directions(
    first: InvestorFlowWindowReconciliation,
    second: InvestorFlowWindowReconciliation,
) -> bool:
    if first.missing_participants or second.missing_participants:
        return False
    reversals = 0
    for participant in DISPLAYED_PARTICIPANTS:
        left = first.participant_flows.get(participant, 0)
        right = second.participant_flows.get(participant, 0)
        if left * right < 0:
            reversals += 1
    return reversals >= 2


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or not number.is_integer():
        return None
    return int(number)
