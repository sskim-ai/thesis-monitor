from datetime import UTC, date, datetime
import asyncio

import httpx
import pytest
from pydantic import ValidationError

from app.providers.kiwoom_kr_market_provider import (
    KiwoomCapabilityMetric,
    KiwoomKrMarketCapabilities,
    KiwoomKrMarketProvider,
    contains_sensitive_data,
    validate_gateway_url,
)


def test_gateway_url_rejects_query_credentials() -> None:
    with pytest.raises(ValueError):
        validate_gateway_url("https://user:pass@gateway.test/path?token=secret")


def test_sensitive_account_fields_are_detected_recursively() -> None:
    assert contains_sensitive_data({"indices": [], "meta": {"account_number": "123"}})
    assert not contains_sensitive_data({"indices": [], "provider": "kiwoom"})


def test_supported_metric_requires_koa_tr_evidence() -> None:
    with pytest.raises(ValidationError):
        KiwoomCapabilityMetric(
            metric="market_breadth",
            status="SUPPORTED",
            request_scope="market_summary",
            verified_in_koa_studio=False,
            denominator_semantics_verified=True,
        )


def test_per_ticker_only_contract_is_not_an_efficient_bridge() -> None:
    capabilities = KiwoomKrMarketCapabilities(
        captured_at=datetime(2026, 8, 17, tzinfo=UTC),
        gateway_platform="Windows OCX gateway",
        source="gateway_fixture",
        metrics=[
            KiwoomCapabilityMetric(
                metric="all_stock_multirow",
                status="PARTIAL",
                tr_or_function="CommKwRqData",
                request_scope="all_stock_multirow",
                verified_in_koa_studio=False,
                notes=["documented function; production row/page bounds unverified"],
            )
        ],
    )

    assert capabilities.efficient_breadth_supported is False


def test_gateway_rejects_sensitive_response_before_snapshot_use() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Gateway-API-Key"] == "gateway-secret"
        return httpx.Response(200, json={"account_number": "forbidden"})

    provider = KiwoomKrMarketProvider(
        gateway_url="https://gateway.test",
        api_key="gateway-secret",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ValueError, match="sensitive"):
        asyncio.run(provider.capabilities())


def test_partial_capability_blocks_snapshot_request() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "contract_version": "kiwoom-kr-market-gateway-v1",
                "captured_at": "2026-08-17T00:00:00Z",
                "gateway_platform": "Windows OCX gateway",
                "source": "gateway_fixture",
                "metrics": [
                    {
                        "metric": "market_breadth",
                        "status": "PARTIAL",
                        "request_scope": "market_summary",
                        "verified_in_koa_studio": False,
                        "denominator_semantics_verified": False,
                    }
                ],
                "account_data_exposed": False,
            },
        )

    provider = KiwoomKrMarketProvider(
        gateway_url="https://gateway.test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(RuntimeError, match="not verified"):
        asyncio.run(provider.collect(date(2026, 8, 14)))
    assert calls == ["/v1/kr-market/capabilities"]


def test_supported_direct_summary_normalizes_verified_snapshot() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("capabilities"):
            return httpx.Response(
                200,
                json={
                    "contract_version": "kiwoom-kr-market-gateway-v1",
                    "captured_at": "2026-08-17T00:00:00Z",
                    "gateway_platform": "Windows OCX gateway",
                    "source": "gateway_fixture",
                    "metrics": [
                        {
                            "metric": "market_breadth",
                            "status": "SUPPORTED",
                            "tr_or_function": "fixture_summary_tr",
                            "request_scope": "market_summary",
                            "verified_in_koa_studio": True,
                            "denominator_semantics_verified": True,
                        }
                    ],
                    "account_data_exposed": False,
                },
            )
        assert request.url.params["date"] == "2026-08-14"
        return httpx.Response(
            200,
            json={
                "contract_version": "kiwoom-kr-market-gateway-v1",
                "session_date": "2026-08-14",
                "as_of": "2026-08-14T15:31:00+09:00",
                "source": "kiwoom",
                "quality": "verified",
                "universe_version": "kiwoom-common-equity-v1",
                "indices": [],
                "breadth": {
                    "eligible_count": 3,
                    "advance_count": 1,
                    "decline_count": 1,
                    "unchanged_count": 1,
                    "advance_ratio": 0.3333333333,
                    "ad_ratio": 1.0,
                    "median_return_pct": 0.0,
                    "equal_weight_return_pct": 0.0,
                    "positive_return_pct": 33.33333333,
                    "negative_return_pct": 33.33333333,
                    "total_trading_volume": 1000,
                    "total_trading_value": 2000000,
                },
                "source_payload_sha256": "a" * 64,
            },
        )

    provider = KiwoomKrMarketProvider(
        gateway_url="https://gateway.test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    section = asyncio.run(provider.collect(date(2026, 8, 14)))

    assert section.market == "KR"
    assert section.quality.provider_role == "bridge_shadow"
    assert section.breadth is not None
    assert section.breadth.eligible_count == 3


def test_gateway_timeout_is_not_reclassified_as_supported() -> None:
    provider = KiwoomKrMarketProvider(
        gateway_url="https://gateway.test",
        api_key="secret",
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(httpx.ConnectTimeout("timeout", request=request))
        ),
    )

    with pytest.raises(httpx.ConnectTimeout):
        asyncio.run(provider.capabilities())
