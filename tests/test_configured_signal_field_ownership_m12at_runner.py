from scripts import configured_signal_field_ownership_m12at as runner


def test_report_sequence_matches_work_instruction() -> None:
    assert len(runner.SLUGS) == 138
    assert runner.SLUGS[10] == "configured-signal-field-ownership-decision"
    assert runner.SLUGS[50] == "new-fictional-model-call-gate"
    assert runner.SLUGS[138] == "program-completion"


def test_runtime_contract_is_frozen() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_ROWS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.EXPECTED_ACTIVE_COUNT == 22


def test_fixture_audit_is_fail_closed() -> None:
    audit = runner._fixture_audit()
    assert audit["status"] == "PASS"
    assert all(row["status"] == "PASS" for row in audit["rows"])
    assert all(
        row["status"] == "PASS" for row in audit["false_fulfillment_rows"]
    )


def test_model_schema_fences_only_current_directional_fields() -> None:
    audit = runner._schema_impact_audit()
    assert audit["status"] == "PASS"
    assert audit["configured_aliases"]
    configured = set(audit["configured_aliases"])
    assert all(
        configured.isdisjoint(values)
        for values in audit["current_field_aliases"].values()
    )
    assert configured <= set(audit["future_field_aliases"])
    assert audit["configured_model_surface_rows"]
