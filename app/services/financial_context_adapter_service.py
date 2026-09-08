from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from app.services.financial_lineage_projection_service import (
    CONTRACT_VERSION as LINEAGE_PROJECTION_CONTRACT,
    LINEAGE_FIELD,
    lineage_projection_digest,
)


CONTRACT_VERSION = "existing-canonical-financial-domain-adapter-v1"
CANONICAL_CASH_FLOW_SOURCE = "canonical_cash_flow_fact"
SIMPLE_CASH_CONVERSION_METRIC = "ocf_less_ppe_capex"
SIMPLE_CASH_CONVERSION_FORMULA = "ocf_less_ppe_capex"

_FACT_TYPE_METRICS = {
    "cash_flow_ocf": "operating_cash_flow",
    "cash_flow_ppe_capex": "ppe_capex_cash_outflow",
    "cash_flow_fcf_ppe": SIMPLE_CASH_CONVERSION_METRIC,
}
_CANONICAL_METRIC_BY_FACT_TYPE = {
    "cash_flow_ocf": "operating_cash_flow",
    "cash_flow_ppe_capex": "ppe_capex_cash_outflow",
    "cash_flow_fcf_ppe": "free_cash_flow_ppe",
}
_DIRECT_FACT_TYPES = {"cash_flow_ocf", "cash_flow_ppe_capex"}
_COMPARABLE_PERIOD_TYPES = {"QTD", "YTD", "FY", "POINT_IN_TIME"}
_PERIOD_TYPES = {*_COMPARABLE_PERIOD_TYPES, "TTM"}
_ATTRIBUTION_BASES = {"total", "parent", "common"}
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
_SOURCE_REF = re.compile(r"^\S{1,240}$")
_DERIVED_PERIOD_FORMULAS = {
    "Q1_QTD_EQUALS_VERIFIED_Q1_YTD": "q1_qtd_equals_verified_q1_ytd",
    "CURRENT_YTD_MINUS_PRIOR_QUARTER_YTD": (
        "current_ytd_minus_prior_quarter_ytd"
    ),
    "PRIOR_FY_PLUS_CURRENT_YTD_MINUS_PRIOR_COMPARABLE_YTD": (
        "prior_fy_plus_current_ytd_minus_prior_comparable_ytd"
    ),
}
_CANONICAL_FCF_FORMULA = "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
_CANONICAL_DERIVATION_VERSION = "cash-flow-capital-efficiency-v1"
_CANONICAL_FACT_TYPES = {"REPORTED", "DERIVED_PERIOD", "DERIVED_METRIC"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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
    issuer_id: str | None = None
    unit: str | None = None
    semantic_mapping: str | None = None

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


def _lineage_projection(
    row: Mapping[str, object],
) -> tuple[Mapping[str, object] | None, tuple[str, ...]]:
    raw = row.get(LINEAGE_FIELD)
    if raw is None:
        return None, ()
    lineage = _mapping(raw)
    if lineage is None:
        return None, ("canonical_lineage_projection_invalid",)
    reasons: list[str] = []
    if lineage.get("contract") != LINEAGE_PROJECTION_CONTRACT:
        reasons.append("canonical_lineage_projection_contract_invalid")
    fact_type = str(row.get("fact_type") or "")
    canonical_fact_type = str(lineage.get("canonical_fact_type") or "")
    if canonical_fact_type not in _CANONICAL_FACT_TYPES:
        reasons.append("canonical_lineage_fact_type_invalid")
    elif fact_type in _DIRECT_FACT_TYPES and canonical_fact_type not in {
        "REPORTED",
        "DERIVED_PERIOD",
    }:
        reasons.append("canonical_lineage_metric_fact_type_mismatch")
    elif fact_type == "cash_flow_fcf_ppe" and canonical_fact_type != "DERIVED_METRIC":
        reasons.append("canonical_lineage_metric_fact_type_mismatch")
    fields = _mapping(row.get("fields")) or {}
    expected_metric = _CANONICAL_METRIC_BY_FACT_TYPE.get(fact_type)
    identity_pairs = (
        ("fact_id", str(row.get("fact_id") or ""), str),
        ("metric", expected_metric, str),
        ("value", _decimal(fields.get("value")), _decimal),
        ("currency", str(fields.get("currency") or "").upper(), str),
        ("period_start", _date(fields.get("period_start")), _date),
        ("period_end", _date(fields.get("period_end")), _date),
        ("period_type", str(fields.get("period_type") or "").upper(), str),
        ("fiscal_year", _integer(fields.get("fiscal_year")), _integer),
        ("fiscal_quarter", _integer(fields.get("fiscal_quarter")), _integer),
        ("entity_scope", str(fields.get("entity_scope") or ""), str),
        ("statement_basis", str(fields.get("statement_basis") or ""), str),
        ("capex_scope", fields.get("capex_scope"), _text),
    )
    for name, expected, normalizer in identity_pairs:
        if normalizer(lineage.get(name)) != expected:
            reasons.append(f"canonical_lineage_{name}_mismatch")
    field_input_ids = _input_fact_ids(fields)
    projected_ids = lineage.get("ordered_input_fact_ids")
    projected_refs = lineage.get("ordered_input_source_refs")
    if not isinstance(projected_ids, (list, tuple)):
        reasons.append("canonical_lineage_input_ids_invalid")
        input_ids: tuple[str, ...] = ()
    else:
        input_ids = tuple(str(item).strip() for item in projected_ids)
        if any(not item for item in input_ids) or len(input_ids) != len(set(input_ids)):
            reasons.append("canonical_lineage_input_ids_invalid")
    if field_input_ids is None or input_ids != field_input_ids:
        reasons.append("canonical_lineage_input_ids_mismatch")
    expected_refs = tuple(_source_ref(fact_id) for fact_id in input_ids)
    if not isinstance(projected_refs, (list, tuple)) or tuple(
        str(item) for item in projected_refs
    ) != expected_refs:
        reasons.append("canonical_lineage_input_refs_mismatch")
    digest = str(lineage.get("lineage_sha256") or "")
    if digest != lineage_projection_digest(lineage):
        reasons.append("canonical_lineage_digest_mismatch")
    formula = _text(lineage.get("derivation_formula"))
    version = _text(lineage.get("derivation_version"))
    if canonical_fact_type == "REPORTED":
        if formula is not None or version is not None or input_ids:
            reasons.append("reported_fact_has_derivation_lineage")
    elif canonical_fact_type in {"DERIVED_PERIOD", "DERIVED_METRIC"}:
        if formula is None:
            reasons.append("canonical_derivation_formula_missing")
        if version is None or not _IDENTIFIER.fullmatch(version):
            reasons.append("canonical_derivation_version_missing")
        elif version != _CANONICAL_DERIVATION_VERSION:
            reasons.append("canonical_derivation_version_unsupported")
        if not input_ids:
            reasons.append("canonical_derivation_input_refs_missing")
    issuer_id = _text(lineage.get("issuer_id"))
    if issuer_id is None or not _SOURCE_REF.fullmatch(issuer_id):
        reasons.append("canonical_lineage_issuer_id_invalid")
    unit = _text(lineage.get("unit"))
    if unit is None or any(char.isspace() for char in unit):
        reasons.append("canonical_lineage_unit_invalid")
    unit_scale = _integer(lineage.get("unit_scale"))
    if unit_scale != 1:
        reasons.append("canonical_lineage_unit_scale_invalid")
    for field_name in (
        "source_provider",
        "source_document_id",
        "source_occurrence_id",
    ):
        if not _text(lineage.get(field_name)):
            reasons.append(f"canonical_lineage_{field_name}_invalid")
    if not _SHA256.fullmatch(str(lineage.get("raw_payload_sha256") or "")):
        reasons.append("canonical_lineage_raw_payload_sha256_invalid")
    return (
        (None, tuple(dict.fromkeys(reasons)))
        if reasons
        else (lineage, ())
    )


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
    lineage, lineage_reasons = _lineage_projection(row)
    reasons.extend(lineage_reasons)

    value = _decimal(fields.get("value"))
    if value is None:
        reasons.append("financial_value_invalid")
    elif metric == "ppe_capex_cash_outflow" and value < 0:
        reasons.append("ppe_capex_not_positive_outflow")
    currency = str(fields.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        reasons.append("financial_currency_invalid")
    unit_scale = _integer(fields.get("unit_scale"))
    if lineage is not None:
        unit_scale = _integer(lineage.get("unit_scale"))
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
            issuer_id=(
                _text(lineage.get("issuer_id")) if lineage is not None else None
            ),
            unit=_text(lineage.get("unit")) if lineage is not None else None,
            semantic_mapping=(
                _text(lineage.get("semantic_mapping"))
                if lineage is not None
                else None
            ),
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
        "issuer_id",
        "unit",
        "semantic_mapping",
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
    candidates: dict[str, CanonicalFinancialIdentity] = {}
    rows_by_id = {
        str(item.get("fact_id")): item
        for item in rows
        if isinstance(item, Mapping) and item.get("fact_id")
    }
    for row in rows:
        candidate, _reasons = canonical_identity_from_fact_catalog(row)
        if candidate is None:
            continue
        result = prior_year_comparison(current, candidate)
        if result.comparison is None:
            continue
        fields = _mapping(row.get("fields")) or {}
        input_ids = _input_fact_ids(fields)
        if input_ids:
            fact_type = str(row.get("fact_type") or "")
            if fact_type in _DIRECT_FACT_TYPES:
                derivation, _ = _derived_period_lineage(
                    candidate,
                    row,
                    rows_by_id,
                )
            else:
                derivation, _ = _derived_cash_conversion(
                    candidate,
                    row,
                    rows_by_id,
                )
            if derivation is None:
                continue
        candidates[candidate.fact_id] = candidate
    if len(candidates) != 1:
        return None
    prior = next(iter(candidates.values()))
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
        "issuer_id",
        "unit",
    ):
        if len({getattr(item, field_name) for item in (current, *inputs)}) != 1:
            reasons.append(f"derivation_{field_name}_mismatch")
    return tuple(reasons)


def _derived_period_common_compatibility(
    current: CanonicalFinancialIdentity,
    inputs: Sequence[CanonicalFinancialIdentity],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name in (
        "metric",
        "currency",
        "unit_scale",
        "entity_scope",
        "statement_basis",
        "attribution_basis",
        "issuer_id",
        "unit",
        "semantic_mapping",
    ):
        if len({getattr(item, field_name) for item in (current, *inputs)}) != 1:
            reasons.append(f"derived_period_{field_name}_mismatch")
    return tuple(reasons)


def _derived_period_lineage(
    current: CanonicalFinancialIdentity,
    row: Mapping[str, object],
    rows_by_id: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object] | None, tuple[str, ...]]:
    lineage, lineage_reasons = _lineage_projection(row)
    if lineage is None:
        return None, tuple(
            dict.fromkeys(
                ["derived_period_lineage_metadata_incomplete", *lineage_reasons]
            )
        )
    if lineage.get("canonical_fact_type") != "DERIVED_PERIOD":
        return None, ("derived_period_canonical_fact_type_invalid",)
    formula = str(lineage.get("derivation_formula") or "")
    context_formula = _DERIVED_PERIOD_FORMULAS.get(formula)
    if context_formula is None:
        return None, ("derived_period_formula_not_supported",)
    input_ids = tuple(str(item) for item in lineage["ordered_input_fact_ids"])
    input_rows = [rows_by_id.get(fact_id) for fact_id in input_ids]
    if any(item is None for item in input_rows):
        return None, ("derived_period_input_ref_missing",)
    identities: list[CanonicalFinancialIdentity] = []
    for input_row in input_rows:
        assert input_row is not None
        identity, reasons = canonical_identity_from_fact_catalog(input_row)
        if identity is None:
            return None, tuple(
                dict.fromkeys(["derived_period_input_invalid", *reasons])
            )
        input_lineage, input_lineage_reasons = _lineage_projection(input_row)
        if input_lineage is None or input_lineage.get("canonical_fact_type") != "REPORTED":
            return None, tuple(
                dict.fromkeys(
                    [
                        "derived_period_input_not_reported",
                        *input_lineage_reasons,
                    ]
                )
            )
        identities.append(identity)
    reasons = list(_derived_period_common_compatibility(current, identities))
    if formula == "Q1_QTD_EQUALS_VERIFIED_Q1_YTD":
        if len(identities) != 1:
            reasons.append("q1_qtd_requires_one_ytd_input")
        else:
            source = identities[0]
            if current.period_type != "QTD" or current.fiscal_quarter != 1:
                reasons.append("q1_qtd_output_period_invalid")
            if source.period_type != "YTD" or source.fiscal_quarter != 1:
                reasons.append("q1_qtd_input_period_invalid")
            if (
                current.fiscal_year,
                current.period_start,
                current.period_end,
            ) != (
                source.fiscal_year,
                source.period_start,
                source.period_end,
            ):
                reasons.append("q1_qtd_period_identity_mismatch")
            if current.value != source.value:
                reasons.append("q1_qtd_arithmetic_mismatch")
    elif formula == "CURRENT_YTD_MINUS_PRIOR_QUARTER_YTD":
        if len(identities) != 2:
            reasons.append("qtd_difference_requires_two_ytd_inputs")
        else:
            current_ytd, prior_ytd = identities
            if current.period_type != "QTD":
                reasons.append("qtd_difference_output_period_invalid")
            if any(item.period_type != "YTD" for item in identities):
                reasons.append("qtd_difference_ytd_inputs_required")
            if (
                current_ytd.fiscal_year != prior_ytd.fiscal_year
                or current.fiscal_year != current_ytd.fiscal_year
            ):
                reasons.append("qtd_difference_fiscal_year_mismatch")
            if (
                current_ytd.fiscal_quarter is None
                or prior_ytd.fiscal_quarter is None
                or current_ytd.fiscal_quarter != prior_ytd.fiscal_quarter + 1
                or current.fiscal_quarter != current_ytd.fiscal_quarter
            ):
                reasons.append("qtd_difference_quarter_sequence_invalid")
            if current_ytd.period_start != prior_ytd.period_start:
                reasons.append("qtd_difference_fiscal_start_mismatch")
            if (
                current.period_start != prior_ytd.period_end + timedelta(days=1)
                or current.period_end != current_ytd.period_end
            ):
                reasons.append("qtd_difference_output_bounds_invalid")
            if current.value != current_ytd.value - prior_ytd.value:
                reasons.append("qtd_difference_arithmetic_mismatch")
    else:
        if len(identities) != 3:
            reasons.append("ttm_requires_three_ordered_inputs")
        else:
            prior_fy, current_ytd, prior_ytd = identities
            if current.period_type != "TTM":
                reasons.append("ttm_output_period_invalid")
            if prior_fy.period_type != "FY" or any(
                item.period_type != "YTD" for item in (current_ytd, prior_ytd)
            ):
                reasons.append("ttm_input_period_types_invalid")
            if (
                current_ytd.fiscal_year != prior_fy.fiscal_year + 1
                or prior_ytd.fiscal_year != prior_fy.fiscal_year
                or current.fiscal_year != current_ytd.fiscal_year
            ):
                reasons.append("ttm_fiscal_relationship_invalid")
            if (
                current_ytd.fiscal_quarter != prior_ytd.fiscal_quarter
                or current_ytd.duration_days != prior_ytd.duration_days
            ):
                reasons.append("ttm_comparable_ytd_mismatch")
            if (
                current.period_start != prior_ytd.period_end + timedelta(days=1)
                or current.period_end != current_ytd.period_end
            ):
                reasons.append("ttm_output_bounds_invalid")
            if current.value != prior_fy.value + current_ytd.value - prior_ytd.value:
                reasons.append("ttm_arithmetic_mismatch")
    if reasons:
        return None, tuple(dict.fromkeys(reasons))
    return (
        {
            "formula": context_formula,
            "input_source_refs": [item.source_ref for item in identities],
            "version": str(lineage["derivation_version"]),
        },
        (),
    )


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
    output_lineage, output_lineage_reasons = _lineage_projection(row)
    if output_lineage_reasons:
        return None, output_lineage_reasons
    if output_lineage is not None and (
        output_lineage.get("canonical_fact_type") != "DERIVED_METRIC"
        or output_lineage.get("derivation_formula") != _CANONICAL_FCF_FORMULA
        or tuple(output_lineage.get("ordered_input_fact_ids") or ()) != input_ids
    ):
        return None, ("simple_cash_conversion_canonical_lineage_invalid",)
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
        nested_input_ids = _input_fact_ids(input_fields)
        if nested_input_ids is None:
            return None, ("simple_cash_conversion_input_refs_invalid",)
        if nested_input_ids:
            nested, nested_reasons = _derived_period_lineage(
                identity,
                input_row,
                rows_by_id,
            )
            if nested is None:
                return None, tuple(
                    dict.fromkeys(
                        [
                            "simple_cash_conversion_input_derivation_unproven",
                            *nested_reasons,
                        ]
                    )
                )
        else:
            input_lineage, input_lineage_reasons = _lineage_projection(input_row)
            if input_lineage_reasons:
                return None, input_lineage_reasons
            if (
                input_lineage is not None
                and input_lineage.get("canonical_fact_type") != "REPORTED"
            ):
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
            derivation, derivation_reasons = _derived_period_lineage(
                current,
                row,
                rows_by_id,
            )
            if derivation is None:
                return FinancialContextAdapterResult(None, derivation_reasons)
            evidence_status = "DERIVED_SAFE"
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
