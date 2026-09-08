from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.action_schema import build_action_schema
from app.main import app
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
    FinancialContext,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.structured_autonomy_alias_service import evidence_content_sha256


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_PACKET_PATH = (
    REPO_ROOT / "docs/reports/20260902-run51-v2-accepted-artifact.json"
)
LEGACY_ARCHIVE_CANONICAL_SHA256 = (
    "6c9d6488e13115a49d2c5aa51563b0a2028ec1ab92d8081821cb32cd1b1cfd8e"
)


def _period_payload(period_type: str = "YTD") -> dict[str, object]:
    if period_type == "POINT_IN_TIME":
        return {
            "type": period_type,
            "start": None,
            "end": "2026-06-30",
            "duration_days": None,
        }
    start = "2025-07-01" if period_type == "FY" else "2026-01-01"
    end = "2026-06-30"
    return {
        "type": period_type,
        "start": start,
        "end": end,
        "duration_days": (date.fromisoformat(end) - date.fromisoformat(start)).days + 1,
    }


def _direct_context_payload(
    *,
    metric: str = "operating_cash_flow",
    period_type: str = "YTD",
    currency: str | None = "USD",
) -> dict[str, object]:
    return {
        "metric": metric,
        "currency": currency,
        "unit_scale": 1,
        "period": _period_payload(period_type),
        "entity_scope": "issuer_consolidated",
        "statement_basis": "official_financial_statement",
        "attribution_basis": "total",
        "evidence_status": "DIRECT_REPORTED",
        "quality": "verified",
        "comparison": None,
        "derivation": None,
        "limitations": [],
    }


def _derivation_payload(
    formula: str,
    input_source_refs: tuple[str, ...] = ("source.current", "source.prior"),
) -> dict[str, object]:
    return {
        "formula": formula,
        "input_source_refs": input_source_refs,
        "version": "financial-derivation-v1",
    }


def _derived_context_payload(
    *,
    metric: str,
    formula: str,
    period_type: str,
    input_source_refs: tuple[str, ...] = ("source.current", "source.prior"),
) -> dict[str, object]:
    payload = _direct_context_payload(metric=metric, period_type=period_type)
    payload["evidence_status"] = "DERIVED_SAFE"
    payload["derivation"] = _derivation_payload(formula, input_source_refs)
    return payload


def _evidence_ref(financial_context: FinancialContext | None = None) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="canonical:financial:test",
        category=EvidenceCategory.EARNINGS_QUALITY,
        label="financial fixture",
        statement="offline typed financial evidence fixture",
        as_of="2026-06-30",
        value=Decimal("1250000"),
        unit="currency",
        source_ref="fixture.financial.test",
        numeric_prose_eligible=True,
        financial_context=financial_context,
    )


@pytest.mark.parametrize(
    ("domain", "payload"),
    (
        (
            "same_period_prior_year_comparison",
            {
                **_direct_context_payload(metric="revenue", period_type="YTD"),
                "comparison": {
                    "kind": "prior_year_comparable",
                    "compatibility_status": "PASS",
                    "input_source_refs": ["filing.current.revenue", "filing.prior.revenue"],
                },
            },
        ),
        ("operating_cash_flow", _direct_context_payload()),
        (
            "ppe_capex_simple_cash_conversion",
            _direct_context_payload(metric="ppe_capex_cash_outflow"),
        ),
        (
            "debt_liquidity",
            _direct_context_payload(
                metric="cash_and_cash_equivalents",
                period_type="POINT_IN_TIME",
            ),
        ),
        (
            "inventory_receivables_working_capital",
            _direct_context_payload(metric="inventory", period_type="POINT_IN_TIME"),
        ),
        (
            "non_operating_financial_income_effects",
            _direct_context_payload(metric="interest_income", period_type="FY"),
        ),
    ),
)
def test_six_financial_domains_support_typed_direct_reported_context(
    domain: str,
    payload: dict[str, object],
) -> None:
    context = FinancialContext.model_validate(payload)
    ref = _evidence_ref(context)

    assert domain
    assert context.evidence_status == FinancialEvidenceStatus.DIRECT_REPORTED
    assert context.derivation is None
    assert context.currency == "USD"
    assert ref.model_dump(mode="json")["financial_context"]["metric"] == context.metric


@pytest.mark.parametrize(
    ("formula", "metric", "period_type", "input_refs"),
    (
        (
            "same_period_absolute_delta",
            "revenue_absolute_delta",
            "YTD",
            ("revenue.current", "revenue.prior_comparable"),
        ),
        (
            "qtd_from_compatible_ytd",
            "revenue",
            "QTD",
            ("revenue.current_ytd", "revenue.prior_quarter_ytd"),
        ),
        (
            "ocf_ttm",
            "operating_cash_flow",
            "TTM",
            ("ocf.prior_fy", "ocf.current_ytd", "ocf.prior_comparable_ytd"),
        ),
        (
            "ocf_less_ppe_capex",
            "free_cash_flow_ppe",
            "YTD",
            ("ocf.current_ytd", "ppe_capex.current_ytd"),
        ),
        (
            "interest_bearing_debt_total",
            "interest_bearing_debt",
            "POINT_IN_TIME",
            ("debt.current_portion", "debt.long_term"),
        ),
        (
            "net_debt",
            "net_debt",
            "POINT_IN_TIME",
            ("debt.interest_bearing_total", "cash.compatible"),
        ),
        (
            "balance_absolute_delta",
            "inventory_absolute_delta",
            "POINT_IN_TIME",
            ("inventory.current", "inventory.prior_comparable"),
        ),
        (
            "verified_non_operating_component_sum",
            "non_operating_financial_income",
            "FY",
            ("interest.income", "interest.expense", "other.financial"),
        ),
    ),
)
def test_eight_safe_derivations_preserve_ordered_input_lineage(
    formula: str,
    metric: str,
    period_type: str,
    input_refs: tuple[str, ...],
) -> None:
    context = FinancialContext.model_validate(
        _derived_context_payload(
            metric=metric,
            formula=formula,
            period_type=period_type,
            input_source_refs=input_refs,
        )
    )

    assert context.evidence_status == FinancialEvidenceStatus.DERIVED_SAFE
    assert context.derivation is not None
    assert context.derivation.formula == formula
    assert context.derivation.input_source_refs == input_refs
    assert context.derivation.version == "financial-derivation-v1"


@pytest.mark.parametrize("period_type", tuple(FinancialPeriodType))
def test_all_financial_period_types_are_structurally_supported(
    period_type: FinancialPeriodType,
) -> None:
    period = FinancialPeriod.model_validate(_period_payload(period_type.value))

    assert period.type == period_type
    if period_type == FinancialPeriodType.POINT_IN_TIME:
        assert period.start is None
        assert period.duration_days is None
    else:
        assert period.start is not None
        assert period.duration_days is not None


def test_comparison_contract_preserves_kind_compatibility_and_order() -> None:
    comparable = FinancialComparison(
        kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        input_source_refs=("current.fact", "prior.fact"),
    )
    year_end = FinancialComparison(
        kind=FinancialComparisonKind.PRIOR_YEAR_END,
        input_source_refs=("current.fact", "prior.year_end.fact"),
    )
    none = FinancialComparison(kind=FinancialComparisonKind.NONE)

    assert comparable.compatibility_status == "PASS"
    assert comparable.input_source_refs == ("current.fact", "prior.fact")
    assert year_end.input_source_refs[-1] == "prior.year_end.fact"
    assert none.input_source_refs == ()


def test_non_currency_metric_may_omit_currency_under_bounded_registry() -> None:
    context = FinancialContext.model_validate(
        _direct_context_payload(
            metric="return_on_invested_capital",
            period_type="FY",
            currency=None,
        )
    )

    assert context.currency is None


def _invalid_context(case: str) -> dict[str, object]:
    payload = _direct_context_payload()
    if case == "derived_without_derivation":
        payload["evidence_status"] = "DERIVED_SAFE"
    elif case == "direct_with_derivation":
        payload["derivation"] = _derivation_payload("ocf_ttm")
    elif case == "duration_without_start":
        payload["period"] = {**_period_payload(), "start": None}
    elif case == "point_in_time_with_start":
        payload["period"] = {**_period_payload("POINT_IN_TIME"), "start": "2026-06-30"}
    elif case == "point_in_time_with_duration":
        payload["period"] = {**_period_payload("POINT_IN_TIME"), "duration_days": 1}
    elif case == "end_before_start":
        payload["period"] = {
            "type": "FY",
            "start": "2026-01-02",
            "end": "2026-01-01",
            "duration_days": 1,
        }
    elif case == "duration_mismatch":
        payload["period"] = {**_period_payload(), "duration_days": 1}
    elif case == "comparison_without_refs":
        payload["comparison"] = {
            "kind": "prior_year_comparable",
            "compatibility_status": "PASS",
            "input_source_refs": [],
        }
    elif case == "none_comparison_with_refs":
        payload["comparison"] = {
            "kind": "none",
            "compatibility_status": "PASS",
            "input_source_refs": ["unexpected.ref"],
        }
    elif case == "empty_metric":
        payload["metric"] = " "
    elif case == "missing_currency":
        payload["currency"] = None
    elif case == "invalid_unit_scale":
        payload["unit_scale"] = 0
    elif case == "empty_derivation_refs":
        payload["evidence_status"] = "DERIVED_SAFE"
        payload["derivation"] = _derivation_payload("ocf_ttm", ())
    elif case == "empty_limitation":
        payload["limitations"] = [""]
    elif case == "duplicate_comparison_ref":
        payload["comparison"] = {
            "kind": "prior_year_comparable",
            "compatibility_status": "PASS",
            "input_source_refs": ["same.ref", "same.ref"],
        }
    elif case == "duplicate_derivation_ref":
        payload["evidence_status"] = "DERIVED_SAFE"
        payload["derivation"] = _derivation_payload(
            "ocf_ttm", ("same.ref", "same.ref")
        )
    elif case == "unknown_evidence_status":
        payload["evidence_status"] = "ESTIMATED"
    elif case == "invalid_period_type":
        payload["period"] = {**_period_payload(), "type": "QUARTER"}
    elif case == "ambiguous_attribution":
        payload["attribution_basis"] = "controlling_or_total"
    else:  # pragma: no cover - test table guards this branch
        raise AssertionError(case)
    return payload


@pytest.mark.parametrize(
    "case",
    (
        "derived_without_derivation",
        "direct_with_derivation",
        "duration_without_start",
        "point_in_time_with_start",
        "point_in_time_with_duration",
        "end_before_start",
        "duration_mismatch",
        "comparison_without_refs",
        "none_comparison_with_refs",
        "empty_metric",
        "missing_currency",
        "invalid_unit_scale",
        "empty_derivation_refs",
        "empty_limitation",
        "duplicate_comparison_ref",
        "duplicate_derivation_ref",
        "unknown_evidence_status",
        "invalid_period_type",
        "ambiguous_attribution",
    ),
)
def test_malformed_financial_context_fails_closed(case: str) -> None:
    with pytest.raises(ValidationError):
        FinancialContext.model_validate(_invalid_context(case))


def test_legacy_ref_serialization_and_roundtrip_are_byte_shape_compatible() -> None:
    ref = _evidence_ref()
    expected = {
        "ref_id": "canonical:financial:test",
        "category": "earnings_quality",
        "label": "financial fixture",
        "statement": "offline typed financial evidence fixture",
        "as_of": "2026-06-30",
        "value": "1250000",
        "unit": "currency",
        "source_ref": "fixture.financial.test",
        "numeric_prose_eligible": True,
        "metric_refs": [],
        "logical_condition": None,
    }

    dumped = ref.model_dump(mode="json")
    assert dumped == expected
    assert "financial_context" not in dumped
    restored = DecisionEvidenceRef.model_validate(dumped)
    assert restored.model_dump(mode="json") == dumped


def test_archived_packet_parse_and_canonical_hash_remain_unchanged() -> None:
    rows = json.loads(ARCHIVED_PACKET_PATH.read_text(encoding="utf-8"))["evidence_packets"]
    packets = tuple(DecisionEvidencePacket.model_validate(row) for row in rows)
    canonical = [packet.model_dump(mode="json") for packet in packets]
    serialized = json.dumps(
        canonical,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    assert len(packets) == 14
    assert all(
        "financial_context" not in ref
        for packet in canonical
        for ref in packet["evidence"]
    )
    assert hashlib.sha256(serialized).hexdigest() == LEGACY_ARCHIVE_CANONICAL_SHA256


def test_typed_context_serialization_and_content_hash_are_deterministic() -> None:
    payload = _derived_context_payload(
        metric="free_cash_flow_ppe",
        formula="ocf_less_ppe_capex",
        period_type="YTD",
        input_source_refs=("ocf.current", "ppe.current"),
    )
    first = _evidence_ref(FinancialContext.model_validate(payload))
    reordered = {key: payload[key] for key in reversed(payload)}
    second = _evidence_ref(FinancialContext.model_validate(reordered))

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert evidence_content_sha256(first) == evidence_content_sha256(second)
    assert "financial_context" in first.model_dump(mode="json")


def test_financial_context_is_optional_in_internal_json_schema_only() -> None:
    schema = DecisionEvidenceRef.model_json_schema()
    public_action = build_action_schema(app)
    operation_ids = [
        operation["operationId"]
        for path_item in public_action["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]

    assert "financial_context" in schema["properties"]
    assert "financial_context" not in schema.get("required", [])
    assert "FinancialContext" in schema["$defs"]
    assert "FinancialContext" not in public_action["components"]["schemas"]
    assert public_action["info"]["version"] == "0.4.5"
    assert len(operation_ids) == len(set(operation_ids)) == 20


def test_production_builder_does_not_emit_or_consume_financial_context() -> None:
    packet = build_decision_evidence_packet(
        packet={
            "packet_id": "m5-offline-producer-negative-control",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        stock={
            "ticker": "M5FIXTURE",
            "company_name": "M5 Fixture",
            "fact_catalog": [
                {
                    "fact_id": "cashflow-reported:fixture",
                    "fact_type": "cash_flow_ocf",
                    "as_of_date": "2026-06-30",
                    "fields": {"value": "100"},
                }
            ],
        },
    )
    compact = compact_ai_context(packet)

    assert packet.evidence
    assert all(ref.financial_context is None for ref in packet.evidence)
    assert all(
        "financial_context" not in ref.model_dump(mode="json")
        for ref in packet.evidence
    )
    assert all("financial_context" not in row for row in compact["evidence"])


def test_schema_rejects_unowned_domain_compatibility_shortcuts() -> None:
    payload = _derived_context_payload(
        metric="interest_bearing_debt",
        formula="interest_bearing_debt_total",
        period_type="POINT_IN_TIME",
    )
    payload["debt_components_complete"] = True

    with pytest.raises(ValidationError):
        FinancialContext.model_validate(payload)


def test_models_are_frozen_and_fixture_input_is_not_mutated() -> None:
    payload = _direct_context_payload()
    original = deepcopy(payload)
    context = FinancialContext.model_validate(payload)

    assert payload == original
    with pytest.raises(ValidationError):
        context.metric = "revenue"
