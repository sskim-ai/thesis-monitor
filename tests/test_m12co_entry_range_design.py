from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12cn_policy_shadow import classify_shadow_failure
from scripts.m12co_entry_range_contract import (
    MethodFamily,
    build_subject_candidate_coverage,
    field_ownership_audit,
    generic_materialization_control_matrix,
    materialize_entry_range,
)


CANONICAL_REFS = (
    "canonical:valuation:book_quality",
    "canonical:valuation:book_value",
    "canonical:valuation:historical_pb",
    "canonical:valuation:trailing_earnings",
    "canonical:valuation:multiple_relation",
    "canonical:valuation:historical_pe",
)


def _row(
    ref_id: str, statement: dict[str, object], *, label: str = "valuation"
) -> dict[str, object]:
    return {
        "ref_id": ref_id,
        "category": "valuation",
        "label": label,
        "statement": statement,
        "as_of": "2026-09-17",
    }


def _packet(ticker: str = "GENERIC_A") -> dict[str, object]:
    return {
        "ticker": ticker,
        "company_name": f"{ticker} Company",
        "assessment_date": "2026-09-17",
        "technical_context_status": "eligible",
        "technical_context_quality": "high",
        "data_quality_cautions": [],
        "evidence": [
            {
                "ref_id": "canonical:price:current",
                "category": "price",
                "label": "price",
                "statement": {
                    "current_price": 100.0,
                    "currency": "USD",
                    "price_as_of": "2026-09-17",
                    "price_basis": "close",
                    "price_state_confirmation": "confirmed",
                },
                "as_of": "2026-09-17",
            },
            {
                "ref_id": "canonical:chart:support",
                "category": "technical",
                "label": "chart_support_zone",
                "statement": {
                    "zone_low": 85.0,
                    "zone_high": 90.0,
                    "currency": "USD",
                    "role": "support_zone",
                },
                "as_of": "2026-09-17",
            },
            _row(
                "canonical:valuation:book_quality",
                {
                    "status": "passed",
                    "price_to_book_basis_status": "directly_comparable",
                    "book_share_basis": "current_security",
                    "book_currency": "USD",
                    "price_currency": "USD",
                    "bvps": 20.0,
                },
            ),
            _row("canonical:valuation:book_value", {"bvps": 20.0, "currency": "USD"}),
            _row(
                "canonical:valuation:historical_pb",
                {
                    "historical_pb_statistics": {
                        "metric": "price_to_book",
                        "history_quality": "high",
                        "deduplicated_observation_count": 100,
                        "history_coverage_ratio": 0.95,
                        "history_end_date": "2026-09-16",
                        "percentile_25": 1.0,
                        "percentile_50": 2.0,
                        "percentile_75": 3.0,
                        "percentile_90": 4.0,
                    }
                },
            ),
            _row(
                "canonical:valuation:trailing_earnings",
                {"ttm_eps": 5.0, "trailing_pe": 20.0, "currency": "USD"},
            ),
            _row(
                "canonical:valuation:multiple_relation",
                {
                    "basis_comparable": True,
                    "interpretation_eligibility": "eligible",
                    "trailing_basis_status": "directly_comparable",
                    "trailing_share_basis": "current_security",
                    "security_basis": "verified_non_depositary",
                    "currency_basis": "USD",
                    "price_currency": "USD",
                    "trailing_value": 20.0,
                },
            ),
            _row(
                "canonical:valuation:historical_pe",
                {
                    "historical_pe_statistics": {
                        "metric": "trailing_pe",
                        "history_quality": "high",
                        "deduplicated_observation_count": 100,
                        "history_coverage_ratio": 0.95,
                        "history_end_date": "2026-09-16",
                        "percentile_25": 10.0,
                        "percentile_50": 15.0,
                        "percentile_75": 20.0,
                        "percentile_90": 25.0,
                    }
                },
            ),
        ],
    }


def _ownership(ticker: str = "GENERIC_A") -> dict[str, object]:
    return {
        "ticker": ticker,
        "core_ref_ids": list(CANONICAL_REFS),
        "timing_ref_ids": ["canonical:price:current", "canonical:chart:support"],
        "expectation_valuation": {"valuation_refs": list(CANONICAL_REFS)},
    }


def _coverage(
    packet: dict[str, object] | None = None,
    ownership: dict[str, object] | None = None,
) -> dict[str, object]:
    return build_subject_candidate_coverage(
        market="fictional",
        packet=packet or _packet(),
        ownership=ownership or _ownership(),
    )


def _evidence(packet: dict[str, object], ref_id: str) -> dict[str, object]:
    return next(row for row in packet["evidence"] if row["ref_id"] == ref_id)


def _method(result: dict[str, object], family: MethodFamily) -> dict[str, object]:
    return next(row for row in result["method_feasibility"] if row["method_family"] == family.value)


def _candidates(result: dict[str, object], family: MethodFamily) -> list[dict[str, object]]:
    return [row for row in result["fundamental_candidates"] if row["method_family"] == family.value]


def test_pe_and_pb_arithmetic_and_exact_quantile_refs() -> None:
    result = _coverage()
    pe = _candidates(result, MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE)
    pb = _candidates(result, MethodFamily.HISTORICAL_PB_QUANTILE)

    assert [(row["low"], row["high"]) for row in pe] == [
        (50.0, 75.0),
        (75.0, 100.0),
        (100.0, 125.0),
    ]
    assert [(row["low"], row["high"]) for row in pb] == [
        (20.0, 40.0),
        (40.0, 60.0),
        (60.0, 80.0),
    ]
    assert pe[0]["formula_inputs"] == {
        "denominator_name": "positive_current_security_ttm_eps",
        "denominator_value": 5.0,
        "denominator_ref": "canonical:valuation:trailing_earnings",
        "multiple_low": 10.0,
        "multiple_high": 15.0,
        "history_ref": "canonical:valuation:historical_pe",
    }
    assert set(pb[0]["evidence_refs"]) == {
        "canonical:valuation:book_quality",
        "canonical:valuation:book_value",
        "canonical:valuation:historical_pb",
    }


def test_negative_earnings_excludes_pe_without_blocking_safe_pb() -> None:
    packet = _packet()
    trailing = _evidence(packet, "canonical:valuation:trailing_earnings")["statement"]
    trailing["ttm_eps"] = -5.0
    result = _coverage(packet)

    assert _candidates(result, MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE) == []
    assert len(_candidates(result, MethodFamily.HISTORICAL_PB_QUANTILE)) == 3
    assert (
        "TTM_EPS_NOT_POSITIVE"
        in _method(result, MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE)["rejected_reasons"]
    )


def test_bad_book_basis_excludes_pb() -> None:
    packet = _packet()
    quality = _evidence(packet, "canonical:valuation:book_quality")["statement"]
    quality["price_to_book_basis_status"] = "unresolved"
    result = _coverage(packet)

    assert _candidates(result, MethodFamily.HISTORICAL_PB_QUANTILE) == []
    assert (
        "BOOK_BASIS_NOT_DIRECTLY_COMPARABLE"
        in _method(result, MethodFamily.HISTORICAL_PB_QUANTILE)["rejected_reasons"]
    )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("history_quality", "low", "HISTORY_QUALITY_NOT_HIGH"),
        ("deduplicated_observation_count", 29, "HISTORY_OBSERVATIONS_INSUFFICIENT"),
        ("history_coverage_ratio", 0.79, "HISTORY_COVERAGE_INSUFFICIENT"),
        ("history_end_date", "2026-03-30", "HISTORY_AS_OF_NOT_ALIGNED"),
    ],
)
def test_history_quality_gates_fail_closed(field: str, value: object, reason: str) -> None:
    packet = _packet()
    history = _evidence(packet, "canonical:valuation:historical_pb")["statement"][
        "historical_pb_statistics"
    ]
    history[field] = value
    result = _coverage(packet)

    assert _candidates(result, MethodFamily.HISTORICAL_PB_QUANTILE) == []
    assert reason in _method(result, MethodFamily.HISTORICAL_PB_QUANTILE)["rejected_reasons"]


def test_forward_metric_basis_mismatches_never_emit_candidates() -> None:
    packet = _packet()
    packet["evidence"].extend(
        [
            _row(
                "canonical:valuation:modeled_forward_book",
                {"forward_bvps": 24.0, "forward_book_basis": "FY1"},
            ),
            _row(
                "canonical:valuation:consensus_forward_earnings",
                {"forward_eps": 7.0, "estimate_period": "FY1"},
            ),
        ]
    )
    result = _coverage(packet)
    forward_book = _method(result, MethodFamily.FORWARD_BOOK_HISTORICAL_PB)
    forward_pe = _method(result, MethodFamily.FORWARD_EPS_HISTORICAL_TRAILING_PE)

    assert forward_book["candidate_emitted"] is False
    assert forward_book["rejected_reasons"] == ["FORWARD_BOOK_HISTORICAL_PB_BASIS_UNRESOLVED"]
    assert forward_pe["candidate_emitted"] is False
    assert forward_pe["rejected_reasons"] == ["FORWARD_EPS_HISTORICAL_TRAILING_PE_BASIS_MISMATCH"]


def test_method_disagreement_is_preserved_without_averaging() -> None:
    result = _coverage()

    assert result["method_disagreement"]["status"] == "METHODS_DIVERGE"
    assert len(result["method_disagreement"]["pairwise"]) == 3
    assert all(not row["overlaps"] for row in result["method_disagreement"]["pairwise"])
    assert "averaged_candidate" not in result["method_disagreement"]


def test_historical_regime_diagnostics_are_descriptive_and_source_bound() -> None:
    result = _coverage()
    diagnostics = result["historical_regime_diagnostics"]
    by_method = {row["method_family"]: row for row in diagnostics["methods"]}

    assert diagnostics["historical_distribution_role"] == ("DESCRIPTIVE_NOT_NORMATIVE_FAIR_VALUE")
    assert diagnostics["ttm_eps_state"] == "POSITIVE_TTM_EPS"
    assert diagnostics["structural_thesis_change"]["status"] == ("NOT_DETERMINISTICALLY_CLASSIFIED")
    assert by_method[MethodFamily.HISTORICAL_PB_QUANTILE.value]["historical_quantiles"] == {
        "percentile_25": 1.0,
        "percentile_50": 2.0,
        "percentile_75": 3.0,
        "percentile_90": 4.0,
    }
    assert (
        by_method[MethodFamily.HISTORICAL_PB_QUANTILE.value]["premium_band_candidate_exists"]
        is True
    )


def test_current_price_is_context_only_and_no_arbitrary_discount_is_used() -> None:
    result = _coverage()

    for candidate in result["fundamental_candidates"]:
        inputs = candidate["formula_inputs"]
        assert "current_price" not in inputs
        assert candidate["low"] == pytest.approx(
            inputs["denominator_value"] * inputs["multiple_low"]
        )
        assert candidate["high"] == pytest.approx(
            inputs["denominator_value"] * inputs["multiple_high"]
        )
        assert candidate["current_price_context"]["used_in_candidate_formula"] is False


def test_candidate_identity_is_stable_and_cross_subject_isolated() -> None:
    first = _coverage()
    second = _coverage()
    renamed_packet = _packet("RENAMED_GENERIC")
    renamed = _coverage(renamed_packet, _ownership("RENAMED_GENERIC"))
    first_ids = [row["candidate_id"] for row in first["fundamental_candidates"]]
    renamed_ids = [row["candidate_id"] for row in renamed["fundamental_candidates"]]

    assert first_ids == [row["candidate_id"] for row in second["fundamental_candidates"]]
    assert set(first_ids).isdisjoint(renamed_ids)
    assert [(row["low"], row["high"]) for row in first["fundamental_candidates"]] == [
        (row["low"], row["high"]) for row in renamed["fundamental_candidates"]
    ]


def test_materializer_projects_catalog_and_fails_closed() -> None:
    catalog = _coverage()
    fundamental = catalog["fundamental_candidates"][0]
    tactical = catalog["tactical_candidates"][0]
    resolved = materialize_entry_range(
        ticker="GENERIC_A",
        new_buyer="WAIT",
        catalog=catalog,
        fundamental_choice=fundamental["candidate_id"],
        tactical_choice=tactical["candidate_id"],
        re_evaluate_conditions=("Reassess when business economics change",),
    )
    unresolved = materialize_entry_range(
        ticker="GENERIC_A",
        new_buyer="WAIT",
        catalog=catalog,
        fundamental_choice="UNRESOLVED",
        tactical_choice=tactical["candidate_id"],
    )

    assert resolved["fundamental_entry_band"]["low"] == fundamental["low"]
    assert resolved["valuation_basis_refs"] == fundamental["evidence_refs"]
    assert unresolved["valuation_basis_refs"] == []
    assert unresolved["preferred_entry_low"] is None

    foreign = deepcopy(catalog)
    foreign["fundamental_candidates"][0]["ticker"] = "GENERIC_B"
    with pytest.raises(ValueError, match="cross_ticker_fundamental_candidate"):
        materialize_entry_range(
            ticker="GENERIC_A",
            new_buyer="WAIT",
            catalog=foreign,
            fundamental_choice=fundamental["candidate_id"],
            tactical_choice="UNRESOLVED",
        )
    with pytest.raises(ValueError, match="unknown_or_cross_ticker_fundamental_candidate"):
        materialize_entry_range(
            ticker="GENERIC_A",
            new_buyer="WAIT",
            catalog=catalog,
            fundamental_choice=tactical["candidate_id"],
            tactical_choice="UNRESOLVED",
        )
    with pytest.raises(ValueError, match="non_wait_candidate_injection_forbidden"):
        materialize_entry_range(
            ticker="GENERIC_A",
            new_buyer="ATTRACTIVE",
            catalog=catalog,
            fundamental_choice=fundamental["candidate_id"],
            tactical_choice=None,
        )


def test_field_ownership_and_generic_materialization_controls_are_complete() -> None:
    ownership = field_ownership_audit()
    controls = generic_materialization_control_matrix()

    assert ownership["status"] == "PASS"
    assert ownership["duplicate_field_count"] == 0
    assert controls["status"] == "PASS"
    assert all(controls["checks"].values())


def test_failure_classification_uses_stage_and_structured_provider_error(tmp_path) -> None:
    schema_log = tmp_path / "schema.log"
    schema_log.write_text(
        'ERROR: {"error":{"type":"invalid_request_error",'
        '"code":"invalid_json_schema","message":"schema rejected"},"status":400}',
        encoding="utf-8",
    )
    benign_log = tmp_path / "benign.log"
    benign_log.write_text(
        "Prompt text discusses rate limit, quota, and 429 without a provider envelope.",
        encoding="utf-8",
    )

    assert (
        classify_shadow_failure(RuntimeError("transport failed"), schema_log)
        == "SCHEMA_REJECTED_PRE_INFERENCE"
    )
    assert (
        classify_shadow_failure(
            RuntimeError("shadow_semantic_validation_failed"),
            benign_log,
            execution_stage="SEMANTIC_VALIDATION",
        )
        == "SEMANTIC_VALIDATION_FAILED"
    )
    assert (
        classify_shadow_failure(RuntimeError("local failure"), benign_log)
        == "OTHER_DOCUMENTED_FAILURE"
    )
