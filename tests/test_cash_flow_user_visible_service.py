from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.services.cash_flow_capital_efficiency_service import PeriodIdentity, PeriodType
from app.services.cash_flow_user_visible_service import (
    CashFlowRolloutMode,
    SelectionState,
    cash_flow_period_claim_contract,
    context_from_notification_payload,
    fact_catalog_entries,
    resolve_rollout_mode,
    resolve_selected_unknowns,
    safe_select_user_visible_cash_flow,
    select_user_visible_cash_flow,
    selection_to_dict,
)
from app.services.numeric_semantic_registry import build_numeric_registry


CUTOFF = date(2026, 8, 21)


def _fact(
    fact_id: str,
    metric: str,
    value: str,
    *,
    input_fact_ids: list[str] | None = None,
    period_type: str = "YTD",
    fiscal_year: int = 2026,
    fiscal_quarter: int | None = 2,
    period_end: str = "2026-06-30",
    filing_date: str = "2026-07-25",
) -> dict[str, object]:
    capex = metric == "ppe_capex_cash_outflow"
    fcf = metric == "free_cash_flow_ppe"
    return {
        "ticker": "TEST",
        "fact_id": fact_id,
        "issuer_id": "sec:fixture",
        "metric": metric,
        "value": value,
        "currency": "USD",
        "unit": "USD",
        "period_start": f"{fiscal_year}-01-01",
        "period_end": period_end,
        "period_type": period_type,
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "entity_scope": "issuer_level",
        "statement_basis": "official_filing_cash_flow_statement",
        "reported_or_derived": "derived_metric" if fcf else "reported",
        "source_provider": "sec_edgar_companyfacts",
        "source_document_id": "filing-1",
        "filing_date": filing_date,
        "source_occurrence_id": f"occurrence:{fact_id}",
        "raw_payload_sha256": "a" * 64,
        "semantic_mapping": (
            "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW" if fcf else metric
        ),
        "fact_type": "DERIVED_METRIC" if fcf else "REPORTED",
        "source_document_type": "10-Q",
        "source_semantic": metric,
        "source_reported_value": None if fcf else value,
        "source_reported_unit": None if fcf else "USD",
        "source_sign": "positive_payment_magnitude" if capex else "economic_signed",
        "normalization_transform": "identity_positive_payment_magnitude" if capex else None,
        "capex_scope": "ppe_only" if capex else None,
        "derivation_formula": "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW" if fcf else None,
        "derivation_version": "cash-flow-capital-efficiency-v1" if fcf else None,
        "input_fact_ids": input_fact_ids or [],
        "quality": "DERIVED_SAFE" if fcf else "REPORTED_VERIFIED",
        "eligibility": "ELIGIBLE",
        "denial_reason": None,
        "cautions": ["sec_companyfacts_issuer_level_context"],
        "as_of_date": "2026-08-20",
    }


def _report(
    path: Path,
    *,
    ticker: str = "TEST",
    market: str = "US_FOREIGN",
    industry: str = "cloud_platform_software",
    financial_type: str = "non_financial",
    status: str = "ELIGIBLE",
    include_fcf: bool = True,
    source: str = "SEC Company Facts official XBRL",
) -> Path:
    ocf = _fact("ocf-current", "operating_cash_flow", "1000000000")
    capex = _fact("capex-current", "ppe_capex_cash_outflow", "400000000")
    fcf = _fact(
        "fcf-current",
        "free_cash_flow_ppe",
        "600000000",
        input_fact_ids=["ocf-current", "capex-current"],
    )
    facts = [ocf, capex, fcf] if include_fcf else [ocf]
    payload = {
        "active_universe": [
            {
                "ticker": ticker,
                "market": market,
                "source": source,
                "industry": industry,
                "financial_type": financial_type,
                "cash_flow_core_status": status,
                "denial_reasons": [],
                "metrics": {
                    "ocf": {"status": "ELIGIBLE", "fact_id": "ocf-current"},
                    "capex_ppe": {
                        "status": "ELIGIBLE" if include_fcf else "BLOCKED",
                        "fact_id": "capex-current" if include_fcf else None,
                    },
                    "fcf": {
                        "status": "ELIGIBLE" if include_fcf else "BLOCKED",
                        "fact_id": "fcf-current" if include_fcf else None,
                    },
                },
            }
        ],
        "canonical_facts": facts,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _select(report: Path, **overrides: object):
    values: dict[str, object] = {
        "ticker": "TEST",
        "cutoff": CUTOFF,
        "latest_formal_period": date(2026, 6, 30),
        "existing_unknowns": ["OCF·CAPEX·FCF를 확인해야 합니다."],
        "materiality_signals": ["AI CAPEX의 현금전환"],
        "source_text": "AI Cloud CAPEX and margin",
        "rollout_mode": "SELECTIVE_CURRENT_FORMAL_FULL_FCF",
        "report_path": report,
    }
    values.update(overrides)
    return select_user_visible_cash_flow(**values)


def test_rollout_mode_is_fail_safe_and_off_has_no_cached_selection(tmp_path: Path) -> None:
    report = _report(tmp_path / "facts.json")
    selected = _select(report)

    assert resolve_rollout_mode("invalid") == CashFlowRolloutMode.OFF
    assert selected.selection_state == SelectionState.SELECTED
    assert _select(report, rollout_mode="OFF").selection_state == SelectionState.OFF
    assert _select(report, rollout_mode="OFF").context_id is None
    assert _select(report, rollout_mode="invalid").facts == ()


def test_delta_first_suppresses_unchanged_visible_fact_but_keeps_unknown_resolved(
    tmp_path: Path,
) -> None:
    report = _report(tmp_path / "facts.json")
    first = _select(report)
    first_context = selection_to_dict(first)
    repeated = _select(report, previous_user_visible_context=first_context)

    assert first.display_reason == "RESOLVED_PRIOR_UNKNOWN"
    assert repeated.selection_state == SelectionState.SUPPRESSED
    assert repeated.display_reason == "SUPPRESSED_NO_DELTA"
    assert repeated.rendered_text is None
    assert all(
        "FCF가 없어" not in item
        for item in resolve_selected_unknowns(
            ["FCF가 없어 확인할 수 없습니다."],
            repeated,
            industry=repeated.industry,
            source_text="AI Cloud",
        )
    )

    changed_context = {**first_context, "evidence_signature": "older-evidence"}
    changed = _select(report, previous_user_visible_context=changed_context)
    assert changed.user_visible_enabled is True
    assert changed.display_reason == "MATERIAL_NEW_FORMAL_PERIOD"


def test_nested_delivery_payload_recovers_previous_visibility_context(
    tmp_path: Path,
) -> None:
    selected = selection_to_dict(_select(_report(tmp_path / "facts.json")))
    payload = {
        "deterministic_payload": {
            "analysis_context": {"cash_flow_user_visible": selected}
        }
    }

    assert context_from_notification_payload(payload) == selected
    assert context_from_notification_payload("not-json") == {}


def test_current_formal_full_fcf_is_selected_with_one_scoped_number(tmp_path: Path) -> None:
    selected = _select(_report(tmp_path / "facts.json"))
    payload = selection_to_dict(selected)

    assert selected.user_visible_enabled is True
    assert selected.context_id and payload["cash_flow_user_visible_context_id"] == selected.context_id
    assert payload["primary_fact_ref"] == "fcf-current"
    assert payload["financial_currency"] == "USD"
    assert payload["freshness_state"] == "CURRENT_FORMAL"
    assert "2026 회계연도 상반기 누계" in str(selected.rendered_text)
    assert "PPE 투자 후 잉여현금흐름은 $600M" in str(selected.rendered_text)
    assert str(selected.rendered_text).count("$600M") == 1
    assert "yield" not in str(selected.rendered_text).casefold()


def test_validated_formal_period_inventory_fills_snapshot_gap(tmp_path: Path) -> None:
    report = _report(tmp_path / "facts.json")
    formal = tmp_path / "formal.json"
    formal.write_text(
        json.dumps(
            {
                "active_universe": [
                    {"ticker": "TEST", "latest_formal_period": "2026-06-30"}
                ]
            }
        ),
        encoding="utf-8",
    )

    selected = _select(
        report,
        latest_formal_period=None,
        formal_period_report_path=formal,
    )

    assert selected.user_visible_enabled is True
    assert selection_to_dict(selected)["freshness_state"] == "CURRENT_FORMAL"

    selected_from_newer_inventory = _select(
        report,
        latest_formal_period=date(2026, 3, 31),
        formal_period_report_path=formal,
    )
    assert selected_from_newer_inventory.user_visible_enabled is True


def test_non_material_lagging_stale_and_ocf_only_are_suppressed(tmp_path: Path) -> None:
    general = _report(
        tmp_path / "general.json", industry="general_non_financial"
    )
    assert _select(
        general, existing_unknowns=[], materiality_signals=[]
    ).selection_state == SelectionState.SUPPRESSED
    assert _select(
        general,
        latest_preliminary_period=date(2026, 7, 31),
    ).selection_state == SelectionState.SUPPRESSED
    assert _select(
        general,
        latest_formal_period=date(2026, 7, 31),
    ).selection_reason == "stale_formal"
    ocf_only = _report(tmp_path / "ocf.json", include_fcf=False)
    assert _select(ocf_only).selection_state == SelectionState.SUPPRESSED
    assert _select(ocf_only).selection_reason == "ocf_only_user_visible_excluded"
    assert fact_catalog_entries(_select(ocf_only)) == []


def test_kr_and_insurance_are_excluded_without_ticker_rules(tmp_path: Path) -> None:
    kr = _report(
        tmp_path / "kr.json",
        market="KR",
        source="OpenDART stored formal evidence",
    )
    assert _select(kr).selection_reason == "initial_market_or_source_scope_excluded"

    insurance = _report(
        tmp_path / "insurance.json",
        industry="insurance_reinsurance",
        financial_type="financial",
        status="NOT_APPLICABLE",
    )
    assert _select(insurance).selection_state == SelectionState.NOT_APPLICABLE


def test_lineage_and_baseline_conflicts_fail_closed(tmp_path: Path) -> None:
    report = _report(tmp_path / "facts.json")
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["canonical_facts"][2]["input_fact_ids"] = ["ocf-current"]
    report.write_text(json.dumps(payload), encoding="utf-8")
    assert _select(report).selection_reason == "full_fcf_input_fact_missing"

    clean = _report(tmp_path / "clean.json")
    assert _select(
        clean, baseline_unresolved_conflicts=["unresolved"]
    ).selection_reason == "baseline_consistency_unresolved"


def test_optional_renderer_failure_isolated_after_safe_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.cash_flow_user_visible_service._render",
        lambda *_args, **_kwargs: None,
    )
    selection = _select(_report(tmp_path / "facts.json"))

    assert selection.selection_state == SelectionState.SUPPRESSED
    assert selection.selection_reason == "cash_flow_optional_renderer_failed"
    assert selection.rendered_text is None


def test_optional_selector_exception_fails_closed_without_raising(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.cash_flow_user_visible_service.select_user_visible_cash_flow",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("fixture")),
    )

    selection = safe_select_user_visible_cash_flow(
        ticker="TEST",
        cutoff=CUTOFF,
        latest_formal_period=date(2026, 6, 30),
        rollout_mode="SELECTIVE_CURRENT_FORMAL_FULL_FCF",
        report_path=_report(tmp_path / "facts.json"),
    )

    assert selection.selection_state == SelectionState.SUPPRESSED
    assert selection.selection_reason == "cash_flow_optional_enrichment_failed:ValueError"


def test_selected_unknowns_and_numeric_registry_use_canonical_fact_ids(tmp_path: Path) -> None:
    selected = _select(_report(tmp_path / "facts.json"))
    unknowns = resolve_selected_unknowns(
        ["FCF가 없어 확인할 수 없습니다.", "Cloud margin은 미확인입니다."],
        selected,
        industry=selected.industry,
        source_text="AI Cloud margin",
    )
    entries = fact_catalog_entries(selected)
    registry = build_numeric_registry(entries)

    assert all("FCF가 없어" not in item for item in unknowns)
    assert {item["fact_id"] for item in entries} == {
        "ocf-current",
        "capex-current",
        "fcf-current",
    }
    assert {item["semantic_type"] for item in registry} == {
        "operating_cash_flow",
        "ppe_capex_cash_outflow",
        "free_cash_flow_ppe",
    }
    assert all(item["registered"] and item["prose_allowed"] for item in registry)


def test_selected_ytd_context_exposes_canonical_ai_period_claim_contract(
    tmp_path: Path,
) -> None:
    selected = _select(_report(tmp_path / "facts.json"))

    payload = selection_to_dict(selected)

    assert payload["period_identity_contract"] == "cash-flow-period-identity-v1"
    assert payload["required_period_label"] == "2026 회계연도 상반기 누계"
    assert payload["duration_basis"] == "fiscal_year_to_date_cumulative"
    assert payload["is_ytd"] is True
    assert payload["is_fy"] is False
    assert payload["fcf_scope"] == "OCF - PPE CAPEX"
    assert payload["primary_period"]["canonical_label"] == (
        "2026 회계연도 상반기 누계"
    )
    assert "standalone_quarter" in payload["forbidden_period_claims"]


def test_fy_and_non_calendar_period_labels_preserve_issuer_fiscal_identity(
    tmp_path: Path,
) -> None:
    report = _report(tmp_path / "facts.json")
    payload = json.loads(report.read_text(encoding="utf-8"))
    for fact in payload["canonical_facts"]:
        fact.update(
            {
                "period_start": "2024-09-01",
                "period_end": "2025-08-31",
                "period_type": "FY",
                "fiscal_year": 2025,
                "fiscal_quarter": None,
            }
        )
    report.write_text(json.dumps(payload), encoding="utf-8")
    selected = _select(report, latest_formal_period=date(2025, 8, 31))

    assert selected.user_visible_enabled is True
    assert "2025 회계연도 연간" in str(selected.rendered_text)
    assert "2025년 4분기" not in str(selected.rendered_text)
    payload = selection_to_dict(selected)
    assert payload["required_period_label"] == "2025 회계연도 연간"
    assert payload["duration_basis"] == "full_fiscal_year"
    assert payload["is_fy"] is True
    assert "year_to_date" in payload["forbidden_period_claims"]


def test_fiscal_q3_ytd_and_qtd_contracts_remain_distinct(tmp_path: Path) -> None:
    ytd_report = _report(tmp_path / "ytd.json")
    ytd_payload = json.loads(ytd_report.read_text(encoding="utf-8"))
    for fact in ytd_payload["canonical_facts"]:
        fact.update(
            {
                "period_start": "2025-08-29",
                "period_end": "2026-05-28",
                "period_type": "YTD",
                "fiscal_year": 2026,
                "fiscal_quarter": 3,
            }
        )
    ytd_report.write_text(json.dumps(ytd_payload), encoding="utf-8")
    ytd = selection_to_dict(
        _select(ytd_report, latest_formal_period=date(2026, 5, 28))
    )

    qtd = cash_flow_period_claim_contract(
        PeriodIdentity(
            start=date(2026, 3, 1),
            end=date(2026, 5, 28),
            period_type=PeriodType.QTD,
            fiscal_year=2026,
            fiscal_quarter=3,
        )
    )

    assert ytd["required_period_label"] == "2026 회계연도 3분기 누계"
    assert ytd["duration_basis"] == "fiscal_year_to_date_cumulative"
    assert qtd is not None
    assert qtd["required_period_label"] == "2026 회계연도 3분기 단독"
    assert qtd["duration_basis"] == "standalone_fiscal_quarter"


def test_negative_currency_amount_uses_canonical_formatter(tmp_path: Path) -> None:
    report = _report(tmp_path / "facts.json")
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["canonical_facts"][0]["value"] = "-100000000"
    payload["canonical_facts"][0]["source_reported_value"] = "-100000000"
    payload["canonical_facts"][2]["value"] = "-500000000"
    report.write_text(json.dumps(payload), encoding="utf-8")

    selected = _select(report)

    assert "$-500M" in str(selected.rendered_text)


def test_renderer_and_numeric_registry_share_half_rounding(tmp_path: Path) -> None:
    report = _report(tmp_path / "facts.json")
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["canonical_facts"][0]["value"] = "-323295000"
    payload["canonical_facts"][0]["source_reported_value"] = "-323295000"
    payload["canonical_facts"][2]["value"] = "-723295000"
    report.write_text(json.dumps(payload), encoding="utf-8")
    selected = _select(report)
    registry = build_numeric_registry(fact_catalog_entries(selected))
    fcf = next(item for item in registry if item["semantic_type"] == "free_cash_flow_ppe")

    assert "$-723.29M" in str(selected.rendered_text)
    assert fcf["canonical_display_value"] == "$-723.29M"
