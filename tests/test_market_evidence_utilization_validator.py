from __future__ import annotations

from app.services.market_evidence_utilization_validator_service import (
    validate_us_market_evidence_utilization,
)


def _item(
    slot: str,
    refs: list[str],
    *,
    required: bool = True,
    omission_reason: str = "SELECTED",
) -> dict[str, object]:
    return {
        "slot": slot,
        "priority": 1,
        "claim_text": slot,
        "evidence_refs": refs,
        "numeric_refs": [],
        "observation_dates": ["2026-08-26"],
        "temporal_roles": ["CURRENT_OBSERVATION"],
        "materiality": "fixture",
        "omission_reason": omission_reason,
        "required_consumption": required,
    }


def _run41_plan() -> dict[str, object]:
    return {
        "contract": "us-market-digest-plan-v1",
        "market": "US",
        "items": [
            _item(
                "CURRENT_MARKET",
                [
                    "market:index:SPY",
                    "market:index:QQQ",
                    "market:index:IWM",
                    "market:sector:SOXX",
                ],
            ),
            _item(
                "PARTICIPATION_STYLE",
                ["market:style:RSP", "market:index:SPY"],
            ),
            _item(
                "SECTOR_DISPERSION",
                ["market:sector:XLI", "market:sector:XLV"],
            ),
            _item(
                "BREADTH_STATE",
                [],
                required=False,
                omission_reason="OMITTED_UNAVAILABLE",
            ),
            _item(
                "MACRO_CONTEXT",
                ["market:real_yield:DFII10"],
                required=False,
            ),
        ],
    }


def test_historical_run41_macro_only_digest_fails_selected_slots() -> None:
    macro_refs = {
        "market:real_yield:DFII10",
        "market:oil:DCOILWTICO",
        "market:nominal_yield:DGS10",
    }

    result = validate_us_market_evidence_utilization(
        _run41_plan(),
        facts_used=macro_refs,
        interpretation_fact_ids=macro_refs,
    )

    assert result.status == "FAIL"
    assert "CORE_MARKET_SLOT_UNCONSUMED" in result.errors
    assert "SELECTED_RSP_SLOT_UNCONSUMED" in result.errors
    assert "SELECTED_SECTOR_DISPERSION_UNCONSUMED" in result.errors
    assert "MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE" in result.errors
    assert result.counters["VALIDATOR_FORCED_NUMERIC_DUMP"] == 0


def test_concise_semantic_consumption_passes_without_numeric_claim_requirement() -> None:
    refs = {
        "market:index:SPY",
        "market:style:RSP",
        "market:sector:XLI",
        "market:sector:XLV",
    }

    result = validate_us_market_evidence_utilization(
        _run41_plan(),
        facts_used=refs,
        interpretation_fact_ids=refs,
    )

    assert result.status == "PASS"
    assert result.errors == ()
    assert all(value == 0 for value in result.counters.values())


def test_rsp_requires_rsp_anchor_not_only_spy_overlap() -> None:
    refs = {
        "market:index:SPY",
        "market:sector:XLI",
        "market:sector:XLV",
    }

    result = validate_us_market_evidence_utilization(
        _run41_plan(),
        facts_used=refs,
        interpretation_fact_ids=refs,
    )

    assert result.status == "FAIL"
    assert "SELECTED_RSP_SLOT_UNCONSUMED" in result.errors
    assert "CORE_MARKET_SLOT_UNCONSUMED" not in result.errors


def test_sector_dispersion_requires_both_selected_extremes() -> None:
    refs = {
        "market:index:SPY",
        "market:style:RSP",
        "market:sector:XLI",
    }

    result = validate_us_market_evidence_utilization(
        _run41_plan(),
        facts_used=refs,
        interpretation_fact_ids=refs,
    )

    assert result.status == "FAIL"
    assert "SELECTED_SECTOR_DISPERSION_UNCONSUMED" in result.errors


def test_interpreted_plan_evidence_must_be_declared_in_facts_used() -> None:
    interpreted = {
        "market:index:SPY",
        "market:style:RSP",
        "market:sector:XLI",
        "market:sector:XLV",
    }

    result = validate_us_market_evidence_utilization(
        _run41_plan(),
        facts_used={"market:index:SPY"},
        interpretation_fact_ids=interpreted,
    )

    assert result.status == "FAIL"
    assert any(error.startswith("PLAN_EVIDENCE_NOT_DECLARED_USED") for error in result.errors)


def test_unknown_omission_reason_fails_closed() -> None:
    plan = _run41_plan()
    plan["items"][3]["omission_reason"] = "NOT_EXPLAINED"

    result = validate_us_market_evidence_utilization(
        plan,
        facts_used={
            "market:index:SPY",
            "market:style:RSP",
            "market:sector:XLI",
            "market:sector:XLV",
        },
        interpretation_fact_ids={
            "market:index:SPY",
            "market:style:RSP",
            "market:sector:XLI",
            "market:sector:XLV",
        },
    )

    assert result.status == "FAIL"
    assert "UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION:BREADTH_STATE" in result.errors
