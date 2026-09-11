from __future__ import annotations

import json
from pathlib import Path

from app.services.directional_financial_context_service import (
    FinancialSemanticCategory,
)
from scripts import directional_financial_context_m12 as m12


GENERATION = "m12-fictional-test-generation"


def test_fictional_manifest_freezes_exact_eight_by_two_by_three_topology() -> None:
    manifest = m12.fictional_manifest(GENERATION)

    assert manifest["fictional_subject_count"] == 8
    assert manifest["fictional_context_count"] == 2
    assert manifest["fictional_repetition_count"] == 3
    assert manifest["model_calls"] == 6
    assert manifest["real_issuer_model_exposure_count"] == 0
    assert tuple(row["ticker"] for row in manifest["subjects"]) == m12.TICKERS
    assert all(row["fictional"] is True for row in manifest["subjects"])


def test_fictional_source_lock_and_contexts_are_deterministic() -> None:
    first = m12.fictional_inputs(GENERATION)
    second = m12.fictional_inputs(GENERATION)
    first_lock = m12._source_lock(GENERATION, *first)
    second_lock = m12._source_lock(GENERATION, *second)

    assert first_lock == second_lock
    assert first_lock["wrapper_auto_retry"] == 0
    assert first_lock["batch_split"] == 0
    assert first_lock["subjects_per_shared_context"] == 4
    assert first_lock["timeout_seconds"] == 1800


def test_qtd_and_ytd_conflict_remain_distinct_selected_items() -> None:
    _packets, owned, _catalogs, contexts = m12.fictional_inputs(GENERATION)
    financial = owned["FIC-FIN-03"]
    context = m12.financial_decision_context_for_owned(financial)

    assert context is not None
    periods = {item.period.type for item in context.evidence_items}
    assert {"QTD", "YTD"} <= {period.value for period in periods}
    assert all(
        item.semantic_category == FinancialSemanticCategory.PERFORMANCE_TREND
        for item in context.evidence_items
    )
    compact_periods = {
        row["period"]["type"]
        for row in contexts["FIC-FIN-03"]["financial_decision_context"][
            "evidence_items"
        ]
    }
    assert compact_periods == {"QTD", "YTD"}


def test_missing_optional_and_financial_sector_cases_fail_closed() -> None:
    _packets, owned, catalogs, contexts = m12.fictional_inputs(GENERATION)
    missing = m12.financial_decision_context_for_owned(owned["FIC-FIN-07"])
    financial_sector = m12.financial_decision_context_for_owned(
        owned["FIC-FIN-08"]
    )

    assert missing is not None
    assert missing.evidence_items == ()
    assert missing.unavailable_or_not_applicable == ("FINANCIAL_VALUE_UNAVAILABLE",)
    assert financial_sector is not None
    assert financial_sector.evidence_items == ()
    assert financial_sector.unavailable_or_not_applicable == (
        "SECTOR_FRAMEWORK_REQUIRED",
    )
    assert contexts["FIC-FIN-07"]["financial_decision_context"][
        "evidence_items"
    ] == []
    assert contexts["FIC-FIN-08"]["financial_decision_context"][
        "evidence_items"
    ] == []
    assert not any(
        owned["FIC-FIN-08"].domain_by_ref[ref].value
        == "LIQUIDITY_CASHFLOW_CURRENT"
        and ref in catalogs["FIC-FIN-08"].by_ref
        for ref in owned["FIC-FIN-08"].domain_by_ref
    )


def test_financial_blocks_contain_no_price_technical_or_supply_refs() -> None:
    _packets, owned, catalogs, contexts = m12.fictional_inputs(GENERATION)

    for ticker in m12.TICKERS:
        block = contexts[ticker].get("financial_decision_context")
        if not block:
            continue
        for item in block["evidence_items"]:
            canonical = catalogs[ticker].by_alias[item["evidence_id"]].canonical_ref
            assert owned[ticker].domain_by_ref[canonical] not in m12.TIMING_DOMAINS


def test_missing_context_is_not_bearish_without_explicit_negative_treatment() -> None:
    packets, owned, catalogs, _contexts = m12.fictional_inputs(GENERATION)
    ticker = "FIC-FIN-07"
    core_ref = next(
        ref
        for ref in catalogs[ticker].by_ref
        if packets[ticker].model_dump(mode="json") and "business-thesis" in ref
    )
    candidate = {
        "sell_drivers": [
            {"text": "Execution remains a supplied business risk.", "evidence_refs": [core_ref]}
        ],
        "unknown_treatments": [
            {
                "summary": "Optional cash evidence is unavailable.",
                "evidence_refs": [core_ref],
                "treatment": "CONFIDENCE_LIMIT",
                "directional_negative_basis": [],
            },
            {
                "summary": "Customer retention detail is unavailable.",
                "evidence_refs": [core_ref],
                "treatment": "DIRECTIONAL_NEGATIVE",
                "directional_negative_basis": [core_ref],
            },
        ],
    }

    assert not m12._missing_context_bearish_default(
        type(
            "Candidate",
            (),
            {
                "sell_drivers": tuple(
                    type("Driver", (), {"text": row["text"]})()
                    for row in candidate["sell_drivers"]
                ),
                "unknown_treatments": tuple(
                    type(
                        "Unknown",
                        (),
                        {
                            "summary": row["summary"],
                            "treatment": row["treatment"],
                        },
                    )()
                    for row in candidate["unknown_treatments"]
                ),
            },
        )()
    )
    assert owned[ticker].sector_framework == "standard_operating_company"


def test_preserved_m12_qtd_ytd_raw_reasoning_passes_repaired_validator() -> None:
    report = json.loads(
        Path(
            "docs/reports/20260909-directional-financial-context-"
            "consumption-specificity-implementation/"
            "33-canary-context-01-run-1.json"
        ).read_text(encoding="utf-8")
    )
    candidate = next(
        row["core"] for row in report["rows"] if row["ticker"] == "FIC-FIN-03"
    )
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(
        report["generation_id"]
    )
    context = m12.financial_decision_context_for_owned(owned["FIC-FIN-03"])
    assert context is not None

    validation = m12.validate_qtd_ytd_conflict_semantics(
        candidate,
        supplied_refs=tuple(row.ref for row in owned["FIC-FIN-03"].evidence),
        required_ref_ids=tuple(item.evidence_id for item in context.evidence_items),
    )

    assert validation.required
    assert validation.valid
    assert validation.linked_claim_count >= 1
    assert validation.explicit_claim_count >= 1
