from __future__ import annotations

from scripts import prospective_monitoring_obligation_m12ax as m12ax


def test_m12ax_report_sequence_is_complete() -> None:
    assert len(m12ax.SLUGS) == 157
    assert m12ax.SLUGS[1] == "repository-provenance"
    assert m12ax.SLUGS[30] == "m12aw-first-call-four-row-offline-reaudit"
    assert m12ax.SLUGS[76] == "fictional-monitoring-obligation-scope-audit"
    assert m12ax.SLUGS[107] == "shadow-monitoring-obligation-scope-audit"
    assert m12ax.SLUGS[157] == "program-completion"


def test_m12ax_monitoring_fixture_gate_passes() -> None:
    audit = m12ax._monitoring_fixtures()

    assert audit["status"] == "PASS"
    assert audit["contract"] == "prospective-financial-monitoring-obligation-v1"
    assert len(audit["positive"]) == 6
    assert len(audit["current_negative"]) == 5
    assert len(audit["no_configured_support"]) == 1
    assert all(row["status"] == "PASS" for row in audit["positive"])
    assert all(row["status"] == "PASS" for row in audit["current_negative"])
    assert all(row["status"] == "PASS" for row in audit["no_configured_support"])


def test_m12ax_does_not_treat_bare_monitoring_word_as_obligation() -> None:
    assert m12ax._prospective_monitoring_obligation_family("감시 대상이다") is None
    assert (
        m12ax._prospective_monitoring_obligation_family("순부채를 감시해야 한다") == "KOREAN_GAMSI"
    )


def test_m12ax_frozen_runtime_contract() -> None:
    assert m12ax.MODEL == "gpt-5.6-sol"
    assert m12ax.EFFORT == "xhigh"
    assert m12ax.TIMEOUT_SECONDS == 1800
    assert m12ax.EXPECTED_FICTIONAL_CALLS == 12
    assert m12ax.EXPECTED_SHADOW_CALLS == 18
    assert m12ax.EXPECTED_ACTIVE_COUNT == 22
    assert m12ax.NEXT_SCOPE == "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
