from __future__ import annotations

import json
from decimal import Decimal

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
    FinancialDerivation,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
    FinancialContext,
)
from app.services.direction_timing_ownership_service import (
    build_owned_evidence_packet,
    financial_decision_context_for_owned,
    stage_alias_catalogs,
)
from app.services.directional_financial_context_service import (
    FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
    build_financial_decision_context,
    compact_financial_decision_context,
    validate_directional_financial_semantics,
    validate_qtd_ytd_conflict_semantics,
)
from scripts import directional_core_price_timing_holdout as holdout


def _financial_ref(
    metric: str,
    value: str,
    *,
    suffix: str | None = None,
    period_type: FinancialPeriodType = FinancialPeriodType.POINT_IN_TIME,
    period_end: str = "2026-06-30",
    comparison_kind: FinancialComparisonKind | None = None,
    limitations: tuple[str, ...] = (),
    derived: bool = False,
) -> DecisionEvidenceRef:
    identity = suffix or metric
    source_ref = f"stock.fact_catalog.{identity}"
    period = (
        FinancialPeriod(type=period_type, end=period_end)
        if period_type == FinancialPeriodType.POINT_IN_TIME
        else FinancialPeriod(
            type=period_type,
            start="2026-01-01",
            end=period_end,
            duration_days=181,
        )
    )
    comparison = (
        FinancialComparison(
            kind=comparison_kind,
            input_source_refs=(source_ref, f"stock.fact_catalog.{identity}.prior"),
        )
        if comparison_kind is not None
        else None
    )
    derivation = (
        FinancialDerivation(
            formula=metric,
            input_source_refs=(f"stock.fact_catalog.{identity}.input",),
            version="test-v1",
        )
        if derived
        else None
    )
    return DecisionEvidenceRef(
        ref_id=f"canonical:{identity}",
        category=EvidenceCategory.EARNINGS,
        label=metric,
        statement=json.dumps({"value": value}, separators=(",", ":")),
        as_of=period_end,
        source_ref=source_ref,
        financial_context=FinancialContext(
            metric=metric,
            currency="USD",
            unit_scale=1,
            period=period,
            entity_scope="consolidated",
            statement_basis="formal_financial_statement",
            evidence_status=(
                FinancialEvidenceStatus.DERIVED_SAFE
                if derived
                else FinancialEvidenceStatus.DIRECT_REPORTED
            ),
            quality=FinancialEvidenceQuality.VERIFIED,
            comparison=comparison,
            derivation=derivation,
            limitations=limitations,
        ),
    )


def _plain_ref(
    ref_id: str,
    category: EvidenceCategory = EvidenceCategory.THESIS,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=category,
        label=ref_id,
        statement=ref_id,
        source_ref=f"fixture.{ref_id}",
    )


def _packet(refs: tuple[DecisionEvidenceRef, ...]) -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="m12-fixture",
        ticker="FIC-FIN",
        company_name="Fictional Finance Context",
        market="us",
        assessment_date="2026-09-09",
        horizon="12m",
        evidence=refs,
        prohibited_claims=(),
        evidence_sha256="fixture-sha",
    )


def test_selector_is_deterministic_bounded_and_direction_neutral() -> None:
    metrics = (
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
        "ocf_less_ppe_capex",
        "cash_and_cash_equivalents",
        "interest_bearing_debt_total",
        "net_debt",
        "inventory",
        "inventory_component",
        "trade_accounts_receivable",
        "accounts_receivable_broad",
        "trade_accounts_payable",
        "net_financial_income_effect",
        "financial_income",
        "financial_cost",
        "sector_unit_growth",
    )
    refs = tuple(
        _financial_ref(
            metric,
            str(index * 10),
            derived=metric in {"ocf_less_ppe_capex", "net_debt"},
            limitations=("ppe_only_not_management_defined_fcf",)
            if metric == "ocf_less_ppe_capex"
            else (),
        )
        for index, metric in enumerate(metrics, start=1)
    )
    first = build_financial_decision_context(
        refs, sector_framework="standard_operating_company"
    )
    second = build_financial_decision_context(
        tuple(reversed(refs)), sector_framework="standard_operating_company"
    )
    negative_refs = tuple(
        ref.model_copy(update={"statement": json.dumps({"value": "-999"})})
        for ref in refs
    )
    negative = build_financial_decision_context(
        negative_refs, sector_framework="standard_operating_company"
    )

    assert first is not None and second is not None and negative is not None
    assert first == second
    assert len(first.evidence_items) <= FINANCIAL_DECISION_CONTEXT_ITEM_CAP
    selected_metrics = [item.metric for item in first.evidence_items]
    assert selected_metrics == [item.metric for item in negative.evidence_items]
    assert "net_debt" in selected_metrics
    assert "interest_bearing_debt_total" not in selected_metrics
    assert "cash_and_cash_equivalents" not in selected_metrics
    assert "inventory" in selected_metrics
    assert "inventory_component" not in selected_metrics
    assert "trade_accounts_receivable" in selected_metrics
    assert "accounts_receivable_broad" not in selected_metrics
    assert "net_financial_income_effect" in selected_metrics
    assert "financial_income" not in selected_metrics
    assert "financial_cost" not in selected_metrics


def test_comparison_value_and_period_are_structurally_preserved() -> None:
    current = _financial_ref(
        "inventory",
        "130",
        suffix="inventory.current",
        comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
    )
    prior = _financial_ref(
        "inventory",
        "100",
        suffix="inventory.current.prior",
        period_end="2025-12-31",
    )
    context = build_financial_decision_context((prior, current))

    assert context is not None
    item = context.evidence_items[0]
    assert item.value == Decimal("130")
    assert item.comparison is not None
    assert item.comparison.kind == FinancialComparisonKind.PRIOR_YEAR_END
    assert item.comparison.comparison_value == Decimal("100")
    assert item.comparison.comparison_period is not None
    assert str(item.comparison.comparison_period.end) == "2025-12-31"


def test_financial_sector_routes_generic_context_out_of_directional_core() -> None:
    refs = (
        _plain_ref("thesis"),
        _financial_ref("net_debt", "500", derived=True),
        _financial_ref("trade_accounts_receivable", "250"),
        _financial_ref("interest_income", "50"),
        _plain_ref("technical", EvidenceCategory.TECHNICAL_FEATURE),
    )
    owned = build_owned_evidence_packet(
        _packet(refs),
        stock={"analysis_framework": "bank_or_insurer", "fact_catalog": []},
    )
    context = financial_decision_context_for_owned(owned)
    core_catalog, timing_catalog = stage_alias_catalogs(owned)

    assert context is not None
    assert context.evidence_items == ()
    assert context.unavailable_or_not_applicable == ("SECTOR_FRAMEWORK_REQUIRED",)
    assert not any(
        ref_id.startswith("canonical:net_debt")
        or ref_id.startswith("canonical:trade_accounts_receivable")
        or ref_id.startswith("canonical:interest_income")
        for ref_id in core_catalog.by_ref
    )
    assert "technical" in " ".join(timing_catalog.by_ref)


def test_directional_context_activates_selected_financial_block_only_for_core() -> None:
    refs = (
        _plain_ref("thesis"),
        _financial_ref("operating_cash_flow", "200"),
        _financial_ref(
            "ocf_less_ppe_capex",
            "120",
            derived=True,
            limitations=("ppe_only_not_management_defined_fcf",),
        ),
        _plain_ref("technical", EvidenceCategory.TECHNICAL_FEATURE),
    )
    owned = build_owned_evidence_packet(
        _packet(refs),
        stock={"analysis_framework": "standard_operating_company", "fact_catalog": []},
    )
    core_catalog, timing_catalog = stage_alias_catalogs(owned)
    core = holdout._owned_context(owned, core_catalog)
    timing = holdout._owned_context(owned, timing_catalog)

    assert "financial_decision_context" in core
    assert "financial_decision_context" not in timing
    assert all("operating_cash_flow" not in row["label"] for row in core["evidence"])
    assert all("financial_context" not in row for row in timing["evidence"])
    aliases = set(core_catalog.by_alias)
    selected = core["financial_decision_context"]["evidence_items"]
    assert selected
    assert all(row["evidence_id"] in aliases for row in selected)


def test_legacy_packet_omits_empty_financial_block() -> None:
    refs = (
        _plain_ref("thesis"),
        _plain_ref("technical", EvidenceCategory.TECHNICAL_FEATURE),
    )
    owned = build_owned_evidence_packet(
        _packet(refs), stock={"fact_catalog": []}
    )
    core_catalog, _ = stage_alias_catalogs(owned)

    assert financial_decision_context_for_owned(owned) is None
    assert "financial_decision_context" not in holdout._owned_context(
        owned, core_catalog
    )


def test_compact_projection_requires_every_selected_alias() -> None:
    ref = _financial_ref("operating_cash_flow", "200")
    context = build_financial_decision_context((ref,))
    assert context is not None

    try:
        compact_financial_decision_context(context, aliases_by_ref={})
    except ValueError as exc:
        assert "selected_financial_ref_missing_alias" in str(exc)
    else:
        raise AssertionError("missing alias must fail closed")


def test_high_risk_financial_claims_fail_closed() -> None:
    proxy = _financial_ref(
        "ocf_less_ppe_capex",
        "100",
        derived=True,
        limitations=("ppe_only_not_management_defined_fcf",),
    )
    inventory = _financial_ref(
        "inventory",
        "130",
        comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
    )
    debt_component = _financial_ref("short_term_borrowings", "90")
    refs = (proxy, inventory, debt_component)
    candidate = {
        "claims": [
            {"text": "FCF가 개선됐습니다.", "evidence_refs": [proxy.ref_id]},
            {"text": "재고가 전년 대비 늘었습니다.", "evidence_refs": [inventory.ref_id]},
            {"text": "순부채가 높습니다.", "evidence_refs": [debt_component.ref_id]},
            {"text": "조정 순이익은 견조합니다.", "evidence_refs": [proxy.ref_id]},
            {"text": "현금흐름 +1점입니다.", "evidence_refs": [proxy.ref_id]},
        ]
    }
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )

    assert not result.valid
    assert result.partial_capex_called_fcf_count == 1
    assert result.year_end_as_yoy_count == 1
    assert result.partial_debt_total_claim_count == 1
    assert result.normalized_earnings_claim_violation_count == 1
    assert result.fixed_financial_score_rule_count == 1


def test_safe_financial_claims_and_period_labels_pass() -> None:
    proxy = _financial_ref(
        "ocf_less_ppe_capex",
        "100",
        derived=True,
        limitations=("ppe_only_not_management_defined_fcf",),
    )
    inventory = _financial_ref(
        "inventory",
        "130",
        comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
    )
    net_debt = _financial_ref("net_debt", "90", derived=True)
    refs = (proxy, inventory, net_debt)
    candidate = {
        "claims": [
            {
                "text": "PPE 지출을 뺀 단순 현금전환 여력이 확인됩니다.",
                "evidence_refs": [proxy.ref_id],
            },
            {
                "text": "재고는 전년 말 대비 늘어 확인 지점입니다.",
                "evidence_refs": [inventory.ref_id],
            },
            {"text": "순부채 부담은 제한적입니다.", "evidence_refs": [net_debt.ref_id]},
        ]
    }
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )

    assert result.valid
    assert result.errors == ()


def test_normalized_earnings_language_requires_the_cited_metric_owner() -> None:
    normalized = _financial_ref("normalized_net_income", "80")
    operating_cash = _financial_ref("operating_cash_flow", "100")
    supplied = (normalized, operating_cash)

    wrong_owner = validate_directional_financial_semantics(
        {
            "claim": {
                "text": "조정 순이익은 견조합니다.",
                "evidence_refs": [operating_cash.ref_id],
            }
        },
        supplied_refs=supplied,
        allowed_ref_ids=tuple(ref.ref_id for ref in supplied),
    )
    correct_owner = validate_directional_financial_semantics(
        {
            "claim": {
                "text": "조정 순이익은 견조합니다.",
                "evidence_refs": [normalized.ref_id],
            }
        },
        supplied_refs=supplied,
        allowed_ref_ids=tuple(ref.ref_id for ref in supplied),
    )

    assert not wrong_owner.valid
    assert wrong_owner.normalized_earnings_claim_violation_count == 1
    assert correct_owner.valid


def test_financial_sector_semantic_use_is_rejected() -> None:
    interest = _financial_ref("interest_income", "50")
    result = validate_directional_financial_semantics(
        {
            "claim": {
                "text": "이자수익을 비영업 개선으로 봅니다.",
                "evidence_refs": [interest.ref_id],
            }
        },
        supplied_refs=(interest,),
        allowed_ref_ids=(interest.ref_id,),
        sector_framework="bank_or_insurer",
    )

    assert not result.valid
    assert result.financial_sector_generic_financial_context_leak_count == 1


def _qtd_ytd_conflict_refs() -> tuple[DecisionEvidenceRef, DecisionEvidenceRef]:
    return (
        _financial_ref(
            "operating_income",
            "30",
            suffix="operating-income.qtd",
            period_type=FinancialPeriodType.QTD,
        ),
        _financial_ref(
            "operating_income",
            "-10",
            suffix="operating-income.ytd",
            period_type=FinancialPeriodType.YTD,
        ),
    )


def test_qtd_ytd_validator_accepts_explicit_bilingual_period_contrasts() -> None:
    refs = _qtd_ytd_conflict_refs()
    texts = (
        "최근 분기는 흑자지만 연초 이후 누적 기준은 적자다.",
        "분기 영업흑자와 누계 영업손실이 공존한다.",
        "QTD profit is positive while YTD operating income remains negative.",
        "The latest quarter is profitable whereas year-to-date income is negative.",
        "Quarterly profit is positive while cumulative operating income is negative.",
        "이번 분기는 개선됐지만 연초부터 누적 실적은 아직 손실이다.",
    )

    for text in texts:
        result = validate_qtd_ytd_conflict_semantics(
            {"claim": {"text": text, "evidence_refs": [ref.ref_id for ref in refs]}},
            supplied_refs=refs,
            required_ref_ids=tuple(ref.ref_id for ref in refs),
        )

        assert result.required
        assert result.valid
        assert result.linked_claim_count == 1
        assert result.explicit_claim_count == 1


def test_qtd_ytd_validator_rejects_vague_unlinked_and_unrelated_markers() -> None:
    qtd, ytd = _qtd_ytd_conflict_refs()
    both = [qtd.ref_id, ytd.ref_id]
    candidates = (
        {"claim": {"text": "최근 실적은 엇갈린다.", "evidence_refs": both}},
        {
            "claim": {
                "text": "분기 실적이 좋지만 누적적으로도 중요하다.",
                "evidence_refs": both,
            }
        },
        {"claim": {"text": "최근 분기 실적만 개선됐다.", "evidence_refs": both}},
        {"claim": {"text": "연초 이후 누적 실적은 손실이다.", "evidence_refs": both}},
        {
            "claim": {
                "text": "분기는 흑자지만 누계는 적자다.",
                "evidence_refs": [qtd.ref_id],
            }
        },
        {
            "claim": {
                "text": "분기는 흑자지만 누계는 적자다.",
                "evidence_refs": [ytd.ref_id],
            }
        },
        {
            "claim": {
                "text": "QTD와 YTD 영업실적을 확인했다.",
                "evidence_refs": both,
            }
        },
        {
            "claims": [
                {"text": "최근 실적은 엇갈린다.", "evidence_refs": both},
                {"text": "다음 분기 수요를 확인한다.", "evidence_refs": []},
            ]
        },
        {
            "claims": [
                {"text": "최근 실적은 엇갈린다.", "evidence_refs": both},
                {"text": "고객 누적 수는 별도 지표다.", "evidence_refs": []},
            ]
        },
    )

    for candidate in candidates:
        result = validate_qtd_ytd_conflict_semantics(
            candidate,
            supplied_refs=(qtd, ytd),
            required_ref_ids=(qtd.ref_id, ytd.ref_id),
        )

        assert result.required
        assert not result.valid
        assert result.errors == ("qtd_ytd_conflict_not_explicit",)


def test_qtd_ytd_validator_is_not_required_without_same_metric_period_pair() -> None:
    qtd, _ytd = _qtd_ytd_conflict_refs()
    other_ytd = _financial_ref(
        "revenue",
        "100",
        suffix="revenue.ytd",
        period_type=FinancialPeriodType.YTD,
    )
    result = validate_qtd_ytd_conflict_semantics(
        {"claim": {"text": "최근 실적은 엇갈린다.", "evidence_refs": []}},
        supplied_refs=(qtd, other_ytd),
        required_ref_ids=(qtd.ref_id, other_ytd.ref_id),
    )

    assert not result.required
    assert result.valid
    assert result.errors == ()


def test_directional_prompt_freezes_m12_financial_specificity_without_timing_leak() -> None:
    core_prompt = holdout._core_prompt(
        packet_id="m12-prompt",
        tickers=("FIC-FIN-01",),
        contexts=({"ticker": "FIC-FIN-01", "evidence": []},),
    )
    timing_prompt = holdout._timing_prompt(
        packet_id="m12-prompt",
        tickers=("FIC-FIN-01",),
        contexts=({"ticker": "FIC-FIN-01", "evidence": []},),
    )

    assert "financial_decision_context" in core_prompt
    assert "in 1–3 typed refs, not narrative alone" in core_prompt
    assert "prior_year_end=since year-end, never YoY" in core_prompt
    assert "cash-conversion proxy, never FCF" in core_prompt
    assert "material financial_decision_context claims" in core_prompt
    assert "no force/list/double count" in core_prompt
    assert "No fixed financial scorecard" in core_prompt
    assert "financial_decision_context" not in timing_prompt
    assert "ocf_less_ppe_capex" not in timing_prompt
