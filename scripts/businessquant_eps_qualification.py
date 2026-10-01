"""Offline Business Quant EPS qualification; no network or runtime integration."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel
from scripts.us_forward_eps_qualification import Security, US14

ROUTE = "https://data.businessquant.com/estimates"
ACCOUNTING = "PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED"
LATEST = "ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT"


class State(StrEnum):
    POSITIVE = "QUALIFIED_FY1_EPS_POSITIVE"
    NONPOSITIVE = "QUALIFIED_FY1_EPS_NONPOSITIVE"
    UNAVAILABLE = "UNAVAILABLE_ESTIMATE"
    UNSUPPORTED = "SOURCE_UNSUPPORTED_SECURITY"
    IDENTITY = "IDENTITY_MISMATCH"
    PERIOD = "PERIOD_IDENTITY_UNRESOLVED"
    BASIS = "CURRENCY_OR_SHARE_BASIS_UNRESOLVED"
    ADR = "ADR_BASIS_UNRESOLVED"
    INVALID = "SOURCE_RESPONSE_INVALID"
    ENTITLEMENT = "SOURCE_ENTITLEMENT_GAP"
    RATE = "SOURCE_RATE_LIMIT"


class ExpectedSecurity(Security):
    cik: str = Field(pattern=r"^[0-9]{1,10}$")
    issuer_identity_source: str = Field(min_length=1)


class HistoricalEPS(ContractModel):
    fiscal_year: int
    value: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    share_basis: Literal["LISTED_SHARE", "LISTED_ADS"]
    authoritative_source: str = Field(min_length=1)


class BasisProof(ContractModel):
    ticker: str
    cik: str
    provider_raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    currency: str
    share_basis: Literal["LISTED_SHARE", "LISTED_ADS"]
    series_scope_source: str = Field(min_length=1)
    historical: tuple[HistoricalEPS, ...]
    adr_ratio: Decimal | None = None
    adr_ratio_source: str | None = None


class FY1(ContractModel):
    ticker: str
    provider: Literal["BUSINESS_QUANT"] = "BUSINESS_QUANT"
    metric: Literal["EPS"] = "EPS"
    estimate_family: Literal["WALL_STREET_CONSENSUS"] = "WALL_STREET_CONSENSUS"
    horizon_kind: Literal["FY1"] = "FY1"
    provider_ticker: str | None = None
    provider_cik: str | None = None
    latest_completed_fy: int | None = None
    fy1_fiscal_year: int | None = None
    fy1_eps: Decimal | None = None
    high_estimate: Decimal | None = None
    low_estimate: Decimal | None = None
    accounting_basis_state: Literal["PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED"] = ACCOUNTING
    estimate_asof: None = None
    estimate_date_state: str = LATEST
    retrieved_at: datetime
    security_kind: str
    eps_currency: str | None = None
    currency_basis_state: str = "UNRESOLVED"
    share_basis_state: str = "UNRESOLVED"
    adr_ratio_state: str = "NOT_APPLICABLE"
    qualification_state: State
    additional_states: tuple[str, ...] = ()
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_pointer: str | None = None
    basis_proof: BasisProof | None = None
    production_consumption: Literal[False] = False

    @model_validator(mode="after")
    def no_denied_values(self):
        if self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieval_timezone_required")
        qualified = self.qualification_state in (State.POSITIVE, State.NONPOSITIVE)
        if qualified:
            if (
                self.fy1_eps is None
                or not self.fy1_eps.is_finite()
                or self.provider_ticker != self.ticker
                or self.basis_proof is None
                or self.basis_proof.provider_raw_sha256 != self.raw_sha256
                or not self.source_pointer
                or self.latest_completed_fy is None
                or self.fy1_fiscal_year != self.latest_completed_fy + 1
                or self.eps_currency is None
                or self.currency_basis_state != "PROVEN_FROM_EPS_EVIDENCE"
            ):
                raise ValueError("qualified_value_ownership_gap")
            if (self.fy1_eps > 0) != (self.qualification_state == State.POSITIVE):
                raise ValueError("sign_state_mismatch")
        elif any(v is not None for v in (self.fy1_eps, self.high_estimate, self.low_estimate)):
            raise ValueError("denied_numeric_value_must_be_null")
        return self


def number(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("numeric_type_invalid")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("numeric_not_finite")
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _basis_matches(s, proof, raw_hash, reported):
    if proof is None:
        return False
    p = BasisProof.model_validate(proof)
    expected_basis = "LISTED_ADS" if s.kind == "ADS" else "LISTED_SHARE"
    if (
        p.ticker != s.ticker
        or p.cik.lstrip("0") != s.cik.lstrip("0")
        or p.provider_raw_sha256 != raw_hash
        or p.currency != s.currency
        or p.share_basis != expected_basis
    ):
        return False
    # Exact Decimal equality only. No similarity threshold or implied FX/ADR conversion.
    years = set()
    for item in p.historical:
        if (
            item.fiscal_year in years
            or item.currency != p.currency
            or item.share_basis != p.share_basis
            or not item.value.is_finite()
            or reported.get(item.fiscal_year) != item.value
        ):
            return False
        years.add(item.fiscal_year)
    if len(years) < 2:
        return False
    if s.kind == "ADS" and (
        p.adr_ratio is None
        or not p.adr_ratio.is_finite()
        or p.adr_ratio <= 0
        or not p.adr_ratio_source
    ):
        return False
    return True


def qualify(
    security: ExpectedSecurity,
    raw: bytes,
    *,
    http_status: int | None,
    retrieved_at: datetime,
    raw_sha256: str,
    basis: BasisProof | None = None,
) -> FY1:
    """HTTP success is not entitlement, identity, or denominator authority."""
    s = ExpectedSecurity.model_validate(security)
    common = dict(
        ticker=s.ticker,
        retrieved_at=retrieved_at,
        security_kind=s.kind,
        raw_sha256=raw_sha256,
        adr_ratio_state="UNRESOLVED" if s.kind == "ADS" else "NOT_APPLICABLE",
    )

    def result(state, *reasons, **fields):
        return FY1(**(common | fields), qualification_state=state, additional_states=reasons)

    if sha256(raw).hexdigest() != raw_sha256:
        return result(State.INVALID, "RAW_HASH_MISMATCH")
    if http_status == 429:
        return result(State.RATE, "HTTP_RATE_LIMIT")
    if http_status in (401, 403):
        return result(State.ENTITLEMENT, "HTTP_ACCESS_DENIED")
    if http_status != 200:
        return result(State.INVALID, "HTTP_OR_TRANSPORT_FAILURE_NOT_ESTIMATE_UNAVAILABLE")
    try:
        basis = BasisProof.model_validate(basis) if basis is not None else None
        body = json.loads(raw, parse_float=Decimal, object_pairs_hook=_object)
        if not isinstance(body, dict) or not isinstance(body.get("metadata"), dict):
            raise ValueError("metadata_missing")
        meta = body["metadata"]
        ticker, cik = meta.get("ticker"), meta.get("cik")
        if (
            not isinstance(ticker, str)
            or isinstance(cik, bool)
            or not re.fullmatch(r"[0-9]{1,10}", str(cik))
        ):
            raise ValueError("metadata_identity_type")
        identity = dict(provider_ticker=ticker, provider_cik=str(cik))
        if ticker != s.ticker or str(cik).lstrip("0") != s.cik.lstrip("0"):
            note = str(meta.get("notes", "")).lower()
            if "free preview" in note and "paid plan" in note:
                return result(
                    State.ENTITLEMENT, "IDENTITY_MISMATCH", "FREE_PREVIEW_SUBSTITUTED", **identity
                )
            return result(State.IDENTITY, "EXACT_TICKER_CIK_MISMATCH", **identity)
        if meta.get("mode") != "eps" or meta.get("metric_display") != "eps":
            raise ValueError("metric_mismatch")
        groups = body.get("data")
        if not isinstance(groups, list):
            raise ValueError("data_not_array")
        if any(not isinstance(g, dict) for g in groups):
            raise ValueError("dimension_not_object")
        annual = [g for g in groups if g.get("dimension") == "annual"]
        if not annual:
            return result(State.PERIOD, "ANNUAL_DIMENSION_MISSING", **identity)
        if len(annual) != 1 or not isinstance(annual[0].get("estimates"), list):
            raise ValueError("annual_dimension_ambiguous")
        rows = annual[0]["estimates"]
        by_year = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not re.fullmatch(
                r"[0-9]{4}", str(row.get("period", ""))
            ):
                raise ValueError("annual_fiscal_label_invalid")
            year = int(row["period"])
            if year in by_year or row.get("data_type") not in ("reported", "estimate"):
                raise ValueError("annual_row_ambiguous")
            actual = number(row.get("value_reported"))
            if (row["data_type"] == "reported") != (actual is not None):
                raise ValueError("reported_estimate_semantics_conflict")
            by_year[year] = (index, row, actual)
        reported = {
            y: actual for y, (_, r, actual) in by_year.items() if r["data_type"] == "reported"
        }
        if not reported:
            return result(State.PERIOD, "LATEST_REPORTED_FY_MISSING", **identity)
        completed = max(reported)
        future = sorted(
            y for y, (_, r, _) in by_year.items() if r["data_type"] == "estimate" and y > completed
        )
        fields = dict(**identity, latest_completed_fy=completed)
        if not future:
            return result(State.UNAVAILABLE, "FORWARD_ANNUAL_ESTIMATE_MISSING", **fields)
        selected = future[0]
        fields["fy1_fiscal_year"] = selected
        if selected != completed + 1:
            return result(State.PERIOD, "FIRST_FUTURE_YEAR_GAP", **fields)
        index, row, _ = by_year[selected]
        value = number(row.get("value_estimate"))
        if value is None:
            return result(State.UNAVAILABLE, "CONSENSUS_VALUE_MISSING", **fields)
        high, low = number(row.get("high_estimate")), number(row.get("low_estimate"))
        if (high is not None and high < value) or (low is not None and low > value):
            raise ValueError("consensus_range_conflict")
        if not _basis_matches(s, basis, raw_sha256, reported):
            return result(
                State.ADR if s.kind == "ADS" else State.BASIS,
                "EPS_SERIES_BASIS_NOT_PROVEN",
                **fields,
            )
        annual_index = groups.index(annual[0])
        return result(
            State.POSITIVE if value > 0 else State.NONPOSITIVE,
            "ACCOUNTING_BASIS_UNSPECIFIED",
            LATEST,
            **fields,
            fy1_eps=value,
            high_estimate=high,
            low_estimate=low,
            eps_currency=basis.currency,
            currency_basis_state="PROVEN_FROM_EPS_EVIDENCE",
            share_basis_state=basis.share_basis,
            adr_ratio_state="PROVEN_WITH_SERIES_BASIS" if s.kind == "ADS" else "NOT_APPLICABLE",
            basis_proof=basis,
            source_pointer=f"/data/{annual_index}/estimates/{index}/value_estimate",
        )
    except (ValueError, TypeError, KeyError, InvalidOperation):
        return result(State.INVALID, "JSON_OR_RESPONSE_CONTRACT_INVALID")


def public_request(ticker: str) -> dict:
    if ticker not in US14:
        raise ValueError("ticker_outside_frozen_universe")
    return dict(
        route=ROUTE, parameters=dict(ticker=ticker, mode="eps"), authentication_redacted=True
    )


def reserve_call(directory: Path, ticker: str) -> dict:
    """Crash-safe one-shot reservation; no transport retries implemented or required."""
    request = public_request(ticker)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if len(list(directory.glob("data-*.json"))) >= 18:
            raise ValueError("TASK_18_CALL_CAP")
        with (directory / f"data-{ticker}.json").open("x") as target:
            json.dump(request, target, sort_keys=True)
    return request
