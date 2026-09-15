from __future__ import annotations

from pathlib import Path

from app.services.direction_timing_ownership_service import canonical_sha256
from scripts import ppe_proxy_fcf_claim_scope_m12ar as runner


def test_m12ar_runner_freezes_shadow_contract() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_ACTIVE_COUNT == 22
    assert runner.EXPECTED_CONTEXT_COUNT == 6
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.WORK_INSTRUCTION_COMMIT == (
        "62b5e6eb24ca78c4d80f785f61b27cbbecf5d7ad"
    )


def test_m12ar_runner_requires_all_reports_once() -> None:
    assert len(runner.SLUGS) == 110
    assert len(set(runner.SLUGS)) == 110
    assert len(runner._required_report_files()) == 110


def test_m12ar_abandoned_precall_generation_is_never_resumed() -> None:
    assert runner.ABANDONED_PRECALL_GENERATION_ID != runner.OLD_SHADOW_GENERATION_ID


def test_m12ar_runner_has_no_candidate_global_proxy_switch() -> None:
    source = Path("app/services/directional_financial_context_service.py").read_text(
        encoding="utf-8"
    )
    assert "candidate_uses_ppe_proxy" not in source


def test_m12ar_runner_uses_existing_canonical_hash_contract() -> None:
    value = {"한국": ["현금흐름", 1]}
    assert runner.canonical_sha256(value) == canonical_sha256(value)
