import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from scripts import synthetic_canary_fixture_repair_ownership_resume as resume


def test_fictional_fixture_separates_identity_from_routing_market() -> None:
    us = resume.fictional_owned("SYNTHETIC_US_TEST", market="us")
    kr = resume.fictional_owned("SYNTHETIC_KR_TEST", market="kr")

    assert us.source_packet.market == "us"
    assert kr.source_packet.market == "kr"
    assert us.source_packet.ticker.startswith("SYNTHETIC_")
    assert kr.source_packet.ticker.startswith("SYNTHETIC_")
    assert not ({us.source_packet.ticker, kr.source_packet.ticker} & set(resume.CURRENT_HOLDOUT))


def test_synthetic_packet_preflight_covers_all_frozen_shapes() -> None:
    proof = resume.preflight_document()

    assert proof["synthetic_packet_schema_preflight"] == "PASS"
    assert proof["production_market_enum_mutation"] == 0
    assert proof["production_packet_schema_mutation"] == 0
    assert proof["real_issuer_used_as_canary"] == 0
    assert {
        (row["case"], row["market"], row["subject_count"])
        for row in proof["cases"]
    } == {
        ("us_single", "us", 1),
        ("kr_single", "kr", 1),
        ("us4", "us", 4),
        ("kr4", "kr", 4),
        ("timing_us", "us", 1),
        ("timing_kr", "kr", 1),
    }


def test_additive_packet_extension_preserves_legacy_schema_and_transport() -> None:
    schema = deepcopy(DecisionEvidencePacket.model_json_schema())
    schema["$defs"]["DecisionEvidenceRef"]["properties"].pop("financial_context")
    for definition in (
        "FinancialAttributionBasis",
        "FinancialComparison",
        "FinancialComparisonKind",
        "FinancialContext",
        "FinancialDerivation",
        "FinancialEvidenceQuality",
        "FinancialEvidenceStatus",
        "FinancialPeriod",
        "FinancialPeriodType",
    ):
        schema["$defs"].pop(definition)
    legacy_schema_sha256 = hashlib.sha256(
        json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    assert resume.packet_schema_sha256() == (
        "a2b03be7380caebb1f7d772c05866b4aebc3991e0411f6b5f2a3d2c78600991b"
    )
    assert legacy_schema_sha256 == resume.EXPECTED_PACKET_SCHEMA_SHA256
    current = resume.transport_hashes(Path.cwd())
    intentional_runtime_isolation_changes = {
        "continuation_harness_file",
        "continuation_transport_adapter",
    }
    assert all(
        current[key] == resume.EXPECTED_TRANSPORT_HASHES[key]
        for key in set(current) - intentional_runtime_isolation_changes
    )
    assert all(
        current[key] != resume.EXPECTED_TRANSPORT_HASHES[key]
        for key in intentional_runtime_isolation_changes
    )
    market_schema = DecisionEvidencePacket.model_json_schema()["properties"]["market"]

    assert market_schema["enum"] == ["kr", "us"]
    assert "synthetic" not in market_schema["enum"]


def test_timeout_batch_and_consumed_cohort_gates_are_frozen() -> None:
    assert resume.MODEL_TIMEOUT_SECONDS == 1800
    assert resume.MODEL_CONTEXT_BATCH_SIZE == 4
    assert resume.MAX_CANARY_MODEL_CALLS == 7
    assert not (set(resume.CONSUMED_LATEST_HOLDOUT16) & set(resume.CURRENT_HOLDOUT))


class _Observer:
    backend = "TEST_OBSERVER"
    capabilities = {
        "protected_window_observable": True,
        "natural_job_observable": True,
        "model_execution_observable": True,
        "ps_dependency": False,
    }

    def __init__(self, *, natural: int = 0, model: int = 0) -> None:
        self.natural = natural
        self.model = model

    def observe(self) -> dict[str, object]:
        return {
            "workload_observation_backend": self.backend,
            "observation_capabilities": self.capabilities,
            "active_natural_job_count": self.natural,
            "running_model_process_count": self.model,
            "natural_job_rows": [],
            "model_execution_pids": [],
        }


def _guard(tmp_path: Path, observer: _Observer, hour_utc: int = 2):
    return resume.LiveWorkloadGuard(
        tmp_path / "guard.json",
        observer=observer,
        clock=lambda: datetime(2026, 9, 7, hour_utc, 0, tzinfo=UTC),
    )


def test_sandbox_guard_allows_observable_zero_contention(tmp_path: Path) -> None:
    result = _guard(tmp_path, _Observer()).preflight(
        stage="DIRECTIONAL_CORE", batch_id="01", subject_count=4
    )

    assert result["status"] == "PASS"
    assert result["safe_to_spawn"] == 1
    assert result["real_model_calls"] == 0
    assert result["transport_receipt_expected"] == 0


@pytest.mark.parametrize(("natural", "model"), ((1, 0), (0, 1)))
def test_sandbox_guard_detects_observable_contention(
    tmp_path: Path, natural: int, model: int
) -> None:
    result = _guard(tmp_path, _Observer(natural=natural, model=model)).preflight(
        stage="DIRECTIONAL_CORE", batch_id="01", subject_count=4
    )

    assert result["status"] == "DEFER"
    assert result["safe_to_spawn"] == 0


def test_protected_kst_window_blocks_even_with_zero_contention(tmp_path: Path) -> None:
    guard = _guard(tmp_path, _Observer(), hour_utc=7)

    result = guard.preflight(
        stage="DIRECTIONAL_CORE", batch_id="01", subject_count=4
    )

    assert result["protected_window"] == "KR_NATURAL"
    assert result["safe_to_spawn"] == 0


def test_observation_unavailable_fails_closed_without_ps_fallback(
    tmp_path: Path,
) -> None:
    class Unavailable(_Observer):
        def observe(self) -> dict[str, object]:
            try:
                raise PermissionError("ps denied")
            except PermissionError as exc:
                raise resume.LiveWorkloadObservationUnavailable(
                    "process_observation_unavailable"
                ) from exc

    guard = _guard(tmp_path, Unavailable())

    with pytest.raises(
        resume.LiveWorkloadObservationUnavailable,
        match="process_observation_unavailable",
    ):
        guard.preflight(
            stage="DIRECTIONAL_CORE", batch_id="01", subject_count=4
        )

    audit = resume.read_json(tmp_path / "guard.json")
    assert audit["observation_unavailable_fail_open_count"] == 0
    assert audit["observation_unavailable_fail_closed_count"] == 1
    assert audit["events"][0]["action"] == "BLOCK"
