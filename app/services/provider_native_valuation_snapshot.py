"""Atomic provider ratios, separate from price/denominator reconstruction.

Pure replay only. Acquisition must bind raw responses to one declared run.
The explicit REV28 policy permits latest-provider context, not same-session
fundamentals, ADR transfer, EPS reconstruction or business-direction evidence.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest

PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT = True
PROVIDER_NATIVE_FORWARD_PE_SNAPSHOT_ALLOWED_FOR_VALUATION_CONTEXT = True
FORWARD_QUALIFIED = "QUALIFIED_PROVIDER_FORWARD_PE_SNAPSHOT_UNSPECIFIED_HORIZON"
FORWARD_FY1_QUALIFIED = "QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE"
FORWARD_SEMANTIC = ("forwardPE", "PROVIDER_REPORTED_FORWARD_PE")
# Pin captured field-specific provenance before claiming an official definition.
# The current official captures do not contain a forwardPE field definition.
FINNHUB_FORWARD_FY1_PROVENANCE: dict | None = None
FINNHUB_FORWARD_FY1_PRODUCT_POLICY = {
    "contract": "finnhub-forwardpe-fy1-product-policy-v1",
    "horizon_authority": "USER_AUTHORIZED_PRODUCT_POLICY",
    "provider": "finnhub",
    "provider_field": "forwardPE",
    "canonical_horizon": "FY1",
    "estimate_basis": "ANALYST_ESTIMATES_FORWARD",
    "owner_kind": "PROVIDER_NATIVE_ATOMIC_RATIO",
    "REV44_document_capture_FY1_definition": "NOT_REPRODUCED",
    "authorization_reference": "20261002-r2b-r9-rev45-fy1-forwardpe-us-fresh-kr-fresh-main-integration",
}


def forward_horizon_metadata():
    fy1 = FINNHUB_FORWARD_FY1_PROVENANCE is not None
    policy = FINNHUB_FORWARD_FY1_PRODUCT_POLICY if not fy1 else None
    return dict(
        forward_horizon_state="PROVIDER_FORWARD_HORIZON_FY1"
        if fy1
        else "CANONICAL_FORWARD_HORIZON_FY1" if policy else "PROVIDER_FORWARD_HORIZON_UNSPECIFIED",
        provider_horizon="NEXT_FISCAL_YEAR" if fy1 else None,
        estimate_basis="ANALYST_ESTIMATES" if fy1 else "ANALYST_ESTIMATES_FORWARD" if policy else None,
        provider_definition=FINNHUB_FORWARD_FY1_PROVENANCE,
        canonical_horizon="FY1" if fy1 or policy else None,
        horizon_authority="OFFICIAL_FIELD_DEFINITION" if fy1 else "USER_AUTHORIZED_PRODUCT_POLICY" if policy else None,
        horizon_policy=policy,
        display_label="fPER(FY1)" if fy1 or policy else "Finnhub Forward P/E",
    )


INPUT_CONTRACT = "provider-native-valuation-input-v1"
KIWOOM_ROUTE = "https://api.kiwoom.com/api/dostk/stkinfo"
FINNHUB_BASE = "https://finnhub.io/api/v1/stock/"
FIELDS = {
    "kiwoom": {"PER": ("per", "PROVIDER_REPORTED_PER"), "PBR": ("pbr", "PROVIDER_REPORTED_PBR")},
    "finnhub": {
        "PER": ("peTTM", "PROVIDER_REPORTED_TTM_PER"),
        "PBR": ("pbQuarterly", "PROVIDER_REPORTED_QUARTERLY_PBR"),
    },
}
MARKETS = {
    "0": ("KOSPI", "\ucf54\uc2a4\ud53c", "\uac70\ub798\uc18c"),
    "10": ("KOSDAQ", "\ucf54\uc2a4\ub2e5"),
}


class ProviderNativeValuationSnapshot(ContractModel):
    contract: Literal["provider-native-valuation-snapshot-v1"] = (
        "provider-native-valuation-snapshot-v1"
    )
    policy: Literal[True] = True
    run_id: str
    provider: Literal["kiwoom", "finnhub"]
    route: str
    api_id: str | None
    requested_security_id: str
    returned_security_id: str | None
    canonical_security_id: str
    security_sha256: str
    security_identity_receipt: dict
    market_exchange: str | None
    currency: str | None
    currency_role: Literal["COMPANY_FILING_CURRENCY", "NOT_REPORTED_BY_ENDPOINT"]
    metric: Literal["PER", "PBR"]
    provider_field: str
    metric_semantic: str
    state: str
    value: float | None = Field(default=None, allow_inf_nan=False)
    retrieval_timestamp: datetime
    snapshot_role: Literal["PROVIDER_LATEST_SNAPSHOT"] = "PROVIDER_LATEST_SNAPSHOT"
    update_policy: str | None
    metric_asof: date | None = None
    underlying_denominator_period: None = None
    raw_sha256: str
    source_receipt_sha256: str
    display_eligible: bool
    new_buyer_valuation_context_eligible: bool
    holder_valuation_context_eligible: bool
    overall_direction_use: Literal[False] = False
    same_session_recomputation: Literal[False] = False
    caveats: tuple[str, ...]
    snapshot_sha256: str

    @model_validator(mode="after")
    def bound(self):
        if self.snapshot_sha256 != digest(
            self.model_dump(mode="json", exclude={"snapshot_sha256"})
        ):
            raise ValueError("native_snapshot_binding_mismatch")
        for value in (self.raw_sha256, self.source_receipt_sha256, self.security_sha256):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("native_snapshot_hash_required")
        identity = self.security_identity_receipt
        if identity.get("receipt_sha256") != digest(
            {k: v for k, v in identity.items() if k != "receipt_sha256"}
        ):
            raise ValueError("native_snapshot_identity_binding")
        if (
            identity.get("run_id") != self.run_id
            or identity.get("security_sha256") != self.security_sha256
            or identity.get("canonical_security_id") != self.canonical_security_id
        ):
            raise ValueError("native_snapshot_identity_scope")
        expected_field = (
            FORWARD_SEMANTIC if self.metric == "FORWARD_PE" else FIELDS[self.provider][self.metric]
        )
        if (self.provider_field, self.metric_semantic) != expected_field:
            raise ValueError("native_snapshot_field_semantic")
        if self.route != (KIWOOM_ROUTE if self.provider == "kiwoom" else FINNHUB_BASE + "metric"):
            raise ValueError("native_snapshot_route")
        if self.api_id != ("ka10001" if self.provider == "kiwoom" else None):
            raise ValueError("native_snapshot_api_id")
        qualified = self.state in (
            {FORWARD_QUALIFIED, FORWARD_FY1_QUALIFIED}
            if self.metric == "FORWARD_PE"
            else {"QUALIFIED_PROVIDER_LATEST_SNAPSHOT"}
        )
        if (
            self.display_eligible,
            self.new_buyer_valuation_context_eligible,
            self.holder_valuation_context_eligible,
        ) != (qualified,) * 3:
            raise ValueError("native_snapshot_permissions")
        if qualified:
            if (
                self.value is None
                or self.value <= 0
                or identity.get("status") != "QUALIFIED_EXACT_SECURITY"
                or self.returned_security_id != self.requested_security_id
            ):
                raise ValueError("native_snapshot_positive_authority_required")
        elif self.value is not None or (
            not self.state.startswith("UNAVAILABLE_")
            and not (
                self.metric == "FORWARD_PE"
                and self.state
                in {"INVALID_FORWARD_PE", "IDENTITY_MISMATCH", "SOURCE_RESPONSE_INVALID"}
            )
        ):
            raise ValueError("native_snapshot_unavailable_value")
        if self.retrieval_timestamp.utcoffset() is None or not self.caveats:
            raise ValueError("native_snapshot_time_caveat_required")
        return self


class ProviderNativeForwardValuationSnapshot(ProviderNativeValuationSnapshot):
    """Atomic multiple; product policy and provider definition stay distinct."""

    provider: Literal["finnhub"]
    metric: Literal["FORWARD_PE"] = "FORWARD_PE"
    state: Literal[
        "QUALIFIED_PROVIDER_FORWARD_PE_SNAPSHOT_UNSPECIFIED_HORIZON",
        "QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE",
        "UNAVAILABLE_FORWARD_PE",
        "INVALID_FORWARD_PE",
        "IDENTITY_MISMATCH",
        "UNAVAILABLE_ADR_FORWARD_VALUATION_IDENTITY",
        "UNAVAILABLE_ADR_FORWARD_VALUATION_CONVERSION",
        "SOURCE_RESPONSE_INVALID",
    ]
    forward_horizon_state: Literal[
        "PROVIDER_FORWARD_HORIZON_UNSPECIFIED", "PROVIDER_FORWARD_HORIZON_FY1",
        "CANONICAL_FORWARD_HORIZON_FY1",
    ] = "PROVIDER_FORWARD_HORIZON_UNSPECIFIED"
    provider_horizon: Literal["NEXT_FISCAL_YEAR"] | None = None
    estimate_basis: Literal["ANALYST_ESTIMATES", "ANALYST_ESTIMATES_FORWARD"] | None = None
    provider_definition: dict | None = None
    canonical_horizon: Literal["FY1"] | None = None
    horizon_authority: Literal["OFFICIAL_FIELD_DEFINITION", "USER_AUTHORIZED_PRODUCT_POLICY"] | None = None
    horizon_policy: dict | None = None
    core_visibility: Literal[False] = False
    pass_a_visibility: Literal[False] = False

    @model_validator(mode="after")
    def horizon_bound(self):
        fy1 = self.forward_horizon_state == "PROVIDER_FORWARD_HORIZON_FY1"
        if fy1:
            if (
                not FINNHUB_FORWARD_FY1_PROVENANCE
                or self.provider_definition != FINNHUB_FORWARD_FY1_PROVENANCE
                or self.provider_horizon != "NEXT_FISCAL_YEAR"
                or self.estimate_basis != "ANALYST_ESTIMATES"
                or self.canonical_horizon != "FY1"
                or self.horizon_authority != "OFFICIAL_FIELD_DEFINITION"
                or self.horizon_policy is not None
                or self.state == FORWARD_QUALIFIED
            ):
                raise ValueError("forward_fy1_official_definition_required")
        elif self.forward_horizon_state == "CANONICAL_FORWARD_HORIZON_FY1":
            if (
                not FINNHUB_FORWARD_FY1_PRODUCT_POLICY
                or self.horizon_policy != FINNHUB_FORWARD_FY1_PRODUCT_POLICY
                or self.horizon_authority != "USER_AUTHORIZED_PRODUCT_POLICY"
                or self.canonical_horizon != "FY1"
                or self.estimate_basis != "ANALYST_ESTIMATES_FORWARD"
                or self.provider_horizon is not None or self.provider_definition is not None
                or self.state == FORWARD_QUALIFIED
            ):
                raise ValueError("forward_fy1_product_policy_binding_required")
        elif (
            self.provider_definition is not None
            or self.provider_horizon is not None
            or self.estimate_basis is not None
            or self.canonical_horizon is not None
            or self.horizon_authority is not None
            or self.horizon_policy is not None
            or self.state == FORWARD_FY1_QUALIFIED
        ):
            raise ValueError("forward_unspecified_definition_overclaim")
        return self

    @property
    def display_label(self):
        return (
            "fPER(FY1)"
            if self.canonical_horizon == "FY1"
            else "Finnhub Forward P/E"
        )


def _response(part, *, inputs, run_id, security, provider, request):
    raw, receipt = part["raw"], part["receipt"]
    inputs["policy"].require("kiwoom_rest" if provider == "kiwoom" else provider)
    if (
        receipt.get("provider") != provider
        or receipt.get("run_id") != run_id
        or receipt.get("security_sha256") != digest(security)
        or receipt.get("source_sha256") != sha256_bytes(raw)
        or receipt.get("acquisition_class") != "FRESH_CURRENT_RUN"
        or receipt.get("http_status") != 200
        or receipt.get("request") != request
        or receipt.get("cache_reused", False)
    ):
        raise ValueError("native_snapshot_source_receipt_mismatch")
    times = [
        inputs["run_started_at"],
        datetime.fromisoformat(receipt["requested_at"]),
        datetime.fromisoformat(receipt["received_at"]),
        inputs["cutoff"],
    ]
    if any(t.utcoffset() is None for t in times) or times != sorted(times):
        raise ValueError("native_snapshot_source_time_mismatch")
    body = json.loads(raw)
    if not isinstance(body, dict) or (provider == "kiwoom" and body.get("return_code") != 0):
        raise ValueError("native_snapshot_provider_response_invalid")
    return body, receipt


def _name(value):
    return "".join(c for c in str(value).casefold() if c.isalnum())


def _exchange(value):
    value = " ".join(str(value or "").upper().split())
    names = {
        "NEW YORK STOCK EXCHANGE, INC.": "NYSE",
        "NEW YORK STOCK EXCHANGE": "NYSE",
        "NASDAQ NMS - GLOBAL MARKET": "NASDAQ",
        "NASDAQ NMS - GLOBAL SELECT MARKET": "NASDAQ",
        "NASDAQ GLOBAL SELECT MARKET": "NASDAQ",
        "NASDAQ GLOBAL MARKET": "NASDAQ",
        "NASDAQ CAPITAL MARKET": "NASDAQ",
    }
    return names.get(value, value)


def _identity(*, inputs, security, body, run_id, provider, metric_receipt):
    ticker = security["ticker"]
    data = inputs["identity_inputs"]
    reasons, bindings = [], [digest(metric_receipt)]
    exchange, currency = None, None
    alias = None
    registered_name_variant = False
    returned = body.get("stk_cd" if provider == "kiwoom" else "symbol")
    kind = str(security.get("security_type", "")).lower()
    if security.get("issuer_type") == "adr" or "depositary" in kind or kind in {"adr", "ads"}:
        reasons.append("UNAVAILABLE_ADR_CONVERSION")
    if returned != ticker:
        reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
    if provider == "kiwoom":
        market = data["market_type"]
        if market not in MARKETS:
            raise ValueError("native_snapshot_kr_market_unsupported")
        pages = data["list_pages"]
        if not pages:
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        matched, previous = [], None
        for page in pages:
            continuation = (
                {}
                if previous is None
                else {"cont-yn": "Y", "next-key": previous["response_headers"].get("next-key")}
            )
            if previous is not None and (
                previous["response_headers"].get("cont-yn") != "Y" or not continuation["next-key"]
            ):
                raise ValueError("native_snapshot_list_continuation_mismatch")
            request = dict(
                method="POST",
                route=KIWOOM_ROUTE,
                api_id="ka10099",
                body={"mrkt_tp": market},
                continuation=continuation,
            )
            payload, receipt = _response(
                page,
                inputs=inputs,
                run_id=run_id,
                security=security,
                provider=provider,
                request=request,
            )
            if not isinstance(payload.get("list"), list):
                raise ValueError("native_snapshot_list_schema")
            matched += [row for row in payload["list"] if row.get("code") == ticker]
            bindings += [sha256_bytes(page["raw"]), digest(receipt)]
            previous = receipt
        if len(matched) != 1:
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        else:
            row = matched[0]
            exchange = row.get("marketName")
            alias_owner = data.get("reviewed_alias_owner")
            if alias_owner is not None:
                from app.services.reviewed_security_alias import ReviewedSecurityAliases
                if not isinstance(alias_owner, ReviewedSecurityAliases):
                    raise ValueError("backend_alias_owner_required")
                alias = alias_owner.translate(security=security, provider=provider,
                    provider_code=row.get("code"), provider_name=row.get("name"),
                    market=market, provider_class=row.get("kind"),
                    observed_at=metric_receipt["received_at"])
                bindings.append(digest(alias))
            if (
                row.get("marketCode") != market
                or exchange not in MARKETS[market]
                or security.get("exchange") not in {"KRX", MARKETS[market][0]}
                or security.get("country") != "KR"
                or not isinstance(row.get("name"), str)
                or not isinstance(body.get("stk_nm"), str)
                or not _name(row.get("name"))
                or not _name(body.get("stk_nm"))
                or _name(body.get("stk_nm")) != _name(row.get("name"))
            ):
                reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
            registered_name_variant = _name(row.get("name")) != _name(security.get("company_name"))
            bindings.append(digest(row))
        contract = "kiwoom-exact-security-code-identity-v1"
    else:
        profile, receipt = _response(
            data["profile"],
            inputs=inputs,
            run_id=run_id,
            security=security,
            provider=provider,
            request=dict(method="GET", route=FINNHUB_BASE + "profile2", params={"symbol": ticker}),
        )
        bindings += [digest(receipt), sha256_bytes(data["profile"]["raw"])]
        exchange, currency = _exchange(profile.get("exchange")), profile.get("currency")
        official = data.get("official_identity")
        if official:
            evidence = OfficialSecurityIdentityEvidence.from_payload(official)
            bindings.append(digest(official))
            if (
                digest(official) != data.get("official_identity_sha256")
                or official != evidence.to_payload()
                or urlsplit(evidence.source_url).hostname != "www.sec.gov"
                or not urlsplit(evidence.source_url).path.startswith("/Archives/edgar/data/")
                or evidence.ticker != ticker
                or _exchange(evidence.exchange) != _exchange(security.get("exchange"))
                or evidence.security_type != "common_stock"
                or evidence.share_class != security.get("share_class")
                or evidence.cik != security.get("cik")
                or not evidence.filing_accession
                or date.fromisoformat(evidence.as_of_date) > inputs["cutoff"].date()
            ):
                reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        if (
            security.get("security_type") != "common_stock"
            or not ticker or not security.get("canonical_security_id")
            or profile.get("ticker") != ticker
            or exchange not in {"NASDAQ", "NYSE"}
            or exchange != _exchange(security.get("exchange"))
            or currency != "USD"
            or security.get("currency", "USD") != "USD"
            or security.get("country") != "US"
        ):
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        # Issuer domicile is not a listing venue or a depositary conversion basis.
        if returned != profile.get("ticker"):
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        contract = "finnhub-direct-us-provider-identity-v2"
    result = dict(
        contract=contract,
        run_id=run_id,
        canonical_security_id=security["canonical_security_id"],
        security_sha256=digest(security),
        requested_security_id=ticker,
        returned_security_id=returned,
        market_exchange=exchange,
        currency=currency,
        input_hashes=bindings,
        status="QUALIFIED_EXACT_SECURITY" if not reasons else reasons[0],
        reasons=sorted(set(reasons)),
    )
    if provider == "finnhub":
        result.update(official_identity_role="OPTIONAL_SUPPORTING_EVIDENCE",
                      official_identity_present=bool(data.get("official_identity")),
                      allowed_fields=("peTTM", "pbQuarterly", "forwardPE"))
    if alias is not None:
        result['name_mapping_proof'] = alias
    if registered_name_variant:
        result['name_diagnostics'] = ['REGISTERED_NAME_VARIANT_NONBLOCKING']
    return dict(**result, receipt_sha256=digest(result))


def _number(value):
    if value is None or value == "":
        return None, "UNAVAILABLE_PROVIDER_FIELD"
    if isinstance(value, bool):
        return None, "UNAVAILABLE_PROVIDER_FIELD"
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        return None, "UNAVAILABLE_PROVIDER_FIELD"
    if not number.is_finite() or number <= 0:
        return (
            None,
            "UNAVAILABLE_PROVIDER_SENTINEL"
            if number.is_finite() and number == 0
            else "UNAVAILABLE_METHOD_BASIS",
        )
    numeric = float(number)
    if numeric == float("inf") or numeric <= 0:
        return None, "UNAVAILABLE_PROVIDER_FIELD"
    return numeric, None


def derive_provider_snapshots(inputs, *, security, run_id):
    if (
        inputs.get("contract") != INPUT_CONTRACT
        or not PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT
    ):
        raise ValueError("native_snapshot_explicit_policy_contract_required")
    ticker = security["ticker"]
    provider = inputs["receipt"]["provider"]
    if provider not in FIELDS:
        raise ValueError("native_snapshot_provider_unsupported")
    request = (
        dict(method="POST", route=KIWOOM_ROUTE, api_id="ka10001", body={"stk_cd": ticker})
        if provider == "kiwoom"
        else dict(
            method="GET", route=FINNHUB_BASE + "metric", params={"symbol": ticker, "metric": "all"}
        )
    )
    body, receipt = _response(
        inputs, inputs=inputs, run_id=run_id, security=security, provider=provider, request=request
    )
    identity = _identity(
        inputs=inputs,
        security=security,
        body=body,
        run_id=run_id,
        provider=provider,
        metric_receipt=receipt,
    )
    fields = body if provider == "kiwoom" else body.get("metric", {})
    if not isinstance(fields, dict):
        raise ValueError("native_snapshot_metric_schema")
    asof, time_reason = None, None
    provided_dates = [body[k] for k in ("metricAsOf", "asOfDate") if body.get(k) is not None]
    if provided_dates:
        try:
            dates = [date.fromisoformat(d) for d in provided_dates]
            if (
                len(set(dates)) != 1
                or dates[0] != datetime.fromisoformat(receipt["received_at"]).date()
            ):
                time_reason = "UNAVAILABLE_CURRENTNESS"
            asof = dates[0]
        except (TypeError, ValueError):
            time_reason = "UNAVAILABLE_CURRENTNESS"
    if body.get("isStale") or body.get("stale") or body.get("cached"):
        time_reason = "UNAVAILABLE_CURRENTNESS"
    metadata_reason = None
    if body.get("currency") is not None and body["currency"] != (identity["currency"] or "KRW"):
        metadata_reason = "UNAVAILABLE_SECURITY_IDENTITY"
    if body.get("shareClass") is not None and body["shareClass"] != security.get("share_class"):
        metadata_reason = "UNAVAILABLE_SECURITY_IDENTITY"
    result = []
    for metric, (field, semantic) in FIELDS[provider].items():
        value, reason = _number(fields.get(field))
        reason = (
            (identity["status"] if identity["status"] != "QUALIFIED_EXACT_SECURITY" else None)
            or time_reason
            or metadata_reason
            or reason
        )
        caveats = ["PROVIDER_SNAPSHOT_NOT_SAME_SESSION_RECOMPUTATION"]
        if asof is None:
            caveats.append("PROVIDER_METRIC_ASOF_NOT_EXPLICIT")
        update = "WEEKLY_OR_EARNINGS_SEASON" if provider == "kiwoom" and metric == "PER" else None
        if update:
            caveats.append("PROVIDER_UPDATE_CADENCE_WEEKLY_OR_EARNINGS_SEASON")
        row = dict(
            run_id=run_id,
            provider=provider,
            route=request["route"],
            api_id=request.get("api_id"),
            requested_security_id=ticker,
            returned_security_id=identity["returned_security_id"],
            canonical_security_id=security["canonical_security_id"],
            security_sha256=digest(security),
            security_identity_receipt=identity,
            market_exchange=identity["market_exchange"],
            currency=identity["currency"],
            currency_role="COMPANY_FILING_CURRENCY"
            if provider == "finnhub"
            else "NOT_REPORTED_BY_ENDPOINT",
            metric=metric,
            provider_field=field,
            metric_semantic=semantic,
            state=reason or "QUALIFIED_PROVIDER_LATEST_SNAPSHOT",
            value=None if reason else value,
            retrieval_timestamp=datetime.fromisoformat(receipt["received_at"]),
            update_policy=update,
            metric_asof=asof,
            raw_sha256=sha256_bytes(inputs["raw"]),
            source_receipt_sha256=digest(receipt),
            display_eligible=not reason,
            new_buyer_valuation_context_eligible=not reason,
            holder_valuation_context_eligible=not reason,
            caveats=tuple(caveats),
        )
        # Pydantic JSON mode is the canonical representation for receipt hashes.
        row = ProviderNativeValuationSnapshot.model_construct(**row, snapshot_sha256="").model_dump(
            mode="json", exclude={"snapshot_sha256"}
        )
        row["snapshot_sha256"] = digest(row)
        result.append(ProviderNativeValuationSnapshot.model_validate(row))
    return tuple(result)


def _signed_finite(value):
    """A nonpositive direct observation is not a usable positive multiple."""
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value).strip())
        result = float(parsed)
    except (InvalidOperation, ValueError, OverflowError):
        return None
    return result if parsed.is_finite() and abs(result) != float('inf') else None


def _quarterly_reference_summary(rows, *, as_of, current):
    """Use provider period observations, not reconstructed point-in-time prices.

    Exact duplicate dates count once; conflicting values for a date do not
    contribute a percentile. Missing observations do not prove a loss.
    """
    from app.services.historical_valuation_service import _percentile
    from calendar import monthrange
    if not isinstance(rows, list):
        return None
    periods = {}
    invalid_dates = future_rows = duplicate_rows = 0
    for row in rows:
        try:
            period = date.fromisoformat(row['period'])
        except (KeyError, TypeError, ValueError):
            invalid_dates += 1
            continue
        if period > as_of:
            future_rows += 1
            continue
        duplicate_rows += int(period in periods)
        periods.setdefault(period, set()).add(_signed_finite(row.get('v')))
    if not periods:
        return None
    start = as_of.replace(year=as_of.year-5,
                         day=min(as_of.day, monthrange(as_of.year-5, as_of.month)[1]))
    def window(selected):
        if not selected:
            return None
        positives = [next(iter(v)) for v in selected.values()
                     if len(v)==1 and next(iter(v)) is not None and next(iter(v))>0]
        nonpositive = sum(len(v)==1 and next(iter(v)) is not None and next(iter(v))<=0
                          for v in selected.values())
        conflicts = sum(len(v)>1 for v in selected.values())
        missing = len(selected)-len(positives)-nonpositive-conflicts
        days = sorted(selected)
        positive_dates = sorted(d for d,v in selected.items()
                                if len(v)==1 and next(iter(v)) is not None and next(iter(v))>0)
        # The common five-year reference window never changes by ticker or
        # price. A price scenario needs more than a handful of observations;
        # smaller/negative-only series remain usable descriptive context.
        result = dict(first_period=days[0].isoformat(), last_period=days[-1].isoformat(),
            observed_periods=len(days), positive_periods=len(positives),
            nonpositive_periods=nonpositive, missing_value_periods=missing,
            conflicting_periods=conflicts,
            first_positive_period=positive_dates[0].isoformat() if positive_dates else None,
            last_positive_period=positive_dates[-1].isoformat() if positive_dates else None,
            price_sample_sufficient=len(positives)>=8 and
                (positive_dates[-1]-positive_dates[0]).days>=365 if positive_dates else False)
        if positives:
            result.update(minimum=min(positives),maximum=max(positives))
            result.update({f'percentile_{p}':round(_percentile(positives,p), 4)
                           for p in (25,50,75,90)})
            if current is not None:
                result['current_percentile']=round(100*sum(v<=current for v in positives)/len(positives),1)
        return result
    return dict(raw_rows=len(rows), duplicate_rows=duplicate_rows,
        invalid_date_rows=invalid_dates, future_rows=future_rows,
        all=window(periods), recent_five_years=window({d:v for d,v in periods.items() if d>=start}),
        recent_window_start=start.isoformat(), as_of=as_of.isoformat())


def provider_reference_context(inputs, snapshots, *, currency, as_of):
    """Read existing admitted native responses, without granting own-EPS basis.

    Field-family comparisons are descriptive product semantics, not a claim
    that the provider has published its exact numerator/denominator algorithm.
    """
    rows = {s.metric:s for s in snapshots if s.metric in ('PER','PBR')}
    if set(rows) != {'PER','PBR'}:
        return None
    per, pb = rows['PER'], rows['PBR']
    identity = per.security_identity_receipt
    if (identity.get('status') != 'QUALIFIED_EXACT_SECURITY'
            or per.returned_security_id != per.requested_security_id
            or per.security_identity_receipt != pb.security_identity_receipt
            or per.provider != pb.provider
            or any(s.state not in {'QUALIFIED_PROVIDER_LATEST_SNAPSHOT',
                                    'UNAVAILABLE_PROVIDER_FIELD','UNAVAILABLE_PROVIDER_SENTINEL',
                                    'UNAVAILABLE_METHOD_BASIS'} for s in (per,pb))
            or any(s.raw_sha256 != sha256_bytes(inputs['raw'])
                   or s.source_receipt_sha256 != digest(inputs['receipt']) for s in (per,pb))):
        return None
    provider = per.provider
    if ((provider == 'kiwoom' and currency != 'KRW')
            or (provider == 'finnhub' and (currency != 'USD' or per.currency != currency))):
        return None
    body = json.loads(inputs['raw'])
    fields = body if provider=='kiwoom' else body.get('metric', {})
    if not isinstance(fields,dict):
        return None
    as_of = date.fromisoformat(str(as_of))
    root = 'native-reference:' + per.canonical_security_id + ':'
    field_specs = (('eps','PER','PROVIDER_PERIOD_UNSPECIFIED'),
                   ('bps','PBR','PROVIDER_PERIOD_UNSPECIFIED')) if provider=='kiwoom' else (
                   ('epsTTM','PER','PROVIDER_TTM'),('bookValuePerShareQuarterly','PBR','PROVIDER_QUARTERLY'))
    direct = []
    for field, metric, period in field_specs:
        value = _signed_finite(fields.get(field))
        if value is not None:
            direct.append(dict(ref_id=root+field,field=field,metric=metric,value=value,
                period=period, period_end=None, currency=currency,
                unit_context='KRW_PER_SHARE_PROVIDER_FIELD' if provider=='kiwoom'
                    else 'USD_PER_SHARE_PROVIDER_FILING_CURRENCY_CONTEXT',
                zero_is_provider_observation_not_proven_zero_earnings=value==0,
                own_denominator_basis_resolved=False))
    histories = []
    if provider=='finnhub':
        series = body.get('series')
        quarterly = series.get('quarterly') if isinstance(series,dict) else None
        if isinstance(quarterly,dict):
            for metric, field in (('PER','peTTM'),('PBR','pb')):
                native = rows[metric]
                summary = _quarterly_reference_summary(quarterly.get(field),as_of=as_of,
                    current=native.value if native.display_eligible else None)
                if summary is None:
                    continue
                histories.append(dict(ref_id=root+'quarterly.'+field,metric=metric,
                    field='series.quarterly.'+field,frequency='PROVIDER_QUARTERLY',
                    current_field=native.provider_field,
                    current_metric_ref='current-valuation:'+per.canonical_security_id+':'+metric,
                    current_value=native.value if native.display_eligible else None,
                    comparison_basis='SAME_PROVIDER_TTM_FIELD_FAMILY' if metric=='PER'
                                     else 'SAME_PROVIDER_QUARTERLY_PB_FIELD_FAMILY',
                    exact_provider_formula_verified=False, **summary))
    if not direct and not histories:
        return None
    return dict(scope='PROVIDER_NATIVE_REFERENCE_NOT_OWN_DENOMINATOR',provider=provider,
        ticker=per.requested_security_id,security_id=per.canonical_security_id,run_id=per.run_id,
        currency=currency,as_of=as_of.isoformat(),raw_sha256=per.raw_sha256,
        source_receipt_sha256=per.source_receipt_sha256,
        snapshot_sha256=[per.snapshot_sha256,pb.snapshot_sha256],
        retrieval_timestamp=per.retrieval_timestamp.isoformat(),
        metric_asof=per.metric_asof.isoformat() if per.metric_asof else None,
        direct=direct,history=histories,overall_direction_use=False)


def derive_forward_snapshot(inputs, *, security, run_id):
    """Consume the existing metric/profile pair; never acquire or reprice data."""
    if not PROVIDER_NATIVE_FORWARD_PE_SNAPSHOT_ALLOWED_FOR_VALUATION_CONTEXT:
        raise ValueError("forward_snapshot_explicit_policy_required")
    if inputs["receipt"]["provider"] != "finnhub":
        raise ValueError("forward_snapshot_finnhub_required")
    # Reuse the exact production source, time, metadata and identity verification.
    per = derive_provider_snapshots(inputs, security=security, run_id=run_id)[0]
    body = json.loads(inputs["raw"])
    raw_value = body.get("metric", {}).get("forwardPE")
    value, numeric_reason = _number(raw_value)
    reason = None
    identity = per.security_identity_receipt
    if "UNAVAILABLE_ADR_CONVERSION" in identity["reasons"]:
        profile = json.loads(inputs["identity_inputs"]["profile"]["raw"])
        remapped = any(
            s is not None and s != security["ticker"]
            for s in (profile.get("ticker"), body.get("symbol"))
        )
        reason = (
            "UNAVAILABLE_ADR_FORWARD_VALUATION_CONVERSION"
            if remapped
            else "UNAVAILABLE_ADR_FORWARD_VALUATION_IDENTITY"
        )
    elif (
        identity["status"] != "QUALIFIED_EXACT_SECURITY"
        or per.state == "UNAVAILABLE_SECURITY_IDENTITY"
    ):
        reason = "IDENTITY_MISMATCH"
    elif per.state == "UNAVAILABLE_CURRENTNESS":
        reason = "SOURCE_RESPONSE_INVALID"
    elif numeric_reason:
        reason = (
            "UNAVAILABLE_FORWARD_PE"
            if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip())
            else "INVALID_FORWARD_PE"
        )
    row = per.model_dump(exclude={"snapshot_sha256"})
    metadata = forward_horizon_metadata()
    metadata.pop("display_label")
    fy1 = metadata["canonical_horizon"] == "FY1"
    horizon = metadata["forward_horizon_state"]
    row.update(
        metric="FORWARD_PE",
        provider_field=FORWARD_SEMANTIC[0],
        metric_semantic=FORWARD_SEMANTIC[1],
        state=reason or (FORWARD_FY1_QUALIFIED if fy1 else FORWARD_QUALIFIED),
        value=None if reason else value,
        display_eligible=not reason,
        new_buyer_valuation_context_eligible=not reason,
        holder_valuation_context_eligible=not reason,
        **metadata,
        caveats=(*per.caveats, horizon, "PROVIDER_FORWARD_DENOMINATOR_NOT_AN_EPS_OWNER",
                 *(() if metadata["horizon_authority"] != "USER_AUTHORIZED_PRODUCT_POLICY"
                   else ("FY1_USER_AUTHORIZED_PRODUCT_POLICY_NOT_PROVIDER_FIELD_DEFINITION",))),
    )
    row = ProviderNativeForwardValuationSnapshot.model_construct(
        **row, snapshot_sha256=""
    ).model_dump(mode="json", exclude={"snapshot_sha256"})
    return ProviderNativeForwardValuationSnapshot.model_validate(
        dict(row, snapshot_sha256=digest(row))
    )
