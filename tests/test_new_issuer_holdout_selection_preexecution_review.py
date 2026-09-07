from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.reference_universe_audit_service import canonical_market_mix
from scripts import new_issuer_holdout_selection_preexecution_review as review


def _membership(
    ticker: str,
    *,
    market: str = "us",
    issuer: str | None = None,
) -> dict[str, object]:
    return {
        "display_symbol": ticker,
        "market": market,
        "canonical_issuer_key": issuer or f"{market}:issuer:{ticker.lower()}",
        "canonical_security_id": f"{market}:security:{ticker.lower()}",
        "eligibility_decision": "ELIGIBLE_SUPPORTED_SECURITY",
    }


def _diagnostic(ticker: str, *, sufficient: bool) -> dict[str, object]:
    return {
        "rank": 1,
        "ticker": ticker,
        "fundamental_source_sufficient": sufficient,
        "failure_reasons": [] if sufficient else ["source_absent"],
        "diagnostic_packet_sha256": f"diagnostic-{ticker}",
        "full_packet_sha256": f"full-{ticker}",
        "price_timing_input_readiness": "READY",
    }


def test_known_source_failure_is_not_relabelled_as_untested() -> None:
    tickers = ("FAIL", "PASS", "UNTESTED")
    ledger, selected = review.build_candidate_ledger(
        market="us",
        ordered_tickers=tickers,
        membership_rows=[_membership(ticker) for ticker in tickers],
        diagnostic_rows=[
            _diagnostic("FAIL", sufficient=False),
            _diagnostic("PASS", sufficient=True),
        ],
        excluded_issuer_keys=set(),
        target=1,
        diagnostic_snapshot="frozen-snapshot",
    )

    by_ticker = {row["ticker"]: row for row in ledger}
    assert selected == ("PASS",)
    assert by_ticker["FAIL"]["source_status"] == "FUNDAMENTAL_SOURCE_FAILED"
    assert by_ticker["FAIL"]["reserve_role"] == "NONPRIMARY_KNOWN_SOURCE_FAILURE"
    assert (
        by_ticker["UNTESTED"]["source_status"]
        == "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED"
    )


def test_global_and_budget_scoped_untested_counts_remain_distinct() -> None:
    rows = [
        {
            "source_status": "FUNDAMENTAL_SOURCE_SUFFICIENT",
            "reserve_role": "PROPOSED_PRIMARY",
        },
        {
            "source_status": "FUNDAMENTAL_SOURCE_FAILED",
            "reserve_role": "NONPRIMARY_KNOWN_SOURCE_FAILURE",
        },
        {
            "source_status": "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED",
            "reserve_role": "IDENTITY_SUPPORTED_RESERVE_UNTESTED",
        },
        {
            "source_status": "IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED",
            "reserve_role": "IDENTITY_SUPPORTED_RESERVE_UNTESTED",
        },
    ]

    summary = review.summarize_us_ledger(rows, budget_scope=3)

    assert summary["untested_global_count"] == 2
    assert summary["untested_within_budget_count"] == 1
    assert summary["known_source_fail_count"] == 1


def test_raw_file_and_canonical_json_hashes_are_distinct() -> None:
    document = {"b": 2, "a": 1}
    raw = json.dumps(document, indent=2).encode()

    assert review.bytes_sha256(raw) != review.canonical_sha256(document)


def test_excluded_issuer_blocks_an_alternate_share_class() -> None:
    shared_issuer = "us:issuer:shared"

    with pytest.raises(ValueError, match="excluded_issuer_in_candidate_order"):
        review.build_candidate_ledger(
            market="us",
            ordered_tickers=("SHARED.B",),
            membership_rows=[
                _membership("SHARED.B", issuer=shared_issuer),
            ],
            diagnostic_rows=[_diagnostic("SHARED.B", sufficient=True)],
            excluded_issuer_keys={shared_issuer},
            target=1,
            diagnostic_snapshot="frozen-snapshot",
        )


def test_nonnumeric_kr_identity_preserves_explicit_market() -> None:
    ticker = "KR-ALPHA"
    ledger, selected = review.build_candidate_ledger(
        market="kr",
        ordered_tickers=(ticker,),
        membership_rows=[_membership(ticker, market="kr")],
        diagnostic_rows=[_diagnostic(ticker, sufficient=True)],
        excluded_issuer_keys=set(),
        target=1,
        diagnostic_snapshot="frozen-snapshot",
    )

    assert selected == (ticker,)
    assert ledger[0]["market"] == "kr"
    assert canonical_market_mix((ticker,), {ticker: "kr"}) == {"us": 0, "kr": 1}


def test_missing_or_conflicting_market_fails_closed() -> None:
    with pytest.raises(ValueError, match="canonical_market_metadata_missing"):
        canonical_market_mix(("SUBJECT",), {})
    with pytest.raises(ValueError, match="canonical_market_metadata_conflict"):
        canonical_market_mix(
            ("SUBJECT",),
            {"SUBJECT": "kr"},
            corroborating_market_by_subject={"SUBJECT": "us"},
        )


def test_review_manifest_is_nonexecutable_and_hash_bound() -> None:
    selected = [
        {
            "ticker": ticker,
            "market": market,
            "canonical_issuer_key": f"{market}:issuer:{ticker.lower()}",
            "canonical_security_id": f"{market}:security:{ticker.lower()}",
        }
        for market, tickers in (
            ("us", ("U1", "U2", "U3", "U4")),
            (
                "kr",
                (
                    "K1",
                    "K2",
                    "K3",
                    "K4",
                    "K5",
                    "K6",
                    "K7",
                    "K8",
                    "K9",
                    "K10",
                    "K11",
                    "K12",
                ),
            ),
        )
        for ticker in tickers
    ]
    source_reviews = {
        str(row["ticker"]): {
            "source_period_rows": [{"period": "2026-FY"}],
            "full_packet_raw_sha256": f"raw-{row['ticker']}",
            "full_packet_canonical_sha256": f"canonical-{row['ticker']}",
            "mandatory_unknowns": [],
        }
        for row in selected
    }

    manifest = review.build_review_manifest(
        implementation_commit="implementation",
        policy_hash="policy",
        input_zip_sha256="input",
        selected_rows=selected,
        source_reviews=source_reviews,
    )

    review.validate_review_manifest(manifest)
    assert manifest["artifact_role"] == "SELECTION_REVIEW_MANIFEST"
    assert manifest["executable"] is False
    assert manifest["model_execution_authorized"] is False
    assert manifest["proof_source_lock"] is None
    assert manifest["execution_authorized"] is False


def test_review_pass_cannot_be_mutated_into_real_adapter_authorization() -> None:
    manifest = {
        "artifact_role": "SELECTION_REVIEW_MANIFEST",
        "executable": True,
        "model_execution_authorized": True,
        "proof_source_lock": "forbidden",
    }
    unhashed = dict(manifest)
    manifest["source_manifest_sha256"] = review.canonical_sha256(unhashed)

    with pytest.raises(ValueError, match="review_manifest_invalid"):
        review.validate_review_manifest(manifest)


def test_policy_keeps_all_request_and_retry_budgets_at_zero() -> None:
    path = Path(review.POLICY_PATH)
    policy = json.loads(path.read_text(encoding="utf-8"))
    budgets = policy["request_budgets"]

    assert policy["status"] == "FROZEN_PRE_REVIEW_DIAGNOSTICS"
    assert budgets["us_additional_route_checks"] == 0
    assert budgets["us_full_fundamental_evaluations"] == 0
    assert budgets["kr_full_fundamental_evaluations"] == 0
    assert budgets["reference_refresh_by_feed"] == 0
    assert budgets["retry_count"] == 0


def test_model_free_adapter_starts_with_zero_real_exposure(tmp_path: Path) -> None:
    adapter = review.RealInputModelFreeAdapter(
        continuation_generation="review-only",
        receipt_root=tmp_path / "receipts",
        owned={},
        core_aliases={},
        timing_aliases={},
    )

    assert review.MODEL_FREE_ARTIFACT_MODE == "MODEL_FREE_REAL_INPUT_REHEARSAL"
    assert adapter.model_call_count == 0
    assert adapter.simulated_invocation_count == 0


def test_real_input_fixture_uses_only_owned_evidence_refs() -> None:
    owned = review.identity_repair.synthetic.fictional_owned(
        "SYNTHETIC_US_REVIEW", market="us"
    )

    core = review.real_input_fixture_core(owned)
    timing = review.real_input_fixture_timing(owned, core)

    core_refs = set(review.runner.frozen._refs(core.model_dump(mode="json")))
    timing_refs = set(review.runner.frozen._refs(timing.model_dump(mode="json")))
    assert core_refs <= owned.core_refs
    assert timing_refs <= owned.timing_refs
