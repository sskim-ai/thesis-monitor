from __future__ import annotations

from pathlib import Path

from scripts import partial_output_forensics_transport_stall_review as review
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic


def test_secret_scanner_blocks_named_secret_and_bearer() -> None:
    clean = review.scan_secret_bytes(b"fictional evidence only")
    blocked = review.scan_secret_bytes(
        b"API_KEY=abcdefghijklmnop Bearer abcdefghijklmnopqrstuvwxyz"
    )

    assert clean["secret_scan_status"] == "PASS"
    assert clean["secret_exposure_count"] == 0
    assert blocked["secret_scan_status"] == "BLOCKED"
    assert blocked["secret_exposure_count"] == 2


def test_lifecycle_fields_preserve_silence_and_namespace() -> None:
    fields = review.lifecycle_fields(
        {
            "generation_id": "fictional-generation",
            "invocation_id": "fictional-invocation",
            "invocation_start_monotonic": 10.0,
            "first_stderr_byte_monotonic": 10.25,
            "last_stderr_byte_monotonic": 10.5,
            "process_exit_monotonic": 20.0,
            "stdin_complete_monotonic": 10.1,
            "transport_metadata": {"runtime_state_namespace_hash": "same"},
            "cli_binary_identity": {"path": "/fictional", "sha256": "abc"},
        }
    )

    assert fields["stdin_complete"] is True
    assert fields["stderr_burst_duration_seconds"] == 0.25
    assert fields["silent_interval_before_exit_seconds"] == 9.5
    assert fields["state_namespace_hash"] == "same"


def test_recovered_core_audit_is_core_only() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_AUDIT", market="us")
    core = synthetic.fixture_core(owned)

    result = review._core_only_audit(core, owned)

    assert result["status"] == "PASS"
    assert result["directional_core_price_technical_refs"] == 0
    assert result["directional_core_supply_refs"] == 0
    assert result["buy_without_nonprice_material_anchor"] == 0
    assert result["sell_without_nonprice_material_anchor"] == 0


def test_probe_precommit_is_fictional_same_namespace_and_sized(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Preserve the historical pre-M12Y 15-20 KB prompt; do not relax the size gate.
    prior = Path("fixtures/pre_m12e_ordinal_calibration_prompt.txt").read_text().strip()
    current_core_prompt = review.frozen._core_prompt
    monkeypatch.setattr(
        review.frozen, "directional_balance_ordinal_calibration_prompt", lambda: prior
    )
    monkeypatch.setattr(
        review.frozen,
        "_core_prompt",
        lambda **kwargs: current_core_prompt(**kwargs).replace(
            "\n\n" + review.frozen.BUSINESS_THESIS_CHANGE_PROMPT + "\n\n",
            "\n\n",
        ),
    )
    rows, namespace = review.build_probe_inputs(tmp_path, "fictional-generation")

    assert [row["market_mix"] for row in rows] == [
        {"us": 4},
        {"kr": 4},
        {"kr": 4},
    ]
    assert [row["same_namespace_sequence_position"] for row in rows] == [1, 2, 3]
    assert {row["state_namespace"] for row in rows} == {namespace}
    assert all(15_000 <= row["input_bytes"] <= 20_000 for row in rows)
    assert all(row["fictional_subject_count"] == 4 for row in rows)
    assert all(row["real_issuer_identity_count"] == 0 for row in rows)
    assert all(
        ticker.startswith("SYNTHETIC_") for row in rows for ticker in row["fictional_subject_ids"]
    )
    assert not {ticker for row in rows for ticker in row["fictional_subject_ids"]} & set(
        review.RETIRED_HOLDOUT + review.CONSUMED_REGRESSION
    )


def test_production_no_change_contract_is_closed() -> None:
    proof = review.production_no_change()

    assert proof["status"] == "PASS"
    assert all(
        proof[field] == 0
        for field in (
            "main_merge",
            "production_db_mutation",
            "production_telegram_send",
            "production_scheduler_change",
            "monitoring_registration_calls",
            "live_structured_autonomy_activation",
            "live_v2_change",
            "night_futures_code_mutation",
        )
    )
