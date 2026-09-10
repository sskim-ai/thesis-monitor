from pathlib import Path

from scripts import positive_stronger_bucket_m12x as x


def test_root_cause_and_branch_are_frozen_before_implementation():
    root = x.read(x.ROOT)
    decision = x.read(
        x.REPORTS / "13-fic-fin-01-root-cause-decision.json"
    )
    assert root["root_cause"] == "EXACT_FIXTURE_TARGET_OVERCONSTRAINED"
    assert root["selected_branch"] == "FIXTURE_TARGET_CORRECTION_ONLY"
    assert decision["root_cause"] == root["root_cause"]
    assert decision["directional_prompt_change_authorized"] is False


def test_fic_fin_01_target_is_generic_6_5_without_other_target_drift():
    targets = x.read(x.ROOT)["semantic_freeze"]["target_buys"]
    assert targets == {
        "FIC-FIN-01": 6.5,
        "FIC-FIN-02": 4.5,
        "FIC-FIN-04": 5.0,
        "FIC-FIN-05": 4.5,
    }


def test_model_free_positive_and_negative_contract_fixtures_pass():
    audit = x.fixture_audit()
    assert audit["status"] == "PASS"
    assert audit["fixed_score_rule_count"] == 0
    assert audit["evidence_count_bucket_rule_count"] == 0
    assert len(audit["rows"]) == 8


def test_stronger_positive_is_symmetric_with_stronger_negative():
    rows = {row["id"]: row for row in x.fixture_audit()["rows"]}
    assert rows["POS-ORD-01"]["expected_buy"] == rows["NEG-ORD-01"]["expected_sell"]
    assert rows["POS-ORD-02"]["expected_buy"] == rows["NEG-ORD-02"]["expected_sell"]
    assert rows["POS-ORD-03"]["expected_buy"] == rows["NEG-ORD-03"]["expected_sell"]


def test_valuation_missing_is_not_a_universal_6_5_cap():
    rows = {row["id"]: row for row in x.fixture_audit()["rows"]}
    assert rows["POS-ORD-04"]["expected_buy"] == 6.5


def test_directional_prompt_and_fictional_source_case_are_unchanged():
    from scripts import business_delta_alias_balance_confidence_m12z as z

    current = Path("app/services/directional_balance_service.py").read_text()
    assert z.without_m12z_prompt(current).encode() == x._base_bytes(
        "app/services/directional_balance_service.py"
    )
    assert x._freeze_paths(("scripts/directional_financial_context_m12.py",))["status"] == "PASS"


def test_runtime_contract_remains_sol_xhigh_model_context_coupled():
    root = x.read(x.ROOT)
    assert (root["model"], root["effort"]) == ("gpt-5.6-sol", "xhigh")
    assert root["selected_timeout_seconds"] == 1800
    assert root["subjects_per_context"] == 4
    assert root["context_count"] == 2
    assert root["repetition_count"] == 3
    assert root["wrapper_retry_count"] == 0
    assert root["runtime"]["selective_retry"] is False
    assert root["runtime"]["fallback_model"] is None


def test_calibration_audit_uses_m12x_target_without_label_override():
    row = {
        "ticker": "FIC-FIN-01",
        "core": {"directional_balance": {"buy": 6.5, "sell": 3.5}},
    }
    assert x.calibration_audit(row)["status"] == "PASS"
    row["core"]["directional_balance"]["buy"] = 6.0
    assert x.calibration_audit(row)["status"] == "FAIL"


def test_phase_a_reports_are_frozen_and_instruction_has_75_slugs():
    assert sorted(x.SLUGS) == list(range(1, 76))
    for number in range(1, 14):
        assert list(Path(x.REPORTS).glob(f"{number:02d}-*.json"))
