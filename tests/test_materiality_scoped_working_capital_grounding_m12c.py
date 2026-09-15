from __future__ import annotations

import inspect
import json
from pathlib import Path

from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g
from scripts import first_class_typed_financial_evidence_m12b as m12b
from scripts import materiality_scoped_working_capital_grounding_m12c as m12c


M12B_GENERATION_ID = (
    "20260909-m12b-fictional-20260909T085320Z-746ef9ba1586"
)
M12B_REPORT_ROOT = Path("docs/reports") / (
    "20260909-first-class-typed-financial-evidence-index-"
    "implementation-full-fictional-canary"
)


def _audit_report_row(
    report: str,
    ticker: str,
) -> dict[str, object]:
    document = json.loads((M12B_REPORT_ROOT / report).read_text())
    row = next(row for row in document["rows"] if row["ticker"] == ticker)
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(
        M12B_GENERATION_ID
    )
    return m12g.audit_financial_grounding(
        row["core"],
        selected_metrics_by_ref=m12g._selected_metrics_for_ticker(
            owned,
            ticker,
        ),
    )


def test_context_only_inventory_is_valid_without_checkpoint_duplication() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "unknown_treatments": [
                {
                    "summary": (
                        "재고는 연말보다 늘었지만 이것만으로 악화를 입증하지 않는다."
                    ),
                    "evidence_refs": ["canonical:inventory"],
                }
            ]
        },
        selected_metrics_by_ref={"canonical:inventory": "inventory"},
    )

    assert audit["status"] == "PASS"
    assert not audit["working_capital_grounding_required"]


def test_cash_conversion_focal_case_allows_secondary_inventory_context() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "core_investment_judgment": {
                "text": "영업현금 전환 약화가 확신을 제한한다.",
                "evidence_refs": ["canonical:ocf"],
            },
            "risk_context": {
                "text": "운전자본 흡수의 원인과 가역성은 확인되지 않았다.",
                "evidence_refs": ["narrative:risk"],
            },
            "unknown_treatments": [
                {
                    "summary": "재고 증가는 맥락 자료로만 취급한다.",
                    "evidence_refs": ["canonical:inventory"],
                }
            ],
        },
        selected_metrics_by_ref={
            "canonical:ocf": "operating_cash_flow",
            "canonical:inventory": "inventory",
        },
    )

    assert audit["status"] == "PASS"
    assert not audit["working_capital_grounding_required"]
    assert audit["used_financial_refs"] == [
        "canonical:inventory",
        "canonical:ocf",
    ]


def test_specific_inventory_checkpoint_is_grounded() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고 정상화가 핵심 확인 조건이다.",
                "evidence_refs": ["canonical:inventory"],
            }
        },
        selected_metrics_by_ref={"canonical:inventory": "inventory"},
    )

    assert audit["status"] == "PASS"
    assert audit["working_capital_grounding_required"]
    assert audit["financial_checkpoint_refs"] == ["canonical:inventory"]


def test_specific_receivables_checkpoint_is_grounded() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "매출채권 회수 정상화가 핵심 확인 조건이다.",
                "evidence_refs": ["canonical:receivables"],
            }
        },
        selected_metrics_by_ref={
            "canonical:receivables": "trade_accounts_receivable"
        },
    )

    assert audit["status"] == "PASS"
    assert audit["financial_checkpoint_refs"] == ["canonical:receivables"]


def test_inventory_claim_without_inventory_ref_is_rejected() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고가 연말보다 크게 늘었다.",
                "evidence_refs": ["narrative:risk"],
            }
        },
        selected_metrics_by_ref={"canonical:inventory": "inventory"},
    )

    assert audit["status"] == "FAIL"
    assert audit["working_capital_grounding_failure_count"] == 1


def test_receivables_claim_without_receivables_ref_is_rejected() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "매출채권 회수가 악화했다.",
                "evidence_refs": ["narrative:risk"],
            }
        },
        selected_metrics_by_ref={
            "canonical:receivables": "trade_accounts_receivable"
        },
    )

    assert audit["status"] == "FAIL"
    assert audit["working_capital_grounding_failure_count"] == 1


def test_inventory_reevaluation_without_typed_ref_is_rejected() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "core_investment_judgment": {
                "text": "영업현금 전환은 유지된다.",
                "evidence_refs": ["canonical:ocf"],
            },
            "business_reevaluation_down": [
                {
                    "text": "재고 증가가 지속되면 하향 재평가한다.",
                    "evidence_refs": ["narrative:risk"],
                }
            ],
            "unknown_treatments": [
                {
                    "summary": "재고 증가의 원인은 확인이 필요하다.",
                    "evidence_refs": ["canonical:inventory"],
                }
            ],
        },
        selected_metrics_by_ref={
            "canonical:inventory": "inventory",
            "canonical:ocf": "operating_cash_flow",
        },
    )

    assert audit["status"] == "FAIL"
    assert audit["material_financial_anchor_grounding_failure_count"] == 0
    assert audit["working_capital_grounding_failure_count"] == 1


def test_irrelevant_typed_ref_does_not_ground_inventory_claim() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고 증가가 지속될 수 있다.",
                "evidence_refs": ["canonical:ocf"],
            }
        },
        selected_metrics_by_ref={
            "canonical:inventory": "inventory",
            "canonical:ocf": "operating_cash_flow",
        },
    )

    assert audit["status"] == "FAIL"
    assert audit["working_capital_grounding_failure_count"] == 1
    assert audit["financial_checkpoint_refs"] == []


def test_m12b_fic_fin_02_and_06_regressions_match_repaired_contract() -> None:
    fic02_run1 = _audit_report_row(
        "33-run-1-context-01.json",
        "FIC-FIN-02",
    )
    fic02_run2 = _audit_report_row(
        "35-run-2-context-01.json",
        "FIC-FIN-02",
    )
    fic06_run1 = _audit_report_row(
        "34-run-1-context-02.json",
        "FIC-FIN-06",
    )

    assert fic02_run1["status"] == "PASS"
    assert fic02_run2["status"] == "PASS"
    assert not fic02_run2["working_capital_grounding_required"]
    assert fic06_run1["status"] == "PASS"
    assert fic06_run1["working_capital_grounding_required"]


def test_old_and_corrected_fic_fin_06_controls_remain_closed() -> None:
    old = json.loads(
        (M12B_REPORT_ROOT / "18-old-fic-fin-06-remains-fail.json").read_text()
    )["row"]
    corrected = json.loads(
        (M12B_REPORT_ROOT / "19-corrected-fic-fin-06-remains-pass.json").read_text()
    )["row"]
    selected = {
        "canonical:fictional:FIC-FIN-06:inventory-current": "inventory",
        "canonical:fictional:FIC-FIN-06:trade-receivables-current": (
            "trade_accounts_receivable"
        ),
    }

    old_audit = m12g.audit_financial_grounding(
        old["core"], selected_metrics_by_ref=selected
    )
    corrected_audit = m12g.audit_financial_grounding(
        corrected["core"], selected_metrics_by_ref=selected
    )

    assert old_audit["status"] == "FAIL"
    assert old_audit["working_capital_grounding_failure_count"] == 1
    assert corrected_audit["status"] == "PASS"


def test_fic_fin_03_qtd_ytd_regression_remains_pass() -> None:
    regressions = m12b._historical_regressions()

    assert regressions["old_fic_fin_03_regression_status"] == "PASS"


def test_generic_validator_has_no_fictional_identity_branch() -> None:
    source = inspect.getsource(m12g.audit_financial_grounding)

    assert "FIC-FIN" not in source
    assert "ticker" not in inspect.signature(
        m12g.audit_financial_grounding
    ).parameters


def test_m12c_fixture_manifests_cover_required_positive_and_negative_cases() -> None:
    regressions = m12c._regressions()
    positive = m12c._positive_fixtures()
    negative = m12c._negative_fixtures(regressions)

    assert positive["fixture_count"] >= 4
    assert positive["fixture_count"] == positive["pass_count"]
    assert positive["status"] == "PASS"
    assert negative["fixture_count"] >= 5
    assert negative["fixture_count"] == negative["rejected_count"]
    assert negative["status"] == "PASS"


def test_m12c_regression_set_closes_overreach_without_weakening_fic06() -> None:
    regressions = m12c._regressions()

    assert regressions["fic02_run1"]["status"] == "PASS"
    assert regressions["fic02_run2"]["status"] == "PASS"
    assert regressions["fic06_m12b_run1"]["status"] == "PASS"
    assert regressions["fic06_old_status"] == "PASS"
    assert regressions["fic06_corrected_status"] == "PASS"
    assert regressions["fic03_status"] == "PASS"


def test_m12c_genericity_and_validator_scope_are_bounded() -> None:
    genericity = m12c._genericity_proof()
    scope = m12c._validator_scope_diff()

    assert genericity["status"] == "PASS"
    assert genericity["production_validator_fictional_branch_count"] == 0
    assert scope["status"] == "PASS"
    assert scope["changed_existing_functions"] == [
        "audit_financial_grounding"
    ]
    assert scope["added_functions"] == [
        "_working_capital_metrics_in_text"
    ]
