from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import fresh_issuer_ownership_proof_transport_risk_carried as proof


def _prior_registry() -> dict[str, object]:
    return {
        "rows": [
            {
                "canonical_issuer_key": f"prior:{index:03d}",
                "security_aliases": [f"OLD{index:03d}"],
            }
            for index in range(proof.PRIOR_EXCLUSION_COUNT)
        ]
    }


def _exposed_state() -> dict[str, object]:
    return {
        "program_generation_id": "fresh-prior-generation",
        "ordered_cohort": [f"NEW{index:02d}" for index in range(16)],
    }


def _references() -> list[dict[str, object]]:
    rows = [
        {
            "display_symbol": f"NEW{index:02d}",
            "canonical_issuer_key": f"issuer:{index:02d}",
            "market": "us" if index < 4 else "kr",
        }
        for index in range(16)
    ]
    rows.append(
        {
            "display_symbol": "NEW00.ALIAS",
            "canonical_issuer_key": "issuer:00",
            "market": "us",
        }
    )
    return rows


def test_budget_and_model_contract_remain_frozen() -> None:
    assert proof.runner.MODEL == "gpt-5.6-sol"
    assert proof.runner.EFFORT == "xhigh"
    assert proof.runner.TIMEOUT_SECONDS == 1800
    assert proof.runner.TIMEOUT_OWNER_COUNT == 1
    assert proof.EXPECTED_CONTEXTS_PER_RUN == 8
    assert proof.EXPECTED_TOTAL_CONTEXTS == 32
    assert proof.PREDECESSOR_MEMBER_COUNT == 329
    assert proof.PREDECESSOR_INDEXED_PAYLOAD_COUNT == 328


def test_merge_exposure_registry_appends_full_latest_cohort() -> None:
    result = proof.merge_exposure_registry(
        _prior_registry(),
        exposed_state=_exposed_state(),
        references=_references(),
    )

    assert result["prior_registry_count"] == 101
    assert result["appended_exposed_issuer_count"] == 16
    assert result["reconciled_registry_count"] == 117
    assert len(result["rows"]) == 117
    latest = next(row for row in result["rows"] if row["canonical_issuer_key"] == "issuer:00")
    assert latest["security_aliases"] == ["NEW00", "NEW00.ALIAS"]
    assert latest["whole_cohort_retired"] is True


def test_merge_exposure_registry_rejects_prior_overlap() -> None:
    prior = _prior_registry()
    prior["rows"][0]["canonical_issuer_key"] = "issuer:00"

    with pytest.raises(ValueError, match="exposed_issuer_duplicate_or_missing"):
        proof.merge_exposure_registry(
            prior,
            exposed_state=_exposed_state(),
            references=_references(),
        )


def test_runtime_artifact_manifest_fails_closed_on_missing_file(
    tmp_path: Path,
) -> None:
    for name in (
        "prompt.txt",
        "schema.json",
        "identity-binding-lock.json",
        "actual-request-identity-preflight.json",
    ):
        (tmp_path / name).write_text("{}", encoding="utf-8")

    result = proof._runtime_artifact_manifest(tmp_path)

    assert result["status"] == "FAIL"
    assert result["failures"] == ["missing:workload-observation.json"]


def test_runtime_artifact_manifest_records_all_required_files(
    tmp_path: Path,
) -> None:
    for name in (
        "prompt.txt",
        "schema.json",
        "identity-binding-lock.json",
        "actual-request-identity-preflight.json",
        "workload-observation.json",
    ):
        (tmp_path / name).write_text("{}", encoding="utf-8")

    result = proof._runtime_artifact_manifest(tmp_path)

    assert result["status"] == "PASS"
    assert not result["failures"]
    assert all(row["sha256"] for row in result["rows"])


def test_work_instruction_is_the_frozen_attachment() -> None:
    path = Path(proof.WORK_INSTRUCTION_PATH)
    assert proof.file_sha256(path) == proof.WORK_INSTRUCTION_SHA256


def test_source_configuration_audit_records_presence_not_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        proof,
        "get_settings",
        lambda: SimpleNamespace(
            sec_user_agent="private-user-agent",
            opendart_api_key="private-api-key",
        ),
    )
    monkeypatch.setenv("THESIS_MONITOR_ENV_FILE", "/private/existing.env")

    result = proof._source_configuration_audit()

    assert result["status"] == "PASS"
    assert result["required_setting_presence"] == {
        "SEC_USER_AGENT": True,
        "OPENDART_API_KEY": True,
    }
    assert "private-user-agent" not in str(result)
    assert "private-api-key" not in str(result)


def test_source_configuration_audit_fails_closed_when_settings_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        proof,
        "get_settings",
        lambda: SimpleNamespace(sec_user_agent=None, opendart_api_key=None),
    )
    monkeypatch.delenv("THESIS_MONITOR_ENV_FILE", raising=False)

    result = proof._source_configuration_audit()

    assert result["status"] == "FAIL"
    assert result["missing_required_settings"] == [
        "OPENDART_API_KEY",
        "SEC_USER_AGENT",
    ]
    assert result["secret_values_recorded"] == 0


def test_artifact_secret_scan_does_not_treat_risk_carried_as_api_key(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "report.txt"
    artifact.write_text("fresh-issuer-ownership-proof-transport-risk-carried")

    result = proof.scan_artifact_secrets([artifact])

    assert result["secret_scan_status"] == "PASS"
    assert result["secret_exposure_count"] == 0


def test_artifact_secret_scan_still_rejects_openai_key_shape(tmp_path: Path) -> None:
    artifact = tmp_path / "secret.txt"
    artifact.write_bytes(b"token=" + b"sk-" + (b"a" * 24))

    result = proof.scan_artifact_secrets([artifact])

    assert result["secret_scan_status"] == "FAIL"
    assert result["category_counts"]["openai_key"] == 1
