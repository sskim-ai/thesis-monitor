from __future__ import annotations

import json

import pytest

from scripts import financial_exclusion_leverage_m12f as audit


def test_complete_scope_freeze_preserves_every_unapproved_owner():
    result = audit.freeze_audit()
    assert result["status"] == "PASS", result
    assert result["unchanged_python_count"] == 654
    assert result["prompt_change_count"] == 0
    assert result["production_validator_fictional_branch_count"] == 0


def test_all_required_reports_are_unique():
    assert set(audit.SLUGS) == set(range(1, 72))
    assert len(set(audit.SLUGS.values())) == 71


def test_root_review_uses_current_generic_contract_not_sol_labels():
    root = audit.read(audit.ROOT)
    assert root["selected_branch"] == "A"
    leverage = root["leverage"]
    assert leverage["root_cause"] == "ASTRA_OUTPUT_CONSISTENT_WITH_CURRENT_5_5_CONTRACT"
    assert leverage["prompt_change"] == 0
    assert leverage["case_data_change"] == 0
    assert (
        leverage["case_change_semantics"]
        == "CURRENT_ABSOLUTE_CONDITION_WITHOUT_EXPLICIT_BASELINE_DETERIORATION"
    )
    fixtures = {r["id"]: r for r in root["leverage_fixtures"]}
    assert set(fixtures) == {"LEV-01", "LEV-02", "LEV-03", "LEV-04", "LEV-05", "LEV-POSITIVE"}
    first = fixtures["LEV-01"]
    assert (
        audit.previous.tie_fixture(first["supportable_buy_buckets"]) == first["selected_buy"] == 4.5
    )
    assert all("weight" not in r and "ticker" not in r for r in fixtures.values())
    assert "NO_TOTAL_OR_NET_DEBT_CONCLUSION" == fixtures["LEV-04"]["expected"]
    assert "INDUSTRIAL_LEVERAGE_NOT_APPLICABLE" == fixtures["LEV-05"]["expected"]


def test_full_offline_replay_closes_exclusion_without_rewriting_history():
    replay = audit.offline_replay()
    assert replay["status"] == "PASS"
    assert len(replay["rows"]) == 8
    old = {r["ticker"]: r for r in audit.preserved_rows()}
    assert old["FIC-FIN-08"]["status"] == "FAIL"
    assert old["FIC-FIN-05"]["core"]["directional_balance"] == {"buy": 4.5, "sell": 5.5}


def test_validator_fixture_false_reject_and_false_accept_zero():
    result = audit.exclusion_fixture_audit()
    assert result["status"] == "PASS"
    assert len(result["rows"]) == 32


def test_canary_rejects_a_failed_phase_a(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    audit.write(tmp_path / "phase-a-receipt.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="phase_a_not_passed"):
        audit.run()


def test_old_generation_cannot_be_resumed(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    audit.write(
        tmp_path / "phase-a-receipt.json",
        {
            "status": "PASS",
            "code_file_sha256": {},
            "config_file_sha256": {},
            "model_inputs": {"contexts": []},
        },
    )
    audit.write(tmp_path / "canary-stop.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="whole_generation_retry_forbidden"):
        audit.run()


def test_code_or_config_change_is_rejected_before_spawn(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    config = tmp_path / "fixture.json"
    config.write_text("{}")
    audit.write(
        tmp_path / "phase-a-receipt.json",
        {
            "status": "PASS",
            "code_file_sha256": {},
            "config_file_sha256": {str(config): "wrong"},
        },
    )
    with pytest.raises(ValueError, match="code_or_config_changed_after_freeze"):
        audit.run()


def test_frozen_input_api_retains_case_contexts(tmp_path):
    original = audit.m12.MODEL, audit.m12.EFFORT
    try:
        audit.configure_runtime()
        _, _, catalogs, contexts = audit.m12.fictional_inputs("m12f-input-api-test")
        inputs = audit.m12._write_frozen_model_inputs(
            generation_id="m12f-input-api-test",
            output_root=tmp_path,
            catalogs=catalogs,
            contexts=contexts,
        )
        assert len(inputs["contexts"]) == 2
        assert (audit.m12.MODEL, audit.m12.EFFORT) == ("gpt-6-astra", "xhigh")
        for row in inputs["contexts"]:
            prompt = audit.Path(row["prompt_path"]).read_text()
            raw_contexts = json.loads(prompt.split("DIRECTIONAL_CORE_CONTEXT:\n", 1)[1])
            assert raw_contexts == [contexts[t] for t in row["tickers"]]
    finally:
        audit.m12.MODEL, audit.m12.EFFORT = original


def test_wrong_fictional_bucket_is_not_accepted_for_stability():
    row = {"ticker": "FIC-FIN-05", "core": {"directional_balance": {"buy": 4, "sell": 6}}}
    assert audit._calibration_audit(row)["status"] == "FAIL"
    row["core"]["directional_balance"] = {"buy": 4.5, "sell": 5.5}
    assert audit._calibration_audit(row)["status"] == "PASS"


def test_artifact_scan_only_exempts_exact_empty_historical_marker_literals(tmp_path):
    safe = audit.artifact_secret_scan(
        [
            (audit.CASE_SERVICE, audit.Path(audit.CASE_SERVICE)),
            (str(audit.BASELINE), audit.BASELINE),
        ]
    )
    assert safe["failures"] == []
    assert safe["known_empty_scanner_marker_literals"] == 12
    leaked = tmp_path / "script.py"
    leaked.write_text(
        audit.Path(audit.CASE_SERVICE).read_text() + "\n# OPENAI_API_" + "KEY=fixture-secret\n"
    )
    result = audit.artifact_secret_scan([(audit.CASE_SERVICE, leaked)])
    assert result["failures"] == [audit.CASE_SERVICE]


def test_scan_still_rejects_secret_markers_in_model_output(tmp_path):
    output = tmp_path / "output.json"
    output.write_text('{"access_' + 'token":"fixture-secret"}')
    assert audit.artifact_secret_scan([("output.json", output)])["failures"] == ["output.json"]


def test_schema_failure_preserves_attempt_receipt_and_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    audit.write(
        tmp_path / "phase-a-receipt.json",
        {
            "status": "PASS",
            "generation_id": "fictional-test",
            "code_file_sha256": {},
            "config_file_sha256": {},
            "model_inputs": {"contexts": []},
        },
    )

    def failed_runner(_args):
        audit.write(
            tmp_path / "model-calls/run-1/context-01/receipt.json",
            {"invocation_id": "fictional-test:run-1:context-01", "status": "PASS"},
        )
        raise ValueError("fixture schema mismatch")

    monkeypatch.setattr(audit.runner, "run_canary", failed_runner)
    target = audit.m12.MODEL, audit.m12.EFFORT
    try:
        with pytest.raises(ValueError, match="fixture schema mismatch"):
            audit.run()
    finally:
        audit.m12.MODEL, audit.m12.EFFORT = target
    assert audit.read(tmp_path / "canary-stop.json")["model_calls_completed"] == 1
    assert (
        audit.read(tmp_path / "model-calls/run-1/context-01/run-document.json")["status"] == "FAIL"
    )
