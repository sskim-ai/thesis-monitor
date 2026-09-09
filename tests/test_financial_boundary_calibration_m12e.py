from __future__ import annotations

import json

import pytest

from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
    directional_balance_ordinal_calibration_prompt,
)
from scripts import financial_boundary_calibration_m12e as audit
from scripts import directional_financial_context_m12 as m12
from scripts import financial_exclusion_expectation_m12u as m12u


def test_calibration_preserves_nonprompt_code_and_other_owners():
    # M12U adds one expectation paragraph and bounded exclusion predicates only.
    result = m12u.scope_audit()
    assert result["status"] == "PASS", result
    assert result["prompt_change_count"] == 1
    assert result["unexpected_file_changes"] == []


def test_all_four_generic_clarifications_are_model_facing():
    prompt = directional_balance_ordinal_calibration_prompt()
    assert "Independent corroboration adds a distinct economic fact" in prompt
    assert "not the number of metrics or evidence references" in prompt
    assert "without becoming negative evidence" in prompt
    assert "by itself it does not support a positive 5.5 lean" in prompt
    assert "the existing tie-break selects 6.0" in prompt
    assert "equally to BUY and SELL strength" in prompt
    assert "not an automatic cap" in prompt
    assert "FIC-FIN" not in prompt
    assert "CAL-BAL" not in prompt
    assert "LOW confidence does not mechanically require HOLD" in prompt


@pytest.mark.parametrize(
    "buy,expected",
    [(6, "BUY"), (5.5, "HOLD"), (5, "HOLD"), (4.5, "HOLD"), (4, "SELL"), (3.5, "SELL")],
)
def test_existing_threshold_and_symmetric_decision(buy, expected):
    assert decision_from_directional_balance(DirectionalBalance(buy=buy, sell=10 - buy)) == expected


def test_existing_half_step_precision():
    with pytest.raises(ValueError, match="false_precision"):
        DirectionalBalance(buy=5.75, sell=4.25)


@pytest.mark.parametrize(
    "buckets,expected",
    [([6, 6.5], 6), ([4, 4.5], 4.5), ([5, 5.5], 5), ([4.5, 5], 5), ([3.5, 4], 4)],
)
def test_explicit_adjacent_fixture_tie_toward_center(buckets, expected):
    assert audit.tie_fixture(buckets) == expected
    assert audit.tie_fixture(list(reversed(buckets))) == expected


@pytest.mark.parametrize("buckets", [[], [6, 6], [5, 6], [4, 5, 6], [5.25], [11]])
def test_fixture_audit_does_not_infer_evidence_buckets(buckets):
    with pytest.raises(ValueError):
        audit.tie_fixture(buckets)


def test_documented_contract_fixtures_not_a_ticker_scorecard():
    fixtures = audit.fixture_audit()
    assert fixtures["status"] == "PASS"
    assert len(fixtures["rows"]) == 8
    for row in fixtures["rows"]:
        assert "ticker" not in row
        assert "weight" not in row
        assert "score" not in row
    assert {r["id"] for r in fixtures["rows"]} >= {f"CAL-BAL-0{i}" for i in range(1, 6)}


def test_runtime_header_identity_is_not_inferred_from_requested_target():
    assert audit.observed_runtime(
        "OpenAI Codex\n--------\nmodel: gpt-6-astra\nreasoning effort: xhigh\n--------\n"
    ) == {"model": "gpt-6-astra", "effort": "xhigh"}
    assert audit.observed_runtime("missing header") == {"model": "", "effort": ""}
    assert audit.observed_runtime(
        "--------\nmodel: gpt-5.6-sol\nreasoning effort: high\n--------"
    ) != {"model": audit.MODEL, "effort": audit.EFFORT}


def test_process_local_runtime_target_does_not_change_historical_default():
    previous = m12.MODEL, m12.EFFORT
    try:
        audit.configure_runtime()
        assert (m12.MODEL, m12.EFFORT, m12.TIMEOUT_SECONDS) == ("gpt-6-astra", "xhigh", 1800)
    finally:
        m12.MODEL, m12.EFFORT = previous


def test_all_required_reports_are_distinct():
    assert len(audit.SLUGS) == len(set(audit.SLUGS)) == 59


def test_historical_transport_prompt_is_exact_prior_text():
    prior = audit.Path("fixtures/pre_m12e_ordinal_calibration_prompt.txt").read_text().strip()
    assert prior == audit.prompt_value(audit.base_bytes(audit.SERVICE).decode())


def test_runtime_only_accepts_frozen_phase_a_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    (tmp_path / "phase-a-receipt.json").write_text(json.dumps({"status": "FAIL"}))
    with pytest.raises(ValueError, match="phase_a_not_passed"):
        audit.run()
