from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import date, datetime
import json
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.providers.kiwoom_rest_client import KiwoomRestClient, KiwoomRestError
from app.services.kiwoom_kr_market_context_service import (
    KA10051_AMOUNT_UNIT_KRW,
    KA10066_AMOUNT_UNIT_KRW,
    KiwoomKrMarketContextService,
    collect_and_persist_kiwoom_market_context,
)
from app.services.market_context_adapter_service import KrMarketContextAdapter
from app.services.market_intelligence_service import build_market_intelligence


KST = ZoneInfo("Asia/Seoul")
SESSION_DATE = date(2026, 8, 25)
OBSERVED_AT = datetime(2026, 8, 25, 17, 0, tzinfo=KST)


def _sector_rows(market_code: str) -> list[dict[str, str]]:
    composite = {
        "001": {
            "stk_cd": "001",
            "stk_nm": "종합(KOSPI)",
            "cur_prc": "+6742.74",
            "flu_rt": "+0.68",
            "rising": "647",
            "fall": "226",
            "stdns": "34",
            "upl": "2",
            "lst": "1",
            "flo_stk_num": "944",
        },
        "101": {
            "stk_cd": "101",
            "stk_nm": "종합(KOSDAQ)",
            "cur_prc": "+827.15",
            "flu_rt": "+1.70",
            "rising": "1186",
            "fall": "466",
            "stdns": "74",
            "upl": "4",
            "lst": "0",
            "flo_stk_num": "1824",
        },
    }[market_code]
    if market_code == "101":
        return [
            composite,
            {
                "stk_cd": "106",
                "stk_nm": "제조",
                "cur_prc": "+2787.60",
                "flu_rt": "+2.44",
                "rising": "745",
                "fall": "276",
                "stdns": "40",
                "upl": "0",
                "lst": "0",
                "flo_stk_num": "1120",
            },
        ]
    return [
        composite,
        *[
            {
                "stk_cd": code,
                "stk_nm": name,
                "cur_prc": value,
                "flu_rt": change,
                "rising": rising,
                "fall": fall,
                "stdns": unchanged,
                "upl": "0",
                "lst": "0",
                "flo_stk_num": listed,
            }
            for code, name, value, change, rising, fall, unchanged, listed in (
                ("002", "대형주", "+7365.32", "+0.62", "70", "27", "3", "100"),
                ("003", "중형주", "+4063.06", "+1.37", "128", "61", "6", "198"),
                ("004", "소형주", "+2385.23", "+1.54", "380", "101", "17", "529"),
                ("008", "기계", "+1045.00", "+1.10", "20", "10", "1", "35"),
            )
        ],
    ]


def _current(market_code: str) -> dict[str, object]:
    return dict(_sector_rows(market_code)[0])


def _history(market_code: str) -> dict[str, object]:
    current = _sector_rows(market_code)[0]
    return {
        "inds_cur_prc_daly_rept": [
            {
                "dt_n": "20260825",
                "cur_prc_n": current["cur_prc"],
                "flu_rt_n": current["flu_rt"],
            }
        ]
    }


def _aggregate(market_code: str) -> dict[str, object]:
    if market_code == "001":
        values = ("-40", "+12", "+10")
        name = "종합(KOSPI)"
    else:
        values = ("+13", "+2", "-15")
        name = "종합(KOSDAQ)"
    foreign, institution, retail = values
    return {
        "inds_netprps": [
            {
                "inds_cd": f"{market_code}_AL",
                "inds_nm": name,
                "frgnr_netprps": foreign,
                "orgn_netprps": institution,
                "ind_netprps": retail,
            }
        ]
    }


def _stock_rows(market_code: str, page: int) -> list[dict[str, str]]:
    values = {
        "001": (
            ("000001_AL", "A", "-2500", "+800", "+600"),
            ("000002_AL", "B", "-1500", "+400", "+400"),
        ),
        "101": (
            ("100001_AL", "C", "+800", "+120", "-900"),
            ("100002_AL", "D", "+500", "+80", "-600"),
        ),
    }[market_code]
    code, name, foreign, institution, retail = values[page - 1]
    return [
        {
            "stk_cd": code,
            "stk_nm": name,
            "frgnr_invsr": foreign,
            "orgn": institution,
            "ind_invsr": retail,
        }
    ]


def _handler(
    requests: list[dict[str, object]],
    *,
    duplicate: bool = False,
    missing_next_key: bool = False,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/token":
            return httpx.Response(
                200,
                json={
                    "return_code": 0,
                    "token": "test-access-token",
                    "expires_dt": "20270825235959",
                },
            )
        body = json.loads(request.content)
        api_id = request.headers["api-id"]
        requests.append(
            {
                "api_id": api_id,
                "body": body,
                "cont_yn": request.headers.get("cont-yn"),
                "authorization_present": bool(request.headers.get("authorization")),
            }
        )
        if api_id == "ka20001":
            code = str(body["inds_cd"])
            return httpx.Response(200, json={**_current(code), "return_code": 0})
        if api_id == "ka20003":
            return httpx.Response(
                200,
                json={"all_inds_idex": _sector_rows(str(body["inds_cd"])), "return_code": 0},
            )
        if api_id == "ka20009":
            return httpx.Response(
                200,
                json={**_history(str(body["inds_cd"])), "return_code": 0},
            )
        if api_id == "ka10051":
            code = "001" if body["mrkt_tp"] == "0" else "101"
            return httpx.Response(200, json={**_aggregate(code), "return_code": 0})
        if api_id != "ka10066":
            raise AssertionError(api_id)
        code = str(body["mrkt_tp"])
        second_page = request.headers.get("cont-yn") == "Y"
        rows = _stock_rows(code, 2 if second_page else 1)
        if duplicate and second_page:
            rows[0]["stk_cd"] = _stock_rows(code, 1)[0]["stk_cd"].removesuffix("_AL")
        headers = {}
        if not second_page:
            headers["cont-yn"] = "Y"
            if not missing_next_key:
                headers["next-key"] = f"next-{code}"
        return httpx.Response(
            200,
            headers=headers,
            json={"opaf_invsr_trde": rows, "return_code": 0},
        )

    return httpx.MockTransport(handler)


def _service(
    requests: list[dict[str, object]],
    *,
    duplicate: bool = False,
    missing_next_key: bool = False,
) -> KiwoomKrMarketContextService:
    client = KiwoomRestClient(
        app_key="app-key",
        secret_key="secret-key",
        base_url="https://api.kiwoom.test",
        request_interval_seconds=0,
        transport=_handler(
            requests,
            duplicate=duplicate,
            missing_next_key=missing_next_key,
        ),
    )
    return KiwoomKrMarketContextService(client, max_pages=5)


def test_official_tr_contract_normalizes_breadth_size_and_flow() -> None:
    requests: list[dict[str, object]] = []
    collection = asyncio.run(
        _service(requests).collect(
            session_date=SESSION_DATE,
            observed_at=OBSERVED_AT,
        )
    )

    section = collection.cross_section
    assert [(item.symbol, item.close, item.return_pct) for item in section.indices] == [
        ("KOSPI", 6742.74, 0.68),
        ("KOSDAQ", 827.15, 1.7),
    ]
    assert section.breadth_by_scope[0].breadth.model_dump()["listed_count"] == 944
    assert section.breadth_by_scope[0].breadth.eligible_count == 907
    assert [item.sector_code for item in section.sectors[:3]] == ["002", "003", "004"]
    assert len(section.market_flows) == 6
    assert next(
        item
        for item in section.market_flows
        if item.market == "KOSPI" and item.actor == "foreign"
    ).net_buy_amount == -4_000_000_000
    assert KA10051_AMOUNT_UNIT_KRW == 100 * KA10066_AMOUNT_UNIT_KRW
    assert len(collection.audit.concentration) == 6
    assert not collection.audit.blocked_concentration_markets
    assert collection.audit.pagination["KOSPI"]["pages"] == 2
    assert collection.audit.pagination["KOSPI"]["complete"] is True
    assert all(item.classification == "EXACT" for item in collection.audit.reconciliation)

    ka10051 = [item for item in requests if item["api_id"] == "ka10051"]
    ka10066 = [item for item in requests if item["api_id"] == "ka10066"]
    assert {item["body"]["amt_qty_tp"] for item in ka10051} == {"0"}
    assert {item["body"]["base_dt"] for item in ka10051} == {"20260825"}
    assert {item["body"]["stex_tp"] for item in ka10051} == {"3"}
    assert {item["body"]["amt_qty_tp"] for item in ka10066} == {"1"}
    assert {item["body"]["trde_tp"] for item in ka10066} == {"0"}
    assert {item["body"]["stex_tp"] for item in ka10066} == {"3"}


def test_ka10066_duplicate_integrated_identity_blocks_concentration() -> None:
    collection = asyncio.run(
        _service([], duplicate=True).collect(
            session_date=SESSION_DATE,
            observed_at=OBSERVED_AT,
        )
    )

    assert collection.audit.concentration == []
    assert collection.audit.blocked_concentration_markets == {
        "KOSPI": ["DUPLICATE_IDENTITY"],
        "KOSDAQ": ["DUPLICATE_IDENTITY"],
    }
    assert all(
        item.classification == "DUPLICATE_IDENTITY"
        for item in collection.audit.reconciliation
    )


def test_interrupted_pagination_keeps_aggregate_flow_and_blocks_concentration() -> None:
    collection = asyncio.run(
        _service([], missing_next_key=True).collect(
            session_date=SESSION_DATE,
            observed_at=OBSERVED_AT,
        )
    )

    assert len(collection.cross_section.market_flows) == 6
    assert collection.audit.concentration == []
    assert collection.audit.pagination["KOSPI"]["complete"] is False
    assert collection.audit.pagination["KOSDAQ"]["complete"] is False
    assert all(
        item.classification == "PAGINATION_INCOMPLETE"
        for item in collection.audit.reconciliation
    )


def test_session_identity_rejects_current_only_data_on_later_date() -> None:
    with pytest.raises(ValueError, match="completed target session"):
        asyncio.run(
            _service([]).collect(
                session_date=SESSION_DATE,
                observed_at=datetime(2026, 8, 26, 17, 0, tzinfo=KST),
            )
        )


def test_client_error_does_not_expose_access_token(caplog: pytest.LogCaptureFixture) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/token":
            return httpx.Response(
                200,
                json={
                    "return_code": 0,
                    "token": "never-log-this-token",
                    "expires_dt": "20270825235959",
                },
            )
        return httpx.Response(500, text="provider failure")

    client = KiwoomRestClient(
        app_key="app-key",
        secret_key="secret-key",
        base_url="https://api.kiwoom.test",
        request_interval_seconds=0,
        max_retries=0,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KiwoomRestError) as caught:
        asyncio.run(
            client.request(
                endpoint="/api/dostk/sect",
                api_id="ka20001",
                body={"mrkt_tp": "0", "inds_cd": "001"},
            )
        )
    combined = str(caught.value) + caplog.text
    assert "never-log-this-token" not in combined
    assert "secret-key" not in combined


def test_adapter_exposes_scoped_context_without_mutating_thesis_inputs() -> None:
    collection = asyncio.run(
        _service([]).collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT)
    )
    stocks = [{"ticker": "000660", "monitoring_state": "maintained"}]
    original = deepcopy(stocks)
    intelligence = build_market_intelligence(
        None,
        SESSION_DATE,
        stocks,
        [],
        market="kr",
        cross_section=collection.cross_section,
    )
    fact_ids = [str(item["fact_id"]) for item in intelligence["fact_catalog"]]
    assert len(fact_ids) == len(set(fact_ids))
    assert len([item for item in fact_ids if item.startswith("market:flow:kr:")]) == 6
    assert stocks == original

    normalized = KrMarketContextAdapter().normalize(
        assessment_date=SESSION_DATE,
        as_of=OBSERVED_AT,
        cutoff=OBSERVED_AT,
        fact_catalog=intelligence["fact_catalog"],
        cross_section=collection.cross_section,
        provider_publication_state="PROVIDER_COMPLETE",
    )
    assert len(normalized.size_context) == 3
    assert [item.symbol for item in normalized.indices] == ["KOSPI", "KOSDAQ"]
    assert len(normalized.market_flows) == 6
    assert len(normalized.concentration) == 6


def test_unconfigured_production_wrapper_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        kiwoom_kr_market_context_enabled=True,
        kiwoom_app_key=None,
        kiwoom_secret_key=None,
        kiwoom_rest_base_url="https://api.kiwoom.com",
        kiwoom_rest_timeout_seconds=30.0,
        kiwoom_rest_request_interval_seconds=0.2,
        kiwoom_rest_max_retries=0,
        kiwoom_rest_max_pages=50,
    )
    monkeypatch.setattr(
        "app.services.kiwoom_kr_market_context_service.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "app.providers.kiwoom_rest_client.get_settings",
        lambda: settings,
    )
    result = asyncio.run(
        collect_and_persist_kiwoom_market_context(
            session_date=SESSION_DATE,
            observed_at=OBSERVED_AT,
        )
    )
    assert result == {
        "status": "NOT_CONFIGURED",
        "packet_continues": True,
        "reason": "kiwoom_credentials_missing",
    }
