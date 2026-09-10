from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import business_delta_alias_balance_confidence_m12z as z


def test_root_causes_and_selected_branch_were_frozen_before_implementation():
    root = z.read(z.ROOT)
    assert root["status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    assert (
        root["delta_alias_resolution"]["root_cause"]
        == "CANONICAL_REFS_COMPARED_TO_ALIAS_KEYED_CONTEXT"
    )
    assert (
        root["positive_bucket"]["primary_root_cause"]
        == "PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED"
    )
    assert (
        root["positive_bucket"]["selected_branch"]
        == "BRANCH_A_BOUNDED_GENERIC_DIRECTIONAL_CLARIFICATION"
    )
    assert root["positive_bucket"]["fic_fin_01_frozen_target"]["buy"] == 6.5


def test_required_artifact_names_are_complete_and_unique():
    assert set(z.SLUGS) == set(range(1, 84))
    assert len(set(z.SLUGS.values())) == 83


def test_alias_and_canonical_business_delta_fixtures_are_fail_closed():
    audit = z.delta_fixture_audit()
    assert audit["status"] == "PASS", audit
    assert audit["false_reject_count"] == 0
    assert audit["false_accept_count"] == 0
    assert len(audit["positive"]) == 4
    assert len(audit["negative"]) == 8


def test_exact_m12y_delta_replay_eliminates_validator_false_rejects():
    replay = z.exact_m12y_delta_replay()
    assert replay["status"] == "PASS", replay
    assert replay["validator_false_reject_count"] == 0
    assert replay["validator_false_accept_count"] == 0
    assert replay["model_semantic_violation_count"] == 0
    assert {row["ticker"]: row["observed"] for row in replay["rows"]} == {
        "FIC-FIN-01": "STRENGTHENED",
        "FIC-FIN-02": "WEAKENED",
        "FIC-FIN-03": "STRENGTHENED",
        "FIC-FIN-04": "UNCHANGED",
    }


def _candidate(ticker: str, ref: str):
    return {
        "ticker": ticker,
        "business_thesis_change": "STRENGTHENED",
        "business_thesis_context": {"evidence_refs": [ref]},
    }


def _context(ticker: str):
    return {
        "ticker": ticker,
        "evidence": [
            {
                "alias": "E01",
                "statement": "Comparable-period operating performance improved.",
            }
        ],
    }


def _catalog(ticker: str, *, canonical_ref: str = "canonical:fix:improved"):
    return {
        "ticker": ticker,
        "entries": [
            {
                "ticker": ticker,
                "alias": "E01",
                "canonical_ref": canonical_ref,
            }
        ],
    }


@pytest.mark.parametrize("selected_ref", ["E01", "canonical:fix:improved"])
def test_business_delta_accepts_selected_alias_or_canonical_identity(selected_ref):
    result = z.business_delta_audit(
        _candidate("FIX", selected_ref),
        _context("FIX"),
        _catalog("FIX"),
    )
    assert result["status"] == "PASS", result
    assert result["linked_evidence"][0]["canonical_ref"] == "canonical:fix:improved"


def test_unknown_reference_fails_closed():
    result = z.business_delta_audit(
        _candidate("FIX", "canonical:fix:missing"),
        _context("FIX"),
        _catalog("FIX"),
    )
    assert result["status"] == "FAIL"
    assert result["alias_resolution_failure_count"] == 1


def test_cross_ticker_catalog_fails_closed():
    result = z.business_delta_audit(
        _candidate("FIX", "E01"),
        _context("FIX"),
        _catalog("OTHER"),
    )
    assert result["status"] == "FAIL"
    assert result["alias_resolution_failure_count"] >= 1


def test_many_to_one_canonical_collision_fails_closed():
    catalog = _catalog("FIX")
    catalog["entries"].append(
        {
            "ticker": "FIX",
            "alias": "E02",
            "canonical_ref": "canonical:fix:improved",
        }
    )
    context = _context("FIX")
    context["evidence"].append(
        {
            "alias": "E02",
            "statement": "Comparable-period operating performance improved.",
        }
    )
    result = z.business_delta_audit(_candidate("FIX", "E01"), context, catalog)
    assert result["status"] == "FAIL"
    assert "INVALID_OR_UNRESOLVED_EVIDENCE_REF:canonical_collision" in result["errors"]


def test_balance_confidence_separation_is_symmetric_and_nonmechanical():
    audit = z.strength_fixture_audit()
    assert audit["status"] == "PASS", audit
    assert audit["fixed_score_rule_count"] == 0
    assert audit["evidence_count_bucket_rule_count"] == 0
    assert audit["confidence_to_balance_mechanical_mapping_count"] == 0
    positives = {row["id"]: row for row in audit["positive"]}
    negatives = {row["id"]: row for row in audit["negative"]}
    assert positives["POS-STAB-01"]["observed_buy"] == 6.5
    assert positives["POS-STAB-02"]["observed_buy"] == 6.0
    assert negatives["NEG-STAB-01"]["observed_buy"] == 3.5
    assert negatives["NEG-STAB-02"]["observed_buy"] == 4.0


def test_targets_thresholds_and_runtime_contract_remain_frozen():
    root = z.read(z.ROOT)
    assert z.TARGET_BUYS == {
        "FIC-FIN-01": 6.5,
        "FIC-FIN-02": 4.5,
        "FIC-FIN-04": 5.0,
        "FIC-FIN-05": 4.0,
    }
    assert z.FIC_FIN_05_DELTA_TARGET == "UNCHANGED"
    assert root["frozen_contracts"]["buy_threshold"] == 6.0
    assert root["frozen_contracts"]["sell_threshold"] == 6.0
    assert root["frozen_contracts"]["increment"] == 0.5
    assert root["frozen_contracts"]["tie_break"].startswith("toward 5.0")
    assert (
        root["runtime"]["model"],
        root["runtime"]["effort"],
        root["runtime"]["timeout_seconds"],
        root["runtime"]["subjects_per_context"],
        root["runtime"]["wrapper_retry_count"],
    ) == ("gpt-5.6-sol", "xhigh", 1800, 4, 0)


def test_only_one_generic_directional_prompt_paragraph_was_added():
    prompt = Path("app/services/directional_balance_service.py").read_text()
    assert prompt.count(z.PROMPT_CLARIFICATION) == 1
    assert z._freeze_paths(
        ("app/services/directional_balance_service.py",),
        expected_changed=("app/services/directional_balance_service.py",),
    )["status"] == "PASS"


def test_fictional_source_contexts_remain_identical_to_m12y():
    _packets, _owned, _catalogs, contexts = z.m12.fictional_inputs("m12z-source-test")
    for ticker in z.m12.TICKERS:
        previous = json.loads(
            (z.M12Y_OUTPUT / "contexts" / f"{ticker}.json").read_text()
        )
        current = contexts[ticker]
        previous["assessment_date"] = current["assessment_date"]
        assert current == previous


def test_canary_rejects_failed_phase_a(tmp_path, monkeypatch):
    monkeypatch.setattr(z, "OUTPUT", tmp_path)
    z.write(tmp_path / "phase-a-receipt.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="m12z_phase_a_not_passed"):
        z.run()


def test_base_hash_has_shallow_checkout_fallback(monkeypatch):
    path = "app/services/directional_balance_service.py"

    def unavailable(_path):
        raise z.subprocess.CalledProcessError(128, ["git", "show"])

    monkeypatch.setattr(z, "_base_bytes", unavailable)
    assert z._base_hash(path) == z.BASE_FILE_SHA256[path]
