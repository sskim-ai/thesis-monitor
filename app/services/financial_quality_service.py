from __future__ import annotations

import copy
from collections.abc import Mapping


DECISION_VERSION = "financial-quality-taint-v1"

PROSE_USABLE_STATES = {"verified_usable", "caution_usable"}

CRITICAL_REASON_CODES = {
    "financial_hard_error",
    "financial_statement_basis_warning",
    "operating_income_exceeds_revenue",
    "net_income_exceeds_revenue",
    "period_mapping_validation_failure",
    "preliminary_period_mapping_failed",
    "preliminary_profitability_outlier",
    "preliminary_validation_failed",
    "unusually_high_or_low_net_margin",
    "unusually_high_or_low_operating_margin",
}

DIRECT_EARNINGS_FIELDS = (
    "latest_revenue",
    "latest_operating_income",
    "latest_operating_margin",
    "latest_revenue_qoq",
    "latest_revenue_yoy",
    "latest_operating_income_qoq",
    "latest_operating_income_yoy",
)

PE_DEPENDENT_FIELDS = (
    "ttm_eps",
    "trailing_pe",
    "forward_eps",
    "forward_pe",
    "historical_pe_statistics.current_value",
    "historical_pe_statistics.current_percentile",
    "valuation_relative_position",
    "valuation_relative_position_reason",
)


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _text_list(value: object) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _field_value(snapshot: Mapping[str, object], path: str) -> object:
    value: object = snapshot
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _quality_record(
    *,
    state: str,
    source_period: str | None,
    source_type: str,
    reason_codes: list[str],
    dependency_fields: list[str],
    denial_reason: str | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "source_period": source_period,
        "source_type": source_type,
        "quality_reason_codes": reason_codes,
        "dependency_fields": dependency_fields,
        "prose_eligible": state in PROSE_USABLE_STATES,
        "denial_reason": denial_reason,
        "decision_version": DECISION_VERSION,
    }


def build_financial_quality_state(
    snapshot_value: Mapping[str, object],
    *,
    source_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build field-level prose eligibility without discarding auditable raw values."""
    snapshot = _dict(snapshot_value)
    coverage = _dict(snapshot.get("data_coverage"))
    source = _dict(source_metadata)
    source_period = str(
        source.get("period") or snapshot.get("latest_earnings_period") or ""
    ) or None
    source_type = str(
        source.get("source_type")
        or snapshot.get("earnings_context_source")
        or (
            "preliminary_earnings"
            if snapshot.get("earnings_context_is_preliminary") is True
            else "validated_financial_snapshot"
        )
    )

    reasons = {
        *_text_list(coverage.get("reason_codes")),
        *_text_list(source.get("hard_errors")),
        *_text_list(source.get("soft_outliers")),
    }
    if source.get("hard_errors"):
        reasons.add("financial_hard_error")
    if source.get("financial_statement_basis_warning") is True:
        reasons.add("financial_statement_basis_warning")
    if source.get("period_mapping_validation_failed") is True:
        reasons.add("period_mapping_validation_failure")
    if source.get("margin_quality_review") is True:
        reasons.add("financial_statement_basis_warning")
    reason_codes = sorted(reasons)
    critical_reasons = sorted(reasons.intersection(CRITICAL_REASON_CODES))
    direct_denied = bool(critical_reasons)

    if direct_denied:
        direct_state = "denied"
        direct_denial = "critical_financial_quality_outlier"
    elif source_type == "preliminary_earnings":
        direct_state = "caution_usable"
        direct_denial = None
    elif any(_field_value(snapshot, field) is not None for field in DIRECT_EARNINGS_FIELDS):
        direct_state = "verified_usable"
        direct_denial = None
    else:
        direct_state = "unknown"
        direct_denial = "financial_source_not_available"

    fields: dict[str, dict[str, object]] = {}
    for field in DIRECT_EARNINGS_FIELDS:
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state=direct_state,
            source_period=source_period,
            source_type=source_type,
            reason_codes=reason_codes,
            dependency_fields=[f"{source_period or 'latest'}:{field}"],
            denial_reason=direct_denial,
        )

    ttm_tainted = direct_denied and snapshot.get("ttm_contains_preliminary") is True
    modeled_forward_tainted = direct_denied and str(
        snapshot.get("forward_pe_source") or ""
    ) == "modeled_forward"
    pe_tainted = ttm_tainted or modeled_forward_tainted

    for field in ("ttm_eps", "trailing_pe"):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state="denied" if ttm_tainted else "verified_usable",
            source_period=source_period,
            source_type="derived_trailing",
            reason_codes=reason_codes if ttm_tainted else [],
            dependency_fields=["latest_earnings_period", "ttm_quarter_series"],
            denial_reason=(
                "denied_preliminary_input_in_ttm_denominator"
                if ttm_tainted
                else None
            ),
        )

    forward_source = str(snapshot.get("forward_pe_source") or "unavailable")
    for field in ("forward_eps", "forward_pe"):
        if _field_value(snapshot, field) is None:
            continue
        independent_consensus = forward_source == "consensus_forward"
        fields[field] = _quality_record(
            state=(
                "denied"
                if modeled_forward_tainted
                else "verified_usable"
                if independent_consensus
                else "caution_usable"
            ),
            source_period=source_period,
            source_type=forward_source,
            reason_codes=reason_codes if modeled_forward_tainted else [],
            dependency_fields=(
                ["latest_earnings_period", "modeled_forward_earnings"]
                if forward_source == "modeled_forward"
                else ["independent_provider_consensus"]
                if independent_consensus
                else ["forward_valuation_source"]
            ),
            denial_reason=(
                "denied_input_in_modeled_forward_earnings"
                if modeled_forward_tainted
                else None
            ),
        )

    for field in (
        "historical_pe_statistics.current_value",
        "historical_pe_statistics.current_percentile",
    ):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state="denied" if pe_tainted else "verified_usable",
            source_period=source_period,
            source_type="historical_valuation",
            reason_codes=reason_codes if pe_tainted else [],
            dependency_fields=["trailing_pe", "historical_pe_distribution"],
            denial_reason=("denied_current_pe_input" if pe_tainted else None),
        )

    if pe_tainted:
        for field in ("valuation_relative_position", "valuation_relative_position_reason"):
            if _field_value(snapshot, field) is None:
                continue
            fields[field] = _quality_record(
                state="denied",
                source_period=source_period,
                source_type="derived_valuation_state",
                reason_codes=reason_codes,
                dependency_fields=["trailing_pe", "historical_pe_statistics"],
                denial_reason="denied_earnings_based_valuation_state",
            )

    # Book-value metrics stay independent unless their own basis contract denies them.
    for field in (
        "bvps",
        "price_to_book",
        "forward_bvps",
        "forward_price_to_book",
        "historical_pb_statistics.current_value",
        "historical_pb_statistics.current_percentile",
    ):
        if _field_value(snapshot, field) is None:
            continue
        fields.setdefault(
            field,
            _quality_record(
                state="verified_usable",
                source_period=source_period,
                source_type="independent_book_value_lineage",
                reason_codes=[],
                dependency_fields=["book_value_inputs"],
            ),
        )

    denied_fields = sorted(
        field for field, quality in fields.items() if quality["state"] == "denied"
    )
    return {
        "decision_version": DECISION_VERSION,
        "source_snapshot": {
            key: value
            for key, value in {
                "period": source_period,
                "source_type": source_type,
                "provider": source.get("provider"),
                "filing_date": source.get("filing_date"),
            }.items()
            if value is not None
        },
        "quality_reason_codes": reason_codes,
        "critical_reason_codes": critical_reasons,
        "fields": fields,
        "denied_fields": denied_fields,
        "prose_eligible_fields": sorted(
            field
            for field, quality in fields.items()
            if quality["state"] in PROSE_USABLE_STATES
        ),
    }


def field_quality(
    state_value: Mapping[str, object] | None,
    field: str,
) -> dict[str, object]:
    state = _dict(state_value)
    fields = _dict(state.get("fields"))
    return _dict(fields.get(field))


def sanitize_financial_snapshot_for_prose(
    snapshot_value: Mapping[str, object],
) -> dict[str, object]:
    snapshot = copy.deepcopy(_dict(snapshot_value))
    quality = build_financial_quality_state(snapshot)
    snapshot["financial_quality"] = quality
    for path in quality["denied_fields"]:
        parts = str(path).split(".")
        target: object = snapshot
        for part in parts[:-1]:
            if not isinstance(target, dict):
                break
            target = target.get(part)
        else:
            if isinstance(target, dict):
                target[parts[-1]] = None
    for multiple in ("trailing_pe", "forward_pe"):
        if multiple in quality["denied_fields"]:
            snapshot[f"{multiple}_status"] = "unavailable"
    if "valuation_relative_position" in quality["denied_fields"]:
        snapshot["valuation_relative_position"] = "unknown"
        snapshot["valuation_relative_position_reason"] = (
            "검증 경고가 있는 이익 입력을 제외해 현재 Valuation 위치 판단을 보류합니다."
        )
    return snapshot
