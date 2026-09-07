from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from app.services.reference_universe_audit_service import (
    IdentityResolutionStatus,
    RoutingSupportStatus,
    canonical_market_mix,
    classify_us_security,
    load_kr_reference_universe,
    load_us_reference_universe,
    reconcile_membership_sets,
    representative_securities,
    validate_us_route_response,
    with_routing_result,
)


def _write_us_references(root: Path) -> tuple[Path, Path, Path]:
    sec = root / "company_tickers.json"
    sec.write_text(
        json.dumps(
            {
                "0": {"cik_str": 1, "ticker": "DUAL", "title": "Dual Corp"},
                "1": {"cik_str": 1, "ticker": "DUAL.B", "title": "Dual Corp"},
                "2": {"cik_str": 2, "ticker": "ADR", "title": "Foreign Corp"},
                "3": {"cik_str": 3, "ticker": "ETF", "title": "Index Fund"},
            }
        ),
        encoding="utf-8",
    )
    nasdaq = root / "nasdaqlisted.txt"
    nasdaq.write_text(
        "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
        "DUAL|Dual Corp - Common Stock|Q|N|N|100|N|N\n"
        "ADR|Foreign Corp - American Depositary Shares|Q|N|N|100|N|N\n"
        "ETF|Index Fund ETF|Q|N|N|100|Y|N\n"
        "File Creation Time: 0904202621:31\n",
        encoding="utf-8",
    )
    other = root / "otherlisted.txt"
    other.write_text(
        "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
        "DUAL.B|Dual Corp Class B Common Stock|N|DUAL.B|N|100|N|DUAL-B\n"
        "UNSUPPORTED|Unsupported Corp Common Stock|P|UNSUPPORTED|N|100|N|UNSUPPORTED\n"
        "File Creation Time: 0904202621:31\n",
        encoding="utf-8",
    )
    return sec, nasdaq, other


def test_us_reference_maps_share_classes_to_one_cik_and_quarantines_unsupported(
    tmp_path: Path,
) -> None:
    sec, nasdaq, other = _write_us_references(tmp_path)

    rows = load_us_reference_universe(
        sec_company_tickers=sec,
        nasdaq_listed=nasdaq,
        other_listed=other,
        retrieved_at="2026-09-07T03:00:00+00:00",
    )

    dual = [row for row in rows if row.display_symbol.startswith("DUAL")]
    assert len(dual) == 2
    assert {row.canonical_issuer_key for row in dual} == {"sec:cik:0000000001"}
    assert all(row.routing_support_status == RoutingSupportStatus.CANDIDATE for row in dual)
    etf = next(row for row in rows if row.display_symbol == "ETF")
    assert etf.eligibility_decision == "QUARANTINED"
    unsupported = next(row for row in rows if row.display_symbol == "UNSUPPORTED")
    assert "provider_exchange_route_not_supported" in unsupported.eligibility_reasons


def test_representative_prefers_non_adr_and_retires_all_share_classes(tmp_path: Path) -> None:
    sec, nasdaq, other = _write_us_references(tmp_path)
    rows = [
        with_routing_result(row, supported=True)
        for row in load_us_reference_universe(
            sec_company_tickers=sec,
            nasdaq_listed=nasdaq,
            other_listed=other,
            retrieved_at="2026-09-07T03:00:00+00:00",
        )
        if row.routing_support_status == RoutingSupportStatus.CANDIDATE
    ]

    representatives = representative_securities(rows, selection_salt="fixed")

    assert len([row for row in representatives if row.canonical_issuer_key == "sec:cik:0000000001"]) == 1
    reconciled = reconcile_membership_sets(
        rows,
        {"sec:cik:0000000001": ("whole_cohort_retirement", "actual_output")},
    )
    assert "sec:cik:0000000001" not in reconciled["unseen_supported_issuer_keys"]
    assert reconciled["within_universe_exclusion_issuer_count"] == 1


def test_ambiguous_sec_identity_is_quarantined(tmp_path: Path) -> None:
    sec, nasdaq, other = _write_us_references(tmp_path)
    payload = json.loads(sec.read_text(encoding="utf-8"))
    payload["4"] = {"cik_str": 99, "ticker": "DUAL", "title": "Conflict Corp"}
    sec.write_text(json.dumps(payload), encoding="utf-8")

    rows = load_us_reference_universe(
        sec_company_tickers=sec,
        nasdaq_listed=nasdaq,
        other_listed=other,
        retrieved_at="2026-09-07T03:00:00+00:00",
    )

    row = next(item for item in rows if item.display_symbol == "DUAL")
    assert row.identity_resolution_status == IdentityResolutionStatus.AMBIGUOUS
    assert row.eligibility_decision == "QUARANTINED"


def test_kr_reference_uses_opendart_corp_code_not_company_name(tmp_path: Path) -> None:
    sector_map = tmp_path / "sector_map.csv"
    sector_map.write_text(
        "code,name,market,sector,industry\n"
        "000001,한글회사,KOSPI,산업,산업\n"
        "000002,한글회사,KOSDAQ,기술,기술\n",
        encoding="utf-8",
    )
    corp_zip = tmp_path / "corp.zip"
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?><result>"
        "<list><corp_code>10000001</corp_code><corp_name>한글회사</corp_name>"
        "<corp_eng_name>A</corp_eng_name><stock_code>000001</stock_code>"
        "<modify_date>20260901</modify_date></list>"
        "<list><corp_code>10000002</corp_code><corp_name>한글회사</corp_name>"
        "<corp_eng_name>B</corp_eng_name><stock_code>000002</stock_code>"
        "<modify_date>20260901</modify_date></list></result>"
    )
    with zipfile.ZipFile(corp_zip, "w") as archive:
        archive.writestr("CORPCODE.xml", xml)

    rows = load_kr_reference_universe(
        sector_map=sector_map,
        opendart_corp_code=corp_zip,
        retrieved_at="2026-09-07T03:00:00+00:00",
    )

    assert len(rows) == 2
    assert len({row.canonical_issuer_key for row in rows}) == 2
    assert all(row.eligibility_decision == "ELIGIBLE_SUPPORTED_SECURITY" for row in rows)


def test_market_mix_uses_explicit_market_for_nonnumeric_kr_subject() -> None:
    assert canonical_market_mix(
        ("FICTIONAL_KR", "AAPL"),
        {"FICTIONAL_KR": "kr", "AAPL": "us"},
    ) == {"us": 1, "kr": 1}


def test_market_mix_rejects_missing_invalid_and_conflicting_metadata() -> None:
    with pytest.raises(ValueError, match="metadata_missing"):
        canonical_market_mix(("A",), {})
    with pytest.raises(ValueError, match="metadata_invalid"):
        canonical_market_mix(("A",), {"A": "synthetic"})
    with pytest.raises(ValueError, match="metadata_conflict"):
        canonical_market_mix(
            ("A",),
            {"A": "kr"},
            corroborating_market_by_subject={"A": "us"},
        )


def test_security_classifier_does_not_promote_acquisition_units() -> None:
    security_type, is_adr, reasons = classify_us_security(
        "Example Acquisition Corp - Units",
        etf="N",
        test_issue="N",
    )

    assert not is_adr
    assert security_type == "unit"
    assert {"unit", "spac"} <= set(reasons)


def test_route_validation_requires_provider_stock_list_identity(tmp_path: Path) -> None:
    sec, nasdaq, other = _write_us_references(tmp_path)
    row = next(
        item
        for item in load_us_reference_universe(
            sec_company_tickers=sec,
            nasdaq_listed=nasdaq,
            other_listed=other,
            retrieved_at="2026-09-07T03:00:00+00:00",
        )
        if item.display_symbol == "DUAL"
    )
    safe, reason, _ = validate_us_route_response(
        row,
        status_code=200,
        payload={
            "resolved_symbol": {
                "code": "DUAL",
                "market": "US",
                "exchange": "ND",
                "matched_by": "us_stock_list_code",
            }
        },
    )
    unsafe, unsafe_reason, _ = validate_us_route_response(
        row,
        status_code=200,
        payload={
            "resolved_symbol": {
                "code": "DUAL",
                "market": "US",
                "exchange": "ND",
                "matched_by": "us_ticker",
            }
        },
    )

    assert safe and reason == "provider_route_verified"
    assert not unsafe and unsafe_reason == "provider_route_not_stock_list_verified"
