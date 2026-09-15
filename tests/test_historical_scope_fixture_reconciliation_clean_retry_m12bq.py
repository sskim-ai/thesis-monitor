from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import zipfile

from scripts import historical_scope_fixture_reconciliation_clean_retry_m12bq as m12bq


def test_frozen_cohort_and_packet_identity_are_exact() -> None:
    assert m12bq.COHORT == (
        "138930",
        "BAC",
        "000270",
        "GM",
        "018260",
        "INTU",
        "004170",
        "SBUX",
        "207940",
        "ABBV",
        "096770",
        "CVX",
    )
    assert set(m12bq.EXPECTED_PACKET_HASHES) == set(m12bq.COHORT)
    assert all(len(value) == 64 for value in m12bq.EXPECTED_PACKET_HASHES.values())
    assert m12bq.PARENT_GENERATION == (
        "20260915-m12bp-fresh-20260914T101849Z-9329c13191bd"
    )


def test_frozen_six_call_plan_is_exact_and_has_no_retry() -> None:
    plan = m12bq._call_plan()

    assert len(plan) == 6
    assert [row["stage"] for row in plan] == [
        "DIRECTIONAL_CORE",
        "DIRECTIONAL_CORE",
        "DIRECTIONAL_CORE",
        "PRICE_TIMING",
        "PRICE_TIMING",
        "PRICE_TIMING",
    ]
    assert [row["tickers"] for row in plan[:3]] == [
        list(m12bq.COHORT[0:4]),
        list(m12bq.COHORT[4:8]),
        list(m12bq.COHORT[8:12]),
    ]
    assert [row["tickers"] for row in plan[3:]] == [
        row["tickers"] for row in plan[:3]
    ]
    assert all(row["attempt_limit"] == 1 for row in plan)
    assert all(row["wrapper_retry"] == 0 for row in plan)
    assert m12bq.TIMEOUT_SECONDS == 1800
    assert (m12bq.MODEL, m12bq.EFFORT) == ("gpt-5.6-sol", "xhigh")


def test_retry_generation_is_new_but_deterministic() -> None:
    as_of = datetime(2026, 9, 15, 1, 2, 3, tzinfo=UTC)
    first = m12bq.retry_generation_id("a" * 40, as_of)
    second = m12bq.retry_generation_id("a" * 40, as_of)

    assert first == second
    assert first.startswith("20260915-m12bq-retry-20260915T010203Z-")
    assert first != m12bq.PARENT_GENERATION


def test_scope_manifest_is_exact_and_report_contract_is_complete() -> None:
    assert m12bq.M12BP_AUTHORIZED_CHANGE_PATHS == (
        "app/services/coldstart_fundamental_enrichment_service.py",
        "app/services/company_profile_service.py",
        "app/services/opendart_financial_recovery_service.py",
        "tests/test_coldstart_fundamental_enrichment_service.py",
        "tests/test_company_profile_service.py",
        "tests/test_opendart_financial_recovery_service.py",
    )
    assert len(m12bq.REPORT_SLUGS) == len(set(m12bq.REPORT_SLUGS)) == 51
    assert m12bq.REPORT_SLUGS[17] == "frozen-packet-identity-reaudit"
    assert m12bq.REPORT_SLUGS[44] == "fresh-unseen-canonical-proof-decision"
    assert m12bq.REPORT_SLUGS[-1] == "program-completion"


def test_production_firewall_is_closed() -> None:
    firewall = m12bq._production_firewall()

    assert all(
        value in {0, False}
        for key, value in firewall.items()
        if key not in {"contract", "status"}
    )
    assert firewall["remote_push_count"] == 0
    assert firewall["main_merges"] == 0
    assert firewall["deployments"] == 0
    assert firewall["production_sends"] == 0


def test_created_zip_verifier_rejects_unindexed_extra(tmp_path: Path) -> None:
    archive_path = tmp_path / "report.zip"
    index_name = "docs/reports/example/artifact-index.json"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            index_name,
            '{"rows": [], "secret_scan_failure_count": 0}',
        )
        archive.writestr("unexpected.txt", "unexpected")

    result = m12bq._verify_created_zip(archive_path)

    assert result["extra_count"] == 1
    assert result["status"] == "FAIL"
