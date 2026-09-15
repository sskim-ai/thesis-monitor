from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.services.coldstart_fundamental_enrichment_service import AnalysisFramework
from scripts import new_fresh_unseen_real_proof_m12bo as proof


def test_candidate_slots_are_fixed_and_sector_balanced() -> None:
    assert len(proof.CANDIDATE_SLOTS) == 12
    assert {market for market, _, _ in proof.CANDIDATE_SLOTS} == {"kr", "us"}

    pairs = [(market, bucket) for market, bucket, _ in proof.CANDIDATE_SLOTS]
    assert len(pairs) == len(set(pairs)) == 12
    assert all(len(candidates) >= 4 for _, _, candidates in proof.CANDIDATE_SLOTS)

    all_candidates = [ticker for _, _, candidates in proof.CANDIDATE_SLOTS for ticker in candidates]
    assert len(all_candidates) == len(set(all_candidates))
    assert all(ticker not in proof.HISTORICAL_FRESH_NEGATIVES for ticker in all_candidates)


def test_seen_registry_recurses_nested_real_subject_records(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    prior = reports / "fresh-holdout" / "nested.json"
    prior.parent.mkdir(parents=True)
    prior.write_text(
        json.dumps(
            {
                "generation_id": "prior-generation",
                "payload": {
                    "rows": [
                        {"ticker": "ABC"},
                        {"subject": {"issuer_ticker": "DEF"}},
                        {"symbol": "SYN_CASE"},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    active_source = tmp_path / "active.sqlite3"
    registry = proof.build_seen_registry(
        reports,
        [{"ticker": "XYZ"}],
        active_source=active_source,
        task_report_dir=reports / "current-task",
    )

    rows = {row["ticker"]: row for row in registry["rows"]}
    assert {"ABC", "DEF", "XYZ"} <= rows.keys()
    assert "SYN_CASE" not in rows
    assert rows["XYZ"]["records"][0]["source_artifact"] == str(active_source)
    assert registry["fictional_subject_count"] == 0
    assert registry["status"] == "PASS"


def test_seen_registry_does_not_exclude_premodel_only_subject_mentions(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "reports"
    stopped = reports / "fresh-premark-stop"
    stopped.mkdir(parents=True)
    (stopped / "candidate-manifest.json").write_text(
        json.dumps({"candidate_tickers": ["BAC", "000270"]}),
        encoding="utf-8",
    )
    (stopped / "program-completion.json").write_text(
        json.dumps(
            {
                "status": "STOP_BEFORE_MODEL",
                "top_level_fresh_proof_result": "FRESH_UNSEEN_PREMODEL_CONTRACT_GAP",
                "model_calls_started": 0,
                "fresh_selected_tickers": ["BAC", "000270"],
            }
        ),
        encoding="utf-8",
    )
    modeled = reports / "fresh-modeled"
    modeled.mkdir(parents=True)
    (modeled / "model-artifacts.json").write_text(
        json.dumps({"generation_id": "modeled", "ticker": "MSFT"}),
        encoding="utf-8",
    )

    registry = proof.build_seen_registry(
        reports,
        [],
        active_source=tmp_path / "active.sqlite3",
        task_report_dir=reports / "current-task",
    )

    tickers = {row["ticker"] for row in registry["rows"]}
    assert "MSFT" in tickers
    assert "BAC" not in tickers
    assert "000270" not in tickers
    assert registry["premodel_only_report_roots"] == ["fresh-premark-stop"]
    assert registry["premodel_only_subject_mentions_ignored"] == ["000270", "BAC"]
    assert registry["premodel_only_false_exclusion_count"] == 0


def test_kr_financial_projection_gap_is_classified_boundedly() -> None:
    slots = [
        {
            "slot": 1,
            "market": "kr",
            "sector_bucket": "financial",
            "status": "UNFILLED",
        }
    ]
    candidates = [
        {
            "slot": 1,
            "ticker": "000810",
            "provider_attempted": True,
            "status": "OBJECTIVE_SOURCE_OR_PACKET_NOT_READY",
            "missing_required_families": ["REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT"],
        },
        {
            "slot": 1,
            "ticker": "032830",
            "provider_attempted": True,
            "status": "OBJECTIVE_SOURCE_OR_PACKET_NOT_READY",
            "missing_required_families": ["REGULATORY_CAPITAL_CURRENTORSECTOR_OPERATING_CURRENT"],
        },
    ]

    failures = proof.diagnose_unfilled_slots(slots, candidates)

    assert failures[0]["failure"] == ("KR_FINANCIAL_SPECIALIZED_EVIDENCE_PROJECTION_GAP")
    assert proof.bounded_input_repair_scope(failures) == (
        "KR_FINANCIAL_REGULATORY_OR_SECTOR_OPERATING_EVIDENCE_PROJECTION"
    )


def test_nonfinancial_unfilled_slot_uses_generic_failure() -> None:
    slots = [
        {
            "slot": 4,
            "market": "us",
            "sector_bucket": "cyclical_industrial",
            "status": "UNFILLED",
        }
    ]
    candidates = [
        {
            "slot": 4,
            "ticker": "GE",
            "provider_attempted": True,
            "status": "PROVIDER_OR_PACKET_EXCEPTION",
            "missing_required_families": [],
        }
    ]

    failures = proof.diagnose_unfilled_slots(slots, candidates)

    assert failures[0]["failure"] == "PROVIDER_READY_UNSEEN_SLOT_UNFILLED"
    assert proof.bounded_input_repair_scope(failures) == (
        "UNFILLED_SECTOR_SLOT_PROVIDER_OR_IDENTITY_READINESS"
    )


def test_selection_rank_is_stable_and_salted() -> None:
    assert proof.selection_rank("BAC") == proof.selection_rank("BAC")
    assert proof.selection_rank("BAC") != proof.selection_rank("GS")
    assert len(proof.selection_rank("BAC")) == 64


def test_asset_heavy_framework_owns_primary_cyclical_bucket() -> None:
    enrichment = SimpleNamespace(
        analysis_framework=AnalysisFramework.ASSET_HEAVY_CYCLICAL,
        official_profile={
            "sector": "Consumer Discretionary",
            "industry": "Automotive",
            "taxonomy_key": "automotive",
        },
    )
    identity = {"sector": "자동차", "industry": "자동차 제조업"}

    assert proof.profile_sector_bucket(identity, enrichment) == ("cyclical_industrial")
