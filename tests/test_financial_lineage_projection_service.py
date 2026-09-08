from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.cash_flow_capital_efficiency_service import (
    CONTRACT_VERSION as CASH_FLOW_CONTRACT,
    CapexScope,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
    derive_fcf,
    derive_qtd_from_ytd,
    derive_ttm,
    financial_fact_from_mapping,
    q1_ytd_as_qtd,
)
from app.services.cash_flow_user_visible_service import fact_catalog_entries
from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
    compact_ai_context,
)
from app.services.financial_context_adapter_service import (
    adapt_fact_catalog_financial_context,
)
from app.services.financial_lineage_projection_service import (
    LINEAGE_FIELD,
    canonical_lineage_projection,
    lineage_projection_digest,
    project_financial_fact_catalog,
    projection_closure,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE9_FACTS = REPO_ROOT / "docs/reports/20260820-phase9-0b-canonical-facts.json"


def _period(
    period_type: PeriodType,
    fiscal_year: int,
    quarter: int | None = None,
) -> PeriodIdentity:
    if period_type == PeriodType.FY:
        return PeriodIdentity(
            date(fiscal_year, 1, 1),
            date(fiscal_year, 12, 31),
            period_type,
            fiscal_year,
        )
    if period_type == PeriodType.YTD:
        assert quarter in {1, 2, 3}
        ends = {1: (3, 31), 2: (6, 30), 3: (9, 30)}
        month, day = ends[quarter]
        return PeriodIdentity(
            date(fiscal_year, 1, 1),
            date(fiscal_year, month, day),
            period_type,
            fiscal_year,
            quarter,
        )
    if period_type == PeriodType.QTD:
        assert quarter in {1, 2, 3, 4}
        starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
        ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
        start_month, start_day = starts[quarter]
        end_month, end_day = ends[quarter]
        return PeriodIdentity(
            date(fiscal_year, start_month, start_day),
            date(fiscal_year, end_month, end_day),
            period_type,
            fiscal_year,
            quarter,
        )
    if period_type == PeriodType.POINT_IN_TIME:
        end = date(fiscal_year, 6, 30)
        return PeriodIdentity(end, end, period_type, fiscal_year)
    raise AssertionError(period_type)


def _fact(
    fact_id: str,
    metric: Metric,
    value: str,
    period: PeriodIdentity,
    *,
    fact_type: FactType = FactType.REPORTED,
    formula: str | None = None,
    input_fact_ids: tuple[str, ...] = (),
    currency: str = "USD",
    issuer_id: str = "sec:fixture",
    entity_scope: str = "issuer_level",
    statement_basis: str = "official_filing_cash_flow_statement",
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        issuer_id=issuer_id,
        metric=metric,
        value=Decimal(value),
        currency=currency,
        unit=currency,
        period=period,
        entity_scope=entity_scope,
        statement_basis=statement_basis,
        reported_or_derived=(
            "reported" if fact_type == FactType.REPORTED else "derived_period"
        ),
        source_provider="official_fixture",
        source_document_id=f"document:{period.end.isoformat()}",
        filing_date=period.end,
        source_occurrence_id=f"occurrence:{fact_id}",
        raw_payload_sha256=hashlib.sha256(fact_id.encode()).hexdigest(),
        semantic_mapping=metric.value,
        fact_type=fact_type,
        capex_scope=(CapexScope.PPE_ONLY if metric == Metric.CAPEX else None),
        derivation_formula=formula,
        derivation_version=CASH_FLOW_CONTRACT if formula else None,
        input_fact_ids=input_fact_ids,
        restatement_policy_id="fixture-restatement-v1",
    )


def _project(facts: list[FinancialFact]) -> list[dict[str, object]]:
    return project_financial_fact_catalog(facts, context_id="m7-fixture")


def _adapt(
    fact_id: str,
    rows: list[dict[str, object]],
):
    row = next(item for item in rows if item["fact_id"] == fact_id)
    return adapt_fact_catalog_financial_context(row, rows)


def _reported_pair(
    period: PeriodIdentity,
    *,
    prefix: str,
    ocf: str = "100",
    ppe: str = "40",
) -> tuple[FinancialFact, FinancialFact]:
    return (
        _fact(f"{prefix}.ocf", Metric.OCF, ocf, period),
        _fact(f"{prefix}.ppe", Metric.CAPEX, ppe, period),
    )


@pytest.mark.parametrize(
    ("period_type", "quarter"),
    (
        (PeriodType.QTD, 2),
        (PeriodType.YTD, 2),
        (PeriodType.FY, None),
    ),
)
def test_compatible_prior_year_projection_enables_comparison(
    period_type: PeriodType,
    quarter: int | None,
) -> None:
    if period_type == PeriodType.QTD:
        current_ytd = _fact(
            "current.ytd",
            Metric.OCF,
            "100",
            _period(PeriodType.YTD, 2026, quarter),
        )
        prior_ytd = _fact(
            "current.q1",
            Metric.OCF,
            "40",
            _period(PeriodType.YTD, 2026, 1),
        )
        prior_current_ytd = _fact(
            "prior.ytd",
            Metric.OCF,
            "80",
            _period(PeriodType.YTD, 2025, quarter),
        )
        prior_q1 = _fact(
            "prior.q1",
            Metric.OCF,
            "30",
            _period(PeriodType.YTD, 2025, 1),
        )
        current = derive_qtd_from_ytd(current_ytd, prior_ytd).fact
        prior = derive_qtd_from_ytd(prior_current_ytd, prior_q1).fact
        assert current is not None and prior is not None
        facts = [current_ytd, prior_ytd, prior_current_ytd, prior_q1, current, prior]
    else:
        current = _fact(
            "current",
            Metric.OCF,
            "100",
            _period(period_type, 2026, quarter),
        )
        prior = _fact(
            "prior",
            Metric.OCF,
            "80",
            _period(period_type, 2025, quarter),
        )
        facts = [current, prior]
    closure = projection_closure(
        facts,
        selected_fact_ids=(current.fact_id,),
        prior_fact_ids=(prior.fact_id,),
    )
    rows = project_financial_fact_catalog(
        (current,),
        context_id="m7-prior",
        lineage_facts=closure,
    )

    result = _adapt(current.fact_id, rows)

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["comparison"] == {
        "kind": "prior_year_comparable",
        "compatibility_status": "PASS",
        "input_source_refs": [
            f"stock.fact_catalog.{current.fact_id}",
            f"stock.fact_catalog.{prior.fact_id}",
        ],
    }
    assert all(
        row.get("consumer_scopes") == ["ARCHIVE_ONLY"]
        for row in rows
        if row["fact_id"] != current.fact_id
    )


def test_projection_closure_deduplicates_and_recursively_preserves_inputs() -> None:
    q1 = _fact("q1", Metric.OCF, "40", _period(PeriodType.YTD, 2026, 1))
    q2 = _fact("q2", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))
    qtd = derive_qtd_from_ytd(q2, q1).fact
    prior = _fact("prior", Metric.OCF, "55", _period(PeriodType.QTD, 2025, 2))
    assert qtd is not None

    first = projection_closure(
        [q1, q2, qtd, prior, prior],
        selected_fact_ids=(qtd.fact_id,),
        prior_fact_ids=(prior.fact_id, prior.fact_id),
    )
    second = projection_closure(
        [q1, q2, qtd, prior],
        selected_fact_ids=(qtd.fact_id,),
        prior_fact_ids=(prior.fact_id,),
    )

    assert first == second
    assert {item.fact_id for item in first} == {
        q1.fact_id,
        q2.fact_id,
        qtd.fact_id,
        prior.fact_id,
    }


@pytest.mark.parametrize("metric", (Metric.OCF, Metric.CAPEX))
@pytest.mark.parametrize("formula", ("Q1", "QTD", "TTM"))
def test_existing_derived_period_lineage_projects_and_validates(
    metric: Metric,
    formula: str,
) -> None:
    if formula == "Q1":
        source = _fact("source.q1", metric, "40", _period(PeriodType.YTD, 2026, 1))
        derived = q1_ytd_as_qtd(source).fact
        facts = [source]
    elif formula == "QTD":
        current = _fact("source.q2", metric, "100", _period(PeriodType.YTD, 2026, 2))
        prior = _fact("source.q1", metric, "40", _period(PeriodType.YTD, 2026, 1))
        derived = derive_qtd_from_ytd(current, prior).fact
        facts = [current, prior]
    else:
        prior_fy = _fact("source.fy", metric, "180", _period(PeriodType.FY, 2025))
        current_ytd = _fact(
            "source.current-ytd",
            metric,
            "100",
            _period(PeriodType.YTD, 2026, 2),
        )
        prior_ytd = _fact(
            "source.prior-ytd",
            metric,
            "80",
            _period(PeriodType.YTD, 2025, 2),
        )
        derived = derive_ttm(prior_fy, current_ytd, prior_ytd).fact
        facts = [prior_fy, current_ytd, prior_ytd]
    assert derived is not None
    rows = _project([*facts, derived])

    result = _adapt(derived.fact_id, rows)

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["evidence_status"] == "DERIVED_SAFE"
    assert result.context["derivation"]["version"] == CASH_FLOW_CONTRACT
    assert result.context["derivation"]["input_source_refs"] == [
        f"stock.fact_catalog.{fact_id}" for fact_id in derived.input_fact_ids
    ]


def test_fcf_accepts_fully_proven_derived_period_inputs() -> None:
    ocf_ytd, ppe_ytd = _reported_pair(
        _period(PeriodType.YTD, 2026, 2),
        prefix="q2",
    )
    ocf_q1, ppe_q1 = _reported_pair(
        _period(PeriodType.YTD, 2026, 1),
        prefix="q1",
        ocf="30",
        ppe="10",
    )
    ocf_qtd = derive_qtd_from_ytd(ocf_ytd, ocf_q1).fact
    ppe_qtd = derive_qtd_from_ytd(ppe_ytd, ppe_q1).fact
    assert ocf_qtd is not None and ppe_qtd is not None
    fcf = derive_fcf(ocf_qtd, ppe_qtd).fact
    assert fcf is not None
    rows = _project([ocf_ytd, ppe_ytd, ocf_q1, ppe_q1, ocf_qtd, ppe_qtd, fcf])

    result = _adapt(fcf.fact_id, rows)

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["metric"] == "ocf_less_ppe_capex"
    assert result.context["derivation"]["formula"] == "ocf_less_ppe_capex"


def test_explicit_kr_duration_facts_support_simple_cash_conversion() -> None:
    period = PeriodIdentity(
        date(2025, 10, 1),
        date(2026, 3, 31),
        PeriodType.YTD,
        2026,
        2,
    )
    ocf, ppe = _reported_pair(period, prefix="kr", ocf="900", ppe="250")
    ocf = replace(ocf, currency="KRW", unit="KRW", issuer_id="opendart:00123456")
    ppe = replace(ppe, currency="KRW", unit="KRW", issuer_id="opendart:00123456")
    fcf = derive_fcf(ocf, ppe).fact
    assert fcf is not None
    rows = _project([ocf, ppe, fcf])

    result = _adapt(fcf.fact_id, rows)

    assert result.denial_reasons == ()
    assert result.context is not None
    assert result.context["currency"] == "KRW"
    assert result.context["period"] == {
        "type": "YTD",
        "start": "2025-10-01",
        "end": "2026-03-31",
        "duration_days": 182,
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("formula_missing", "canonical_derivation_formula_missing"),
        ("version_missing", "canonical_derivation_version_missing"),
        ("input_refs_missing", "canonical_lineage_input_ids_mismatch"),
        ("input_order", "qtd_difference_quarter_sequence_invalid"),
        ("period_start", "financial_duration_period_start_required"),
        ("currency", "derived_period_currency_mismatch"),
        ("entity", "derived_period_entity_scope_mismatch"),
        ("statement", "derived_period_statement_basis_mismatch"),
        ("issuer", "derived_period_issuer_id_mismatch"),
        ("missing_source", "derived_period_input_ref_missing"),
    ),
)
def test_incomplete_or_incompatible_derived_lineage_stays_blocked(
    mutation: str,
    expected: str,
) -> None:
    current = _fact("q2", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))
    prior = _fact("q1", Metric.OCF, "40", _period(PeriodType.YTD, 2026, 1))
    derived = derive_qtd_from_ytd(current, prior).fact
    assert derived is not None
    rows = _project([current, prior, derived])
    row = next(item for item in rows if item["fact_id"] == derived.fact_id)
    lineage = copy.deepcopy(row[LINEAGE_FIELD])
    fields = copy.deepcopy(row["fields"])
    if mutation == "formula_missing":
        lineage["derivation_formula"] = None
    elif mutation == "version_missing":
        lineage["derivation_version"] = None
    elif mutation == "input_refs_missing":
        lineage["ordered_input_fact_ids"] = []
        lineage["ordered_input_source_refs"] = []
    elif mutation == "input_order":
        lineage["ordered_input_fact_ids"].reverse()
        lineage["ordered_input_source_refs"].reverse()
        fields["input_fact_ids"].reverse()
    elif mutation == "period_start":
        fields["period_start"] = None
    elif mutation in {"currency", "entity", "statement", "issuer"}:
        input_row = next(item for item in rows if item["fact_id"] == prior.fact_id)
        input_fields = copy.deepcopy(input_row["fields"])
        input_lineage = copy.deepcopy(input_row[LINEAGE_FIELD])
        key = {
            "currency": "currency",
            "entity": "entity_scope",
            "statement": "statement_basis",
            "issuer": "issuer_id",
        }[mutation]
        value = {
            "currency": "KRW",
            "entity": "issuer_separate",
            "statement": "separate_cash_flow_statement",
            "issuer": "sec:different-issuer",
        }[mutation]
        if key in input_fields:
            input_fields[key] = value
        input_lineage[key] = value
        input_lineage["lineage_sha256"] = lineage_projection_digest(input_lineage)
        input_row["fields"] = input_fields
        input_row[LINEAGE_FIELD] = input_lineage
    elif mutation == "missing_source":
        rows[:] = [item for item in rows if item["fact_id"] != prior.fact_id]
    lineage["lineage_sha256"] = lineage_projection_digest(lineage)
    row[LINEAGE_FIELD] = lineage
    row["fields"] = fields

    result = adapt_fact_catalog_financial_context(row, rows)

    assert result.context is None
    assert expected in result.denial_reasons


def test_duplicate_compatible_prior_candidates_are_ambiguous() -> None:
    current = _fact("current", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))
    prior_a = _fact("prior.a", Metric.OCF, "80", _period(PeriodType.YTD, 2025, 2))
    prior_b = replace(prior_a, fact_id="prior.b", value=Decimal("81"))
    rows = _project([current, prior_a, prior_b])

    result = _adapt(current.fact_id, rows)

    assert result.context is not None
    assert result.context["comparison"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("currency", "KRW"),
        ("entity_scope", "other_issuer_scope"),
        ("statement_basis", "separate_cash_flow_statement"),
    ),
)
def test_incompatible_prior_is_not_projected_as_comparison(
    field: str,
    value: str,
) -> None:
    current = _fact("current", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))
    prior = replace(
        _fact("prior", Metric.OCF, "80", _period(PeriodType.YTD, 2025, 2)),
        **{field: value},
    )
    rows = _project([current, prior])

    result = _adapt(current.fact_id, rows)

    assert result.context is not None
    assert result.context["comparison"] is None


def test_projection_metadata_does_not_change_compact_ai_context() -> None:
    current = _fact("current", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))
    prior = _fact("prior", Metric.OCF, "80", _period(PeriodType.YTD, 2025, 2))
    rows = project_financial_fact_catalog(
        (current,),
        context_id="m7-non-leak",
        lineage_facts=(prior,),
    )
    packet = build_decision_evidence_packet(
        packet={
            "packet_id": "m7-non-leak",
            "market": "us",
            "assessment_date": "2026-09-08",
        },
        stock={"ticker": "M7", "fact_catalog": rows},
    )
    legacy = packet.model_copy(
        update={
            "evidence": tuple(
                ref.model_copy(update={"financial_context": None})
                for ref in packet.evidence
            )
        }
    )

    canonical_refs = [
        ref for ref in packet.evidence if ref.ref_id.startswith("canonical:")
    ]
    assert [ref.ref_id for ref in canonical_refs] == ["canonical:current"]
    assert canonical_refs[0].financial_context is not None
    assert canonical_refs[0].financial_context.comparison is not None
    assert compact_ai_context(packet) == compact_ai_context(legacy)


def test_preserved_phase9_archive_projects_every_complete_context() -> None:
    report = json.loads(PHASE9_FACTS.read_text(encoding="utf-8"))
    rows = fact_catalog_entries(
        SimpleNamespace(
            user_visible_enabled=True,
            facts=tuple(
                financial_fact_from_mapping(item)
                for item in report["canonical_facts"]
            ),
            context_id="m7-archive-proof",
        )
    )

    results = [adapt_fact_catalog_financial_context(row, rows) for row in rows]

    assert len(rows) == 606
    assert all(result.context is not None for result in results)
    assert sum(bool(result.context["comparison"]) for result in results) == 164


def test_lineage_projection_digest_is_deterministic() -> None:
    fact = _fact("digest", Metric.OCF, "100", _period(PeriodType.YTD, 2026, 2))

    first = canonical_lineage_projection(fact)
    second = canonical_lineage_projection(fact)

    assert first == second
    assert first["lineage_sha256"] == lineage_projection_digest(first)
