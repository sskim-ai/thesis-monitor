"""Atomic provider ratios, separate from price/denominator reconstruction.

Pure replay only. Acquisition must bind raw responses to one declared run.
The explicit REV28 policy permits latest-provider context, not same-session
fundamentals, ADR transfer, forward estimates or business-direction evidence.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.security_identity_service import identity_source_tier
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest

PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT = True
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
MARKETS = {"0": ("KOSPI", "\ucf54\uc2a4\ud53c"), "10": ("KOSDAQ", "\ucf54\uc2a4\ub2e5")}


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
        if (self.provider_field, self.metric_semantic) != FIELDS[self.provider][self.metric]:
            raise ValueError("native_snapshot_field_semantic")
        if self.route != (KIWOOM_ROUTE if self.provider == "kiwoom" else FINNHUB_BASE + "metric"):
            raise ValueError("native_snapshot_route")
        if self.api_id != ("ka10001" if self.provider == "kiwoom" else None):
            raise ValueError("native_snapshot_api_id")
        qualified = self.state == "QUALIFIED_PROVIDER_LATEST_SNAPSHOT"
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
        elif not self.state.startswith("UNAVAILABLE_") or self.value is not None:
            raise ValueError("native_snapshot_unavailable_value")
        if self.retrieval_timestamp.utcoffset() is None or not self.caveats:
            raise ValueError("native_snapshot_time_caveat_required")
        return self


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
    names = {
        "NEW YORK STOCK EXCHANGE, INC.": "NYSE",
        "NASDAQ NMS - GLOBAL MARKET": "NASDAQ",
        "NASDAQ NMS - GLOBAL SELECT MARKET": "NASDAQ",
        "NASDAQ CAPITAL MARKET": "NASDAQ",
    }
    return names.get(value, value)


def _identity(*, inputs, security, body, run_id, provider, metric_receipt):
    ticker = security["ticker"]
    data = inputs["identity_inputs"]
    reasons, bindings = [], [digest(metric_receipt)]
    exchange, currency = None, None
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
            if (
                row.get("marketCode") != market
                or exchange not in MARKETS[market]
                or security.get("exchange") not in {"KRX", MARKETS[market][0]}
                or security.get("country") != "KR"
                or _name(row.get("name")) != _name(security.get("company_name"))
                or _name(body.get("stk_nm")) != _name(row.get("name"))
            ):
                reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
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
        tier = identity_source_tier(
            security.get("identity_provider"), security.get("identity_quality")
        )
        if not official:
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        else:
            evidence = OfficialSecurityIdentityEvidence.from_payload(official)
            bindings.append(digest(official))
            if (
                digest(official) != data.get("official_identity_sha256")
                or official != evidence.to_payload()
                or urlsplit(evidence.source_url).hostname != "www.sec.gov"
                or not urlsplit(evidence.source_url).path.startswith("/Archives/edgar/data/")
                or evidence.ticker != ticker
                or evidence.exchange != security.get("exchange")
                or evidence.security_type != "common_stock"
                or evidence.share_class != security.get("share_class")
                or evidence.cik != security.get("cik")
                or not evidence.filing_accession
                or date.fromisoformat(evidence.as_of_date) > inputs["cutoff"].date()
            ):
                reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        if (
            tier != "tier_a_authoritative"
            or security.get("identity_quality") != "verified"
            or security.get("security_type") != "common_stock"
            or profile.get("ticker") != ticker
            or exchange != security.get("exchange")
            or currency != "USD"
            or security.get("country") != "US"
        ):
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        # A profile's currency is a filing currency, not an ADR conversion basis.
        if profile.get("country") not in (None, "US") or returned != profile.get("ticker"):
            reasons.append("UNAVAILABLE_SECURITY_IDENTITY")
        contract = "sec-finnhub-direct-security-identity-v1"
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
