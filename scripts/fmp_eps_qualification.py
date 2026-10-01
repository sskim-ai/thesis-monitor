"""Offline FMP annual EPS qualification. Not a production valuation feed."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
import fcntl
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel
from scripts.businessquant_eps_qualification import _object, number
from scripts.us_forward_eps_qualification import Security, US14

ROUTE = "https://financialmodelingprep.com/stable/analyst-estimates"
ACCOUNTING = "PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED"
LATEST = "ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT"


class State(StrEnum):
    POSITIVE = "QUALIFIED_FY1_EPS_POSITIVE"
    NONPOSITIVE = "QUALIFIED_FY1_EPS_NONPOSITIVE"
    UNAVAILABLE = "UNAVAILABLE_ESTIMATE"
    UNSUPPORTED = "SOURCE_UNSUPPORTED_SECURITY"
    ENTITLEMENT = "SOURCE_ENTITLEMENT_GAP"
    RATE = "SOURCE_RATE_LIMIT"
    IDENTITY = "IDENTITY_MISMATCH_OR_UNRESOLVED"
    PERIOD = "PERIOD_IDENTITY_UNRESOLVED"
    BASIS = "CURRENCY_OR_SHARE_BASIS_UNRESOLVED"
    ADR = "ADR_BASIS_UNRESOLVED"
    INVALID = "SOURCE_RESPONSE_INVALID"


class PeriodOwner(ContractModel):
    ticker: str
    latest_completed_fy: int
    latest_completed_period_end: date
    source: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_available_at: date


class BasisProof(ContractModel):
    ticker: str
    provider_raw_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reporting_currency: str = Field(pattern=r"^[A-Z]{3}$")
    reporting_currency_source: str = Field(min_length=1)
    share_basis: Literal["LISTED_SHARE", "LISTED_ADS"]
    share_basis_source: str = Field(min_length=1)
    provider_series_scope_source: str = Field(min_length=1)
    adr_ratio: Decimal | None = None
    adr_ratio_source: str | None = None


class FY1(ContractModel):
    ticker: str
    provider: Literal["FMP"] = "FMP"
    provider_symbol: str | None = None
    latest_completed_fy: int | None = None
    fy1_fiscal_year: int | None = None
    fy1_period_end: date | None = None
    fy1_eps_avg: Decimal | None = None
    fy1_eps_high: Decimal | None = None
    fy1_eps_low: Decimal | None = None
    num_analysts_eps: int | None = None
    estimate_asof: None = None
    estimate_date_state: str = LATEST
    accounting_basis_state: Literal["PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED"] = ACCOUNTING
    currency: str | None = None
    currency_state: str = "UNRESOLVED"
    share_basis_state: str = "UNRESOLVED"
    security_kind: Literal["COMMON", "ADS"]
    adr_ratio_state: str = "NOT_APPLICABLE"
    qualification_state: State
    additional_states: tuple[str, ...] = ()
    raw_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    retrieved_at: datetime
    source_pointer: str | None = None
    period_owner: PeriodOwner | None = None
    basis_proof: BasisProof | None = None
    annual_selection_valid: bool = False
    production_consumption: Literal[False] = False

    @model_validator(mode="after")
    def ownership(self):
        if self.retrieved_at.utcoffset() is None:
            raise ValueError("timezone_required")
        positive = self.qualification_state == State.POSITIVE
        qualified = positive or self.qualification_state == State.NONPOSITIVE
        if qualified:
            p, b = self.period_owner, self.basis_proof
            expected_basis = "LISTED_ADS" if self.security_kind == "ADS" else "LISTED_SHARE"
            if (
                p is None
                or b is None
                or not self.annual_selection_valid
                or p.ticker != self.ticker
                or b.ticker != self.ticker
                or self.provider_symbol != self.ticker
                or not self.source_pointer
                or b.provider_raw_sha256 != self.raw_sha256
                or self.latest_completed_fy != p.latest_completed_fy
                or self.fy1_fiscal_year != p.latest_completed_fy + 1
                or self.fy1_period_end is None
                or self.fy1_period_end <= p.latest_completed_period_end
                or self.fy1_eps_avg is None
                or not self.fy1_eps_avg.is_finite()
                or self.currency != b.reporting_currency
                or b.share_basis != expected_basis
                or self.share_basis_state != expected_basis
                or self.currency_state != "PROVEN_REPORTING_CURRENCY"
            ):
                raise ValueError("qualified_ownership_gap")
            if (self.fy1_eps_avg > 0) != positive:
                raise ValueError("sign_state_mismatch")
        elif any(v is not None for v in (self.fy1_eps_avg, self.fy1_eps_high, self.fy1_eps_low)):
            raise ValueError("denied_numeric_value_must_be_null")
        return self


def public_request(ticker: str) -> dict:
    if ticker not in US14:
        raise ValueError("outside_monitored_universe")
    return dict(route=ROUTE, params=dict(symbol=ticker, period="annual", page=0, limit=10))


def qualify(
    security: Security,
    raw: bytes,
    *,
    http_status: int | None,
    retrieved_at: datetime,
    raw_sha256: str,
    period_owner: PeriodOwner | None,
    basis: BasisProof | None = None,
    period: str = "annual",
) -> FY1:
    """Bind the earliest annual forecast after the independently owned completed FY."""
    s = Security.model_validate(security)
    p = PeriodOwner.model_validate(period_owner) if period_owner is not None else None
    common = dict(
        ticker=s.ticker,
        security_kind=s.kind,
        raw_sha256=raw_sha256,
        retrieved_at=retrieved_at,
        latest_completed_fy=p.latest_completed_fy if p else None,
        period_owner=p,
        adr_ratio_state="UNRESOLVED" if s.kind == "ADS" else "NOT_APPLICABLE",
    )

    def result(state, *reasons, **fields):
        return FY1(**(common | fields), qualification_state=state, additional_states=reasons)

    if sha256(raw).hexdigest() != raw_sha256:
        return result(State.INVALID, "RAW_HASH_MISMATCH")
    if http_status == 429:
        return result(State.RATE, "HTTP_RATE_LIMIT")
    if http_status in (402, 403):
        return result(State.ENTITLEMENT, "HTTP_ACCESS_DENIED")
    if http_status == 401:
        return result(State.INVALID, "AUTHENTICATION_REJECTED")
    if http_status != 200:
        return result(State.INVALID, "HTTP_OR_TRANSPORT_FAILURE")
    try:
        body = json.loads(raw, parse_float=Decimal, object_pairs_hook=_object)
        if isinstance(body, dict):
            message = str(body.get("Error Message", body.get("error", ""))).lower()
            if any(
                word in message
                for word in ("subscription", "premium", "upgrade", "restricted", "plan")
            ):
                return result(State.ENTITLEMENT, "PROVIDER_PLAN_ERROR")
            if "limit" in message:
                return result(State.RATE, "PROVIDER_RATE_ERROR")
            if "symbol" in message and any(w in message for w in ("not found", "unsupported")):
                return result(State.UNSUPPORTED, "PROVIDER_UNSUPPORTED_SYMBOL")
            raise ValueError("array_required")
        if not isinstance(body, list):
            raise ValueError("array_required")
        if not body:
            return result(State.UNAVAILABLE, "VALID_EMPTY_RESULT")
        if any(not isinstance(row, dict) for row in body):
            raise ValueError("row_object_required")
        if any(row.get("symbol") != s.ticker for row in body):
            return result(State.IDENTITY, "EXACT_LISTED_SYMBOL_REQUIRED")
        common["provider_symbol"] = s.ticker
        if period != "annual" or p is None:
            return result(State.PERIOD, "ANNUAL_REQUEST_AND_COMPLETED_FY_OWNER_REQUIRED")
        if (
            p.ticker != s.ticker
            or p.latest_completed_period_end > retrieved_at.date()
            or p.source_available_at > retrieved_at.date()
        ):
            return result(State.PERIOD, "COMPLETED_FY_OWNER_IDENTITY_OR_AVAILABILITY")
        rows = {}
        for i, row in enumerate(body):
            end = date.fromisoformat(row["date"])
            if end.isoformat() != row["date"] or end in rows:
                raise ValueError("ambiguous_period")
            rows[end] = (i, row)
        future = sorted(end for end in rows if end > p.latest_completed_period_end)
        if not future:
            return result(State.UNAVAILABLE, "NO_FUTURE_ANNUAL_ROW")
        end = future[0]
        # A stale completed-FY owner must not turn already-ended forecasts into FY1.
        if end <= retrieved_at.date() or end.year - p.latest_completed_period_end.year != 1:
            return result(State.PERIOD, "STALE_OWNER_OR_MISSING_FIRST_ANNUAL_FORECAST")
        ordinal, row = rows[end]
        avg, high, low = (number(row.get(k)) for k in ("epsAvg", "epsHigh", "epsLow"))
        analysts = row.get("numAnalystsEps")
        if analysts is not None and (type(analysts) is not int or analysts < 0):
            raise ValueError("analyst_count_invalid")
        if avg is None or analysts == 0:
            return result(State.UNAVAILABLE, "EPS_OR_ANALYST_COVERAGE_ABSENT")
        if (high is not None and high < avg) or (low is not None and low > avg):
            raise ValueError("estimate_bounds_invalid")
        common.update(
            fy1_period_end=end,
            fy1_fiscal_year=p.latest_completed_fy + 1,
            source_pointer=f"/{ordinal}/epsAvg",
            annual_selection_valid=True,
        )
        b = BasisProof.model_validate(basis) if basis is not None else None
        expected_basis = "LISTED_ADS" if s.kind == "ADS" else "LISTED_SHARE"
        if (
            b is None
            or b.ticker != s.ticker
            or b.provider_raw_sha256 != raw_sha256
            or b.reporting_currency != s.currency
            or b.share_basis != expected_basis
        ):
            return result(
                State.ADR if s.kind == "ADS" else State.BASIS,
                "EPS_CURRENCY_AND_LISTED_SHARE_PROOF_REQUIRED",
            )
        if s.kind == "ADS" and (
            b.adr_ratio is None
            or not b.adr_ratio.is_finite()
            or b.adr_ratio <= 0
            or not b.adr_ratio_source
        ):
            return result(State.ADR, "EXACT_ADS_SCOPE_AND_RATIO_REQUIRED")
        return result(
            State.POSITIVE if avg > 0 else State.NONPOSITIVE,
            "ACCOUNTING_BASIS_UNSPECIFIED",
            LATEST,
            fy1_eps_avg=avg,
            fy1_eps_high=high,
            fy1_eps_low=low,
            num_analysts_eps=analysts,
            currency=b.reporting_currency,
            currency_state="PROVEN_REPORTING_CURRENCY",
            share_basis_state=b.share_basis,
            adr_ratio_state="PROVEN_LISTED_ADS" if s.kind == "ADS" else "NOT_APPLICABLE",
            basis_proof=b,
        )
    except (ValueError, TypeError, KeyError):
        return result(State.INVALID, "RESPONSE_SCHEMA_OR_BASIS_INVALID")


def reserve_call(directory: Path, ticker: str, *, retry: bool = False) -> Path:
    """Persist intent before dispatch; crashes are conservatively charged to budget."""
    public_request(ticker)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (directory / "CLOSED").exists():
            raise ValueError("acquisition_closed")
        reservations = sorted(directory.glob("*-attempt-*.json"))
        if len(reservations) >= 16:
            raise ValueError("normal_hard_cap")
        prior = sorted(directory.glob(f"{ticker}-attempt-*.json"))
        if prior and not retry:
            raise ValueError("duplicate_call_use_offline_replay")
        if retry:
            if len(prior) != 1 or len(list(directory.glob("*-attempt-2.json"))) >= 2:
                raise ValueError("retry_budget")
            receipt_path = directory / (ticker + "-response.json")
            receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {}
            code = receipt.get("http_status")
            if receipt.get("valid_response_body") is not False or not (
                receipt.get("transport_failure") is True
                or isinstance(code, int)
                and 500 <= code <= 599
            ):
                raise ValueError("retry_requires_empty_transport_or_5xx")
        path = directory / f"{ticker}-attempt-{2 if retry else 1}.json"
        with path.open("x") as stream:
            json.dump(dict(ticker=ticker, retry=retry, request=public_request(ticker)), stream)
        return path
