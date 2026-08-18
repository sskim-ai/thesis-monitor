from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.providers.krx_kr_market_provider import (
    KOSDAQ_DAILY_PATH,
    KOSDAQ_INDEX_PATH,
    KOSDAQ_REFERENCE_PATH,
    KOSPI_DAILY_PATH,
    KOSPI_INDEX_PATH,
    KOSPI_REFERENCE_PATH,
    KrxKrMarketProvider,
    krx_capability_matrix,
    validate_krx_base_url,
)


SESSION = date(2026, 8, 14)


def _daily(
    ticker: str,
    market: str,
    close: str,
    change: str,
    return_pct: str,
    *,
    volume: str = "100",
    trading_value: str = "11000",
) -> dict[str, str]:
    return {
        "BAS_DD": "20260814",
        "ISU_CD": ticker,
        "ISU_NM": ticker,
        "MKT_NM": market,
        "SECT_TP_NM": "",
        "TDD_CLSPRC": close,
        "CMPPREVDD_PRC": change,
        "FLUC_RT": return_pct,
        "TDD_OPNPRC": close,
        "TDD_HGPRC": close,
        "TDD_LWPRC": close,
        "ACC_TRDVOL": volume,
        "ACC_TRDVAL": trading_value,
        "MKTCAP": "100000",
        "LIST_SHRS": "1000",
    }


def _reference(
    ticker: str,
    market: str,
    *,
    security_group: str = "주권",
    certificate: str = "보통주",
    segment: str = "우량기업부",
    name: str | None = None,
    listing_date: str = "20200101",
) -> dict[str, str]:
    return {
        "ISU_CD": f"KR7{ticker}0000",
        "ISU_SRT_CD": ticker,
        "ISU_NM": name or ticker,
        "ISU_ABBRV": name or ticker,
        "ISU_ENG_NM": ticker,
        "LIST_DD": listing_date,
        "MKT_TP_NM": market,
        "SECUGRP_NM": security_group,
        "SECT_TP_NM": segment,
        "KIND_STKCERT_TP_NM": certificate,
        "PARVAL": "5000",
        "LIST_SHRS": "1000",
    }


def _index(index_class: str, name: str, close: str, return_pct: str) -> dict[str, str]:
    return {
        "BAS_DD": "20260814",
        "IDX_CLSS": index_class,
        "IDX_NM": name,
        "CLSPRC_IDX": close,
        "CMPPREVDD_IDX": "1",
        "FLUC_RT": return_pct,
        "OPNPRC_IDX": close,
        "HGPRC_IDX": close,
        "LWPRC_IDX": close,
        "ACC_TRDVOL": "1000",
        "ACC_TRDVAL": "2000",
        "MKTCAP": "3000",
    }


def _fixtures() -> dict[str, list[dict[str, str]]]:
    return {
        KOSPI_DAILY_PATH: [
            _daily("000001", "KOSPI", "110", "10", "10.00", trading_value="11,000"),
            _daily("000002", "KOSPI", "90", "-10", "-10.00"),
            _daily("000003", "KOSPI", "100", "0", "0.00"),
        ],
        KOSDAQ_DAILY_PATH: [
            _daily("100001", "KOSDAQ", "95", "-5", "-5.00", trading_value="4,750"),
            _daily("100002", "KOSDAQ", "2000", "0", "0.00"),
            _daily("100003", "KOSDAQ", "100", "0", "0.00"),
        ],
        KOSPI_REFERENCE_PATH: [
            _reference("000001", "KOSPI", segment=""),
            _reference("000002", "KOSPI", certificate="구형우선주", segment=""),
            _reference("000003", "KOSPI", security_group="부동산투자회사", segment=""),
        ],
        KOSDAQ_REFERENCE_PATH: [
            _reference("100001", "KOSDAQ"),
            _reference(
                "100002", "KOSDAQ", segment="SPAC(소속부없음)", name="테스트스팩"
            ),
            _reference("100003", "KOSDAQ", listing_date="20260814"),
        ],
        KOSPI_INDEX_PATH: [
            _index("KOSPI", "코스피", "3000", "2.00"),
            _index("KOSPI", "코스피 200", "400", "2.50"),
            _index("KOSPI", "코스피 200 정보기술", "500", "3.00"),
        ],
        KOSDAQ_INDEX_PATH: [
            _index("KOSDAQ", "코스닥", "900", "-1.00"),
            _index("KOSDAQ", "코스닥 150", "1200", "-1.50"),
            _index("KOSDAQ", "코스닥 150 헬스케어", "800", "-2.00"),
        ],
    }


def _provider(tmp_path: Path, fixtures: dict[str, list[dict[str, str]]] | None = None):
    payloads = fixtures or _fixtures()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        endpoint = "/".join(request.url.path.split("/")[-2:])
        return httpx.Response(200, json={"OutBlock_1": payloads.get(endpoint, [])})

    return (
        KrxKrMarketProvider(
            api_key="secret-test-key",
            base_url="https://krx.example.test/svc/apis",
            cache_dir=tmp_path,
            transport=httpx.MockTransport(handler),
        ),
        requests,
    )


def test_base_url_rejects_credentials_and_query() -> None:
    with pytest.raises(ValueError):
        validate_krx_base_url("https://user:pass@krx.test/svc?key=secret")


def test_capability_matrix_keeps_flow_and_sector_breadth_limits_explicit() -> None:
    capabilities = {item.metric: item for item in krx_capability_matrix()}

    assert capabilities["major_indices"].status == "SUPPORTED"
    assert capabilities["common_share_breadth"].status == "PARTIAL"
    assert capabilities["market_wide_investor_flow"].status == "UNSUPPORTED"
    assert capabilities["sector_participation"].status == "PARTIAL"


def test_collect_builds_explicit_common_share_and_segment_breadth(tmp_path: Path) -> None:
    provider, requests = _provider(tmp_path)

    section = asyncio.run(
        provider.collect(session_date=SESSION, expected_session_date=SESSION)
    )

    assert len(requests) == 6
    assert all(request.headers["AUTH_KEY"] == "secret-test-key" for request in requests)
    assert all(request.url.params["basDd"] == "20260814" for request in requests)
    assert section.breadth is not None
    assert section.breadth.eligible_count == 2
    assert section.breadth.advance_count == 1
    assert section.breadth.decline_count == 1
    assert section.breadth.total_trading_value == 15750
    assert section.breadth_by_segment["KOSPI"].advance_count == 1
    assert section.breadth_by_segment["KOSDAQ"].decline_count == 1
    assert section.quality.exclusion_reason_counts == {
        "ineligible_certificate_type": 1,
        "ineligible_security_group": 1,
        "new_listing_no_prior_close": 1,
        "spac": 1,
    }
    assert section.market_flows == []
    assert {item.symbol for item in section.indices} == {
        "KOSPI",
        "KOSPI200",
        "KOSDAQ",
        "KOSDAQ150",
    }
    assert {item.metric_role for item in section.sectors} == {"sector_price_proxy"}


def test_cache_contains_no_key_and_avoids_repeated_network(tmp_path: Path) -> None:
    provider, requests = _provider(tmp_path)

    first = asyncio.run(provider.collect(session_date=SESSION))
    second = asyncio.run(provider.collect(session_date=SESSION))

    assert first == second
    assert len(requests) == 6
    cache_text = "".join(path.read_text() for path in tmp_path.rglob("*.json"))
    assert "secret-test-key" not in cache_text
    assert "AUTH_KEY" not in cache_text


def test_empty_or_duplicate_response_fails_closed(tmp_path: Path) -> None:
    empty = _fixtures()
    empty[KOSPI_DAILY_PATH] = []
    provider, _requests = _provider(tmp_path / "empty", empty)
    with pytest.raises(ValueError, match="no rows"):
        asyncio.run(provider.collect(session_date=SESSION))

    duplicate = _fixtures()
    duplicate[KOSPI_DAILY_PATH] = [
        duplicate[KOSPI_DAILY_PATH][0],
        dict(duplicate[KOSPI_DAILY_PATH][0]),
    ]
    provider, _requests = _provider(tmp_path / "duplicate", duplicate)
    with pytest.raises(ValueError, match="duplicate"):
        asyncio.run(provider.collect(session_date=SESSION))


def test_wrong_response_date_and_expected_session_fail_closed(tmp_path: Path) -> None:
    fixtures = _fixtures()
    fixtures[KOSPI_DAILY_PATH][0]["BAS_DD"] = "20260813"
    provider, _requests = _provider(tmp_path / "wrong-date", fixtures)
    with pytest.raises(ValueError, match="session date mismatch"):
        asyncio.run(provider.collect(session_date=SESSION))

    provider, _requests = _provider(tmp_path / "expected")
    with pytest.raises(ValueError, match="expected XKRX"):
        asyncio.run(
            provider.collect(
                session_date=SESSION,
                expected_session_date=date(2026, 8, 13),
            )
        )


def test_invalid_official_units_are_unavailable_not_zero(tmp_path: Path) -> None:
    fixtures = _fixtures()
    fixtures[KOSPI_DAILY_PATH][0]["FLUC_RT"] = "not-a-number"
    provider, _requests = _provider(tmp_path, fixtures)

    section = asyncio.run(provider.collect(session_date=SESSION))

    assert section.breadth is not None
    assert section.breadth.eligible_count == 1
    assert section.quality.exclusion_reason_counts["official_return_missing"] == 1


def test_listing_date_and_comparable_close_contract_is_fail_closed(
    tmp_path: Path,
) -> None:
    provider, _requests = _provider(tmp_path)
    daily = [
        _daily("200001", "KOSPI", "110", "10", "10.00"),
        _daily("200002", "KOSPI", "110", "10", "10.00"),
        _daily("200003", "KOSPI", "110", "10", "10.00"),
        _daily("200004", "KOSPI", "110", "10", "10.00"),
        _daily("200005", "KOSPI", "100", "100", "0.00"),
    ]
    references = [
        _reference("200001", "KOSPI", listing_date="20260813"),
        _reference("200002", "KOSPI", listing_date="20260814"),
        _reference("200003", "KOSPI", listing_date="20260815"),
        _reference("200004", "KOSPI", listing_date=""),
        _reference("200005", "KOSPI", listing_date="20200101"),
    ]

    rows, exclusions = provider.normalize(
        session_date=SESSION,
        daily_envelopes=[{"rows": daily}],
        reference_envelopes=[{"rows": references}],
    )
    by_ticker = {row.ticker: row for row in rows}

    assert by_ticker["200001"].eligible is True
    assert by_ticker["200001"].previous_close == 100
    assert by_ticker["200002"].eligible is False
    assert by_ticker["200002"].exclusion_reasons == ["new_listing_no_prior_close"]
    assert by_ticker["200003"].exclusion_reasons == ["future_listing"]
    assert by_ticker["200004"].exclusion_reasons == ["listing_date_missing"]
    assert by_ticker["200005"].exclusion_reasons == [
        "missing_comparable_previous_close"
    ]
    assert exclusions == {
        "new_listing_no_prior_close": 1,
        "future_listing": 1,
        "listing_date_missing": 1,
        "missing_comparable_previous_close": 1,
    }


def test_readiness_market_not_completed_does_not_call_provider(tmp_path: Path) -> None:
    provider, requests = _provider(tmp_path)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=date(2026, 8, 18),
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "MARKET_NOT_COMPLETED"
    assert result.current_snapshot_promotable is False
    assert result.endpoints == []
    assert requests == []


def test_readiness_empty_200_is_provider_pending(tmp_path: Path) -> None:
    fixtures = _fixtures()
    for endpoint in (
        KOSPI_DAILY_PATH,
        KOSDAQ_DAILY_PATH,
        KOSPI_INDEX_PATH,
        KOSDAQ_INDEX_PATH,
    ):
        fixtures[endpoint] = []
    provider, requests = _provider(tmp_path, fixtures)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "MARKET_COMPLETED_PROVIDER_PENDING"
    assert result.current_snapshot_promotable is False
    assert {item.status for item in result.endpoints} == {"EMPTY"}
    assert len(requests) == 4


def test_readiness_partial_bundle_is_not_promotable(tmp_path: Path) -> None:
    fixtures = _fixtures()
    fixtures[KOSDAQ_DAILY_PATH] = []
    provider, _requests = _provider(tmp_path, fixtures)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "PROVIDER_PARTIAL"
    assert result.current_snapshot_promotable is False
    assert {item.status for item in result.endpoints} == {"EMPTY", "READY"}


def test_readiness_complete_bundle_is_promotable(tmp_path: Path) -> None:
    provider, _requests = _provider(tmp_path)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "PROVIDER_COMPLETE"
    assert result.current_snapshot_promotable is True
    assert result.first_non_empty_at is not None
    assert result.first_complete_at is not None
    assert result.provider_publication_timestamp is None
    assert {item.status for item in result.endpoints} == {"READY"}


def test_readiness_missing_required_index_identity_is_partial(tmp_path: Path) -> None:
    fixtures = _fixtures()
    fixtures[KOSPI_INDEX_PATH] = [fixtures[KOSPI_INDEX_PATH][0]]
    provider, _requests = _provider(tmp_path, fixtures)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "PROVIDER_PARTIAL"
    kospi = next(item for item in result.endpoints if item.endpoint == KOSPI_INDEX_PATH)
    assert kospi.status == "PARTIAL"
    assert kospi.missing_required_identities == ["KOSPI:코스피 200"]


def test_readiness_stale_provider_date_is_not_promotable(tmp_path: Path) -> None:
    provider, _requests = _provider(tmp_path)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=date(2026, 8, 18),
            latest_completed_session=date(2026, 8, 18),
        )
    )

    assert result.status == "STALE_PROVIDER_DATE"
    assert result.current_snapshot_promotable is False
    assert {item.status for item in result.endpoints} == {"STALE"}


def test_readiness_provider_error_is_distinct_from_pending(tmp_path: Path) -> None:
    provider = KrxKrMarketProvider(
        api_key="test",
        base_url="https://krx.example.test/svc/apis",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(503, json={"error": "unavailable"})
        ),
    )

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
        )
    )

    assert result.status == "PROVIDER_ERROR"
    assert result.current_snapshot_promotable is False
    assert {item.error_code for item in result.endpoints} == {"http_error"}


def test_zero_volume_common_share_stays_in_explicit_unchanged_denominator(
    tmp_path: Path,
) -> None:
    fixtures = _fixtures()
    fixtures[KOSPI_DAILY_PATH][0]["ACC_TRDVOL"] = "0"
    fixtures[KOSPI_DAILY_PATH][0]["CMPPREVDD_PRC"] = "0"
    fixtures[KOSPI_DAILY_PATH][0]["FLUC_RT"] = "0.00"
    provider, _requests = _provider(tmp_path, fixtures)

    section = asyncio.run(provider.collect(session_date=SESSION))

    assert section.breadth_by_segment["KOSPI"].eligible_count == 1
    assert section.breadth_by_segment["KOSPI"].unchanged_count == 1
    assert any("suspension flag" in item for item in section.quality.warnings)


def test_http_error_and_bad_schema_fail_closed(tmp_path: Path) -> None:
    limited = KrxKrMarketProvider(
        api_key="test",
        base_url="https://krx.example.test/svc/apis",
        cache_dir=tmp_path / "limited",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(429, json={"error": "rate limit"})
        ),
    )
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(limited.collect(session_date=SESSION))

    malformed = KrxKrMarketProvider(
        api_key="test",
        base_url="https://krx.example.test/svc/apis",
        cache_dir=tmp_path / "malformed",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"unexpected": []})
        ),
    )
    with pytest.raises(ValueError, match="OutBlock_1"):
        asyncio.run(malformed.collect(session_date=SESSION))


def test_stale_cache_request_date_is_rejected(tmp_path: Path) -> None:
    provider, _requests = _provider(tmp_path)
    path = provider._cache_path(KOSPI_DAILY_PATH, SESSION)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "endpoint": KOSPI_DAILY_PATH,
                "request_date": "2026-08-13",
                "rows": [_fixtures()[KOSPI_DAILY_PATH][0]],
            }
        )
    )

    with pytest.raises(ValueError, match="request date mismatch"):
        asyncio.run(provider.collect(session_date=SESSION))
