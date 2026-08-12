import asyncio
from datetime import date, datetime, timezone
import json
from urllib.parse import parse_qs

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.jobs.probe_krx_night_futures import (
    KRX_FUTURES_DAILY_URL,
    fetch_live_probe,
    parse_krx_futures_payload,
)
from app.macro.providers.krx import KrxNightFuturesProvider
from app.macro.storage import persist_observation


def _row(
    product: str,
    session: str,
    contract: str,
    name: str,
    close: str,
    business_date: str = "20260811",
) -> dict[str, str]:
    return {
        "BAS_DD": business_date,
        "PROD_NM": product,
        "MKT_NM": session,
        "ISU_CD": contract,
        "ISU_NM": name,
        "TDD_CLSPRC": close,
        "CMPPREVDD_PRC": "0",
        "ACC_TRDVOL": "1000",
        "ACC_OPNINT_QTY": "500",
    }


def test_same_contract_regular_and_night_rows_produce_verified_changes() -> None:
    result = parse_krx_futures_payload(
        {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "KR4101V60003", "코스피200 F 202609", "428.35"),
                _row("KOSPI 200 선물", "야간", "KR4101V60003", "코스피200 F 202609 야간", "431.20"),
                _row("KOSDAQ 150 선물", "정규", "KR4201V60001", "코스닥150 F 202609", "1335.20"),
                _row("KOSDAQ 150 선물", "야간", "KR4201V60001", "코스닥150 F 202609 야간", "1331.00"),
            ]
        }
    )

    assert result.night_session_usable is True
    assert result.source_date == date(2026, 8, 11)
    by_product = {item.product: item for item in result.observations}
    assert by_product["KOSPI200"].contract_code == "KR4101V60003"
    assert by_product["KOSPI200"].point_change == 2.85
    assert by_product["KOSPI200"].change_pct == pytest.approx(0.66534376)
    assert by_product["KOSDAQ150"].point_change == -4.2


def test_rows_without_explicit_session_are_not_inferred() -> None:
    rows = [
        _row("KOSPI 200 선물", "", "A", "코스피200 F 202609", "428.35"),
        _row("KOSPI 200 선물", "", "A", "코스피200 F 202609", "431.20"),
    ]

    result = parse_krx_futures_payload({"OutBlock_1": rows})

    assert result.night_session_usable is False
    assert result.observations == []


def test_contract_mismatch_is_not_compared() -> None:
    result = parse_krx_futures_payload(
        {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428.35"),
                _row("KOSPI 200 선물", "야간", "DEC", "코스피200 F 202612 야간", "431.20"),
            ]
        }
    )

    assert result.night_session_usable is False


def test_roll_selection_uses_nearest_complete_expiry_not_volume() -> None:
    rows = [
        _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428"),
        _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429"),
        _row("KOSPI 200 선물", "정규", "DEC", "코스피200 F 202612", "430"),
        _row("KOSPI 200 선물", "야간", "DEC", "코스피200 F 202612 야간", "435"),
    ]
    rows[2]["ACC_TRDVOL"] = "9999999"
    rows[3]["ACC_TRDVOL"] = "9999999"

    result = parse_krx_futures_payload({"OutBlock_1": rows})

    assert result.observations[0].contract_code == "SEP"


def test_partial_and_stale_source_preserve_only_verified_product_and_date() -> None:
    result = parse_krx_futures_payload(
        {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428", "20260808"),
                _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429", "20260808"),
                _row("KOSDAQ 150 선물", "정규", "QSEP", "코스닥150 F 202609", "1330", "20260808"),
            ]
        }
    )

    assert result.night_session_usable is True
    assert result.source_date == date(2026, 8, 8)
    assert [item.product for item in result.observations] == ["KOSPI200"]


def test_maturity_must_be_explicitly_interpretable() -> None:
    result = parse_krx_futures_payload(
        {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "A", "코스피200 최근월", "428"),
                _row("KOSPI 200 선물", "야간", "A", "코스피200 최근월 야간", "429"),
            ]
        }
    )

    assert result.night_session_usable is False


def test_live_probe_uses_auth_header_and_never_query_string_for_secret() -> None:
    secret = "test-secret-key"
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428"),
                _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429"),
            ]
        }
        return httpx.Response(200, json=payload)

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key=secret,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result.night_session_usable is True
    assert len(requests) == 1
    assert requests[0].headers["AUTH_KEY"] == secret
    assert str(requests[0].url).startswith(KRX_FUTURES_DAILY_URL)
    assert secret not in str(requests[0].url)
    assert parse_qs(requests[0].url.query.decode())["basDd"] == ["20260812"]
    assert secret not in json.dumps(result.model_dump(mode="json"))


def test_missing_key_is_not_configured_without_http_request() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    result = asyncio.run(
        fetch_live_probe(api_key="", transport=httpx.MockTransport(handler))
    )

    assert result.status == "not_configured"
    assert calls == 0


def test_provider_preserves_same_contract_regular_close_as_comparison(monkeypatch) -> None:
    probe = parse_krx_futures_payload(
        {
            "OutBlock_1": [
                _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "989.80"),
                _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "974.95"),
            ]
        }
    )

    async def fake_probe(**kwargs):
        return probe

    monkeypatch.setattr("app.macro.providers.krx.fetch_live_probe", fake_probe)
    provider_result = asyncio.run(
        KrxNightFuturesProvider().collect(
            datetime(2026, 8, 11, 22, 50, tzinfo=timezone.utc)
        )
    )
    observation = provider_result.observations[0]
    assert observation.series_code == "KRX_KOSPI200_NIGHT_FUT"
    assert observation.previous_value == 989.8
    assert observation.value == 974.95
    assert observation.change_value == -14.85

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        row, created = persist_observation(
            session,
            provider_result.provider,
            observation,
            datetime(2026, 8, 11, 22, 50, tzinfo=timezone.utc),
        )

    assert created is True
    assert row.previous_value == 989.8
    assert row.change_value == -14.85
    assert row.change_pct == pytest.approx(-1.50030309)
