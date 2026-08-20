from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone

import httpx

from app.providers.krx_publication_provider import (
    CORE_READINESS_ENDPOINTS,
    KOSDAQ_DAILY_PATH,
    KOSDAQ_INDEX_PATH,
    KOSPI_DAILY_PATH,
    KOSPI_INDEX_PATH,
    KrxPublicationProvider,
)


SESSION = date(2026, 8, 14)
OBSERVED_AT = datetime(2026, 8, 14, 7, 5, tzinfo=timezone.utc)


def _fixtures(session: date = SESSION) -> dict[str, list[dict[str, object]]]:
    business_date = session.strftime("%Y%m%d")
    return {
        KOSPI_DAILY_PATH: [{"BAS_DD": business_date, "ISU_CD": "005930"}],
        KOSDAQ_DAILY_PATH: [{"BAS_DD": business_date, "ISU_CD": "035720"}],
        KOSPI_INDEX_PATH: [
            {"BAS_DD": business_date, "IDX_CLSS": "KOSPI", "IDX_NM": "코스피"},
            {
                "BAS_DD": business_date,
                "IDX_CLSS": "KOSPI",
                "IDX_NM": "코스피 200",
            },
        ],
        KOSDAQ_INDEX_PATH: [
            {"BAS_DD": business_date, "IDX_CLSS": "KOSDAQ", "IDX_NM": "코스닥"},
            {
                "BAS_DD": business_date,
                "IDX_CLSS": "KOSDAQ",
                "IDX_NM": "코스닥 150",
            },
        ],
    }


def _provider(
    fixtures: dict[str, list[dict[str, object]]],
    *,
    status_code: int = 200,
) -> tuple[KrxPublicationProvider, list[str]]:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        endpoint = request.url.path.split("/svc/apis/", 1)[-1]
        requests.append(endpoint)
        return httpx.Response(
            status_code,
            json={"OutBlock_1": fixtures.get(endpoint, [])},
            request=request,
        )

    return (
        KrxPublicationProvider(
            api_key="test",
            base_url="https://krx.example.test/svc/apis",
            transport=httpx.MockTransport(handler),
        ),
        requests,
    )


def test_complete_bundle_requires_all_core_endpoints_and_dates() -> None:
    provider, requests = _provider(_fixtures())

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "PROVIDER_COMPLETE"
    assert result.current_snapshot_promotable is True
    assert result.observed_complete_by == OBSERVED_AT
    assert {item.status for item in result.endpoints} == {"READY"}
    assert all(item.payload_sha256 for item in result.endpoints)
    assert requests == list(CORE_READINESS_ENDPOINTS)


def test_empty_200_bundle_is_pending_not_zero_market_data() -> None:
    provider, requests = _provider({endpoint: [] for endpoint in CORE_READINESS_ENDPOINTS})

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "MARKET_COMPLETED_PROVIDER_PENDING"
    assert result.current_snapshot_promotable is False
    assert {item.status for item in result.endpoints} == {"EMPTY"}
    assert requests == list(CORE_READINESS_ENDPOINTS)


def test_stale_provider_date_fails_closed() -> None:
    provider, _requests = _provider(_fixtures(date(2026, 8, 13)))

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "STALE_PROVIDER_DATE"
    assert {item.status for item in result.endpoints} == {"STALE"}
    assert result.current_snapshot_promotable is False


def test_missing_required_index_identity_is_partial() -> None:
    fixtures = _fixtures()
    fixtures[KOSPI_INDEX_PATH] = fixtures[KOSPI_INDEX_PATH][:1]
    provider, _requests = _provider(fixtures)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "PROVIDER_PARTIAL"
    kospi = next(item for item in result.endpoints if item.endpoint == KOSPI_INDEX_PATH)
    assert kospi.status == "PARTIAL"
    assert kospi.missing_required_identities == ["KOSPI:코스피 200"]


def test_http_error_is_not_provider_pending() -> None:
    provider, _requests = _provider(_fixtures(), status_code=503)

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "PROVIDER_ERROR"
    assert {item.error_code for item in result.endpoints} == {"http_error"}


def test_future_session_makes_no_provider_calls() -> None:
    provider, requests = _provider(_fixtures())

    result = asyncio.run(
        provider.probe_publication_readiness(
            target_session=date(2026, 8, 15),
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "MARKET_NOT_COMPLETED"
    assert requests == []
