"""Pure synthetic contract tests; no provider calls or operating-state access."""

from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json

import pytest
from pydantic import ValidationError

from scripts.us_forward_eps_qualification import (
    Estimate,
    ForwardEPS,
    Observation,
    Security,
    State,
    composite,
    from_response,
    qualify,
    yahoo_observation,
)

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def security(**overrides):
    value = dict(
        ticker="EXAMPLE",
        exchange="NMS",
        currency="USD",
        kind="COMMON",
        identity_source="fictional exact listing",
    )
    value.update(overrides)
    return Security.model_validate(value)


def row(**overrides):
    value = dict(
        metric="EPS",
        horizon="FY1",
        fiscal_year=2026,
        period_end="2026-12-31",
        row_kind="FORECAST",
        value="-2.50",
        currency="USD",
        share_basis="LISTED_SHARE",
        accounting_basis="GAAP",
        source_pointer="/estimates/0/eps",
    )
    value.update(overrides)
    return Estimate.model_validate(value)


def observation(**overrides):
    value = dict(
        provider="FICTIONAL",
        provider_security_id="EXAMPLE",
        exchange="NMS",
        source_route="https://example.invalid/annual",
        source_raw_sha256="a" * 64,
        retrieved_at=NOW,
        snapshot_semantic="PROVIDER_CURRENT_ESTIMATE",
        snapshot_semantic_source="documented latest estimate",
        period_basis="PROVIDER_FY",
        completed_fy=2025,
        completed_period_end="2025-12-31",
        completed_source_pointer="/actuals/2025",
        rows=[row()],
    )
    value.update(overrides)
    return Observation.model_validate(value)


def test_first_forecast_not_max_year_and_negative_is_valid():
    result = qualify(
        security(),
        observation(rows=[row(fiscal_year=2028, period_end="2028-12-31", value="8"), row()]),
    )
    assert (result.fiscal_year, result.eps_value, result.qualification_state) == (
        2026,
        Decimal("-2.50"),
        State.FY1,
    )
    assert result.estimate_asof is None and result.estimate_date_state == State.LATEST
    assert result.production_consumption is False


def test_non_calendar_fy_and_provider_period_labels():
    result = qualify(
        security(),
        observation(
            completed_fy=2026,
            completed_period_end="2026-09-03",
            rows=[row(fiscal_year=2027, period_end="2027-08-31")],
        ),
    )
    assert result.qualification_state == State.FY1
    assert result.fiscal_period_end == date(2027, 8, 31)


@pytest.mark.parametrize(
    "change,state",
    [
        ({"rows": [row(row_kind="ACTUAL")]}, State.UNAVAILABLE),
        ({"rows": [row(period_end=None)]}, State.PERIOD),
        ({"rows": [row(fiscal_year=None)]}, State.PERIOD),
        ({"rows": [row(fiscal_year=2027, period_end="2027-12-31")]}, State.PERIOD),
        ({"rows": [row(), row()]}, State.PERIOD),
        ({"rows": [row(period_end="2025-12-31")]}, State.PERIOD),
        ({"completed_period_end": None}, State.PERIOD),
        ({"completed_period_end": "2027-01-01"}, State.PERIOD),
        ({"completed_source_pointer": None}, State.PERIOD),
        ({"rows": [row(metric="forwardPE")]}, State.HORIZON),
        ({"rows": [row(horizon="forward")]}, State.HORIZON),
        ({"snapshot_semantic": "UNKNOWN"}, State.ACCESS),
        ({"snapshot_semantic_source": ""}, State.ACCESS),
        ({"provider_security_id": "OTHER"}, State.IDENTITY),
        ({"exchange": "NYQ"}, State.IDENTITY),
        ({"rows": [row(currency="TWD")]}, State.CURRENCY),
        ({"rows": [row(currency=None)]}, State.CURRENCY),
        ({"rows": [row(share_basis="ORDINARY_SHARE")]}, State.SHARE),
        ({"rows": [row(share_basis="UNKNOWN")]}, State.SHARE),
        ({"rows": [row(value=None)]}, State.UNAVAILABLE),
        ({"rows": [row(accounting_basis="")]}, State.INVALID),
        ({"rows": [row(source_pointer="")]}, State.INVALID),
        ({"source_error": State.ACCESS}, State.ACCESS),
        ({"source_error": State.PAYWALL}, State.PAYWALL),
        ({"source_error": State.UNSUPPORTED}, State.UNSUPPORTED),
    ],
)
def test_fail_closed(change, state):
    result = qualify(security(), observation(**change))
    assert result.qualification_state == state and result.eps_value is None


def test_dated_snapshot_does_not_replace_asof_with_retrieval():
    asof = datetime(2026, 9, 30, tzinfo=timezone.utc)
    result = qualify(security(), observation(estimate_asof=asof, snapshot_semantic="DATED"))
    assert result.estimate_asof == asof and result.estimate_asof != result.retrieved_at


@pytest.mark.parametrize(
    "field,value",
    [
        ("retrieved_at", datetime(2026, 10, 1)),
        ("estimate_asof", datetime(2026, 10, 2, tzinfo=timezone.utc)),
        ("source_error", State.FY1),
    ],
)
def test_invalid_observation(field, value):
    with pytest.raises(ValidationError):
        observation(**{field: value})


def test_ADS_requires_both_direct_EPS_basis_and_ratio_authority():
    s = security(kind="ADS")
    o = observation(
        rows=[row(share_basis="LISTED_ADS")],
        adr_ratio="5",
        adr_ratio_source="official depositary document",
        adr_eps_basis_source="provider per ADS",
    )
    assert qualify(s, o).qualification_state == State.FY1
    for key in ("adr_ratio", "adr_ratio_source", "adr_eps_basis_source"):
        assert qualify(s, o.model_copy(update={key: None})).qualification_state == State.ADR
    assert (
        qualify(
            s, observation(adr_ratio="5", adr_ratio_source="official ratio only")
        ).qualification_state
        == State.ADR
    )


def test_explicit_NTM_is_separate_and_generic_forward_is_rejected():
    r = row(horizon="NTM", fiscal_year=None, period_end=None)
    o = observation(
        rows=[r], ntm_definition_source="provider rolling next-twelve-month EPS definition"
    )
    result = qualify(security(), o, "NTM")
    assert result.qualification_state == State.NTM
    assert qualify(security(), observation(rows=[r]), "NTM").qualification_state == State.HORIZON
    fy1 = qualify(security(), observation())
    assert len(composite([result, fy1])) == 2


def test_composite_source_identity_never_silently_overwrites():
    first = qualify(security(), observation())
    other = qualify(security(), observation(provider="OTHER", source_raw_sha256="b" * 64))
    with pytest.raises(ValueError, match="explicit_composite_owner"):
        composite([first, other])
    assert composite([first])[("EXAMPLE", "FY1")].source_raw_sha256 == "a" * 64


def public_fixture():
    estimates = []
    for period, year, value in (("0y", 2026, 2), ("+1y", 2027, 3)):
        estimates.append(
            dict(
                period=period,
                endDate=f"{year}-12-31",
                earningsEstimate=dict(
                    avg=dict(raw=value, fmt=str(value)),
                    earningsCurrency="USD",
                    numberOfAnalysts=dict(raw=2),
                ),
                epsTrend=dict(current=dict(raw=value, fmt=str(value))),
            )
        )
    body = dict(
        price=dict(symbol="EXAMPLE", exchange="NMS", quoteType="EQUITY"),
        earningsTrend=dict(defaultMethodology="gaap", trend=estimates),
        earningsTrendGaap=dict(trend=estimates),
        earnings=dict(
            financialsChart=dict(yearly=[dict(date=2025)]),
            earningsChart=dict(
                quarterly=[
                    dict(
                        fiscalQuarter="4Q2025",
                        actual=dict(raw=1),
                        periodEndDate=dict(fmt="2025-12-31"),
                        reportedDate=dict(fmt="2026-02-01"),
                    )
                ]
            ),
        ),
    )
    envelope = json.dumps(dict(status=200, body=json.dumps(dict(quoteSummary=dict(result=[body])))))
    html = (
        '<script type="application/json" data-url="https://query1.finance.yahoo.com/v10/finance/quoteSummary/EXAMPLE">'
        + envelope
        + '</script><section data-testid="earningsEstimate">'
        '<input checked value="gaap"><table><tr><th>Currency in USD</th>'
        '<th data-testid-header="0y">Current Year (2026)</th>'
        '<th data-testid-header="+1y">Next Year (2027)</th></tr>'
        "<tr><td>Avg. Estimate</td><td>2</td><td>3</td></tr>"
        "<tr><td>No. of Analysts</td><td>2</td><td>2</td></tr></table></section>"
        '<section data-testid="epsTrend"><table><tr><td>Current Estimate</td>'
        "<td>2</td><td>3</td></tr></table></section>"
    )
    return html.encode()


def test_public_visible_and_embedded_JSON_bind():
    raw = public_fixture()
    result = qualify(security(), yahoo_observation(raw, security(), NOW))
    assert result.qualification_state == State.FY1 and result.eps_value == 2
    assert result.source_raw_sha256 == sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "before,after",
    [
        (b"<td>2</td>", b"<td>Upgrade</td>"),
        (b"Current Year (2026)", b"Current Year"),
        (b"Currency in USD", b"Currency in TWD"),
        (b'checked value="gaap"', b'checked value="nongaap"'),
        (b"query1.finance.yahoo.com", b"example.invalid"),
        (b'"status": 200', b'"status": 403'),
        (b'earningsEstimate"', b'unknownEstimate"'),
    ],
)
def test_public_parser_failures_are_not_absent_estimates(before, after):
    raw = public_fixture().replace(before, after)
    receipt = dict(
        raw_sha256=sha256(raw).hexdigest(),
        http_status=200,
        transport="RESPONSE",
        retrieved_at=NOW.isoformat(),
    )
    assert from_response(raw, security(), receipt)["qualification_state"] == State.INVALID


@pytest.mark.parametrize("status", [302, 403, 429, 500, None])
def test_transport_not_missing_estimate(status):
    raw = b""
    receipt = dict(raw_sha256=sha256(raw).hexdigest(), http_status=status, transport="RESPONSE")
    assert from_response(raw, security(), receipt)["qualification_state"] == State.ACCESS


def test_raw_hash_and_qualified_record_tamper_rejected():
    with pytest.raises(ValueError, match="raw_hash"):
        from_response(b"changed", security(), dict(raw_sha256="a" * 64))
    result = qualify(security(), observation()).model_dump(mode="json")
    for change in (
        {"eps_value": None},
        {"fiscal_year": 2028},
        {"share_basis": "UNKNOWN"},
        {"horizon_kind": "NTM"},
        {"provider_security_id": "OTHER"},
        {"estimate_date_state": "UNKNOWN"},
        {"snapshot_semantic_source": ""},
        {"accounting_basis": ""},
        {"completed_source_pointer": None},
        {"estimate_asof": "2027-01-01T00:00:00Z"},
    ):
        with pytest.raises(ValidationError):
            ForwardEPS.model_validate({**result, **change})
