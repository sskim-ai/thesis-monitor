from __future__ import annotations

from scripts import shadow_active_universe_count_compatibility_m12be as program


def test_m12be_report_contract_and_runtime_are_frozen() -> None:
    assert len(program.REPORT_SLUGS) == 124
    assert len(set(program.REPORT_SLUGS)) == 124
    assert program.REPORT_SLUGS[0] == "repository-provenance"
    assert program.REPORT_SLUGS[-1] == "program-completion"
    assert program.MODEL == "gpt-5.6-sol"
    assert program.EFFORT == "xhigh"
    assert program.M12BD_GENERATION_ID == (
        "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"
    )


def test_m12be_has_no_fixed_active_universe_count_constant() -> None:
    assert not hasattr(program, "EXPECTED_ACTIVE_COUNT")
    assert program.SUBJECTS_PER_CONTEXT == 4


def test_frozen_packet_source_override_survives_legacy_path_configuration(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "frozen-source"
    program.write_json(
        source / "shadow/program-state.json",
        {"tickers": [], "packet_paths": {}, "packet_hashes": {}},
    )
    monkeypatch.setattr(
        program.capability,
        "FROZEN_PACKET_SOURCE_OVERRIDE",
        source,
    )
    monkeypatch.setattr(
        program.capability,
        "PREVIOUS_OUTPUT",
        tmp_path / "legacy-missing-source",
    )

    state, packets = program.capability._previous_source_packets()

    assert state["tickers"] == []
    assert packets == {}


def test_m12ba_reads_its_contract_owned_expectation_report() -> None:
    source = program.Path(
        "scripts/financial_sector_replacement_verb_parity_m12ba.py"
    ).read_text(encoding="utf-8")

    assert 'REPORTS / f"101-{SLUGS[101]}.json"' in source
    assert "report_subject_identity(upstream(101))" not in source
