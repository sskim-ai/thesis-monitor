from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from scripts import existing_source_env_binding_fresh_holdout_resume as proof


def test_contract_and_frozen_selection_state() -> None:
    assert len(proof.REPORT_NAMES) == 64
    assert proof.EXPECTED_SELECTION_POLICY_SHA256 == (
        "07defbbe29042495ebaa08cb24ca5fcc57cd42c859bfbf80ccc5d984068b2f8f"
    )
    assert proof.EXPECTED_EXCLUSION_REGISTRY_SHA256 == (
        "7ffd6fed1125e88073efb867d3d5adc4024a0f22485e0c376151fbe5e3b6b437"
    )
    assert proof.EXPECTED_EXCLUSION_COUNT == 117
    assert proof.FROZEN_EVALUATION_CUTOFF == "2026-09-07T15:27:51+00:00"
    assert proof.runner.MODEL == "gpt-5.6-sol"
    assert proof.runner.EFFORT == "xhigh"
    assert proof.runner.TIMEOUT_SECONDS == 1800
    assert proof.runner.TIMEOUT_OWNER_COUNT == 1


def test_work_instruction_matches_attachment() -> None:
    assert proof.file_sha256(Path(proof.WORK_INSTRUCTION_PATH)) == (
        proof.WORK_INSTRUCTION_SHA256
    )


def test_source_configuration_audit_binds_external_file_without_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    protected = tmp_path / "protected.env"
    protected.write_text(
        "OPENDART_API_KEY=private-dart-value\n"
        "SEC_USER_AGENT=private-sec-identity\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", str(protected))

    result = proof.source_configuration_audit(repository)

    assert result["status"] == "PASS"
    assert result["protected_source_config_bound"] is True
    assert result["required_setting_presence"] == {
        "OPENDART_API_KEY": True,
        "SEC_USER_AGENT": True,
    }
    assert "private-dart-value" not in str(result)
    assert "private-sec-identity" not in str(result)
    proof.get_settings.cache_clear()


def test_source_configuration_audit_fails_closed_without_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("THESIS_MONITOR_ENV_FILE", raising=False)
    monkeypatch.chdir(tmp_path)

    result = proof.source_configuration_audit(tmp_path)

    assert result["status"] == "FAIL"
    assert result["protected_source_config_bound"] is False
    proof.get_settings.cache_clear()


def test_failed_preflight_performs_no_source_smoke_requests(
    tmp_path: Path,
) -> None:
    result = asyncio.run(
        proof._source_smokes(
            expansion_zip=tmp_path / "not-opened.zip",
            configuration={"status": "FAIL"},
        )
    )

    assert result["us"]["status"] == "NOT_RUN"
    assert result["kr"]["status"] == "NOT_RUN"
    assert result["us"]["request_count"] == 0
    assert result["kr"]["request_count"] == 0


def test_secret_scan_rejects_exact_bound_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protected = tmp_path / "protected.env"
    protected.write_text(
        "OPENDART_API_KEY=private-dart-value\n"
        "SEC_USER_AGENT=private-sec-identity\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", str(protected))
    artifact = tmp_path / "artifact.json"
    artifact.write_text("private-dart-value", encoding="utf-8")

    result = proof.scan_artifact_secrets([artifact])

    assert result["secret_scan_status"] == "FAIL"
    assert result["protected_value_exact_match_count"] == 1
    proof.get_settings.cache_clear()


def test_secret_scan_allows_only_configuration_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protected = tmp_path / "protected.env"
    protected.write_text(
        "OPENDART_API_KEY=private-dart-value\n"
        "SEC_USER_AGENT=private-sec-identity\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", str(protected))
    artifact = tmp_path / "artifact.json"
    artifact.write_text(
        '{"OPENDART_API_KEY": true, "SEC_USER_AGENT": true}', encoding="utf-8"
    )

    result = proof.scan_artifact_secrets([artifact])

    assert result["secret_scan_status"] == "PASS"
    proof.get_settings.cache_clear()
