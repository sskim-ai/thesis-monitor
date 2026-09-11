from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.cross_market_decision_engine_service import FinancialPeriodType
from app.services.directional_financial_context_service import (
    validate_qtd_ytd_conflict_semantics,
)
from scripts import directional_financial_context_m12 as m12


M12C_REPORT_ROOT = Path("docs/reports") / (
    "20260909-materiality-scoped-working-capital-grounding-validator-repair-full-fictional-canary"
)
M12R_REPORT_ROOT = Path("docs/reports") / (
    "20260909-bounded-directional-financial-context-validator-repair-full-fictional-canary"
)


def _period_refs() -> tuple[object, object]:
    refs, _framework = m12._case_refs("FIC-FIN-03")
    qtd = next(
        ref
        for ref in refs
        if ref.financial_context is not None
        and ref.financial_context.metric == "operating_income"
        and ref.financial_context.period.type == FinancialPeriodType.QTD
    )
    ytd = next(
        ref
        for ref in refs
        if ref.financial_context is not None
        and ref.financial_context.metric == "operating_income"
        and ref.financial_context.period.type == FinancialPeriodType.YTD
    )
    return qtd, ytd


def _validate_text(
    text: str,
    *,
    linked_refs: tuple[object, ...] | None = None,
) -> object:
    qtd, ytd = _period_refs()
    refs = linked_refs if linked_refs is not None else (qtd, ytd)
    return validate_qtd_ytd_conflict_semantics(
        {
            "claim": {
                "text": text,
                "evidence_refs": [ref.ref_id for ref in refs],
            }
        },
        supplied_refs=(qtd, ytd),
        required_ref_ids=(qtd.ref_id, ytd.ref_id),
    )


@pytest.mark.parametrize(
    "text",
    (
        "분기 영업흑자와 누적 영업손실이 상충한다.",
        "분기 흑자와 연초 이후 누적 적자가 공존한다.",
        "분기 기준은 흑자지만 누계 기준은 적자다.",
        "이번 분기는 흑자지만 YTD는 손실이다.",
    ),
)
def test_m12d_accepts_explicit_plain_korean_qtd_ytd_claims(text: str) -> None:
    result = _validate_text(text)

    assert result.required
    assert result.valid
    assert result.explicit_claim_count == 1


@pytest.mark.parametrize(
    "text",
    (
        "분기점이 중요하며 누적 영업손실과 상충한다.",
        "분기 영업흑자만 확인됐다.",
        "누적 영업손실만 확인됐다.",
        "서로 다른 실적이 있다.",
        "QTD와 YTD 영업실적을 확인했다.",
    ),
)
def test_m12d_rejects_unexplicit_period_claims_with_both_refs(text: str) -> None:
    result = _validate_text(text)

    assert result.required
    assert not result.valid
    assert result.errors == ("qtd_ytd_conflict_not_explicit",)


def test_m12d_rejects_period_language_without_both_linked_refs() -> None:
    qtd, ytd = _period_refs()

    for refs in ((qtd,), (ytd,), ()):
        result = _validate_text(
            "분기 영업흑자와 누적 영업손실이 상충한다.",
            linked_refs=refs,
        )
        assert result.required
        assert not result.valid


def test_m12d_rejects_unrelated_plain_quarter_claim_path() -> None:
    qtd, ytd = _period_refs()
    result = validate_qtd_ytd_conflict_semantics(
        {
            "core_investment_judgment": {
                "text": "실적이 엇갈린다.",
                "evidence_refs": [qtd.ref_id, ytd.ref_id],
            },
            "sector_interpretation": {
                "text": "사업의 분기별 구조를 본다.",
                "evidence_refs": [],
            },
        },
        supplied_refs=(qtd, ytd),
        required_ref_ids=(qtd.ref_id, ytd.ref_id),
    )

    assert result.required
    assert not result.valid
    assert result.linked_claim_count == 1


def test_m12d_does_not_require_conflict_for_different_metrics() -> None:
    qtd, _ytd = _period_refs()
    refs, _framework = m12._case_refs("FIC-FIN-03")
    ytd_revenue = next(
        (
            ref
            for ref in refs
            if ref.financial_context is not None
            and ref.financial_context.metric == "revenue"
            and ref.financial_context.period.type == FinancialPeriodType.YTD
        ),
        None,
    )
    if ytd_revenue is None:
        ytd_revenue = qtd.model_copy(
            update={
                "ref_id": "canonical:fixture:revenue-ytd",
                "financial_context": qtd.financial_context.model_copy(
                    update={
                        "metric": "revenue",
                        "period": qtd.financial_context.period.model_copy(
                            update={"type": FinancialPeriodType.YTD}
                        ),
                    }
                ),
            }
        )
    result = validate_qtd_ytd_conflict_semantics(
        {
            "claim": {
                "text": "분기 영업흑자와 누적 매출이 상충한다.",
                "evidence_refs": [qtd.ref_id, ytd_revenue.ref_id],
            }
        },
        supplied_refs=(qtd, ytd_revenue),
        required_ref_ids=(qtd.ref_id, ytd_revenue.ref_id),
    )

    assert not result.required
    assert result.valid


def _report_row(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return next(row for row in document["rows"] if row["ticker"] == "FIC-FIN-03")


@pytest.mark.parametrize(
    "path",
    (
        M12R_REPORT_ROOT / "08-historical-raw-output-regression.json",
        M12C_REPORT_ROOT / "34-run-1-context-01.json",
        M12C_REPORT_ROOT / "36-run-2-context-01.json",
        M12C_REPORT_ROOT / "38-run-3-context-01.json",
    ),
)
def test_m12d_preserved_fic_fin_03_outputs_pass(path: Path) -> None:
    qtd, ytd = _period_refs()
    row = _report_row(path)
    result = validate_qtd_ytd_conflict_semantics(
        row["core"],
        supplied_refs=(qtd, ytd),
        required_ref_ids=(qtd.ref_id, ytd.ref_id),
    )

    assert result.required
    assert result.valid
    assert result.explicit_claim_count >= 1
