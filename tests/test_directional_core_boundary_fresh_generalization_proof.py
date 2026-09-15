from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts import directional_core_boundary_fresh_generalization_proof as proof


def _prior_registry() -> dict[str, object]:
    rows = [
        {
            "canonical_issuer_key": f"prior:{index:03d}",
            "security_aliases": [f"P{index:03d}"],
        }
        for index in range(proof.PREVIOUS_EXCLUSION_COUNT)
    ]
    return {
        "rows": rows,
        "all_excluded_issuer_keys": [row["canonical_issuer_key"] for row in rows],
    }


def _identities() -> dict[str, object]:
    current = []
    for index, ticker in enumerate(proof.RETIRED_COHORT):
        market = "us" if index < proof.TARGET_US else "kr"
        current.append(
            {
                "canonical_issuer_key": f"current:{ticker}",
                "display_symbol": ticker,
                "market": market,
                "provider_aliases": [ticker],
            }
        )
    fresh_us = [
        {
            "canonical_issuer_key": f"fresh:us:{index}",
            "display_symbol": f"US{index}",
            "market": "us",
        }
        for index in range(proof.TARGET_US)
    ]
    fresh_kr = [
        {
            "canonical_issuer_key": f"fresh:kr:{index}",
            "display_symbol": f"KR{index}",
            "market": "kr",
        }
        for index in range(proof.TARGET_KR)
    ]
    return {
        "us": [row for row in current if row["market"] == "us"] + fresh_us,
        "kr": [row for row in current if row["market"] == "kr"] + fresh_kr,
    }


def test_registry_retires_all_fully_exposed_issuers() -> None:
    registry = proof.expand_exclusion_registry(
        _prior_registry(),
        _identities(),
        exposed_generation_id="previous-generation",
    )

    assert registry["prior_registry_count"] == 133
    assert registry["appended_exposed_issuer_count"] == 16
    assert registry["reconciled_registry_count"] == 149
    appended = [
        row
        for row in registry["rows"]
        if row["canonical_issuer_key"].startswith("current:")
    ]
    assert len(appended) == 16
    assert all(row["actual_output_exposure"] is True for row in appended)
    assert all(row["actual_real_model_spawn"] is True for row in appended)
    assert all(len(row["lineage"]) == 8 for row in appended)


def test_candidate_filter_removes_retired_cohort_without_reordering() -> None:
    identities = _identities()
    registry = proof.expand_exclusion_registry(
        _prior_registry(),
        identities,
        exposed_generation_id="previous-generation",
    )

    filtered = proof.filter_candidate_identities(identities, registry)

    assert [row["display_symbol"] for row in filtered["us"]] == [
        f"US{index}" for index in range(proof.TARGET_US)
    ]
    assert [row["display_symbol"] for row in filtered["kr"]] == [
        f"KR{index}" for index in range(proof.TARGET_KR)
    ]


def test_source_and_runtime_generation_ids_are_new_and_separate() -> None:
    source, runtime = proof.source_generation_ids(
        "implementation-commit", datetime(2026, 9, 8, 6, 30, tzinfo=UTC)
    )

    assert source.startswith("20260908-directional-calibration-source-20260908T063000Z-")
    assert runtime.startswith("20260908-directional-calibration-proof-20260908T063000Z-")
    assert source != runtime


def test_calibration_freeze_accepts_stopped_post_freeze_state(
    monkeypatch,
) -> None:
    state = {
        "state": "FRESH_REAL_PROOF_STOPPED",
        "fictional_model_invocation_count": 6,
        "fictional_calibration_unstable_count": 0,
        "calibration_freeze_seal_sha256": proof.CALIBRATION_FREEZE_SHA256,
        "calibration_contract_sha256": proof.CALIBRATION_CONTRACT_SHA256,
        "calibration_architecture_hashes": {"owner": "frozen"},
    }
    seal = {"seal": "frozen"}
    monkeypatch.setattr(proof, "read_json", lambda path: state if "artifacts" in str(path) else seal)
    monkeypatch.setattr(proof, "canonical_sha256", lambda value: proof.CALIBRATION_FREEZE_SHA256)
    monkeypatch.setattr(
        proof.calibration,
        "calibration_architecture_hashes",
        lambda repo_root: {"owner": "frozen"},
    )

    result = proof.assert_calibration_frozen(Path("/repo"))

    assert result["status"] == "PASS"
    assert result["observed_program_state"] == "FRESH_REAL_PROOF_STOPPED"
