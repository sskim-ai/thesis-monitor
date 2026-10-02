"""Offline forward-EPS qualification. Not imported by any production consumer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel

US14 = (
    "CORZ",
    "CPNG",
    "CRCL",
    "GOOGL",
    "HUT",
    "IBM",
    "MU",
    "RXRX",
    "SKHY",
    "SNDK",
    "TSLA",
    "TSM",
    "WRD",
    "WULF",
)
CONTRACT = "us-exact-forward-eps-source-qualification-v1"


class State(StrEnum):
    FY1 = "QUALIFIED_FY1_EPS"
    NTM = "QUALIFIED_EXACT_NTM_EPS"
    UNAVAILABLE = "UNAVAILABLE_ESTIMATE"
    UNSUPPORTED = "SOURCE_UNSUPPORTED_SECURITY"
    PAYWALL = "SOURCE_PAYWALL"
    IDENTITY = "IDENTITY_MISMATCH"
    HORIZON = "HORIZON_AMBIGUOUS"
    PERIOD = "PERIOD_IDENTITY_UNRESOLVED"
    LATEST = "ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_SNAPSHOT"
    CURRENCY = "CURRENCY_BASIS_UNRESOLVED"
    SHARE = "SHARE_BASIS_UNRESOLVED"
    ADR = "ADR_BASIS_UNRESOLVED"
    INVALID = "SOURCE_RESPONSE_INVALID"
    ACCESS = "SOURCE_ACCESS_UNSTABLE"


class Security(ContractModel):
    ticker: str = Field(min_length=1)
    exchange: str = Field(min_length=1)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    kind: Literal["COMMON", "ADS"]
    identity_source: str = Field(min_length=1)


class Estimate(ContractModel):
    metric: str
    horizon: str
    fiscal_year: int | None = None
    period_end: date | None = None
    row_kind: Literal["FORECAST", "ACTUAL"]
    value: Decimal | None = None
    currency: str | None = None
    share_basis: Literal["LISTED_SHARE", "LISTED_ADS", "ORDINARY_SHARE", "UNKNOWN"]
    accounting_basis: str
    source_pointer: str


class Observation(ContractModel):
    provider: str
    provider_security_id: str
    exchange: str
    source_route: str
    source_raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: datetime
    estimate_asof: datetime | None = None
    snapshot_semantic: Literal["DATED", "PROVIDER_CURRENT_ESTIMATE", "UNKNOWN"]
    snapshot_semantic_source: str
    completed_fy: int | None = None
    completed_period_end: date | None = None
    completed_source_pointer: str | None = None
    period_basis: str
    rows: tuple[Estimate, ...]
    adr_ratio: Decimal | None = None
    adr_ratio_source: str | None = None
    adr_eps_basis_source: str | None = None
    ntm_definition_source: str | None = None
    source_error: State | None = None

    @model_validator(mode="after")
    def safe_time(self):
        if self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieval_timezone_required")
        if self.estimate_asof is not None and (
            self.estimate_asof.utcoffset() is None or self.estimate_asof > self.retrieved_at
        ):
            raise ValueError("invalid_estimate_asof")
        if self.source_error in (State.FY1, State.NTM, State.LATEST):
            raise ValueError("positive_state_is_not_source_error")
        return self


class ForwardEPS(ContractModel):
    contract: Literal["us-exact-forward-eps-source-qualification-v1"] = CONTRACT
    security: Security
    provider: str
    provider_security_id: str
    metric: Literal["EPS"] = "EPS"
    horizon_kind: Literal["FY1", "NTM"]
    fiscal_year: int | None
    fiscal_period_end: date | None
    latest_completed_fiscal_year: int | None
    latest_completed_period_end: date | None
    completed_source_pointer: str | None
    eps_value: Decimal | None
    eps_currency: str | None
    share_basis: str | None
    accounting_basis: str | None
    adr_ratio: Decimal | None
    adr_ratio_source: str | None
    adr_eps_basis_source: str | None
    ntm_definition_source: str | None
    estimate_asof: datetime | None
    estimate_date_state: str
    snapshot_semantic_source: str
    retrieved_at: datetime
    source_route: str
    source_raw_sha256: str
    source_pointer: str | None
    period_basis: str
    qualification_state: State
    denial_reasons: tuple[str, ...]
    production_consumption: Literal[False] = False

    @model_validator(mode="after")
    def no_value_leak(self):
        positive = self.qualification_state in (State.FY1, State.NTM)
        if positive:
            if (
                self.eps_value is None
                or not self.eps_value.is_finite()
                or self.denial_reasons
                or not self.source_pointer
                or self.eps_currency != self.security.currency
                or self.provider_security_id != self.security.ticker
                or not self.accounting_basis
                or not re.fullmatch(r"[0-9a-f]{64}", self.source_raw_sha256)
                or self.retrieved_at.utcoffset() is None
            ):
                raise ValueError("qualified_value_contract_gap")
            if self.estimate_asof is None:
                if self.estimate_date_state != State.LATEST or not self.snapshot_semantic_source:
                    raise ValueError("qualified_latest_snapshot_gap")
            elif (
                self.estimate_date_state != "DATED"
                or self.estimate_asof.utcoffset() is None
                or self.estimate_asof > self.retrieved_at
            ):
                raise ValueError("qualified_asof_gap")
            if self.horizon_kind == "FY1":
                if (
                    self.qualification_state != State.FY1
                    or self.fiscal_year is None
                    or self.latest_completed_fiscal_year is None
                    or self.fiscal_year != self.latest_completed_fiscal_year + 1
                    or self.fiscal_period_end is None
                    or self.latest_completed_period_end is None
                    or not self.completed_source_pointer
                    or self.latest_completed_period_end > self.retrieved_at.date()
                    or self.fiscal_period_end <= self.latest_completed_period_end
                ):
                    raise ValueError("qualified_FY1_period_gap")
            elif self.qualification_state != State.NTM or not self.ntm_definition_source:
                raise ValueError("qualified_NTM_state_mismatch")
            if self.security.kind == "ADS" and (
                self.share_basis != "LISTED_ADS"
                or self.adr_ratio is None
                or self.adr_ratio <= 0
                or not self.adr_ratio_source
                or not self.adr_eps_basis_source
            ):
                raise ValueError("qualified_ADS_basis_gap")
            if self.security.kind == "COMMON" and self.share_basis != "LISTED_SHARE":
                raise ValueError("qualified_share_basis_gap")
        elif self.eps_value is not None:
            raise ValueError("denied_value_must_be_null")
        return self


def qualify(security: Security, observation: Observation, horizon="FY1") -> ForwardEPS:
    """Select by owned fiscal identity, never MAX(year), PE inversion or FX inference."""
    s = Security.model_validate(security)
    o = Observation.model_validate(observation)
    if horizon not in ("FY1", "NTM"):
        raise ValueError("unsupported_horizon")
    result = dict(
        security=s,
        provider=o.provider,
        provider_security_id=o.provider_security_id,
        horizon_kind=horizon,
        fiscal_year=None,
        fiscal_period_end=None,
        latest_completed_fiscal_year=o.completed_fy,
        latest_completed_period_end=o.completed_period_end,
        eps_value=None,
        completed_source_pointer=o.completed_source_pointer,
        eps_currency=None,
        share_basis=None,
        accounting_basis=None,
        adr_ratio=o.adr_ratio,
        adr_ratio_source=o.adr_ratio_source,
        adr_eps_basis_source=o.adr_eps_basis_source,
        ntm_definition_source=o.ntm_definition_source,
        estimate_asof=o.estimate_asof,
        retrieved_at=o.retrieved_at,
        estimate_date_state="DATED" if o.estimate_asof else State.LATEST.value,
        snapshot_semantic_source=o.snapshot_semantic_source,
        source_route=o.source_route,
        source_raw_sha256=o.source_raw_sha256,
        source_pointer=None,
        period_basis=o.period_basis,
    )

    def deny(state, reason):
        return ForwardEPS(**result, qualification_state=state, denial_reasons=(reason,))

    if o.source_error:
        return deny(o.source_error, "source_failure_not_an_absent_estimate")
    if (s.ticker, s.exchange) != (o.provider_security_id, o.exchange):
        return deny(State.IDENTITY, "exact_listing_mismatch")
    if o.estimate_asof is None and (
        o.snapshot_semantic != "PROVIDER_CURRENT_ESTIMATE" or not o.snapshot_semantic_source
    ):
        result["estimate_date_state"] = "UNKNOWN"
        return deny(State.ACCESS, "estimate_time_not_owned")
    if o.estimate_asof is not None and o.snapshot_semantic != "DATED":
        return deny(State.INVALID, "dated_snapshot_semantic_mismatch")
    if any(r.metric != "EPS" for r in o.rows):
        return deny(State.HORIZON, "generic_forwardPE_or_non_EPS_is_not_an_EPS_owner")
    if any(r.horizon not in ("FY1", "NTM") for r in o.rows):
        return deny(State.HORIZON, "ambiguous_forward_horizon")
    if horizon == "FY1":
        if (
            o.completed_fy is None
            or o.completed_period_end is None
            or not o.completed_source_pointer
            or o.completed_period_end > o.retrieved_at.date()
        ):
            return deny(State.PERIOD, "latest_completed_fiscal_period_not_owned")
        rows = [r for r in o.rows if r.horizon == "FY1" and r.row_kind == "FORECAST"]
        if any(r.period_end is None or r.fiscal_year is None for r in rows):
            return deny(State.PERIOD, "forecast_period_missing")
        rows = sorted(
            (r for r in rows if r.fiscal_year > o.completed_fy),
            key=lambda r: (r.fiscal_year, r.period_end),
        )
        if not rows:
            return deny(State.UNAVAILABLE, "no_forward_annual_estimate_rows")
        row = rows[0]
        if (
            row.fiscal_year != o.completed_fy + 1
            or row.period_end <= o.completed_period_end
            or sum(r.fiscal_year == row.fiscal_year for r in rows) != 1
        ):
            return deny(State.PERIOD, "first_forecast_fiscal_year_gap_or_duplicate")
    else:
        if not o.ntm_definition_source:
            return deny(State.HORIZON, "rolling_next_twelve_month_definition_required")
        rows = [r for r in o.rows if r.horizon == "NTM" and r.row_kind == "FORECAST"]
        if len(rows) != 1:
            return deny(State.HORIZON, "single_explicit_NTM_EPS_required")
        row = rows[0]
    result.update(
        fiscal_year=row.fiscal_year,
        fiscal_period_end=row.period_end,
        eps_currency=row.currency,
        share_basis=row.share_basis,
        accounting_basis=row.accounting_basis,
        source_pointer=row.source_pointer,
    )
    if row.currency != s.currency:
        return deny(State.CURRENCY, "EPS_currency_not_security_currency_no_FX_owner")
    if s.kind == "ADS":
        if (
            row.share_basis != "LISTED_ADS"
            or o.adr_ratio is None
            or not o.adr_ratio.is_finite()
            or o.adr_ratio <= 0
            or not o.adr_ratio_source
            or not o.adr_eps_basis_source
        ):
            return deny(State.ADR, "listed_ADS_EPS_and_authoritative_ratio_both_required")
    elif row.share_basis != "LISTED_SHARE":
        return deny(State.SHARE, "exact_listed_share_EPS_basis_required")
    if row.value is None:
        return deny(State.UNAVAILABLE, "provider_explicitly_has_no_EPS_value")
    if not row.value.is_finite():
        return deny(State.INVALID, "nonfinite_EPS")
    if not row.accounting_basis or not row.source_pointer:
        return deny(State.INVALID, "EPS_method_or_pointer_missing")
    return ForwardEPS(
        **{**result, "eps_value": row.value},
        qualification_state=State.FY1 if horizon == "FY1" else State.NTM,
        denial_reasons=(),
    )


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self):
        return " ".join(
            " ".join(c.text() if isinstance(c, Node) else c for c in self.children).split()
        )

    def find(self, tag=None, **attrs):
        result = []
        if (tag is None or self.tag == tag) and all(
            self.attrs.get(k) == v for k, v in attrs.items()
        ):
            result.append(self)
        for child in self.children:
            if isinstance(child, Node):
                result.extend(child.find(tag, **attrs))
        return result


class PublicHTML(HTMLParser):
    """Parse public HTML/JSON without executing scripts or discovering private routes."""

    VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(raw.decode("utf-8", errors="strict"))
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def only(rows):
    if len(rows) != 1:
        raise ValueError("unique_public_owner_required")
    return rows[0]


def number(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError("invalid_number_type")
    result = Decimal(str(value).replace(",", ""))
    if not result.is_finite():
        raise ValueError("nonfinite_number")
    return result


def public_quote_summary(document, symbol):
    owners = []
    for node in document.find("script", type="application/json"):
        route = node.attrs.get("data-url", "")
        parts = urlsplit(route)
        if (
            parts.hostname not in ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
            or parts.path != f"/v10/finance/quoteSummary/{symbol}"
        ):
            continue
        envelope = json.loads("".join(node.children))
        if envelope["status"] != 200:
            raise ValueError("embedded_response_not_OK")
        body = json.loads(envelope["body"], parse_float=Decimal)
        if body["quoteSummary"].get("error") is not None:
            raise ValueError("embedded_source_error")
        owners.append(only(body["quoteSummary"]["result"]))
    return only(owners)


def yahoo_observation(raw: bytes, security: Security, retrieved_at: datetime) -> Observation:
    """Bind annual JSON to the public Earnings Estimate and Current Estimate tables."""
    doc = PublicHTML(raw).root
    body = public_quote_summary(doc, security.ticker)
    price = body["price"]
    if price.get("quoteType") != "EQUITY":
        raise ValueError("exact_equity_listing_required")
    estimate = only(doc.find(**{"data-testid": "earningsEstimate"}))
    trend = only(doc.find(**{"data-testid": "epsTrend"}))
    table = only(estimate.find("table"))
    table_rows = table.find("tr")
    headers = table_rows[0].find("th")
    cells = [r.find("td") for r in table_rows[1:]]
    avg = only([r for r in cells if r and r[0].text() == "Avg. Estimate"])
    count = only([r for r in cells if r and r[0].text() == "No. of Analysts"])
    current = only(
        [
            r.find("td")
            for r in trend.find("tr")
            if r.find("td") and r.find("td")[0].text() == "Current Estimate"
        ]
    )
    currency_match = re.fullmatch(r"Currency in ([A-Z]{3})", headers[0].text())
    if currency_match is None:
        raise ValueError("EPS_table_currency_missing")
    currency = currency_match[1]
    module = body["earningsTrend"]
    method = module.get("defaultMethodology")
    if method not in ("gaap", "nongaap"):
        raise ValueError("accounting_basis_missing")
    checked = [n.attrs.get("value") for n in estimate.find("input") if "checked" in n.attrs]
    if checked != [method]:
        raise ValueError("visible_accounting_basis_mismatch")
    explicit = body["earningsTrendGaap" if method == "gaap" else "earningsTrendNonGaap"]
    if module["trend"] != explicit["trend"]:
        raise ValueError("default_and_explicit_method_mismatch")
    rows = []
    for i, header in enumerate(headers):
        period = header.attrs.get("data-testid-header")
        if period not in ("0y", "+1y"):
            continue
        match = re.fullmatch(r"(?:Current|Next) Year \((\d{4})\)", header.text())
        if not match:
            raise ValueError("annual_year_identity_missing")
        source = only([r for r in module["trend"] if r["period"] == period])
        eps = source["earningsEstimate"]
        value = number(eps.get("avg", {}).get("raw"))
        if eps.get("earningsCurrency") != currency:
            raise ValueError("visible_and_JSON_EPS_currency_mismatch")
        if value is not None:
            if (
                number(avg[i].text()) != number(eps["avg"]["fmt"])
                or number(current[i].text()) != number(source["epsTrend"]["current"]["fmt"])
                or number(source["epsTrend"]["current"]["raw"]) != value
                or number(count[i].text()) != number(eps["numberOfAnalysts"]["raw"])
                or number(eps["numberOfAnalysts"]["raw"]) <= 0
            ):
                raise ValueError("public_visible_EPS_current_estimate_mismatch")
        elif avg[i].text() not in ("--", "N/A", "-"):
            raise ValueError("missing_value_display_mismatch")
        rows.append(
            Estimate(
                metric="EPS",
                horizon="FY1",
                fiscal_year=int(match[1]),
                period_end=date.fromisoformat(source["endDate"]),
                row_kind="FORECAST",
                value=value,
                currency=currency,
                share_basis="LISTED_SHARE" if security.kind == "COMMON" else "UNKNOWN",
                accounting_basis="GAAP" if method == "gaap" else "NORMALIZED_NON_GAAP",
                source_pointer=(
                    "/quoteSummary/result/0/earningsTrend/trend/"
                    f"{module['trend'].index(source)}/earningsEstimate/avg/raw"
                ),
            )
        )
    if len(rows) != 2:
        raise ValueError("annual_table_pair_missing")
    completed = []
    annual_years = [r["date"] for r in body["earnings"]["financialsChart"]["yearly"]]
    for row in body["earnings"]["earningsChart"]["quarterly"]:
        match = re.fullmatch(r"4Q(\d{4})", row.get("fiscalQuarter", ""))
        if match and row.get("actual", {}).get("raw") is not None:
            end = date.fromisoformat(row["periodEndDate"]["fmt"])
            reported = date.fromisoformat(row["reportedDate"]["fmt"])
            if not end <= reported <= retrieved_at.date():
                raise ValueError("completed_period_availability_gap")
            completed.append((int(match[1]), end))
    completed_fy, completed_end = max(completed) if completed else (None, None)
    if completed_fy not in annual_years or completed_fy != max(annual_years, default=None):
        completed_fy, completed_end = None, None
    return Observation(
        provider="Yahoo_PUBLIC_ANALYSIS",
        provider_security_id=price["symbol"],
        exchange=price["exchange"],
        source_route=f"https://finance.yahoo.com/quote/{security.ticker}/analysis/",
        source_raw_sha256=sha256(raw).hexdigest(),
        retrieved_at=retrieved_at,
        estimate_asof=None,
        snapshot_semantic="PROVIDER_CURRENT_ESTIMATE",
        snapshot_semantic_source="public epsTrend Current Estimate; estimate timestamp not supplied",
        completed_fy=completed_fy,
        completed_period_end=completed_end,
        completed_source_pointer="earnings/earningsChart/quarterly/4Q_actual_and_financialsChart/yearly",
        period_basis="PROVIDER_FISCAL_YEAR_AND_PERIOD_END_NOT_EXACT_52_53_WEEK_FILING_DATE",
        rows=tuple(rows),
    )


def from_response(raw, security, receipt):
    """Transport failures never masquerade as provider-confirmed absence."""
    if sha256(raw).hexdigest() != receipt["raw_sha256"]:
        raise ValueError("raw_hash_mismatch")
    if receipt["http_status"] != 200 or receipt["transport"] != "RESPONSE":
        return dict(
            qualification_state=State.ACCESS.value,
            eps_value=None,
            denial_reasons=["public_source_request_not_successful"],
        )
    try:
        observation = yahoo_observation(
            raw, security, datetime.fromisoformat(receipt["retrieved_at"])
        )
        result = qualify(security, observation)
        return dict(
            record=result.model_dump(mode="json"), observation=observation.model_dump(mode="json")
        )
    except (KeyError, ValueError, TypeError, IndexError, InvalidOperation) as exc:
        return dict(
            qualification_state=State.INVALID.value,
            eps_value=None,
            denial_reasons=[type(exc).__name__ + ":" + str(exc)[:100]],
        )


def composite(records):
    """No implicit provider preference, cross-source field filling or horizon overwrite."""
    result = {}
    for record in records:
        record = ForwardEPS.model_validate(record)
        key = (record.security.ticker, record.horizon_kind)
        if key in result:
            raise ValueError("explicit_composite_owner_required")
        result[key] = record
    return result
