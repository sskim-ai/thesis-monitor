from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


CONTRACT_VERSION = "existing-canonical-financial-domain-adapter-v1"
CANONICAL_CASH_FLOW_SOURCE = "canonical_cash_flow_fact"
SIMPLE_CASH_CONVERSION_METRIC = "ocf_less_ppe_capex"
SIMPLE_CASH_CONVERSION_FORMULA = "ocf_less_ppe_capex"

_FACT_TYPE_METRICS = {
    "cash_flow_ocf": "operating_cash_flow",
    "cash_flow_ppe_capex": "ppe_capex_cash_outflow",
    "cash_flow_fcf_ppe": SIMPLE_CASH_CONVERSION_METRIC,
}
_DIRECT_FACT_TYPES = {"cash_flow_ocf", "cash_flow_ppe_capex"}
_COMPARABLE_PERIOD_TYPES = {"QTD", "YTD", "FY", "POINT_IN_TIME"}
_PERIOD_TYPES = {*_COMPARABLE_PERIOD_TYPES, "TTM"}
_ATTRIBUTION_BASES = {"total", "parent", "common"}
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
_SOURCE_REF = re.compile(r"^\S{1,240}$")


@dataclass(frozen=True)
class CanonicalFinancialIdentity:
    fact_id: str
    source_ref: str
    metric: str
    value: Decimal
    currency: str
    unit_scale: int
    period_type: str
    period_start: date | None
    period_end: date
    duration_days: int | None
    fiscal_year: int
    fiscal_quarter: int | None
    entity_scope: str
    statement_basis: str
    attribution_basis: str | None

    def period_payload(self) -> dict[str, object]:
        return {
            "type": self.period_type,
            "start": self.period_start.isoformat() if self.period_start else None,
            "end": self.period_end.isoformat(),
            "duration_days": self.duration_days,
        }


@dataclass(frozen=True)
class FinancialComparisonAdapterResult:
    comparison: dict[str, object] | None
    denial_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class FinancialContextAdapterResult:
    context: dict[str, object] | None
    denial_reasons: tuple[str, ...] = ()


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _integer(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def _date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _source_ref(fact_id: str) -> str:
    return f"stock.fact_catalog.{fact_id}"


def _input_fact_ids(fields: Mapping[str, object]) -> tuple[str, ...] | None:
    raw = fields.get("input_fact_ids")
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        return None
    values = tuple(str(item).strip() for item in raw)
    if any(not item or not _SOURCE_REF.fullmatch(_source_ref(item)) for item in values):
        return None
    if len(values) != len(set(values)):
        return None
    return values


def canonical_identity_from_fact_catalog(
    row: Mapping[str, object],
) -> tuple[CanonicalFinancialIdentity | None, tuple[str, ...]]:
    reasons: list[str] = []
    if row.get("source") != CANONICAL_CASH_FLOW_SOURCE:
        reasons.append("source_is_not_existing_canonical_cash_flow")
    fact_type = str(row.get("fact_type") or "")
    metric = _FACT_TYPE_METRICS.get(fact_type)
    if metric is None:
        reasons.append("metric_not_in_m6_adapter_scope")
    fact_id = str(row.get("fact_id") or "").strip()
    source_ref = _source_ref(fact_id)
    if not fact_id or not _SOURCE_REF.fullmatch(source_ref):
        reasons.append("source_ref_invalid")
    fields = _mapping(row.get("fields"))
    if fields is None:
        return None, tuple(dict.fromkeys([*reasons, "financial_fields_missing"]))

    value = _decimal(fields.get("value"))
    if value is None:
        reasons.append("financial_value_invalid")
    elif metric == "ppe_capex_cash_outflow" and value < 0:
        reasons.append("ppe_capex_not_positive_outflow")
    currency = str(fields.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        reasons.append("financial_currency_invalid")
    unit_scale = _integer(fields.get("unit_scale"))
    if unit_scale is None:
        unit_scale = 1
    if unit_scale != 1:
        reasons.append("noncanonical_unit_scale_not_supported")

    period_type = str(fields.get("period_type") or "").strip().upper()
    if period_type not in _PERIOD_TYPES:
        reasons.append("financial_period_type_invalid")
    period_end = _date(fields.get("period_end"))
    if period_end is None:
        reasons.append("financial_period_end_invalid")
    period_start = _date(fields.get("period_start"))
    duration_days: int | None = None
    if period_type == "POINT_IN_TIME":
        if fields.get("period_start") not in (None, ""):
            reasons.append("point_in_time_start_forbidden")
    elif period_start is None:
        reasons.append("financial_duration_period_start_required")
    elif period_end is not None:
        if period_end < period_start:
            reasons.append("financial_period_end_before_start")
        else:
            duration_days = (period_end - period_start).days + 1

    fiscal_year = _integer(fields.get("fiscal_year"))
    if fiscal_year is None:
        reasons.append("financial_fiscal_year_required")
    fiscal_quarter = _integer(fields.get("fiscal_quarter"))
    if period_type in {"QTD", "YTD"} and fiscal_quarter not in {1, 2, 3, 4}:
        reasons.append("financial_fiscal_quarter_required")
    if fiscal_quarter is not None and fiscal_quarter not in {1, 2, 3, 4}:
        reasons.append("financial_fiscal_quarter_invalid")

    entity_scope = str(fields.get("entity_scope") or "").strip()
    if not _IDENTIFIER.fullmatch(entity_scope):
        reasons.append("financial_entity_scope_invalid")
    statement_basis = str(fields.get("statement_basis") or "").strip()
    if not _IDENTIFIER.fullmatch(statement_basis):
        reasons.append("financial_statement_basis_invalid")
    attribution_basis = _text(fields.get("attribution_basis"))
    if attribution_basis is not None and attribution_basis not in _ATTRIBUTION_BASES:
        reasons.append("financial_attribution_basis_invalid")

    if reasons:
        return None, tuple(dict.fromkeys(reasons))
    assert metric is not None
    assert value is not None
    assert period_end is not None
    assert fiscal_year is not None
    return (
        CanonicalFinancialIdentity(
            fact_id=fact_id,
            source_ref=source_ref,
            metric=metric,
            value=value,
            currency=currency,
            unit_scale=unit_scale,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            duration_days=duration_days,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            entity_scope=entity_scope,
            statement_basis=statement_basis,
            attribution_basis=attribution_basis,
        ),
        (),
    )


def prior_year_comparison(
    current: CanonicalFinancialIdentity,
    prior: CanonicalFinancialIdentity,
) -> FinancialComparisonAdapterResult:
    reasons: list[str] = []
    if current.fact_id == prior.fact_id:
        reasons.append("comparison_same_fact")
    for field_name in (
        "metric",
        "currency",
        "unit_scale",
        "period_type",
        "entity_scope",
        "statement_basis",
        "attribution_basis",
    ):
        if getattr(current, field_name) != getattr(prior, field_name):
            reasons.append(f"comparison_{field_name}_mismatch")
    if current.period_type not in _COMPARABLE_PERIOD_TYPES:
        reasons.append("comparison_period_type_not_supported")
    if current.fiscal_year != prior.fiscal_year + 1:
        reasons.append("comparison_fiscal_year_not_consecutive")
    if current.period_type in {"QTD", "YTD"}:
        if current.fiscal_quarter != prior.fiscal_quarter:
            reasons.append("comparison_fiscal_quarter_mismatch")
        if current.duration_days != prior.duration_days:
            reasons.append("comparison_duration_mismatch")
    elif current.period_type == "FY":
        if current.duration_days != prior.duration_days:
            reasons.append("comparison_duration_mismatch")
    elif current.period_type == "POINT_IN_TIME":
        if (
            current.period_end.month,
            current.period_end.day,
        ) != (
            prior.period_end.month,
            prior.period_end.day,
        ):
            reasons.append("comparison_point_in_time_date_mismatch")
    if prior.period_end >= current.period_end:
        reasons.append("comparison_prior_not_before_current")
    if reasons:
        return FinancialComparisonAdapterResult(None, tuple(dict.fromkeys(reasons)))
    return FinancialComparisonAdapterResult(
        {
            "kind": "prior_year_comparable",
            "compatibility_status": "PASS",
            "input_source_refs": [current.source_ref, prior.source_ref],
        }
    )


def _prior_comparison(
    current: CanonicalFinancialIdentity,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object] | None:
    candidates: list[CanonicalFinancialIdentity] = []
    for row in rows:
        candidate, _reasons = canonical_identity_from_fact_catalog(row)
        if candidate is None:
            continue
        result = prior_year_comparison(current, candidate)
        if result.comparison is not None:
            candidates.append(candidate)
    if not candidates:
        return None
    prior = max(candidates, key=lambda item: (item.period_end, item.source_ref))
    return prior_year_comparison(current, prior).comparison


def _same_basis(
    current: CanonicalFinancialIdentity,
    inputs: Sequence[CanonicalFinancialIdentity],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name in (
        "currency",
        "unit_scale",
        "period_type",
        "period_start",
        "period_end",
        "duration_days",
        "fiscal_year",
        "fiscal_quarter",
        "entity_scope",
        "statement_basis",
        "attribution_basis",
    ):
        if len({getattr(item, field_name) for item in (current, *inputs)}) != 1:
            reasons.append(f"derivation_{field_name}_mismatch")
    return tuple(reasons)


def _derived_cash_conversion(
    current: CanonicalFinancialIdentity,
    row: Mapping[str, object],
    rows_by_id: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object] | None, tuple[str, ...]]:
    fields = _mapping(row.get("fields"))
    assert fields is not None
    input_ids = _input_fact_ids(fields)
    if input_ids is None or len(input_ids) != 2:
        return None, ("simple_cash_conversion_requires_two_input_refs",)
    input_rows = [rows_by_id.get(fact_id) for fact_id in input_ids]
    if any(item is None for item in input_rows):
        return None, ("simple_cash_conversion_input_ref_missing",)
    identities: list[CanonicalFinancialIdentity] = []
    for input_row in input_rows:
        assert input_row is not None
        identity, reasons = canonical_identity_from_fact_catalog(input_row)
        if identity is None:
            return None, tuple(
                dict.fromkeys(["simple_cash_conversion_input_invalid", *reasons])
            )
        input_fields = _mapping(input_row.get("fields"))
        assert input_fields is not None
        if _input_fact_ids(input_fields) != ():
            return None, ("simple_cash_conversion_input_derivation_unproven",)
        identities.append(identity)
    if [item.metric for item in identities] != [
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
    ]:
        return None, ("simple_cash_conversion_input_metric_order_invalid",)
    capex_fields = _mapping(input_rows[1].get("fields"))
    assert capex_fields is not None
    if capex_fields.get("capex_scope") != "ppe_only":
        return None, ("simple_cash_conversion_capex_scope_not_ppe_only",)
    compatibility = _same_basis(current, identities)
    if compatibility:
        return None, compatibility
    if current.value != identities[0].value - identities[1].value:
        return None, ("simple_cash_conversion_arithmetic_mismatch",)
    return (
        {
            "formula": SIMPLE_CASH_CONVERSION_FORMULA,
            "input_source_refs": [item.source_ref for item in identities],
            "version": CONTRACT_VERSION,
        },
        (),
    )


def adapt_fact_catalog_financial_context(
    row: Mapping[str, object],
    all_rows: Sequence[Mapping[str, object]],
) -> FinancialContextAdapterResult:
    current, reasons = canonical_identity_from_fact_catalog(row)
    if current is None:
        return FinancialContextAdapterResult(None, reasons)
    rows_by_id = {
        str(item.get("fact_id")): item
        for item in all_rows
        if isinstance(item, Mapping) and item.get("fact_id")
    }
    fact_type = str(row.get("fact_type") or "")
    fields = _mapping(row.get("fields"))
    assert fields is not None
    input_ids = _input_fact_ids(fields)
    if input_ids is None:
        return FinancialContextAdapterResult(None, ("financial_input_refs_invalid",))

    evidence_status = "DIRECT_REPORTED"
    derivation: dict[str, object] | None = None
    limitations: list[str] = []
    if fact_type in _DIRECT_FACT_TYPES:
        if input_ids:
            return FinancialContextAdapterResult(
                None,
                ("derived_period_lineage_metadata_incomplete",),
            )
        if fact_type == "cash_flow_ppe_capex":
            if fields.get("capex_scope") != "ppe_only":
                return FinancialContextAdapterResult(None, ("ppe_capex_scope_not_ppe_only",))
            limitations.append("growth_vs_maintenance_capex_unknown")
    else:
        evidence_status = "DERIVED_SAFE"
        if fields.get("capex_scope") != "ppe_only":
            return FinancialContextAdapterResult(
                None,
                ("simple_cash_conversion_scope_not_ppe_only",),
            )
        derivation, derivation_reasons = _derived_cash_conversion(
            current,
            row,
            rows_by_id,
        )
        if derivation is None:
            return FinancialContextAdapterResult(None, derivation_reasons)
        limitations.extend(
            (
                "growth_vs_maintenance_capex_unknown",
                "ppe_only_not_management_defined_fcf",
            )
        )

    return FinancialContextAdapterResult(
        {
            "metric": current.metric,
            "currency": current.currency,
            "unit_scale": current.unit_scale,
            "period": current.period_payload(),
            "entity_scope": current.entity_scope,
            "statement_basis": current.statement_basis,
            "attribution_basis": current.attribution_basis,
            "evidence_status": evidence_status,
            "quality": "verified",
            "comparison": _prior_comparison(current, all_rows),
            "derivation": derivation,
            "limitations": limitations,
        }
    )
