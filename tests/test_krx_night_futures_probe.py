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
    expected_latest_completed_krx_session,
    fetch_live_probe,
    parse_krx_futures_payload,
    parse_krx_futures_payloads,
)
from app.macro.providers.krx import KrxNightFuturesProvider
from app.macro.providers.base import CollectedObservation
from app.macro.storage import persist_observation
from app.services.market_session import preceding_exchange_session_date


def _row(
    product: str,
    session: str,
    contract: str,
    name: str,
    close: str,
    business_date: str = "20260811",
    provider_change: str | None = None,
) -> dict[str, str]:
    return {
        "BAS_DD": business_date,
        "PROD_NM": product,
        "MKT_NM": session,
        "ISU_CD": contract,
        "ISU_NM": name,
        "TDD_CLSPRC": close,
        "CMPPREVDD_PRC": provider_change or "",
        "ACC_TRDVOL": "1000",
        "ACC_OPNINT_QTY": "500",
    }


@pytest.mark.parametrize(
    ("session_date", "expected_reference"),
    [
        (date(2026, 8, 14), date(2026, 8, 13)),
        (date(2026, 8, 15), date(2026, 8, 14)),
        (date(2026, 8, 17), date(2026, 8, 14)),
        (date(2026, 8, 18), date(2026, 8, 14)),
    ],
)
def test_preceding_xkrx_session_traverses_weekends_and_holidays(
    session_date: date,
    expected_reference: date,
) -> None:
    assert preceding_exchange_session_date("XKRX", session_date) == expected_reference


def test_holiday_aware_pair_uses_preceding_eligible_day_for_both_products() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 14): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "A0169000",
                        "코스피200 F 202609",
                        "1098.90",
                        "20260814",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "정규",
                        "A0669000",
                        "코스닥150 F 202609",
                        "1487.50",
                        "20260814",
                    ),
                ]
            },
            date(2026, 8, 18): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "A0169000",
                        "코스피200 F 202609 야간",
                        "1094.95",
                        "20260818",
                        "-3.95",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "야간",
                        "A0669000",
                        "코스닥150 F 202609 야간",
                        "1477.30",
                        "20260818",
                        "-10.20",
                    ),
                ]
            },
        }
    )

    assert result.night_session_usable is True
    assert result.source_date == date(2026, 8, 18)
    by_product = {item.product: item for item in result.observations}
    kospi = by_product["KOSPI200"]
    kosdaq = by_product["KOSDAQ150"]
    assert kospi.reference_date == date(2026, 8, 14)
    assert kospi.contract_code == "A0169000"
    assert kospi.point_change == -3.95
    assert kospi.change_pct == pytest.approx(-0.35945036)
    assert kospi.provider_change_point == -3.95
    assert kospi.provider_change_match is True
    assert kosdaq.reference_date == date(2026, 8, 14)
    assert kosdaq.contract_code == "A0669000"
    assert kosdaq.point_change == -10.20
    assert kosdaq.change_pct == pytest.approx(-0.68571429)
    assert kosdaq.provider_change_match is True
    assert "source_timestamp" not in kospi.model_dump()
    assert "night_timestamp" not in kospi.model_dump()


def test_regular_preceding_session_control_uses_august_13_for_august_14() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 13): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "A0169000",
                        "코스피200 F 202609",
                        "1073.70",
                        "20260813",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "정규",
                        "A0669000",
                        "코스닥150 F 202609",
                        "1500.00",
                        "20260813",
                    ),
                ]
            },
            date(2026, 8, 14): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "A0169000",
                        "코스피200 F 202609 야간",
                        "1095.40",
                        "20260814",
                        "+21.70",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "야간",
                        "A0669000",
                        "코스닥150 F 202609 야간",
                        "1512.30",
                        "20260814",
                        "+12.30",
                    ),
                ]
            },
        }
    )

    assert result.night_session_usable is True
    by_product = {item.product: item for item in result.observations}
    assert by_product["KOSPI200"].reference_date == date(2026, 8, 13)
    assert by_product["KOSPI200"].point_change == 21.70
    assert by_product["KOSDAQ150"].reference_date == date(2026, 8, 13)
    assert by_product["KOSDAQ150"].point_change == 12.30


def test_provider_change_conflict_is_fail_closed() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 14): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "A0169000",
                        "코스피200 F 202609",
                        "1098.90",
                        "20260814",
                    )
                ]
            },
            date(2026, 8, 18): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "A0169000",
                        "코스피200 F 202609 야간",
                        "1094.95",
                        "20260818",
                        "+16.70",
                    )
                ]
            },
        }
    )

    assert result.night_session_usable is False
    assert result.observations == []
    assert any("provider change conflicts" in item for item in result.warnings)


def test_current_empty_does_not_promote_older_holiday_pair_as_fresh() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        if target == "20260818":
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "A0169000",
                    "코스피200 F 202609 야간",
                    "1094.95",
                    target,
                    "-3.95",
                )
            ]
        elif target == "20260814":
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "A0169000",
                    "코스피200 F 202609",
                    "1098.90",
                    target,
                )
            ]
        else:
            rows = []
        return httpx.Response(200, json={"OutBlock_1": rows})

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 19),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert result.source_date == date(2026, 8, 18)
    assert result.expected_latest_session_date == date(2026, 8, 19)
    assert result.session_freshness == "stale"
    assert result.observations[0].reference_date == date(2026, 8, 14)


def test_future_day_row_cannot_be_used_as_night_reference() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 18): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "A0169000",
                        "코스피200 F 202609 야간",
                        "1094.95",
                        "20260818",
                    )
                ]
            },
            date(2026, 8, 19): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "A0169000",
                        "코스피200 F 202609",
                        "1098.90",
                        "20260819",
                    )
                ]
            },
        }
    )

    assert result.night_session_usable is False
    assert result.observations == []


def test_same_business_date_day_and_night_rows_are_not_compared() -> None:
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

    assert result.night_session_usable is False
    assert result.observations == []
    assert result.reason == "night_reference_session_or_contract_identity_not_verifiable"


def test_preceding_day_same_contract_rows_produce_verified_changes() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 10): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "KR4101V60003",
                        "코스피200 F 202609",
                        "428.35",
                        "20260810",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "정규",
                        "KR4201V60001",
                        "코스닥150 F 202609",
                        "1335.20",
                        "20260810",
                    ),
                ]
            },
            date(2026, 8, 11): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "KR4101V60003",
                        "코스피200 F 202609 야간",
                        "431.20",
                        "20260811",
                    ),
                    _row(
                        "KOSDAQ 150 선물",
                        "야간",
                        "KR4201V60001",
                        "코스닥150 F 202609 야간",
                        "1331.00",
                        "20260811",
                    ),
                ]
            },
        }
    )

    assert result.night_session_usable is True
    assert result.source_date == date(2026, 8, 11)
    by_product = {item.product: item for item in result.observations}
    assert by_product["KOSPI200"].contract_code == "KR4101V60003"
    assert by_product["KOSPI200"].point_change == 2.85
    assert by_product["KOSPI200"].change_pct == pytest.approx(0.66534376)
    assert by_product["KOSDAQ150"].point_change == -4.2


def test_zero_reference_price_is_not_promoted() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 10): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "SEP",
                        "코스피200 F 202609",
                        "0",
                        "20260810",
                    )
                ]
            },
            date(2026, 8, 11): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "SEP",
                        "코스피200 F 202609 야간",
                        "431.20",
                        "20260811",
                    )
                ]
            },
        }
    )

    assert result.night_session_usable is False
    assert result.observations == []


def test_rows_without_explicit_session_are_not_inferred() -> None:
    rows = [
        _row("KOSPI 200 선물", "", "A", "코스피200 F 202609", "428.35"),
        _row("KOSPI 200 선물", "", "A", "코스피200 F 202609", "431.20"),
    ]

    result = parse_krx_futures_payload({"OutBlock_1": rows})

    assert result.night_session_usable is False
    assert result.observations == []


def test_contract_mismatch_is_not_compared() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 10): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "SEP",
                        "코스피200 F 202609",
                        "428.35",
                        "20260810",
                    )
                ]
            },
            date(2026, 8, 11): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "DEC",
                        "코스피200 F 202612 야간",
                        "431.20",
                        "20260811",
                    )
                ]
            },
        }
    )

    assert result.night_session_usable is False


def test_roll_selection_uses_nearest_complete_expiry_not_volume() -> None:
    day_rows = [
        _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428", "20260810"),
        _row("KOSPI 200 선물", "정규", "DEC", "코스피200 F 202612", "430", "20260810"),
    ]
    night_rows = [
        _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429", "20260811"),
        _row("KOSPI 200 선물", "야간", "DEC", "코스피200 F 202612 야간", "435", "20260811"),
    ]
    day_rows[1]["ACC_TRDVOL"] = "9999999"
    night_rows[1]["ACC_TRDVOL"] = "9999999"

    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 10): {"OutBlock_1": day_rows},
            date(2026, 8, 11): {"OutBlock_1": night_rows},
        }
    )

    assert result.observations[0].contract_code == "SEP"


def test_partial_and_stale_source_preserve_only_verified_product_and_date() -> None:
    result = parse_krx_futures_payloads(
        {
            date(2026, 8, 7): {
                "OutBlock_1": [
                    _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428", "20260807"),
                    _row("KOSDAQ 150 선물", "정규", "QSEP", "코스닥150 F 202609", "1330", "20260807"),
                ]
            },
            date(2026, 8, 8): {
                "OutBlock_1": [
                    _row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429", "20260808")
                ]
            },
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
        target = request.url.params["basDd"]
        rows = (
            [_row("KOSPI 200 선물", "야간", "SEP", "코스피200 F 202609 야간", "429", target)]
            if target == "20260812"
            else [_row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428", target)]
        )
        payload = {"OutBlock_1": rows}
        return httpx.Response(200, json=payload)

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key=secret,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result.night_session_usable is True
    assert len(requests) == 2
    assert requests[0].headers["AUTH_KEY"] == secret
    assert str(requests[0].url).startswith(KRX_FUTURES_DAILY_URL)
    assert secret not in str(requests[0].url)
    assert [parse_qs(item.url.query.decode())["basDd"] for item in requests] == [
        ["20260812"],
        ["20260811"],
    ]
    assert secret not in json.dumps(result.model_dump(mode="json"))


def test_live_probe_continues_past_nonempty_unusable_date() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        target = request.url.params["basDd"]
        if target == "20260812":
            return httpx.Response(
                200,
                json={
                    "OutBlock_1": [
                        _row(
                            "KOSPI 200 선물",
                            "야간",
                            "SEP",
                            "코스피200 F 202609 야간",
                            "429",
                            "20260812",
                        )
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "OutBlock_1": [
                    _row("KOSPI 200 선물", "정규", "SEP", "코스피200 F 202609", "428"),
                    _row(
                        "KOSDAQ 150 선물",
                        "정규",
                        "QSEP",
                        "코스닥150 F 202609",
                        "1330",
                    ),
                ]
            },
        )

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert [request.url.params["basDd"] for request in requests] == [
        "20260812",
        "20260811",
    ]
    assert result.night_session_usable is True
    assert result.source_date == date(2026, 8, 12)
    assert result.queried_dates == [date(2026, 8, 12), date(2026, 8, 11)]
    assert not any("2026-08-12: rows present" in item for item in result.warnings)


def test_newer_market_rows_make_older_verified_pair_stale() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        if target == "20260813":
            rows = []
        elif target == "20260812":
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
        else:
            rows = (
                [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "SEP",
                        "코스피200 F 202609 야간",
                        "429",
                        target,
                    )
                ]
                if target == "20260811"
                else [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "SEP",
                        "코스피200 F 202609",
                        "428",
                        target,
                    )
                ]
            )
        return httpx.Response(200, json={"OutBlock_1": rows})

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 13),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert result.source_date == date(2026, 8, 11)
    assert result.expected_latest_session_date == date(2026, 8, 13)
    assert result.session_freshness == "stale"
    assert [item.result for item in result.date_statuses] == [
        "empty",
        "rows_without_verified_pair",
        "verified_pair",
        "rows_without_verified_pair",
    ]


def test_empty_expected_business_date_is_refresh_due_not_a_holiday() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        rows = (
            [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "SEP",
                    "코스피200 F 202609 야간",
                    "429",
                    target,
                )
            ]
            if target == "20260811"
            else [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
            if target == "20260810"
            else []
        )
        return httpx.Response(200, json={"OutBlock_1": rows})

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 13),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert expected_latest_completed_krx_session(date(2026, 8, 13)) == date(2026, 8, 13)
    assert result.source_date == date(2026, 8, 11)
    assert result.expected_latest_session_date == date(2026, 8, 13)
    assert result.session_freshness == "stale"


@pytest.mark.parametrize(
    ("run_date", "source_date"),
    [
        (date(2026, 8, 10), date(2026, 8, 8)),
        (date(2026, 8, 18), date(2026, 8, 15)),
    ],
)
def test_empty_weekend_or_holiday_dates_keep_latest_verified_session_fresh(
    run_date: date,
    source_date: date,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        rows = (
            [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "SEP",
                    "코스피200 F 202609 야간",
                    "429",
                    target,
                )
            ]
            if target == source_date.strftime("%Y%m%d")
            else [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
            if target == (source_date - date.resolution).strftime("%Y%m%d")
            else []
        )
        return httpx.Response(200, json={"OutBlock_1": rows})

    result = asyncio.run(
        fetch_live_probe(
            run_date=run_date,
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert expected_latest_completed_krx_session(run_date) == source_date
    assert result.source_date == source_date
    assert result.expected_latest_session_date == source_date
    assert result.session_freshness == "fresh"


def test_live_probe_prefers_fresh_partial_over_older_full_result() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        target = request.url.params["basDd"]
        rows = (
            [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "SEP",
                    "코스피200 F 202609 야간",
                    "429",
                    target,
                )
            ]
            if target == "20260812"
            else [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                ),
                _row(
                    "KOSDAQ 150 선물",
                    "정규",
                    "QSEP",
                    "코스닥150 F 202609",
                    "1330",
                    target,
                ),
            ]
        )
        return httpx.Response(
            200,
            json={"OutBlock_1": rows},
        )

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )
    )

    assert len(requests) == 2
    assert result.source_date == date(2026, 8, 12)
    assert [item.product for item in result.observations] == ["KOSPI200"]


def test_live_probe_tracks_multiple_unusable_dates_before_verified_pair() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        if target == "20260812":
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
        elif target == "20260811":
            rows = [
                _row("KOSPI 200 선물", "정규", "A", "코스피200 최근월", "428", target),
                _row("KOSPI 200 선물", "야간", "A", "코스피200 최근월 야간", "429", target),
            ]
        elif target == "20260810":
            rows = []
        elif target == "20260809":
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "SEP",
                    "코스피200 F 202609 야간",
                    "429",
                    target,
                ),
            ]
        else:
            rows = [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
        return httpx.Response(200, json={"OutBlock_1": rows})

    result = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
            max_lookback_days=6,
        )
    )

    assert result.source_date == date(2026, 8, 9)
    assert result.queried_dates == [
        date(2026, 8, 12),
        date(2026, 8, 11),
        date(2026, 8, 10),
        date(2026, 8, 9),
        date(2026, 8, 8),
        date(2026, 8, 7),
    ]
    assert sum("rows present" in item for item in result.warnings) == 3


def test_live_probe_distinguishes_all_nonempty_unusable_from_all_empty() -> None:
    def unusable_handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        return httpx.Response(
            200,
            json={
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "SEP",
                        "코스피200 F 202609",
                        "428",
                        target,
                    )
                ]
            },
        )

    unusable = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key="dummy",
            transport=httpx.MockTransport(unusable_handler),
            max_lookback_days=3,
        )
    )
    empty = asyncio.run(
        fetch_live_probe(
            run_date=date(2026, 8, 12),
            api_key="dummy",
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, json={"OutBlock_1": []})
            ),
            max_lookback_days=3,
        )
    )

    assert unusable.night_session_usable is False
    assert unusable.observations == []
    assert unusable.reason == "no_recent_verified_night_reference_pair"
    assert unusable.row_count == 3
    assert len(unusable.queried_dates) == 3
    assert empty.reason == "no_recent_business_date_data"
    assert empty.row_count == 0


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
    probe = parse_krx_futures_payloads(
        {
            date(2026, 8, 10): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "정규",
                        "SEP",
                        "코스피200 F 202609",
                        "989.80",
                        "20260810",
                    )
                ]
            },
            date(2026, 8, 11): {
                "OutBlock_1": [
                    _row(
                        "KOSPI 200 선물",
                        "야간",
                        "SEP",
                        "코스피200 F 202609 야간",
                        "974.95",
                        "20260811",
                    )
                ]
            },
        }
    )
    probe.expected_latest_session_date = date(2026, 8, 11)
    probe.session_freshness = "fresh"

    async def fake_probe(**kwargs):
        return probe

    monkeypatch.setattr("app.macro.providers.krx.fetch_live_probe", fake_probe)
    provider_result = asyncio.run(
        KrxNightFuturesProvider().collect(
            datetime(2026, 8, 11, 22, 50, tzinfo=timezone.utc)
        )
    )
    assert len(provider_result.observations) == 1
    observation = provider_result.observations[0]
    assert observation.series_code == "KRX_KOSPI200_NIGHT_FUT"
    assert observation.previous_value == 989.8
    assert observation.value == 974.95
    assert observation.change_value == -14.85
    assert observation.quality_status == "fresh"
    assert observation.raw_payload["trade_date"] == "2026-08-11"
    assert observation.raw_payload["reference_date"] == "2026-08-10"
    assert observation.raw_payload["session_type"] == "NIGHT"
    assert observation.raw_payload["reference_session"] == "DAY"
    assert observation.raw_payload["expected_latest_session_date"] == "2026-08-11"

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
    assert row.quality_status == "fresh"


def test_provider_marks_older_pair_stale_and_storage_refreshes_existing_quality(
    monkeypatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        target = request.url.params["basDd"]
        rows = (
            [
                _row(
                    "KOSPI 200 선물",
                    "정규",
                    "SEP",
                    "코스피200 F 202609",
                    "428",
                    target,
                )
            ]
            if target in {"20260812", "20260810"}
            else [
                _row(
                    "KOSPI 200 선물",
                    "야간",
                    "SEP",
                    "코스피200 F 202609 야간",
                    "429",
                    target,
                )
            ]
            if target == "20260811"
            else []
        )
        return httpx.Response(200, json={"OutBlock_1": rows})

    async def fake_probe(**kwargs):
        return await fetch_live_probe(
            run_date=date(2026, 8, 13),
            api_key="dummy",
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("app.macro.providers.krx.fetch_live_probe", fake_probe)
    provider_result = asyncio.run(
        KrxNightFuturesProvider().collect(
            datetime(2026, 8, 12, 22, 50, tzinfo=timezone.utc)
        )
    )

    assert provider_result.observations[0].quality_status == "stale"
    assert (
        provider_result.observations[0].raw_payload["expected_latest_session_date"]
        == "2026-08-13"
    )
    assert provider_result.warnings

    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    stale = provider_result.observations[0]
    fresh = CollectedObservation(
        series_code="KRX_KOSPI200_NIGHT_FUT",
        category="kr_night_futures",
        observed_at=stale.observed_at,
        value=429,
        source_url=KRX_FUTURES_DAILY_URL,
        quality_status="fresh",
        raw_payload={"session_freshness": "fresh"},
    )
    with Session(isolated_engine) as session:
        first, created = persist_observation(
            session,
            provider_result.provider,
            fresh,
            datetime(2026, 8, 12, 22, 40, tzinfo=timezone.utc),
        )
        updated, created_again = persist_observation(
            session,
            provider_result.provider,
            stale,
            datetime(2026, 8, 12, 22, 50, tzinfo=timezone.utc),
        )

    assert created is True
    assert created_again is False
    assert first.id == updated.id
    assert updated.quality_status == "stale"
    assert json.loads(updated.raw_payload)["session_freshness"] == "stale"
