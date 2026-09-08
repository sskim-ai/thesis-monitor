from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    FundamentalEvidenceFamily,
    evaluate_source_sufficiency,
)
from app.services.cash_flow_capital_efficiency_service import financial_fact_from_mapping
from app.services.cash_flow_user_visible_service import fact_catalog_entries
from app.services.cross_market_decision_engine_service import (
    FinancialEvidenceStatus,
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.financial_context_adapter_service import (
    CONTRACT_VERSION,
    CanonicalFinancialIdentity,
    adapt_fact_catalog_financial_context,
    canonical_identity_from_fact_catalog,
    prior_year_comparison,
)
from app.services.nonproduction_lifecycle_decision_service import (
    DeltaState,
    LifecycleMode,
    NonproductionLifecycleContext,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _period(
    period_type: str,
    fiscal_year: int,
    *,
    fiscal_quarter: int | None = None,
) -> tuple[str | None, str]:
    if period_type == "QTD":
        assert fiscal_quarter == 2
        return f"{fiscal_year}-04-01", f"{fiscal_year}-06-30"
    if period_type == "YTD":
        return f"{fiscal_year}-01-01", f"{fiscal_year}-06-30"
    if period_type == "FY":
        return f"{fiscal_year}-01-01", f"{fiscal_year}-12-31"
    if period_type == "POINT_IN_TIME":
        return None, f"{fiscal_year}-06-30"
    raise AssertionError(period_type)


def _row(
    fact_id: str,
    fact_type: str,
    value: str,
    *,
    period_type: str = "YTD",
    fiscal_year: int = 2026,
    fiscal_quarter: int | None = 2,
    currency: str = "USD",
    entity_scope: str = "issuer_consolidated",
    statement_basis: str = "official_filing_cash_flow_statement",
    attribution_basis: str | None = None,
    input_fact_ids: tuple[str, ...] = (),
    capex_scope: str | None = None,
    period_start: str | None | object = ...,
) -> dict[str, object]:
    start, end = _period(
        period_type,
        fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )
    if period_start is not ...:
        start = period_start if isinstance(period_start, str) else None
    fields: dict[str, object] = {
        "value": value,
        "currency": currency,
        "period_start": start,
        "period_end": end,
        "period_type": period_type,
        "fiscal_year": str(fiscal_year),
        "fiscal_quarter": (
            str(fiscal_quarter) if fiscal_quarter is not None else None
        ),
        "entity_scope": entity_scope,
        "statement_basis": statement_basis,
        "attribution_basis": attribution_basis,
        "capex_scope": capex_scope,
        "input_fact_ids": list(input_fact_ids),
        "cash_flow_user_visible_context_id": "fixture-context",
    }
    return {
        "fact_id": fact_id,
        "fact_type": fact_type,
        "as_of_date": end,
        "source": "canonical_cash_flow_fact",
        "fields": fields,
        "prose_eligible": True,
        "interpretation_eligible": True,
        "numeric_registry_eligible": True,
    }


def _cash_conversion_rows(
    *,
    period_type: str = "YTD",
    currency: str = "USD",
    entity_scope: str = "issuer_consolidated",
    statement_basis: str = "official_filing_cash_flow_statement",
    input_ids: tuple[str, ...] = ("ocf.current", "ppe.current"),
    fcf_value: str = "60",
) -> list[dict[str, object]]:
    quarter = 2 if period_type in {"QTD", "YTD"} else None
    ocf = _row(
        "ocf.current",
        "cash_flow_ocf",
        "100",
        period_type=period_type,
        fiscal_quarter=quarter,
        currency=currency,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
    )
    capex = _row(
        "ppe.current",
        "cash_flow_ppe_capex",
        "40",
        period_type=period_type,
        fiscal_quarter=quarter,
        currency=currency,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        capex_scope="ppe_only",
    )
    fcf = _row(
        "fcf.current",
        "cash_flow_fcf_ppe",
        fcf_value,
        period_type=period_type,
        fiscal_quarter=quarter,
        currency=currency,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        input_fact_ids=input_ids,
        capex_scope="ppe_only",
    )
    return [ocf, capex, fcf]


def _identity(
    *,
    fact_id: str,
    metric: str = "operating_cash_flow",
    period_type: str = "YTD",
    fiscal_year: int = 2026,
    fiscal_quarter: int | None = 2,
    currency: str = "USD",
    entity_scope: str = "issuer_consolidated",
    statement_basis: str = "official_financial_statement",
    attribution_basis: str | None = "total",
) -> CanonicalFinancialIdentity:
    start_text, end_text = _period(
        period_type,
        fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )
    start = date.fromisoformat(start_text) if start_text else None
    end = date.fromisoformat(end_text)
    return CanonicalFinancialIdentity(
        fact_id=fact_id,
        source_ref=f"fixture.{fact_id}",
        metric=metric,
        value=Decimal("100"),
        currency=currency,
        unit_scale=1,
        period_type=period_type,
        period_start=start,
        period_end=end,
        duration_days=((end - start).days + 1 if start else None),
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        attribution_basis=attribution_basis,
    )


@pytest.mark.parametrize(
    ("period_type", "quarter"),
    (("QTD", 2), ("YTD", 2), ("FY", None)),
)
def test_same_period_prior_year_comparison_emits_only_compatible_lineage(
    period_type: str,
    quarter: int | None,
) -> None:
    current = _row(
        "ocf.current",
        "cash_flow_ocf",
        "100",
        period_type=period_type,
        fiscal_year=2026,
        fiscal_quarter=quarter,
    )
    prior = _row(
        "ocf.prior",
        "cash_flow_ocf",
        "80",
        period_type=period_type,
        fiscal_year=2025,
        fiscal_quarter=quarter,
    )

    adapted = adapt_fact_catalog_financial_context(current, [current, prior])

    assert adapted.denial_reasons == ()
    assert adapted.context is not None
    assert adapted.context["comparison"] == {
        "kind": "prior_year_comparable",
        "compatibility_status": "PASS",
        "input_source_refs": [
            "stock.fact_catalog.ocf.current",
            "stock.fact_catalog.ocf.prior",
        ],
    }


def test_point_in_time_prior_year_comparison_is_supported_by_shared_adapter() -> None:
    current = _identity(
        fact_id="cash.current",
        metric="cash_and_cash_equivalents",
        period_type="POINT_IN_TIME",
        fiscal_year=2026,
        fiscal_quarter=None,
    )
    prior = _identity(
        fact_id="cash.prior",
        metric="cash_and_cash_equivalents",
        period_type="POINT_IN_TIME",
        fiscal_year=2025,
        fiscal_quarter=None,
    )

    result = prior_year_comparison(current, prior)

    assert result.denial_reasons == ()
    assert result.comparison is not None
    assert result.comparison["input_source_refs"] == [
        "fixture.cash.current",
        "fixture.cash.prior",
    ]


@pytest.mark.parametrize(
    ("fact_type", "period_type", "quarter", "metric"),
    (
        ("cash_flow_ocf", "YTD", 2, "operating_cash_flow"),
        ("cash_flow_ocf", "FY", None, "operating_cash_flow"),
        ("cash_flow_ppe_capex", "YTD", 2, "ppe_capex_cash_outflow"),
        ("cash_flow_ppe_capex", "FY", None, "ppe_capex_cash_outflow"),
    ),
)
def test_direct_ocf_and_ppe_context_preserve_reported_period_and_basis(
    fact_type: str,
    period_type: str,
    quarter: int | None,
    metric: str,
) -> None:
    row = _row(
        f"{fact_type}.{period_type}",
        fact_type,
        "100",
        period_type=period_type,
        fiscal_quarter=quarter,
        capex_scope="ppe_only" if fact_type == "cash_flow_ppe_capex" else None,
    )

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is not None
    assert result.context["metric"] == metric
    assert result.context["evidence_status"] == "DIRECT_REPORTED"
    assert result.context["period"]["type"] == period_type
    assert result.context["derivation"] is None
    if fact_type == "cash_flow_ppe_capex":
        assert result.context["limitations"] == [
            "growth_vs_maintenance_capex_unknown"
        ]


@pytest.mark.parametrize("market_prefix", ("us", "kr"))
def test_explicit_known_period_is_market_neutral_and_allowed(
    market_prefix: str,
) -> None:
    row = _row(
        f"{market_prefix}.ocf.known",
        "cash_flow_ocf",
        "100",
    )

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is not None
    assert result.context["period"]["start"] == "2026-01-01"


@pytest.mark.parametrize("period_type", ("YTD", "FY"))
def test_ocf_less_ppe_context_is_safe_derived_and_fully_lineaged(
    period_type: str,
) -> None:
    rows = _cash_conversion_rows(period_type=period_type)

    result = adapt_fact_catalog_financial_context(rows[2], rows)

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["metric"] == "ocf_less_ppe_capex"
    assert result.context["evidence_status"] == "DERIVED_SAFE"
    assert result.context["derivation"] == {
        "formula": "ocf_less_ppe_capex",
        "input_source_refs": [
            "stock.fact_catalog.ocf.current",
            "stock.fact_catalog.ppe.current",
        ],
        "version": CONTRACT_VERSION,
    }
    assert result.context["limitations"] == [
        "growth_vs_maintenance_capex_unknown",
        "ppe_only_not_management_defined_fcf",
    ]


@pytest.mark.parametrize(
    ("change", "expected_reason"),
    (
        ({"period_type": "QTD"}, "comparison_period_type_mismatch"),
        ({"metric": "revenue"}, "comparison_metric_mismatch"),
        ({"currency": "KRW"}, "comparison_currency_mismatch"),
        ({"entity_scope": "issuer_separate"}, "comparison_entity_scope_mismatch"),
        ({"statement_basis": "separate_statement"}, "comparison_statement_basis_mismatch"),
        ({"attribution_basis": "parent"}, "comparison_attribution_basis_mismatch"),
    ),
)
def test_incompatible_prior_year_comparison_fails_closed(
    change: dict[str, object],
    expected_reason: str,
) -> None:
    current = _identity(fact_id="current")
    prior_values = {
        "fact_id": "prior",
        "fiscal_year": 2025,
        **change,
    }
    if change.get("period_type") == "QTD":
        prior_values["fiscal_quarter"] = 2
    prior = _identity(**prior_values)

    result = prior_year_comparison(current, prior)

    assert result.comparison is None
    assert expected_reason in result.denial_reasons


@pytest.mark.parametrize(
    ("fact_type", "fact_id"),
    (
        ("cash_flow_ocf", "kr.ocf.ambiguous"),
        ("cash_flow_ppe_capex", "kr.ppe.ambiguous"),
    ),
)
def test_kr_ambiguous_duration_period_is_not_emitted(
    fact_type: str,
    fact_id: str,
) -> None:
    row = _row(
        fact_id,
        fact_type,
        "100",
        period_start=None,
        capex_scope="ppe_only" if fact_type == "cash_flow_ppe_capex" else None,
    )

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is None
    assert "financial_duration_period_start_required" in result.denial_reasons


def test_us_ocf_duration_without_start_is_not_emitted() -> None:
    row = _row(
        "us.ocf.missing-start",
        "cash_flow_ocf",
        "100",
        period_start=None,
    )

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is None
    assert "financial_duration_period_start_required" in result.denial_reasons


def _mutate_fields(row: dict[str, object], **values: object) -> dict[str, object]:
    fields = dict(row["fields"])
    fields.update(values)
    return {**row, "fields": fields}


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    (
        ("period", "derivation_period_type_mismatch"),
        ("currency", "derivation_currency_mismatch"),
        ("entity", "derivation_entity_scope_mismatch"),
        ("statement", "derivation_statement_basis_mismatch"),
        ("attribution", "derivation_attribution_basis_mismatch"),
        ("missing_ref", "simple_cash_conversion_input_ref_missing"),
        ("wrong_order", "simple_cash_conversion_input_metric_order_invalid"),
        ("derived_input", "simple_cash_conversion_input_derivation_unproven"),
        ("arithmetic", "simple_cash_conversion_arithmetic_mismatch"),
        ("capex_scope", "simple_cash_conversion_capex_scope_not_ppe_only"),
    ),
)
def test_unsafe_cash_conversion_derivation_is_not_emitted(
    mutation: str,
    expected_reason: str,
) -> None:
    rows = _cash_conversion_rows()
    if mutation == "period":
        rows[1] = _row(
            "ppe.current",
            "cash_flow_ppe_capex",
            "40",
            period_type="FY",
            fiscal_quarter=None,
            capex_scope="ppe_only",
        )
    elif mutation == "currency":
        rows[1] = _mutate_fields(rows[1], currency="KRW")
    elif mutation == "entity":
        rows[1] = _mutate_fields(rows[1], entity_scope="issuer_separate")
    elif mutation == "statement":
        rows[1] = _mutate_fields(rows[1], statement_basis="separate_cash_flow_statement")
    elif mutation == "attribution":
        rows[1] = _mutate_fields(rows[1], attribution_basis="parent")
    elif mutation == "missing_ref":
        rows[2] = _mutate_fields(
            rows[2], input_fact_ids=["ocf.current", "ppe.missing"]
        )
    elif mutation == "wrong_order":
        rows[2] = _mutate_fields(
            rows[2], input_fact_ids=["ppe.current", "ocf.current"]
        )
    elif mutation == "derived_input":
        rows[0] = _mutate_fields(rows[0], input_fact_ids=["ocf.raw"])
    elif mutation == "arithmetic":
        rows[2] = _mutate_fields(rows[2], value="61")
    elif mutation == "capex_scope":
        rows[1] = _mutate_fields(rows[1], capex_scope="ppe_plus_intangibles")

    result = adapt_fact_catalog_financial_context(rows[2], rows)

    assert result.context is None
    assert expected_reason in result.denial_reasons


def test_non_m6_financial_domains_are_not_accidentally_adapted() -> None:
    row = _row("inventory.current", "working_capital_inventory", "100")

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is None
    assert "metric_not_in_m6_adapter_scope" in result.denial_reasons


def test_noncanonical_unit_scale_is_not_ad_hoc_normalized() -> None:
    row = _row("ocf.scaled", "cash_flow_ocf", "100")
    row = _mutate_fields(row, unit_scale=1000)

    identity, reasons = canonical_identity_from_fact_catalog(row)

    assert identity is None
    assert "noncanonical_unit_scale_not_supported" in reasons


def test_negative_ppe_value_is_not_reinterpreted_as_positive_outflow() -> None:
    row = _row(
        "ppe.negative",
        "cash_flow_ppe_capex",
        "-40",
        capex_scope="ppe_only",
    )

    result = adapt_fact_catalog_financial_context(row, [row])

    assert result.context is None
    assert "ppe_capex_not_positive_outflow" in result.denial_reasons


def test_cash_conversion_output_without_ppe_only_scope_is_not_emitted() -> None:
    rows = _cash_conversion_rows()
    rows[2] = _mutate_fields(rows[2], capex_scope=None)

    result = adapt_fact_catalog_financial_context(rows[2], rows)

    assert result.context is None
    assert "simple_cash_conversion_scope_not_ppe_only" in result.denial_reasons


def test_packet_builder_emits_typed_context_without_model_input_leak() -> None:
    rows = _cash_conversion_rows()
    enriched = build_decision_evidence_packet(
        packet={
            "packet_id": "m6-offline-context-emission",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        stock={
            "ticker": "M6FIXTURE",
            "company_name": "M6 Fixture",
            "fact_catalog": rows,
        },
    )
    legacy = enriched.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None})
                for ref in enriched.evidence
            )
        }
    )

    contexts = {
        ref.label: ref.financial_context
        for ref in enriched.evidence
        if ref.label.startswith("cash_flow_")
    }
    assert set(contexts) == {
        "cash_flow_ocf",
        "cash_flow_ppe_capex",
        "cash_flow_fcf_ppe",
    }
    assert all(context is not None for context in contexts.values())
    assert contexts["cash_flow_ocf"].evidence_status == (
        FinancialEvidenceStatus.DIRECT_REPORTED
    )
    assert contexts["cash_flow_fcf_ppe"].evidence_status == (
        FinancialEvidenceStatus.DERIVED_SAFE
    )
    before = compact_ai_context(legacy)
    after = compact_ai_context(enriched)
    assert after == before
    assert hashlib.sha256(
        json.dumps(after, sort_keys=True, default=str).encode()
    ).hexdigest() == hashlib.sha256(
        json.dumps(before, sort_keys=True, default=str).encode()
    ).hexdigest()
    assert all("financial_context" not in row for row in after["evidence"])


def test_preserved_phase9_canonical_chain_emits_without_new_source_mapping() -> None:
    report = json.loads(
        (REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json").read_text(
            encoding="utf-8"
        )
    )
    raw_fcf = next(
        row
        for row in report["canonical_facts"]
        if row["metric"] == "free_cash_flow_ppe"
        and row["fact_type"] == "DERIVED_METRIC"
        and len(row["input_fact_ids"]) == 2
    )
    by_id = {row["fact_id"]: row for row in report["canonical_facts"]}
    facts = tuple(
        financial_fact_from_mapping(by_id[fact_id])
        for fact_id in (*raw_fcf["input_fact_ids"], raw_fcf["fact_id"])
    )
    rows = fact_catalog_entries(
        SimpleNamespace(
            user_visible_enabled=True,
            facts=facts,
            context_id="m6-preserved-phase9-fixture",
        )
    )

    packet = build_decision_evidence_packet(
        packet={
            "packet_id": "m6-preserved-phase9",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        stock={"ticker": str(raw_fcf["ticker"]), "fact_catalog": rows},
    )
    financial_refs = [
        ref for ref in packet.evidence if ref.financial_context is not None
    ]

    assert len(financial_refs) == 3
    assert {ref.financial_context.metric for ref in financial_refs} == {
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
        "ocf_less_ppe_capex",
    }
    assert next(
        ref for ref in financial_refs if ref.financial_context.metric == "ocf_less_ppe_capex"
    ).financial_context.derivation.input_source_refs == tuple(
        f"stock.fact_catalog.{fact_id}" for fact_id in raw_fcf["input_fact_ids"]
    )


def test_adapter_and_packet_build_are_idempotent_without_duplicate_refs() -> None:
    rows = _cash_conversion_rows()
    first_context = adapt_fact_catalog_financial_context(rows[2], rows)
    second_context = adapt_fact_catalog_financial_context(rows[2], rows)
    args = {
        "packet": {
            "packet_id": "m6-idempotency",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        "stock": {"ticker": "M6IDEMPOTENT", "fact_catalog": rows},
    }

    first_packet = build_decision_evidence_packet(**args)
    second_packet = build_decision_evidence_packet(**args)

    assert first_context == second_context
    assert first_packet == second_packet
    assert first_packet.evidence_sha256 == second_packet.evidence_sha256
    ref_ids = [ref.ref_id for ref in first_packet.evidence]
    canonical_ref_ids = [ref_id for ref_id in ref_ids if ref_id.startswith("canonical:")]
    assert len(ref_ids) == len(set(ref_ids))
    assert len(canonical_ref_ids) == len(set(canonical_ref_ids)) == 3


def test_source_sufficiency_is_identical_with_optional_packet_metadata() -> None:
    facts = [
        {
            "fact_id": "identity",
            "evidence_family": FundamentalEvidenceFamily.IDENTITY_SECURITY.value,
            "evidence_quality": "current",
        },
        {
            "fact_id": "business",
            "evidence_family": FundamentalEvidenceFamily.BUSINESS_CURRENT.value,
            "evidence_quality": "current",
        },
        {
            "fact_id": "earnings",
            "evidence_family": FundamentalEvidenceFamily.EARNINGS_FINANCIAL_CURRENT.value,
            "evidence_quality": "current",
        },
    ]
    after = [dict(row) for row in facts]
    after[-1]["financial_context"] = {
        "metric": "operating_cash_flow",
        "adapter": CONTRACT_VERSION,
    }

    before_result = evaluate_source_sufficiency(
        facts,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )
    after_result = evaluate_source_sufficiency(
        after,
        framework=AnalysisFramework.STANDARD_OPERATING,
    )

    assert after_result == before_result


def test_bootstrap_context_remains_baseline_and_never_becomes_daily_delta() -> None:
    before = NonproductionLifecycleContext(
        fixture_id="m6-baseline-before",
        mode="MONITORING_BASELINE",
        subject_lifecycle="EXISTING_MONITORED",
        explicit_monitoring_intent=True,
        onboarding_complete=True,
        bootstrap_enrichment=True,
    )
    after = before.model_copy(update={"fixture_id": "m6-baseline-after"})

    assert before.mode == after.mode == LifecycleMode.MONITORING_BASELINE
    assert before.delta_state == after.delta_state == DeltaState.NOT_APPLICABLE
    assert "financial_context" not in NonproductionLifecycleContext.model_fields
