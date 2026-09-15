from __future__ import annotations

from scripts import ppe_proxy_fcf_claim_safety_m12an as runner


def test_m12an_runner_freezes_branch_b_and_model_contract() -> None:
    assert runner.BRANCH_SELECTED == "BRANCH_B_METADATA_AND_VALIDATOR"
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_OUTPUTS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18


def test_m12an_runner_uses_non_fcf_model_facing_proxy_metadata() -> None:
    assert runner.OLD_PROXY_LABEL == "cash_flow_fcf_ppe"
    assert runner.OLD_PROXY_METRIC_REFS == ["FCF"]
    assert runner.NEW_PROXY_LABEL == "cash_conversion_ocf_less_ppe"
    assert "fcf" not in runner.NEW_PROXY_LABEL.casefold()
    assert runner.NEW_PROXY_METRIC_REFS == []


def test_m12an_runner_requires_exactly_99_reports() -> None:
    reports = runner._required_report_files()

    assert len(reports) == 99
    assert len(set(reports)) == 99
    assert any(path.name.startswith("28b-") for path in reports)
    assert any(path.name.startswith("47b-") for path in reports)
    assert any(path.name.startswith("99-") for path in reports)
