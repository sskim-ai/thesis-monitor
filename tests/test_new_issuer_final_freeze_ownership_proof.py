from __future__ import annotations

from datetime import UTC, datetime

from scripts import new_issuer_final_freeze_ownership_proof as proof


def test_reviewed_cohort_and_market_groups_are_frozen() -> None:
    assert len(proof.COHORT) == 16
    assert proof.COHORT[:4] == ("NVMI", "SKYH", "WKSP", "EROC")
    assert all(proof.MARKET_BY_TICKER[ticker] == "us" for ticker in proof.COHORT[:4])
    assert all(proof.MARKET_BY_TICKER[ticker] == "kr" for ticker in proof.COHORT[4:])
    assert tuple(len(group) for group in proof.CONTEXT_GROUPS) == (4, 4, 4, 4)


def test_source_and_runtime_generation_identities_are_distinct() -> None:
    source, runtime = proof.source_generation_ids(
        "implementation", datetime(2026, 9, 7, 5, 30, tzinfo=UTC)
    )

    assert source != runtime
    assert source.startswith("20260907-new-issuer-source-")
    assert runtime.startswith("20260907-new-issuer-proof-")


def test_precommitted_model_call_budget_is_exact() -> None:
    assert proof.EXPECTED_INVOCATIONS_PER_RUN == 8
    assert proof.EXPECTED_TOTAL_INVOCATIONS == 32


def test_review_manifest_hash_excludes_only_its_hash_field() -> None:
    document = {"contract": "fixture", "value": 1}
    expected = proof.canonical_sha256(document)
    document["source_manifest_sha256"] = expected

    assert proof.canonical_document_hash(document, "source_manifest_sha256") == expected


def test_existing_route_policy_does_not_claim_verified_free() -> None:
    policy, _ = proof._policy(proof.Path.cwd().resolve())

    assert policy["cost_policy"]["existing_configured_data_routes_only"] is True
    assert policy["cost_policy"]["new_paid_data_dependency"] == 0
    assert policy["cost_policy"]["all_routes_verified_free_claimed"] == 0
    assert policy["stop_rules"]["hotfix_after_real_output"] == 0
