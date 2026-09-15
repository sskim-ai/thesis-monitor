from __future__ import annotations

from scripts import bounded_us_source_coverage_remediation_holdout_resume as resume


def test_resume_contract_keeps_frozen_model_transport_and_proof_shape() -> None:
    assert resume.MODEL == "gpt-5.6-sol"
    assert resume.EFFORT == "xhigh"
    assert resume.TIMEOUT_SECONDS == 1800
    assert resume.TIMEOUT_OWNER_COUNT == 1
    assert resume.BATCH_SEMANTICS == "MODEL_CONTEXT_COUPLED"
    assert resume.CONTEXT_SIZE == 4
    assert (resume.TARGET_US, resume.TARGET_KR, resume.TARGET_TOTAL) == (4, 12, 16)
    assert len(resume.PROOF_NAMES) == 65
    assert resume.PROOF_NAMES[12] == "13-expanded-us-reserve-policy"
    assert resume.PROOF_NAMES[64] == "65-program-completion"


def test_mark_first_sufficient_preserves_order_and_deduplicates_issuer() -> None:
    rows = [
        {
            "ticker": "A",
            "issuer_key": "issuer-a",
            "eligible_for_final_holdout": True,
            "selected": False,
        },
        {
            "ticker": "A2",
            "issuer_key": "issuer-a",
            "eligible_for_final_holdout": True,
            "selected": False,
        },
        {
            "ticker": "B",
            "issuer_key": "issuer-b",
            "eligible_for_final_holdout": False,
            "selected": False,
        },
        {
            "ticker": "C",
            "issuer_key": "issuer-c",
            "eligible_for_final_holdout": True,
            "selected": False,
        },
    ]

    selected = resume.mark_first_sufficient(rows, 2)

    assert selected == ["A", "C"]
    assert rows[1]["duplicate_issuer"] is True
    assert rows[2]["selected"] is False


def test_expanded_reserve_policy_is_frozen_before_outcomes(monkeypatch) -> None:
    ranked = [
        {"ticker": ticker, "market": "us"}
        for ticker in (*resume.ORIGINAL_US, "R1", "R2")
    ]
    monkeypatch.setattr(resume.prior, "exposure_tickers", lambda registry: set())
    monkeypatch.setattr(
        resume.prior,
        "ranked_market_candidates",
        lambda rows, market: ranked,
    )
    universe = [*ranked, {"ticker": "000001", "market": "kr"}]

    policy, order, exclusions = resume.expanded_reserve_policy(
        universe=universe,
        registry={"rows": []},
    )

    assert order == ["R1", "R2"]
    assert policy["reserve_extension_count"] == 2
    assert policy["selection_uses_source_outcome"] == 0
    assert policy["selection_uses_model_output"] == 0
    assert set(resume.ORIGINAL_US).isdisjoint(order)
    assert isinstance(exclusions, set)


def test_configure_prior_runner_uses_resume_proof_numbering() -> None:
    original_names = resume.prior.PROOF_NAMES
    original_numbers = resume.prior.RUN_PROOFS
    try:
        resume.configure_prior_runner()
        assert resume.prior.PROOF_NAMES is resume.PROOF_NAMES
        assert resume.prior.RUN_PROOFS["first"] == (32, 33, 34, 35, 36, 37)
        assert resume.prior.RUN_PROOFS["c"] == (50, 51, 52, 53, 54, 55)
    finally:
        resume.prior.PROOF_NAMES = original_names
        resume.prior.RUN_PROOFS = original_numbers
