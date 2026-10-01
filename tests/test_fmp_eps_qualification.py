from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from scripts.fmp_eps_qualification import (
    ACCOUNTING,
    LATEST,
    BasisProof,
    FY1,
    PeriodOwner,
    Security,
    State,
    public_request,
    qualify,
    reserve_call,
)


def security(kind="COMMON"):
    return Security(
        ticker="FICTION",
        exchange="XNAS",
        currency="USD",
        kind=kind,
        identity_source="synthetic listed-security owner",
    )


def owner(end="2025-12-31", fy=2025):
    return PeriodOwner(
        ticker="FICTION",
        latest_completed_fy=fy,
        latest_completed_period_end=date.fromisoformat(end),
        source="synthetic issuer annual release",
        source_sha256="a" * 64,
        source_available_at=date(2026, 1, 10),
    )


def rows(value=2):
    return [
        dict(symbol="FICTION", date="2027-12-31", epsAvg=8),
        dict(
            symbol="FICTION",
            date="2026-12-31",
            epsAvg=value,
            epsHigh=value + 1,
            epsLow=value - 1,
            numAnalystsEps=5,
        ),
        dict(symbol="FICTION", date="2025-12-31", epsAvg=1),
    ]


def run(body=None, *, status=200, basis_changes=None, **kwargs):
    raw = json.dumps(rows() if body is None else body).encode()
    digest = sha256(raw).hexdigest()
    basis = BasisProof(
        ticker="FICTION",
        provider_raw_sha256=digest,
        reporting_currency="USD",
        reporting_currency_source="synthetic financial statements USD EPS",
        share_basis="LISTED_SHARE",
        share_basis_source="synthetic common-share class",
        provider_series_scope_source="synthetic explicit reported-currency/listed-share scope",
    )
    if basis_changes:
        basis = BasisProof.model_validate(basis.model_dump() | basis_changes)
    args = dict(
        http_status=status,
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        raw_sha256=digest,
        period_owner=owner(),
        basis=basis,
    )
    args.update(kwargs)
    return qualify(security(), raw, **args)


def test_calendar_first_future_not_max_and_null_asof():
    r = run()
    assert r.qualification_state == State.POSITIVE
    assert r.fy1_period_end == date(2026, 12, 31) and r.fy1_eps_avg == 2
    assert r.fy1_fiscal_year == 2026 and r.source_pointer == "/1/epsAvg"
    assert r.estimate_asof is None and r.estimate_date_state == LATEST
    assert r.accounting_basis_state == ACCOUNTING and r.production_consumption is False
    assert FY1.model_validate_json(r.model_dump_json()) == r


def test_noncalendar_52_53_week_fiscal_owner():
    body = [
        dict(symbol="FICTION", date=d, epsAvg=2) for d in ("2028-08-31", "2027-08-31", "2026-08-31")
    ]
    r = run(body, period_owner=owner("2026-09-03", 2026))
    assert r.qualification_state == State.POSITIVE
    assert r.fy1_period_end == date(2027, 8, 31) and r.fy1_fiscal_year == 2027


@pytest.mark.parametrize("value", [-12.5, -0.01, 0, 1.5])
def test_sign_preserved(value):
    r = run(rows(value))
    assert r.qualification_state == (State.POSITIVE if value > 0 else State.NONPOSITIVE)
    assert str(r.fy1_eps_avg) == str(value)


@pytest.mark.parametrize(
    "code,state",
    [
        (400, State.INVALID),
        (401, State.INVALID),
        (402, State.ENTITLEMENT),
        (403, State.ENTITLEMENT),
        (404, State.INVALID),
        (422, State.INVALID),
        (429, State.RATE),
        (500, State.INVALID),
        (None, State.INVALID),
        (302, State.INVALID),
    ],
)
def test_http_states(code, state):
    assert run(status=code).qualification_state == state


@pytest.mark.parametrize(
    "body,state",
    [
        ([], State.UNAVAILABLE),
        ({"Error Message": "Restricted endpoint; upgrade subscription"}, State.ENTITLEMENT),
        ({"error": "Rate limit"}, State.RATE),
        ({"error": "Symbol not found"}, State.UNSUPPORTED),
        ({"error": "unknown"}, State.INVALID),
        ([1], State.INVALID),
        (False, State.INVALID),
    ],
)
def test_body_states(body, state):
    assert run(body).qualification_state == state


def test_mismatched_one_row_rejects_whole_series():
    body = rows()
    body[0]["symbol"] = "OTHER"
    assert run(body).qualification_state == State.IDENTITY


@pytest.mark.parametrize(
    "field,value",
    [
        ("epsAvg", True),
        ("epsAvg", "2"),
        ("epsAvg", float("inf")),
        ("epsAvg", float("nan")),
        ("epsHigh", 0),
        ("epsLow", 3),
        ("numAnalystsEps", True),
        ("numAnalystsEps", -1),
        ("numAnalystsEps", 1.5),
        ("date", "not-date"),
    ],
)
def test_bad_schema(field, value):
    body = rows()
    body[1][field] = value
    assert run(body).qualification_state == State.INVALID


@pytest.mark.parametrize("changes", [{"epsAvg": None}, {"numAnalystsEps": 0}])
def test_valid_unavailable(changes):
    body = rows()
    body[1].update(changes)
    assert run(body).qualification_state == State.UNAVAILABLE


def test_duplicate_date_and_duplicate_json_key():
    assert run(rows() + [rows()[1]]).qualification_state == State.INVALID
    raw = b'[{"symbol":"FICTION","symbol":"FICTION"}]'
    assert (
        qualify(
            security(),
            raw,
            http_status=200,
            retrieved_at=datetime.now(timezone.utc),
            raw_sha256=sha256(raw).hexdigest(),
            period_owner=owner(),
        ).qualification_state
        == State.INVALID
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"period": "quarter"},
        {"period_owner": None},
        {"period_owner": owner().model_copy(update={"ticker": "OTHER"})},
        {"period_owner": owner().model_copy(update={"source_available_at": date(2028, 1, 1)})},
    ],
)
def test_period_owner_required(kwargs):
    assert run(**kwargs).qualification_state == State.PERIOD


def test_missing_next_year_and_stale_owner():
    assert run([rows()[0]]).qualification_state == State.PERIOD
    assert (
        run([dict(symbol="FICTION", date="2026-03-31", epsAvg=2)]).qualification_state
        == State.PERIOD
    )
    assert run([rows()[2]]).qualification_state == State.UNAVAILABLE


@pytest.mark.parametrize(
    "change",
    [
        {"reporting_currency": "CNY"},
        {"ticker": "OTHER"},
        {"provider_raw_sha256": "f" * 64},
        {"share_basis": "LISTED_ADS"},
    ],
)
def test_currency_and_share_basis_not_inferred_from_quote(change):
    r = run(basis_changes=change)
    assert r.qualification_state == State.BASIS and r.fy1_eps_avg is None


def test_basis_missing_and_hash_mismatch():
    assert run(basis=None).qualification_state == State.BASIS
    assert run(raw_sha256="0" * 64).qualification_state == State.INVALID


def test_ads_ratio_does_not_prove_eps_scope():
    raw = json.dumps(rows()).encode()
    args = dict(
        http_status=200,
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        raw_sha256=sha256(raw).hexdigest(),
        period_owner=owner(),
    )
    assert qualify(security("ADS"), raw, **args).qualification_state == State.ADR
    b = BasisProof(
        ticker="FICTION",
        provider_raw_sha256=sha256(raw).hexdigest(),
        reporting_currency="USD",
        reporting_currency_source="synthetic currency evidence",
        share_basis="LISTED_ADS",
        share_basis_source="synthetic explicit per ADS evidence",
        provider_series_scope_source="synthetic provider ADS definition",
    )
    assert qualify(security("ADS"), raw, basis=b, **args).qualification_state == State.ADR
    b = b.model_copy(
        update={"adr_ratio": Decimal(5), "adr_ratio_source": "synthetic depositary contract"}
    )
    b = BasisProof.model_validate(b.model_dump())
    assert qualify(security("ADS"), raw, basis=b, **args).qualification_state == State.POSITIVE


def test_redacted_request_and_no_other_endpoint():
    r = public_request("GOOGL")
    assert r["params"] == dict(symbol="GOOGL", period="annual", page=0, limit=10)
    assert "apikey" not in json.dumps(r).lower()
    with pytest.raises(ValueError):
        public_request("INVALID?apikey=secret")


def test_duplicate_crash_and_closed_call_guard(tmp_path):
    reserve_call(tmp_path, "GOOGL")
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "GOOGL")
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "GOOGL", retry=True)
    (tmp_path / "CLOSED").touch()
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "MU")


@pytest.mark.parametrize("status", [200, 400, 401, 402, 403, 404, 422, 429])
def test_no_semantic_or_http_denial_retry(tmp_path, status):
    reserve_call(tmp_path, "GOOGL")
    (tmp_path / "GOOGL-response.json").write_text(
        json.dumps(dict(valid_response_body=False, http_status=status, transport_failure=False))
    )
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "GOOGL", retry=True)


def test_transport_retry_per_ticker_and_total_cap(tmp_path):
    for ticker in ("GOOGL", "MU", "TSM"):
        reserve_call(tmp_path, ticker)
        (tmp_path / (ticker + "-response.json")).write_text(
            json.dumps(dict(valid_response_body=False, http_status=503, transport_failure=False))
        )
    reserve_call(tmp_path, "GOOGL", retry=True)
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "GOOGL", retry=True)
    reserve_call(tmp_path, "MU", retry=True)
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "TSM", retry=True)


def test_valid_5xx_body_cannot_retry(tmp_path):
    reserve_call(tmp_path, "MU")
    (tmp_path / "MU-response.json").write_text(
        json.dumps(dict(valid_response_body=True, http_status=503, transport_failure=False))
    )
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "MU", retry=True)


def test_normal_hard_cap(tmp_path):
    for i in range(16):
        (tmp_path / f"FICTION{i}-attempt-1.json").write_text("{}")
    with pytest.raises(ValueError):
        reserve_call(tmp_path, "GOOGL")


def test_denied_values_invariant():
    r = run()
    with pytest.raises(ValueError):
        FY1.model_validate(r.model_dump() | dict(qualification_state=State.ENTITLEMENT))
