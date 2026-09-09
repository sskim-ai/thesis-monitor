from __future__ import annotations

from scripts.bounded_directional_financial_context_stability_m12s import (
    build_fingerprint,
    classify_interpretation_delta,
    classify_subject,
    evidence_roles,
)


def _core(
    *,
    buy: float = 4.0,
    direction: str = "SELL",
    buyer: str = "AVOID",
    holder: str = "REVIEW",
    thesis: str = "WEAKENED",
    cash_in_buy: bool = False,
) -> dict[str, object]:
    cash_ref = "canonical:test:ocf"
    operating_ref = "test:operating"
    buy_refs = [operating_ref]
    if cash_in_buy:
        buy_refs.append(cash_ref)
    return {
        "ticker": "FIC-TEST",
        "overall_direction": direction,
        "directional_balance": {"buy": buy, "sell": 10.0 - buy},
        "hold_lean": "SELL_LEAN" if direction == "HOLD" else "NOT_HOLD",
        "business_thesis_change": thesis,
        "directional_confidence": "MEDIUM",
        "business_thesis_context": {"text": "x", "evidence_refs": [operating_ref]},
        "earnings_estimate_context": {"text": "x", "evidence_refs": [operating_ref]},
        "market_expectation_context": {"text": "x", "evidence_refs": [operating_ref]},
        "valuation_context": {"text": "x", "evidence_refs": ["test:valuation"]},
        "risk_context": {"text": "x", "evidence_refs": [cash_ref]},
        "sector_interpretation": {"text": "x", "evidence_refs": [cash_ref]},
        "dominant_evidence": {"text": "x", "evidence_refs": [cash_ref]},
        "uncertainty_limit": {"text": "x", "evidence_refs": ["test:valuation"]},
        "core_investment_judgment": {"text": "x", "evidence_refs": [cash_ref]},
        "buy_drivers": [{"text": "x", "evidence_refs": buy_refs}],
        "sell_drivers": [
            {
                "text": "x",
                "classification": "STRUCTURAL_RISK",
                "evidence_refs": [] if cash_in_buy else [cash_ref],
            }
        ],
        "unknown_treatments": [
            {
                "summary": "x",
                "evidence_refs": ["test:valuation"],
                "treatment": "CONFIDENCE_LIMIT",
                "directional_negative_basis": [],
            }
        ],
        "business_reevaluation_up": [{"text": "x", "evidence_refs": [operating_ref]}],
        "business_reevaluation_down": [{"text": "x", "evidence_refs": [cash_ref]}],
        "material_directional_anchor_basis": [cash_ref],
        "fundamental_new_buyer": {
            "stance": buyer,
            "summary": "x",
            "confirmation_business_condition": "x",
            "confirmation_business_condition_refs": [cash_ref],
        },
        "fundamental_holder": {
            "stance": holder,
            "summary": "x",
            "business_invalidation_condition": "x",
            "business_invalidation_condition_refs": [cash_ref],
        },
    }


def _metadata() -> dict[str, dict[str, object]]:
    return {
        "canonical:test:ocf": {
            "category": "earnings",
            "label": "operating_cash_flow",
            "financial_metric": "operating_cash_flow",
            "semantic_category": "CASH_CONVERSION",
            "period_type": "YTD",
        },
        "test:operating": {
            "category": "earnings",
            "label": "operating-evidence",
            "financial_metric": None,
            "semantic_category": None,
            "period_type": None,
        },
        "test:valuation": {
            "category": "valuation",
            "label": "valuation-limit",
            "financial_metric": None,
            "semantic_category": None,
            "period_type": None,
        },
    }


def _fingerprint(repetition: int, **kwargs: object) -> dict[str, object]:
    return build_fingerprint(
        repetition=repetition,
        row={"ticker": "FIC-TEST", "core": _core(**kwargs)},
        metadata=_metadata(),
    )


def test_evidence_roles_are_claim_path_specific() -> None:
    roles = evidence_roles(_core())
    assert "material_directional_anchor" in roles["canonical:test:ocf"]
    assert any(
        role.startswith("sell_driver:STRUCTURAL_RISK") for role in roles["canonical:test:ocf"]
    )
    assert "new_buyer_confirmation" in roles["canonical:test:ocf"]
    assert "holder_invalidation" in roles["canonical:test:ocf"]


def test_fingerprint_normalizes_financial_semantics() -> None:
    row = _fingerprint(1)
    assert row["semantic_flags"]["cash_conversion"] == "NEGATIVE"
    assert row["semantic_flags"]["operating_trend"] == "POSITIVE"
    assert row["semantic_flags"]["missing_data_confidence_limit"] is True
    assert row["financial_context_metrics_actually_used"] == ["operating_cash_flow"]


def test_positive_evidence_co_cited_in_risk_does_not_flip_polarity() -> None:
    core = _core(cash_in_buy=True)
    core["sell_drivers"] = [
        {
            "text": "risk context",
            "classification": "STRUCTURAL_RISK",
            "evidence_refs": ["canonical:test:ocf"],
        }
    ]
    row = build_fingerprint(
        repetition=1,
        row={"ticker": "FIC-TEST", "core": core},
        metadata=_metadata(),
    )
    assert row["semantic_flags"]["cash_conversion"] == "POSITIVE"


def test_adjacent_bucket_and_stance_do_not_create_material_interpretation_delta() -> None:
    left = _fingerprint(1)
    right = _fingerprint(2, buy=4.5, direction="HOLD", buyer="WAIT")
    delta = classify_interpretation_delta(left, right)
    assert delta["classification"] == "NO_MATERIAL_INTERPRETATION_DELTA"
    assert delta["adjacent_balance_only"] is True


def test_adjacent_bucket_is_primary_over_secondary_new_buyer_variance() -> None:
    rows = [
        _fingerprint(1),
        _fingerprint(2, buy=4.5, direction="HOLD", buyer="WAIT"),
        _fingerprint(3, buyer="WAIT"),
    ]
    result = classify_subject(rows, "UNSTABLE")
    assert result["primary_root_cause"] == ("ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY")
    assert "NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY" in result["secondary_root_causes"]
    assert result["material_interpretation_delta"] == ("NO_MATERIAL_INTERPRETATION_DELTA")


def test_holder_variance_is_classified_separately() -> None:
    rows = [
        _fingerprint(1, holder="REDUCE"),
        _fingerprint(2, holder="REVIEW"),
        _fingerprint(3, holder="REDUCE"),
    ]
    result = classify_subject(rows, "BOUNDARY_UNCERTAINTY")
    assert result["primary_root_cause"] == "HOLDER_STANCE_CALIBRATION_AMBIGUITY"


def test_stable_control_keeps_variance_as_advisory() -> None:
    rows = [
        _fingerprint(1),
        _fingerprint(2, thesis="UNRESOLVED"),
        _fingerprint(3, thesis="STRENGTHENED"),
    ]
    result = classify_subject(rows, "STABLE")
    assert result["primary_root_cause"] is None
    assert result["stability_root_cause_scope"] == "STABLE_CONTROL_ADVISORY_ONLY"
    assert "FORMAL_CLASSIFIER_SENSITIVITY" in result["secondary_root_causes"]


def test_economic_polarity_change_is_material() -> None:
    left = _fingerprint(1)
    right = _fingerprint(2, cash_in_buy=True, buy=6.0, direction="BUY", buyer="ATTRACTIVE")
    delta = classify_interpretation_delta(left, right)
    assert delta["classification"] == "MATERIAL_INTERPRETATION_DELTA"
    assert "ECONOMIC_POLARITY_REVERSED:cash_conversion" in delta["reasons"]


def test_mixed_to_positive_is_emphasis_not_polarity_reversal() -> None:
    left = _fingerprint(1, cash_in_buy=True)
    left["semantic_flags"]["operating_trend"] = "MIXED"
    right = _fingerprint(2, cash_in_buy=True)
    delta = classify_interpretation_delta(left, right)
    assert delta["classification"] == "MINOR_EMPHASIS_DELTA"
    assert delta["material_semantic_change"] is False
