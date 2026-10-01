"""Fictional responses only. Tests never fetch Business Quant or any provider."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json

import pytest
from pydantic import ValidationError

from scripts.businessquant_eps_qualification import (
    ACCOUNTING,
    LATEST,
    BasisProof,
    ExpectedSecurity,
    FY1,
    State,
    public_request,
    qualify,
    reserve_call,
)
from scripts.us_forward_eps_qualification import US14

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def security(**updates):
    return ExpectedSecurity.model_validate(
        dict(
            ticker="FICTION",
            cik="0000123456",
            exchange="TEST",
            currency="USD",
            kind="COMMON",
            identity_source="fixture:listing",
            issuer_identity_source="fixture:issuer",
        )
        | updates
    )


def payload(value=3):
    return dict(
        metadata=dict(ticker="FICTION", cik=123456, mode="eps", metric_display="eps"),
        data=[
            dict(dimension="quarterly", estimates=[dict(period="Q1 26", value_estimate=999)]),
            dict(
                dimension="annual",
                estimates=[
                    dict(period="2024", data_type="reported", value_reported=1, value_estimate=1.1),
                    dict(period="2025", data_type="reported", value_reported=2, value_estimate=2.1),
                    dict(
                        period="2028", data_type="estimate", value_reported=None, value_estimate=8
                    ),
                    dict(
                        period="2026",
                        data_type="estimate",
                        value_reported=None,
                        value_estimate=value,
                        high_estimate=value + 1,
                        low_estimate=value - 1,
                    ),
                ],
            ),
        ],
    )


def raw(data):
    return json.dumps(data).encode()


def proof(data, **updates):
    return BasisProof.model_validate(
        dict(
            ticker="FICTION",
            cik="123456",
            provider_raw_sha256=sha256(raw(data)).hexdigest(),
            currency="USD",
            share_basis="LISTED_SHARE",
            series_scope_source="fixture:authoritative-series-scope",
            historical=[
                dict(
                    fiscal_year=y,
                    value=v,
                    currency="USD",
                    share_basis="LISTED_SHARE",
                    authoritative_source="fixture:issuer-annual-" + str(y),
                )
                for y, v in [(2024, 1), (2025, 2)]
            ],
        )
        | updates
    )


def run(data=None, *, identity=None, basis=None, status=200, digest=None, at=NOW):
    data = payload() if data is None else data
    b = data if isinstance(data, bytes) else raw(data)
    return qualify(
        identity or security(),
        b,
        http_status=status,
        retrieved_at=at,
        raw_sha256=digest or sha256(b).hexdigest(),
        basis=basis,
    )


@pytest.mark.parametrize("value", [3, -3, 0])
def test_exact_annual_selection_sign_and_noncalendar_label(value):
    data = payload(value)
    data["data"][1]["estimates"][3]["period_end_date"] = "2026-08-29"
    result = run(data, basis=proof(data))
    assert result.qualification_state == (State.POSITIVE if value > 0 else State.NONPOSITIVE)
    assert result.fy1_fiscal_year == 2026 and result.latest_completed_fy == 2025
    assert result.fy1_eps == Decimal(value)
    assert result.source_pointer == "/data/1/estimates/3/value_estimate"
    assert result.accounting_basis_state == ACCOUNTING
    assert result.estimate_asof is None and result.estimate_date_state == LATEST
    assert result.production_consumption is False


@pytest.mark.parametrize("field,value", [("ticker", "OTHER"), ("cik", 999)])
def test_exact_metadata_identity(field, value):
    data = payload()
    data["metadata"][field] = value
    result = run(data)
    assert result.qualification_state == State.IDENTITY and result.fy1_eps is None


def test_http_200_preview_is_entitlement_and_identity_gap_not_data():
    data = payload()
    data["metadata"].update(
        ticker="PREVIEW",
        cik=777,
        notes="Free preview: preview only. Upgrade to any paid plan to unlock all tickers",
    )
    result = run(data)
    assert result.qualification_state == State.ENTITLEMENT
    assert "IDENTITY_MISMATCH" in result.additional_states
    assert result.provider_ticker == "PREVIEW" and result.latest_completed_fy is None
    assert result.fy1_eps is None


@pytest.mark.parametrize(
    "status,expected",
    [
        (400, State.INVALID),
        (401, State.ENTITLEMENT),
        (403, State.ENTITLEMENT),
        (404, State.INVALID),
        (429, State.RATE),
        (500, State.INVALID),
        (None, State.INVALID),
    ],
)
def test_http_errors_never_estimate_unavailable(status, expected):
    assert run(b"", status=status).qualification_state == expected


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"<html>error</html>",
        b"[]",
        b'{"metadata":{},"metadata":{}}',
        {"metadata": True},
        {"metadata": {"ticker": "FICTION", "cik": True}},
        {"metadata": {"ticker": "FICTION", "cik": "not-a-cik"}},
    ],
)
def test_malformed_responses(data):
    assert run(data).qualification_state == State.INVALID


def test_raw_hash_binding_precedes_any_use():
    assert run(digest="0" * 64).qualification_state == State.INVALID


@pytest.mark.parametrize("field,value", [("mode", "revenue"), ("metric_display", "revenue")])
def test_metric_scope(field, value):
    data = payload()
    data["metadata"][field] = value
    assert run(data).qualification_state == State.INVALID


def test_quarters_are_not_annual():
    data = payload()
    data["data"] = data["data"][:1]
    assert run(data).qualification_state == State.PERIOD


def test_annual_dimension_duplicates_rejected():
    data = payload()
    data["data"].append(deepcopy(data["data"][1]))
    assert run(data).qualification_state == State.INVALID


def test_year_gap_not_max_period():
    data = payload()
    data["data"][1]["estimates"].pop()
    assert run(data).qualification_state == State.PERIOD


def test_completed_period_required():
    data = payload()
    data["data"][1]["estimates"] = data["data"][1]["estimates"][2:]
    assert run(data).qualification_state == State.PERIOD


def test_no_annual_forward_estimate():
    data = payload()
    data["data"][1]["estimates"] = data["data"][1]["estimates"][:2]
    assert run(data).qualification_state == State.UNAVAILABLE


def test_null_value_is_not_zero():
    data = payload()
    data["data"][1]["estimates"][3]["value_estimate"] = None
    assert run(data).qualification_state == State.UNAVAILABLE


@pytest.mark.parametrize("value", [True, "3", float("nan"), float("inf")])
def test_bad_numeric(value):
    data = payload()
    data["data"][1]["estimates"][3]["value_estimate"] = value
    assert run(data).qualification_state == State.INVALID


def test_duplicate_year_and_reported_estimate_mismatch():
    data = payload()
    data["data"][1]["estimates"].append(deepcopy(data["data"][1]["estimates"][0]))
    assert run(data).qualification_state == State.INVALID
    data = payload()
    data["data"][1]["estimates"][3]["value_reported"] = 3
    assert run(data).qualification_state == State.INVALID


def test_common_quote_currency_is_not_eps_currency_proof():
    assert run().qualification_state == State.BASIS


@pytest.mark.parametrize(
    "change",
    [
        dict(currency="TWD"),
        dict(cik="888"),
        dict(ticker="OTHER"),
        dict(provider_raw_sha256="0" * 64),
        dict(historical=[]),
        dict(share_basis="LISTED_ADS"),
    ],
)
def test_basis_identity_and_scope(change):
    data = payload()
    assert run(data, basis=proof(data, **change)).qualification_state == State.BASIS


def test_calibration_requires_distinct_exact_annual_values():
    data = payload()
    p = proof(data).model_dump()
    p["historical"][0]["value"] = Decimal("1.0001")
    assert run(data, basis=BasisProof.model_validate(p)).qualification_state == State.BASIS
    p = proof(data).model_dump()
    p["historical"] = (p["historical"][0], p["historical"][0])
    assert run(data, basis=BasisProof.model_validate(p)).qualification_state == State.BASIS


def test_adr_ratio_alone_never_proves_eps_basis():
    data = payload()
    result = run(
        data,
        identity=security(kind="ADS"),
        basis=proof(data, adr_ratio=5, adr_ratio_source="fixture:depositary"),
    )
    assert result.qualification_state == State.ADR and result.fy1_eps is None


def test_ads_requires_series_and_historical_basis_plus_ratio():
    data = payload()
    p = proof(data).model_dump()
    p.update(share_basis="LISTED_ADS", adr_ratio=5, adr_ratio_source="fixture:depositary")
    for item in p["historical"]:
        item["share_basis"] = "LISTED_ADS"
    result = run(data, identity=security(kind="ADS"), basis=BasisProof.model_validate(p))
    assert result.qualification_state == State.POSITIVE
    assert result.fy1_eps == 3 and result.adr_ratio_state == "PROVEN_WITH_SERIES_BASIS"


def test_deterministic_replay_and_no_live_calls(monkeypatch):
    import socket

    def denied(*a, **k):
        raise AssertionError("no_live_calls")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    data = payload()
    p = proof(data)
    assert run(data, basis=p).model_dump_json() == run(data, basis=p).model_dump_json()


def test_serialized_denied_result_cannot_retain_numeric():
    data = run().model_dump()
    data["fy1_eps"] = 3
    with pytest.raises(ValidationError):
        FY1.model_validate(data)


def test_timezone_required():
    with pytest.raises(ValidationError):
        run(at=NOW.replace(tzinfo=None))


def test_receipt_has_no_auth_parameter_and_no_unapproved_route():
    for ticker in US14:
        receipt = public_request(ticker)
        assert receipt["parameters"] == {"ticker": ticker, "mode": "eps"}
        assert "api_key" not in json.dumps(receipt)
        assert receipt["route"] == "https://data.businessquant.com/estimates"
    with pytest.raises(ValueError):
        public_request("AAPL")


def test_one_shot_reservation_and_stricter_18_call_cap(tmp_path):
    reserve_call(tmp_path, "GOOGL")
    with pytest.raises(FileExistsError):
        reserve_call(tmp_path, "GOOGL")
    for i in range(17):
        (tmp_path / f"data-fixture-{i}.json").write_text("{}")
    with pytest.raises(ValueError, match="18_CALL_CAP"):
        reserve_call(tmp_path, "MU")


def test_offline_module_has_no_provider_model_message_interfaces():
    import ast
    from pathlib import Path
    import scripts.businessquant_eps_qualification as m

    tree = ast.parse(Path(m.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(
        any(
            term in name.lower()
            for term in ("httpx", "requests", "openai", "telegram", "alphavantage")
        )
        for name in imports
        if name
    )
