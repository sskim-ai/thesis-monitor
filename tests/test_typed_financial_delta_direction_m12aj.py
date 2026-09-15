from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.business_delta_evidence_service import (
    FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
    SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS,
    BusinessDeltaCapability,
    audit_business_delta_direction_projection,
    build_business_delta_evidence_view,
    derive_financial_comparison_direction,
    validate_business_delta_candidate,
)
from app.services.cross_market_decision_engine_service import (
    FinancialEvidenceQuality,
    FinancialPeriodType,
)
from scripts import directional_financial_context_m12 as m12


M12AI_RUN = Path(
    "docs/reports/"
    "20260911-business-delta-evidence-capability-gate-fictional-reproof-"
    "full-monitored-shadow/29-stage1-run1-context01.json"
)
M12AI_CAPABILITIES = Path(
    "docs/reports/"
    "20260911-business-delta-evidence-capability-gate-fictional-reproof-"
    "full-monitored-shadow/26-fictional-delta-capability-manifest.json"
)
FIXTURES = Path("tests/fixtures/typed_financial_delta_direction_m12aj.json")


def _fictional_views(generation: str = "m12aj-test"):
    _packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    return {
        ticker: build_business_delta_evidence_view(
            owned[ticker],
            catalogs[ticker],
            context=contexts[ticker],
        )
        for ticker in m12.TICKERS
    }


def _cash_pair(
    metric: str,
    *,
    current_value: str,
    prior_value: str,
    period_type: FinancialPeriodType = FinancialPeriodType.YTD,
):
    derived = metric == "ocf_less_ppe_capex"
    prior, current = m12._financial_pair(
        "DIR-CASH",
        metric,
        metric,
        current_value=current_value,
        prior_value=prior_value,
        period_type=period_type,
        current_start="2026-01-01",
        current_end="2026-06-30",
        prior_start="2025-01-01",
        prior_end="2025-06-30",
        comparison_kind=m12.FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        derived=derived,
    )
    return prior, current


@pytest.mark.parametrize(
    "fixture",
    [
        row
        for row in json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]
        if row["id"] in {f"DIR-CASH-0{index}" for index in range(1, 6)}
    ],
    ids=lambda row: row["id"],
)
def test_cash_conversion_direction_fixtures(
    fixture: dict[str, object],
) -> None:
    prior, current = _cash_pair(
        str(fixture["metric"]),
        current_value=str(fixture["current"]),
        prior_value=str(fixture["prior"]),
    )
    result = derive_financial_comparison_direction(
        current,
        {prior.source_ref: prior, current.source_ref: current},
    )
    assert result.contract == FINANCIAL_COMPARISON_DIRECTION_CONTRACT
    assert result.comparability_safe is True
    assert result.supported_change_directions == tuple(fixture["expected"])


def test_unverified_cash_comparison_has_no_safe_direction() -> None:
    prior, current = _cash_pair(
        "operating_cash_flow",
        current_value="180",
        prior_value="110",
    )
    assert current.financial_context is not None
    current = current.model_copy(
        update={
            "financial_context": current.financial_context.model_copy(
                update={"quality": FinancialEvidenceQuality.PARTIAL}
            )
        }
    )
    result = derive_financial_comparison_direction(
        current,
        {prior.source_ref: prior, current.source_ref: current},
    )
    assert result.comparability_safe is False
    assert result.supported_change_directions == ()


def test_period_and_basis_mismatch_suppress_direction() -> None:
    prior, current = _cash_pair(
        "operating_cash_flow",
        current_value="180",
        prior_value="110",
    )
    assert prior.financial_context is not None
    mismatched_period = prior.financial_context.model_copy(
        update={
            "period": m12._period(
                FinancialPeriodType.QTD,
                start="2025-04-01",
                end="2025-06-30",
            )
        }
    )
    mismatched_basis = prior.financial_context.model_copy(
        update={"entity_scope": "issuer_standalone"}
    )
    for prior_context in (mismatched_period, mismatched_basis):
        unsafe_prior = prior.model_copy(update={"financial_context": prior_context})
        result = derive_financial_comparison_direction(
            current,
            {
                unsafe_prior.source_ref: unsafe_prior,
                current.source_ref: current,
            },
        )
        assert result.comparability_safe is False
        assert result.supported_change_directions == ()


def test_exact_fic_fin_02_direction_projection_and_offline_revalidation() -> None:
    views = _fictional_views("m12aj-fic-fin-02")
    view = views["FIC-FIN-02"]
    items = {item.alias: item for item in view.items}
    assert view.capability == BusinessDeltaCapability.AI_JUDGMENT
    assert view.eligible_change_refs == ("E01", "E04", "E08", "E10")
    assert items["E01"].supported_change_directions == ("WEAKENED",)
    assert items["E08"].supported_change_directions == ("WEAKENED",)
    assert items["E10"].supported_change_directions == ("STRENGTHENED",)
    assert items["E04"].supported_change_directions == ()
    assert view.eligible_change_direction_hints == {
        "E01": ("WEAKENED",),
        "E08": ("WEAKENED",),
        "E10": ("STRENGTHENED",),
    }
    projection = audit_business_delta_direction_projection(view)
    assert projection["direction_hint_projection_mismatch_count"] == 0

    stopped = json.loads(M12AI_RUN.read_text(encoding="utf-8"))
    candidate = stopped["raw_candidates_by_ticker"]["FIC-FIN-02"]
    result = validate_business_delta_candidate(candidate, view)
    assert result["status"] == "PASS"
    assert result["business_delta_direction_violation_count"] == 0


def test_fic_fin_01_positive_cash_conversion_is_typed_strengthening() -> None:
    view = _fictional_views("m12aj-fic-fin-01")["FIC-FIN-01"]
    cash_items = [
        item
        for item in view.items
        if item.canonical_ref.endswith((":ocf-current", ":cash-conversion-current"))
    ]
    assert len(cash_items) == 2
    assert all(
        item.supported_change_directions == ("STRENGTHENED",)
        for item in cash_items
    )


def test_working_capital_change_remains_eligible_but_direction_unspecified() -> None:
    view = _fictional_views("m12aj-working-capital")["FIC-FIN-02"]
    inventory = next(item for item in view.items if item.alias == "E04")
    assert inventory.role.value == "ELIGIBLE_OBSERVED_CHANGE"
    assert inventory.supported_change_directions == ()


def test_mixed_and_partial_direction_validation_preserves_ai_judgment() -> None:
    view = _fictional_views("m12aj-mixed")["FIC-FIN-02"]
    mixed = {
        "ticker": "FIC-FIN-02",
        "business_thesis_change": "WEAKENED",
        "business_thesis_context": {
            "text": "현금 전환 약화와 영업 개선을 함께 반영했습니다.",
            "evidence_refs": ["E06", "E01", "E10"],
        },
    }
    unspecified = {
        "ticker": "FIC-FIN-02",
        "business_thesis_change": "WEAKENED",
        "business_thesis_context": {
            "text": "관측된 재고 변화를 사업 맥락에서 판단했습니다.",
            "evidence_refs": ["E04"],
        },
    }
    contradiction = {
        "ticker": "FIC-FIN-02",
        "business_thesis_change": "STRENGTHENED",
        "business_thesis_context": {
            "text": "현금 전환이 논리를 강화했습니다.",
            "evidence_refs": ["E01"],
        },
    }
    assert validate_business_delta_candidate(mixed, view)["status"] == "PASS"
    assert validate_business_delta_candidate(unspecified, view)["status"] == "PASS"
    rejected = validate_business_delta_candidate(contradiction, view)
    assert rejected["status"] == "FAIL"
    assert "BUSINESS_DELTA_DIRECTION_CONTRADICTS_EVIDENCE" in rejected["errors"]


def test_capability_classification_is_identical_to_m12ai() -> None:
    previous = json.loads(M12AI_CAPABILITIES.read_text(encoding="utf-8"))
    expected = {
        row["ticker"]: {
            "capability": row["capability"],
            "eligible_change_refs": row["eligible_change_refs"],
            "baseline_context_refs": row["baseline_context_refs"],
            "ambiguous_change_refs": row["ambiguous_change_refs"],
            "allowed_business_thesis_changes": row[
                "allowed_business_thesis_changes"
            ],
        }
        for row in previous["rows"]
    }
    actual = {}
    for ticker, view in _fictional_views("m12aj-classification").items():
        actual[ticker] = {
            "capability": view.capability.value,
            "eligible_change_refs": list(view.eligible_change_refs),
            "baseline_context_refs": list(view.baseline_context_refs),
            "ambiguous_change_refs": list(view.ambiguous_change_refs),
            "allowed_business_thesis_changes": list(
                view.allowed_business_thesis_changes
            ),
        }
    assert actual == expected
    assert SAFE_HIGHER_IS_STRONGER_FINANCIAL_METRICS == {
        "operating_cash_flow",
        "ocf_less_ppe_capex",
    }
