from __future__ import annotations

import copy
from collections.abc import Mapping

from app.services.financial_amount_period_service import AMOUNT_PERIOD_CONTRACT
from app.services.security_identity_service import (
    IDENTITY_CONFLICT,
    IDENTITY_UNKNOWN,
    VERIFIED_NON_DEPOSITARY,
)


DECISION_VERSION = "financial-quality-taint-v2"
VALUATION_COHERENCE_VERSION = "valuation-coherence-v1"

PROSE_USABLE_STATES = {"verified_usable", "caution_usable"}
COMPARABLE_BASIS_STATES = {
    "directly_comparable",
    "normalized_to_current_security",
}

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

BOOK_DENIAL_REASON_CODES = {
    "financial_hard_error",
    "financial_statement_basis_warning",
    "period_mapping_validation_failure",
    "preliminary_period_mapping_failed",
    "preliminary_validation_failed",
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


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _dict_list(value: object) -> list[dict[str, object]]:
    return [dict(item) for item in _list(value) if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _field_value(snapshot: Mapping[str, object], path: str) -> object:
    value: object = snapshot
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _source_reasons(source_value: Mapping[str, object]) -> list[str]:
    source = _dict(source_value)
    reasons = {
        *_text_list(source.get("quality_reason_codes")),
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
    return sorted(reasons)


def _quality_record(
    *,
    state: str,
    source_period: str | None,
    source_type: str,
    provider: str | None,
    reason_codes: list[str],
    dependency_fields: list[str],
    dependency_periods: list[str] | None = None,
    denominator_period: str | None = None,
    lineage_verification_status: str,
    denial_reason: str | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "source_period": source_period,
        "source_type": source_type,
        "provider": provider,
        "quality_reason_codes": reason_codes,
        "dependency_fields": dependency_fields,
        "dependency_periods": dependency_periods or [],
        "denominator_period": denominator_period,
        "lineage_verification_status": lineage_verification_status,
        "prose_eligible": state in PROSE_USABLE_STATES,
        "denial_reason": denial_reason,
        "decision_version": DECISION_VERSION,
    }


def _dependency_periods(records: list[dict[str, object]]) -> list[str]:
    return list(
        dict.fromkeys(
            str(item.get("period"))
            for item in records
            if item.get("period") not in (None, "")
        )
    )


def _dependency_quality(
    records: list[dict[str, object]],
    *,
    critical_codes: set[str] = CRITICAL_REASON_CODES,
) -> tuple[list[str], bool, list[str], str | None]:
    periods = _dependency_periods(records)
    complete = bool(records) and all(
        item.get("lineage_verified") is True and item.get("period")
        for item in records
    )
    reasons = sorted(
        {
            reason
            for item in records
            for reason in _source_reasons(item)
        }
    )
    critical = sorted(set(reasons).intersection(critical_codes))
    provider_values = list(
        dict.fromkeys(
            str(item.get("provider"))
            for item in records
            if item.get("provider") not in (None, "")
        )
    )
    provider = provider_values[0] if len(provider_values) == 1 else None
    return periods, complete, critical, provider


def _basis_is_usable(
    snapshot: Mapping[str, object],
    status_field: str,
    conflict_field: str,
) -> bool:
    return (
        str(snapshot.get(status_field) or "") in COMPARABLE_BASIS_STATES
        and snapshot.get(conflict_field) is not True
    )


def _book_valuation_coherence(
    snapshot: Mapping[str, object],
    fields: dict[str, dict[str, object]],
) -> dict[str, object]:
    price = _field_value(snapshot, "current_price")
    bvps = _field_value(snapshot, "bvps")
    pbr = _field_value(snapshot, "price_to_book")
    price_currency = str(snapshot.get("currency") or "") or None
    book_currency = str(snapshot.get("book_currency") or "") or None
    pbr_quality = _dict(fields.get("price_to_book"))
    bvps_quality = _dict(fields.get("bvps"))
    pbr_period = (
        snapshot.get("pbr_denominator_period_end")
        or pbr_quality.get("denominator_period")
    )
    bvps_period = bvps_quality.get("denominator_period")
    basis_status = str(snapshot.get("price_to_book_basis_status") or "")
    reasons: list[str] = []
    status = "not_applicable"
    if isinstance(pbr, (int, float)):
        status = "passed"
        if not _basis_is_usable(
            snapshot,
            "price_to_book_basis_status",
            "price_to_book_basis_conflict",
        ):
            reasons.append("price_to_book_basis_unverified")
        if price_currency and book_currency and price_currency != book_currency:
            reasons.append("price_to_book_currency_basis_mismatch")
        if pbr_period and bvps_period and pbr_period != bvps_period:
            reasons.append("price_to_book_period_basis_mismatch")
        if (
            isinstance(price, (int, float))
            and float(price) > 0
            and isinstance(bvps, (int, float))
            and float(bvps) <= 0
        ):
            reasons.append("non_positive_bvps_cannot_support_pbr_multiple")
        if reasons:
            status = "failed"
            for field in (
                "price_to_book",
                "historical_pb_statistics.current_value",
                "historical_pb_statistics.current_percentile",
            ):
                existing = _dict(fields.get(field))
                if not existing:
                    continue
                if existing.get("prose_eligible") is False:
                    continue
                fields[field] = {
                    **existing,
                    "state": "denied",
                    "prose_eligible": False,
                    "quality_reason_codes": list(
                        dict.fromkeys(
                            [
                                *(str(item) for item in existing.get("quality_reason_codes", [])),
                                *reasons,
                            ]
                        )
                    ),
                    "denial_reason": "valuation_coherence_failed",
                }
    return {
        "contract": VALUATION_COHERENCE_VERSION,
        "status": status,
        "current_price": price,
        "price_currency": price_currency,
        "bvps": bvps,
        "book_currency": book_currency,
        "price_to_book": pbr,
        "price_to_book_source": snapshot.get("price_to_book_source"),
        "price_to_book_method": snapshot.get("price_to_book_method"),
        "price_to_book_basis_status": basis_status or None,
        "price_to_book_denominator_period": pbr_period,
        "bvps_denominator_period": bvps_period,
        "book_share_basis": snapshot.get("share_count_security_basis"),
        "reasons": reasons,
    }


def _state_from_lineage(
    *,
    critical: list[str],
    complete: bool,
    usable_state: str,
    denied_reason: str,
    unknown_reason: str,
) -> tuple[str, str | None, str]:
    if critical:
        return "denied", denied_reason, "verified_tainted"
    if complete:
        return usable_state, None, "verified"
    return "unknown", unknown_reason, "unverified"


def build_financial_quality_state(
    snapshot_value: Mapping[str, object],
    *,
    source_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build exact field-level eligibility while retaining raw audit values."""
    snapshot = _dict(snapshot_value)
    coverage = _dict(snapshot.get("data_coverage"))
    source = _dict(
        source_metadata
        if source_metadata is not None
        else snapshot.get("financial_quality_source_metadata")
    )
    source_period = str(
        source.get("period") or snapshot.get("latest_earnings_period") or ""
    ) or None
    source_type = str(
        source.get("source_type")
        or snapshot.get("earnings_context_source")
        or "unknown"
    )
    source_provider = str(source.get("provider") or "") or None

    aggregate_reasons = {
        *_text_list(coverage.get("reason_codes")),
        *_source_reasons(source),
    }
    reason_codes = sorted(aggregate_reasons)
    critical_reasons = sorted(aggregate_reasons.intersection(CRITICAL_REASON_CODES))

    direct_sources = _dict(source.get("direct_field_sources"))
    amount_period_contract_active = (
        source.get("financial_amount_period_contract") == AMOUNT_PERIOD_CONTRACT
    )
    fields: dict[str, dict[str, object]] = {}
    for field in DIRECT_EARNINGS_FIELDS:
        if _field_value(snapshot, field) is None:
            continue
        records = _dict_list(direct_sources.get(field))
        if records:
            periods, complete, critical, provider = _dependency_quality(records)
            if amount_period_contract_active and any(
                item.get("provider") == "opendart" for item in records
            ):
                complete = bool(
                    complete
                    and all(
                        item.get("amount_period_type")
                        and item.get("amount_period_start")
                        and item.get("amount_period_end")
                        and item.get("source_row_identity")
                        and item.get("consolidated_separate_basis")
                        and item.get("statement_basis_source")
                        and item.get("statement_basis_state")
                        in {"verified_consolidated", "verified_separate"}
                        for item in records
                    )
                )
            if amount_period_contract_active and field.endswith(("_qoq", "_yoy")):
                complete = bool(
                    complete
                    and all(
                        item.get("comparison_period_verified") is True
                        for item in records
                    )
                )
            source_types = list(
                dict.fromkeys(
                    str(item.get("source_type"))
                    for item in records
                    if item.get("source_type") not in (None, "")
                )
            )
            field_source_type = (
                source_types[0] if len(source_types) == 1 else "mixed_sources"
            )
            field_reasons = sorted(
                {
                    reason
                    for item in records
                    for reason in _source_reasons(item)
                }
            )
            state, denial, verification = _state_from_lineage(
                critical=critical,
                complete=complete,
                usable_state=(
                    "caution_usable"
                    if any(
                        item.get("source_type") == "preliminary_earnings"
                        for item in records
                    )
                    else "verified_usable"
                ),
                denied_reason="critical_financial_quality_outlier",
                unknown_reason="direct_financial_lineage_unverified",
            )
        else:
            periods = [source_period] if source_period else []
            provider = source_provider
            field_reasons = reason_codes
            if critical_reasons:
                state, denial, verification = (
                    "denied",
                    "critical_financial_quality_outlier",
                    "snapshot_quality_tainted",
                )
            elif source_period and source_type != "unknown":
                state = (
                    "caution_usable"
                    if source_type == "preliminary_earnings"
                    else "verified_usable"
                )
                denial = None
                verification = "snapshot_source_metadata"
            else:
                state, denial, verification = (
                    "unknown",
                    "direct_financial_lineage_unverified",
                    "unverified",
                )
            field_source_type = source_type
        quality_record = _quality_record(
            state=state,
            source_period=periods[-1] if periods else source_period,
            source_type=field_source_type,
            provider=provider,
            reason_codes=field_reasons,
            dependency_fields=[f"earnings.{field}"],
            dependency_periods=periods,
            denominator_period=periods[-1] if periods else source_period,
            lineage_verification_status=verification,
            denial_reason=denial,
        )
        if records:
            amount = records[0]
            quality_record.update(
                {
                    key: amount.get(key)
                    for key in (
                        "amount_period_type",
                        "amount_period_start",
                        "amount_period_end",
                        "financial_lineage_contract",
                        "single_quarter_cumulative_flag",
                        "source_filing_identifier",
                        "source_row_identity",
                        "account_identifier",
                        "account_name",
                        "currency",
                        "consolidated_separate_basis",
                        "statement_basis_contract",
                        "statement_basis_state",
                        "statement_basis_source",
                        "statement_basis_evidence",
                        "comparison_type",
                        "comparison_period_start",
                        "comparison_period_end",
                        "dependency_lineages",
                    )
                }
            )
            if amount_period_contract_active and field.endswith(("_qoq", "_yoy")):
                quality_record["comparison_period_verified"] = all(
                    item.get("comparison_period_verified") is True
                    for item in records
                )
                if not quality_record["comparison_period_verified"]:
                    quality_record.update(
                        state="unknown",
                        prose_eligible=False,
                        denial_reason="financial_comparison_period_unverified",
                        lineage_verification_status="unverified",
                    )
        fields[field] = quality_record

    ttm_records = _dict_list(source.get("ttm_sources"))
    ttm_periods, ttm_complete, ttm_critical, ttm_provider = _dependency_quality(
        ttm_records
    )
    ttm_denominator = str(snapshot.get("trailing_pe_denominator_period_end") or "") or None
    expected_ttm_periods = [
        str(item.get("period"))
        for item in _dict_list(snapshot.get("earnings_quarter_series"))
        if item.get("period") and item.get("normalized_eps_usable") is not False
    ]
    ttm_complete = bool(
        ttm_complete
        and len(ttm_records) == len(expected_ttm_periods) >= 4
        and ttm_periods == expected_ttm_periods
        and ttm_denominator == expected_ttm_periods[-1]
        and snapshot.get("ttm_eps_usable") is not False
        and _basis_is_usable(
            snapshot,
            "trailing_pe_basis_status",
            "trailing_pe_basis_conflict",
        )
    )
    ttm_state, ttm_denial, ttm_verification = _state_from_lineage(
        critical=ttm_critical,
        complete=ttm_complete,
        usable_state="verified_usable",
        denied_reason="critical_input_in_ttm_denominator",
        unknown_reason="ttm_dependency_lineage_unverified",
    )
    for field in ("ttm_eps", "trailing_pe"):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state=ttm_state,
            source_period=ttm_denominator,
            source_type="derived_trailing",
            provider=ttm_provider,
            reason_codes=ttm_critical,
            dependency_fields=["earnings_quarter_series.eps"],
            dependency_periods=expected_ttm_periods,
            denominator_period=ttm_denominator,
            lineage_verification_status=ttm_verification,
            denial_reason=ttm_denial,
        )

    forward_source = str(snapshot.get("forward_pe_source") or "unavailable")
    forward_period = str(snapshot.get("forward_pe_input_period") or "") or None
    forward_records = _dict_list(source.get("modeled_forward_sources"))
    forward_periods, forward_complete, forward_critical, forward_provider = (
        _dependency_quality(forward_records)
    )
    forward_basis_usable = _basis_is_usable(
        snapshot,
        "forward_pe_basis_status",
        "forward_pe_basis_conflict",
    )
    if forward_source == "consensus_forward":
        provider_native_multiple = bool(
            forward_period
            and snapshot.get("provider")
            and snapshot.get("currency")
            and snapshot.get("security_identity_state")
            == VERIFIED_NON_DEPOSITARY
            and str(snapshot.get("forward_pe_basis_status") or "")
            == "not_applicable"
            and snapshot.get("forward_pe_basis_conflict") is not True
        )
        forward_complete = bool(
            forward_period and (forward_basis_usable or provider_native_multiple)
        )
        forward_state, forward_denial, forward_verification = _state_from_lineage(
            critical=[],
            complete=forward_complete,
            usable_state="verified_usable",
            denied_reason="unused",
            unknown_reason="consensus_forward_lineage_unverified",
        )
        forward_periods = [forward_period] if forward_period else []
        forward_provider = str(snapshot.get("provider") or "") or None
        forward_dependency_fields = [
            "independent_provider_consensus",
            (
                "provider_native_multiple_contract"
                if provider_native_multiple
                else "verified_per_security_basis"
            ),
        ]
    elif forward_source == "modeled_forward":
        expected_forward_count = int(
            source.get("modeled_forward_expected_count") or len(forward_records)
        )
        forward_complete = bool(
            forward_complete
            and len(forward_records) >= expected_forward_count > 0
            and forward_basis_usable
        )
        forward_state, forward_denial, forward_verification = _state_from_lineage(
            critical=forward_critical,
            complete=forward_complete,
            usable_state="caution_usable",
            denied_reason="critical_input_in_modeled_forward_earnings",
            unknown_reason="modeled_forward_dependency_lineage_unverified",
        )
        forward_dependency_fields = ["modeled_forward_earnings_inputs"]
    else:
        forward_state, forward_denial, forward_verification = (
            "unknown",
            "forward_source_unavailable",
            "unverified",
        )
        forward_dependency_fields = ["forward_valuation_source"]
    for field in ("forward_eps", "forward_pe"):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state=forward_state,
            source_period=forward_period,
            source_type=forward_source,
            provider=forward_provider,
            reason_codes=forward_critical,
            dependency_fields=forward_dependency_fields,
            dependency_periods=forward_periods,
            denominator_period=forward_period,
            lineage_verification_status=forward_verification,
            denial_reason=forward_denial,
        )

    trailing_quality = _dict(fields.get("trailing_pe"))
    for field in (
        "historical_pe_statistics.current_value",
        "historical_pe_statistics.current_percentile",
    ):
        if _field_value(snapshot, field) is None:
            continue
        trailing_state = str(trailing_quality.get("state") or "unknown")
        fields[field] = _quality_record(
            state=trailing_state,
            source_period=ttm_denominator,
            source_type="historical_trailing_pe",
            provider=ttm_provider,
            reason_codes=list(trailing_quality.get("quality_reason_codes") or []),
            dependency_fields=["trailing_pe", "historical_pe_distribution"],
            dependency_periods=expected_ttm_periods,
            denominator_period=ttm_denominator,
            lineage_verification_status=str(
                trailing_quality.get("lineage_verification_status") or "unverified"
            ),
            denial_reason=(
                "current_trailing_pe_not_prose_eligible"
                if trailing_state not in PROSE_USABLE_STATES
                else None
            ),
        )

    if str(trailing_quality.get("state") or "unknown") not in PROSE_USABLE_STATES:
        for field in (
            "valuation_relative_position",
            "valuation_relative_position_reason",
        ):
            if _field_value(snapshot, field) is None:
                continue
            fields[field] = _quality_record(
                state="unknown",
                source_period=ttm_denominator,
                source_type="derived_valuation_state",
                provider=ttm_provider,
                reason_codes=list(trailing_quality.get("quality_reason_codes") or []),
                dependency_fields=["trailing_pe", "historical_pe_statistics"],
                dependency_periods=expected_ttm_periods,
                denominator_period=ttm_denominator,
                lineage_verification_status=str(
                    trailing_quality.get("lineage_verification_status") or "unverified"
                ),
                denial_reason="earnings_based_valuation_state_unavailable",
            )

    book_source = _dict(source.get("book_source"))
    book_period = str(
        book_source.get("period") or snapshot.get("pbr_denominator_period_end") or ""
    ) or None
    book_reasons = _source_reasons(book_source)
    book_critical = sorted(set(book_reasons).intersection(BOOK_DENIAL_REASON_CODES))
    book_basis_usable = _basis_is_usable(
        snapshot,
        "price_to_book_basis_status",
        "price_to_book_basis_conflict",
    )
    book_lineage_verified = bool(
        book_period
        and book_basis_usable
        and (
            book_source.get("lineage_verified") is True
            or not source_metadata
        )
    )
    book_state, book_denial, book_verification = _state_from_lineage(
        critical=book_critical,
        complete=book_lineage_verified,
        usable_state=("verified_usable" if book_source else "caution_usable"),
        denied_reason="critical_book_value_input",
        unknown_reason="book_value_dependency_lineage_unverified",
    )
    book_provider = str(book_source.get("provider") or "") or None
    book_source_type = str(book_source.get("source_type") or "reported_book_value")
    for field in ("bvps", "price_to_book"):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state=book_state,
            source_period=book_period,
            source_type=book_source_type,
            provider=book_provider,
            reason_codes=book_reasons,
            dependency_fields=["book_value_denominator"],
            dependency_periods=[book_period] if book_period else [],
            denominator_period=book_period,
            lineage_verification_status=book_verification,
            denial_reason=book_denial,
        )

    forward_book_source = str(
        snapshot.get("forward_price_to_book_source") or "unavailable"
    )
    forward_book_period = str(snapshot.get("forward_pb_input_period") or "") or None
    forward_book_records = _dict_list(source.get("modeled_forward_book_sources"))
    (
        forward_book_periods,
        forward_book_complete,
        forward_book_critical,
        forward_book_provider,
    ) = _dependency_quality(forward_book_records)
    forward_book_basis_usable = _basis_is_usable(
        snapshot,
        "forward_price_to_book_basis_status",
        "forward_price_to_book_basis_conflict",
    )
    if forward_book_source == "modeled_forward":
        expected_forward_book_count = int(
            source.get("modeled_forward_book_expected_count")
            or len(forward_book_records)
        )
        forward_book_complete = bool(
            forward_book_complete
            and len(forward_book_records) >= expected_forward_book_count > 0
            and forward_book_basis_usable
            and book_state in PROSE_USABLE_STATES
        )
        forward_book_state, forward_book_denial, forward_book_verification = (
            _state_from_lineage(
                critical=forward_book_critical,
                complete=forward_book_complete,
                usable_state="caution_usable",
                denied_reason="critical_input_in_modeled_forward_book_value",
                unknown_reason="modeled_forward_book_lineage_unverified",
            )
        )
    else:
        forward_book_state, forward_book_denial, forward_book_verification = (
            "unknown",
            "forward_book_source_unavailable",
            "unverified",
        )
    for field in ("forward_bvps", "forward_price_to_book"):
        if _field_value(snapshot, field) is None:
            continue
        fields[field] = _quality_record(
            state=forward_book_state,
            source_period=forward_book_period,
            source_type=forward_book_source,
            provider=forward_book_provider,
            reason_codes=forward_book_critical,
            dependency_fields=["modeled_forward_book_value_inputs"],
            dependency_periods=forward_book_periods,
            denominator_period=forward_book_period,
            lineage_verification_status=forward_book_verification,
            denial_reason=forward_book_denial,
        )

    current_book_quality = _dict(fields.get("price_to_book"))
    for field in (
        "historical_pb_statistics.current_value",
        "historical_pb_statistics.current_percentile",
    ):
        if _field_value(snapshot, field) is None:
            continue
        current_book_state = str(current_book_quality.get("state") or "unknown")
        fields[field] = _quality_record(
            state=current_book_state,
            source_period=book_period,
            source_type="historical_price_to_book",
            provider=book_provider,
            reason_codes=list(current_book_quality.get("quality_reason_codes") or []),
            dependency_fields=["price_to_book", "historical_pb_distribution"],
            dependency_periods=[book_period] if book_period else [],
            denominator_period=book_period,
            lineage_verification_status=str(
                current_book_quality.get("lineage_verification_status") or "unverified"
            ),
            denial_reason=(
                "current_price_to_book_not_prose_eligible"
                if current_book_state not in PROSE_USABLE_STATES
                else None
            ),
        )

    identity_metadata = _dict(source.get("security_identity"))
    identity_state = str(
        snapshot.get("security_identity_state")
        or identity_metadata.get("identity_state")
        or IDENTITY_UNKNOWN
    )
    if identity_state in {IDENTITY_CONFLICT, IDENTITY_UNKNOWN}:
        identity_denial = (
            "security_identity_conflict"
            if identity_state == IDENTITY_CONFLICT
            else "security_identity_unverified"
        )
        identity_quality_state = (
            "denied" if identity_state == IDENTITY_CONFLICT else "unknown"
        )
        identity_verification = (
            "conflicted" if identity_state == IDENTITY_CONFLICT else "unverified"
        )
        identity_reasons = [
            *(
                str(item)
                for item in (
                    snapshot.get("security_identity_conflict_reasons")
                    or identity_metadata.get("conflict_reasons")
                    or []
                )
                if str(item).strip()
            ),
            identity_denial,
        ]
        security_basis_fields = (
            "ttm_eps",
            "trailing_pe",
            "forward_eps",
            "forward_pe",
            "bvps",
            "price_to_book",
            "forward_bvps",
            "forward_price_to_book",
            "historical_pe_statistics.current_value",
            "historical_pe_statistics.current_percentile",
            "historical_pb_statistics.current_value",
            "historical_pb_statistics.current_percentile",
            "valuation_relative_position",
            "valuation_relative_position_reason",
        )
        for field in security_basis_fields:
            if _field_value(snapshot, field) is None:
                continue
            existing = _dict(fields.get(field))
            fields[field] = _quality_record(
                state=identity_quality_state,
                source_period=(
                    str(existing.get("source_period"))
                    if existing.get("source_period") is not None
                    else None
                ),
                source_type=str(existing.get("source_type") or "security_basis"),
                provider=(
                    str(existing.get("provider"))
                    if existing.get("provider") is not None
                    else None
                ),
                reason_codes=list(dict.fromkeys(identity_reasons)),
                dependency_fields=[
                    *(
                        str(item)
                        for item in existing.get("dependency_fields", [])
                    ),
                    "security_identity.current_security_basis",
                ],
                dependency_periods=[
                    str(item)
                    for item in existing.get("dependency_periods", [])
                ],
                denominator_period=(
                    str(existing.get("denominator_period"))
                    if existing.get("denominator_period") is not None
                    else None
                ),
                lineage_verification_status=identity_verification,
                denial_reason=identity_denial,
            )

    valuation_coherence = _book_valuation_coherence(snapshot, fields)
    denied_fields = sorted(
        field for field, quality in fields.items() if quality["state"] == "denied"
    )
    non_prose_fields = sorted(
        field
        for field, quality in fields.items()
        if quality["state"] not in PROSE_USABLE_STATES
    )
    return {
        "decision_version": DECISION_VERSION,
        "source_snapshot": {
            key: value
            for key, value in {
                "period": source_period,
                "period_type": source.get("period_type"),
                "fiscal_year": source.get("fiscal_year"),
                "period_scope": source.get("period_scope"),
                "is_cumulative": source.get("is_cumulative"),
                "source_type": source_type,
                "provider": source_provider,
                "filing_date": source.get("filing_date"),
            }.items()
            if value is not None
        },
        "quality_reason_codes": reason_codes,
        "critical_reason_codes": critical_reasons,
        "valuation_coherence": valuation_coherence,
        "fields": fields,
        "denied_fields": denied_fields,
        "non_prose_fields": non_prose_fields,
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
    for path in quality["non_prose_fields"]:
        parts = str(path).split(".")
        target: object = snapshot
        for part in parts[:-1]:
            if not isinstance(target, dict):
                break
            target = target.get(part)
        else:
            if isinstance(target, dict):
                target[parts[-1]] = None
    for multiple in (
        "trailing_pe",
        "forward_pe",
        "price_to_book",
        "forward_price_to_book",
    ):
        if multiple in quality["non_prose_fields"]:
            snapshot[f"{multiple}_status"] = "unavailable"
    if "valuation_relative_position" in quality["non_prose_fields"]:
        snapshot["valuation_relative_position"] = "unknown"
        source = _dict(snapshot.get("financial_quality_source_metadata"))
        identity = _dict(source.get("security_identity"))
        identity_state = str(
            snapshot.get("security_identity_state")
            or identity.get("identity_state")
            or IDENTITY_UNKNOWN
        )
        snapshot["valuation_relative_position_reason"] = (
            "증권 유형과 주당 기준의 일치 여부를 확인하지 못해 배수 비교를 보류합니다."
            if identity_state in {IDENTITY_CONFLICT, IDENTITY_UNKNOWN}
            else "검증 경고가 있는 이익 입력을 제외해 현재 Valuation 위치 판단을 보류합니다."
        )
    return snapshot
