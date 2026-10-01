"""Offline current-close/FY1 owner. Not registered in production or AI inputs.

KIS schedule query completeness is distinct from effective-date coverage.
V1 stays fail closed; V2 admits an explicitly bounded exact-security policy.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
import re
from zoneinfo import ZoneInfo

from app.services.price_structure_wave_fibonacci_v3_service import (
    _calendar_for_range, _latest_completed_session,
)
from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.kis_fy1_semantic_owner import ALLOWED_ROLES, PROHIBITED_ROLES, SemanticGap
from scripts.kis_output3_protocol_owner import SNAPSHOT

PRICE = "CurrentFY1PriceReceipt"
ACTION = "CorporateActionCompatibilityReceipt"
FPER = "CurrentFY1FperReceipt"
CALENDAR = "CurrentFY1CompletedSessionCalendar"
FAMILY = "KISShareUnitScheduleFamilyV1"
PRICE_BASIS = "KIS_UNADJUSTED_COMPLETED_SESSION_CLOSE"
PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
PRICE_TR = "FHKST01010400"
ROUTES = {
    "merger_split": ("merger-split", "HHKDB669104C0", {}),
    "rev_split": ("rev-split", "HHKDB669105C0", {"MARKET_GB": "0"}),
    "bonus_issue": ("bonus-issue", "HHKDB669101C0", {}),
    "paidin_capin": ("paidin-capin", "HHKDB669100C0", {"GB1": "2"}),
    "cap_dcrs": ("cap-dcrs", "HHKDB669106C0", {}),
}
ROUNDING = {"decimal_precision": 50, "display_places": 2, "mode": "ROUND_HALF_UP",
            "exact_quotient_representation": "REDUCED_INTEGER_NUMERATOR_DENOMINATOR"}


def _decimal(value):
    if not isinstance(value, str):
        raise SemanticGap("NON_DECIMAL_WIRE_VALUE")
    try:
        result = Decimal(value)
    except Exception:
        raise SemanticGap("NON_DECIMAL_WIRE_VALUE") from None
    if not result.is_finite():
        raise SemanticGap("NON_FINITE_VALUE")
    return result


def _at(value):
    at = datetime.fromisoformat(value)
    if at.utcoffset() is None:
        raise SemanticGap("TIMEZONE_REQUIRED")
    return at


def calendar_receipt(as_of):
    at = _at(as_of).astimezone(ZoneInfo("Asia/Seoul"))
    name, calendar = _calendar_for_range("KR", start=at.date() - timedelta(days=14), end=at.date())
    target = _latest_completed_session(calendar, at)
    if target is None:
        raise SemanticGap("COMPLETED_SESSION_SELECTION_GAP")
    close = calendar.session_close(calendar.date_to_session(target)).isoformat()
    return sealed({"contract": CALENDAR, "calendar": name, "as_of": as_of,
        "latest_completed_session": target.isoformat(), "session_close": close,
        "calendar_owner": "price_structure_wave_fibonacci_v3_service._latest_completed_session",
        "weekday_fallback": False})


def verify_calendar(value):
    verified(value, CALENDAR)
    if value != calendar_receipt(value["as_of"]):
        raise SemanticGap("COMPLETED_SESSION_SELECTION_GAP")


def eps_receipt(eps):
    verified(eps, SNAPSHOT)
    s = eps.get("security", {})
    code = eps.get("security_code", "")
    if (not re.fullmatch(r"\d{6}", code) or eps.get("state") != "KIS_FY1_EPS_ESTIMATE_SNAPSHOT"
            or eps.get("metric") != "EPS" or eps.get("unit") != "KRW_PER_SHARE"
            or eps.get("source_kind") != "KIS_HOUSE_RESEARCH_NOT_CONSENSUS"
            or eps.get("overall_direction_use") is not False or s.get("state") != "QUALIFIED"
            or s.get("request_code") != code or s.get("short_code") != code
            or s.get("provider_product_number") != "00000A" + code
            or s.get("estimate_sht_cd") != "A" + code or s.get("product_type") != "300"
            or not re.fullmatch(r"KR[0-9A-Z]{10}", s.get("standard_code", ""))
            or tuple(eps.get("allowed_roles", ())) != ALLOWED_ROLES
            or tuple(eps.get("prohibited_roles", ())) != PROHIBITED_ROLES):
        raise SemanticGap("EPS_IDENTITY_UNIT_OR_AUTHORITY_GAP")
    date.fromisoformat(eps["estdate"])
    return _decimal(eps["value"])


def price_params(code):
    return {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code,
            "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"}


def action_params(family, start, end):
    return {"CTS": "", "F_DT": date.fromisoformat(start).strftime("%Y%m%d"),
            "T_DT": date.fromisoformat(end).strftime("%Y%m%d"), "SHT_CD": "", **ROUTES[family][2]}


def _source(evidence, receipt, path, tr_id, params):
    payload = evidence.payload()
    request = receipt.get("request", {})
    if (receipt.get("http_status") != 200 or receipt.get("raw_sha256") != evidence.sha256
            or request.get("method") != "GET" or request.get("path") != path
            or request.get("tr_id") != tr_id or request.get("params") != params
            or request.get("redirects") is not False or payload.get("rt_cd") != "0"
            or _at(receipt["ended_at"]) < _at(request["started_at"])):
        raise SemanticGap("SOURCE_RECEIPT_BINDING_GAP")
    return payload


def price_receipt(eps, security, evidence, receipt, calendar, documentation):
    eps_receipt(eps)
    verify_calendar(calendar)
    code = eps["security_code"]
    if (security.get("ticker") != code or not security.get("canonical_security_id")
            or security.get("exchange") != "KRX" or security.get("currency") != "KRW"
            or security.get("standard_code") != eps["security"]["standard_code"]):
        raise SemanticGap("PRICE_SECURITY_CURRENCY_GAP")
    if documentation.get("price", {}).get("params") != {"FID_ORG_ADJ_PRC": {"0": "UNADJUSTED", "1": "ADJUSTED"}}:
        raise SemanticGap("UNADJUSTED_CLOSE_DOCUMENTATION_GAP")
    payload = _source(evidence, receipt, PRICE_PATH, PRICE_TR, price_params(code))
    if receipt.get("response_headers", {}).get("tr_cont") not in {"", "D", "E"}:
        raise SemanticGap("PRICE_CONTINUATION_GAP")
    if _at(receipt["request"]["started_at"]) < _at(calendar["as_of"]):
        raise SemanticGap("PRICE_BEFORE_FROZEN_CUTOFF")
    rows = payload.get("output")
    if not isinstance(rows, list):
        raise SemanticGap("PRICE_ROWS_GAP")
    target = date.fromisoformat(calendar["latest_completed_session"])
    selected, excluded = [], []
    for row in rows:
        try:
            day = datetime.strptime(row["stck_bsop_date"], "%Y%m%d").date()
        except (TypeError, KeyError, ValueError):
            raise SemanticGap("PRICE_ROW_DATE_GAP") from None
        # Some KIS responses have no row security field: bind via the exact request.
        if row.get("sht_cd", code) != code:
            raise SemanticGap("PRICE_ROW_SECURITY_GAP")
        if day == target:
            selected.append(row)
        else:
            excluded.append({"session": str(day), "reason": "INCOMPLETE_OR_LATER" if day > target else "HISTORICAL"})
    if len(selected) != 1:
        raise SemanticGap("COMPLETED_SESSION_ROW_MISSING_OR_DUPLICATE")
    row = selected[0]
    close, low, high, opening = [_decimal(row.get(k)) for k in
        ("stck_clpr", "stck_lwpr", "stck_hgpr", "stck_oprc")]
    if not (0 < low <= min(close, opening) <= max(close, opening) <= high):
        raise SemanticGap("PRICE_TARGET_OHLC_INTEGRITY_GAP")
    return sealed({"contract": PRICE, "state": "QUALIFIED", "security_code": code,
        "canonical_security_id": security["canonical_security_id"], "standard_code": security["standard_code"],
        "kis_product_identity": eps["security"]["provider_product_number"],
        "session_date": str(target), "close": str(close), "currency": "KRW", "market": "KRX",
        "price_basis": PRICE_BASIS, "fid_org_adj_prc": "0", "current_session_complete": True,
        "raw_response_sha256": evidence.sha256, "source_receipt_sha256": digest(receipt),
        "retrieved_at": receipt["ended_at"], "calendar_owner_receipt": calendar,
        "official_documentation_sha256": digest(documentation), "selected_row": deepcopy(row),
        "excluded_rows": excluded, "identity_binding": "EXACT_REQUEST_PLUS_SEALED_KIS_PRODUCT_IDENTITY",
        "overall_direction_use": False})


def action_family_receipt(family, start, end, pages, documentation):
    """Verify each page, chain and terminal status; never equate this to date coverage."""
    path, tr_id, _ = ROUTES[family]
    params = action_params(family, start, end)
    rows, hashes, errors = [], [], []
    previous = None
    if not pages:
        errors.append("MISSING_FAMILY_SOURCE")
    for index, (evidence, receipt) in enumerate(pages):
        try:
            payload = _source(evidence, receipt, "/uapi/domestic-stock/v1/ksdinfo/" + path, tr_id, params)
            if receipt["request"].get("tr_cont") != ("" if index == 0 else "N"):
                raise SemanticGap("CONTINUATION_REQUEST_GAP")
            if index and previous != "M":
                raise SemanticGap("CONTINUATION_CHAIN_GAP")
            previous = receipt.get("response_headers", {}).get("tr_cont")
            if previous not in {"", "D", "E", "M"}:
                raise SemanticGap("CONTINUATION_STATUS_GAP")
            output = payload.get("output1")
            if not isinstance(output, list) or any(not isinstance(r, dict) for r in output):
                raise SemanticGap("ACTION_ROWS_GAP")
            if evidence.sha256 in hashes:
                raise SemanticGap("REPEATED_PAGE_GAP")
            hashes.append(evidence.sha256)
            rows.extend(deepcopy(output))
        except (SemanticGap, KeyError, ValueError) as exc:
            errors.append(str(exc) if isinstance(exc, SemanticGap) else "MALFORMED_ACTION_SOURCE")
    if previous == "M":
        errors.append("CONTINUATION_INCOMPLETE")
    if any(not re.fullmatch(r"\d{6}", r.get("sht_cd", "")) for r in rows):
        errors.append("ACTION_SECURITY_CODE_UNRESOLVED")
    # Official examples expose record/listing/ex-rights dates, not an effective-
    # date range query. A record date before this window can take effect inside it.
    return sealed({"contract": FAMILY, "family": family,
        "state": "COMPLETE_QUERY" if not errors else "SOURCE_INCOMPLETE", "errors": sorted(set(errors)),
        "window_start": start, "window_end": end, "source_hashes": hashes,
        "rows": rows, "source_receipt_hashes": [digest(r) for _, r in pages],
        "effective_window_coverage": "UNPROVEN",
        "coverage_reason": "RECORD_OR_UNSPECIFIED_QUERY_DATE_NOT_EFFECTIVE_DATE_COVERAGE",
        "official_documentation_sha256": digest(documentation)})


def validate_price_receipt(candidate, **inputs):
    verified(candidate, PRICE)
    if candidate != price_receipt(**inputs):
        raise SemanticGap("PRICE_RECEIPT_REPRODUCTION_GAP")


def evaluate_effective_events(events, estimate_date, price_date):
    """Pure date policy on already owned events; not an acquisition/absence proof."""
    start, end = date.fromisoformat(estimate_date), date.fromisoformat(price_date)
    if start > end:
        raise SemanticGap("ESTIMATE_AFTER_PRICE")
    decisions = []
    for event in events:
        family = event["family"]
        if family == "CASH_DIVIDEND":
            decisions.append({**event, "affects_window": False})
            continue
        if family not in ROUTES or event.get("effective_date_authority") != "OWNED_SECURITY_UNIT_EFFECTIVE_DATE":
            raise SemanticGap("ACTION_EFFECTIVE_DATE_UNRESOLVED")
        day = date.fromisoformat(event["effective_date"])
        decisions.append({**event, "affects_window": start < day <= end})
    return decisions


def effective_window_state(events, estimate_date, price_date, *, complete_families):
    """Policy for an independently proved effective-date set, not KIS query coverage."""
    if set(complete_families) != set(ROUTES):
        return "CORPORATE_ACTION_SOURCE_INCOMPLETE"
    decisions = evaluate_effective_events(events, estimate_date, price_date)
    return ("SHARE_UNIT_CHANGE_REQUIRES_ADJUSTMENT" if any(e["affects_window"] for e in decisions)
            else "NO_SHARE_UNIT_CHANGE_IN_WINDOW")


def compatibility_receipt(eps, price, families):
    eps_receipt(eps)
    verified(price, PRICE)
    code = eps["security_code"]
    if price.get("security_code") != code:
        raise SemanticGap("ACTION_SECURITY_MISMATCH")
    start, end = eps["estdate"], price["session_date"]
    errors, selected, source_hashes, family_hashes = [], [], [], []
    if set(families) != set(ROUTES):
        errors.append("REQUIRED_ACTION_FAMILY_MISSING_OR_EXTRA")
    for family, receipt in families.items():
        verified(receipt, FAMILY)
        family_hashes.append(receipt["receipt_sha256"])
        source_hashes.extend(receipt["source_hashes"])
        if (receipt.get("family") != family or receipt.get("state") != "COMPLETE_QUERY"
                or not receipt["window_start"] <= start <= end <= receipt["window_end"]):
            errors.append("ACTION_FAMILY_SOURCE_OR_WINDOW_INCOMPLETE:" + family)
        if receipt.get("effective_window_coverage") != "COMPLETE_EFFECTIVE_DATE_WINDOW":
            errors.append("ACTION_EFFECTIVE_WINDOW_COVERAGE_UNPROVEN:" + family)
        for row in receipt["rows"]:
            if row.get("sht_cd") == code:
                # Preserve dates without promoting listing/record dates to unit-effective dates.
                selected.append({"family": family, "raw": deepcopy(row), "effective_date": None,
                    "effective_date_authority": "UNRESOLVED", "share_unit_changing": None})
                errors.append("ACTION_EFFECTIVE_DATE_UNRESOLVED:" + family)
    state = "CORPORATE_ACTION_SOURCE_INCOMPLETE" if errors else "NO_SHARE_UNIT_CHANGE_IN_WINDOW"
    return sealed({"contract": ACTION, "state": state, "security_code": code,
        "canonical_security_id": price["canonical_security_id"], "estimate_date": start,
        "price_date": end, "queried_families": sorted(families), "events": selected,
        "share_unit_changing": None if errors else False, "denial_reasons": sorted(set(errors)),
        "source_hashes": source_hashes, "family_receipt_hashes": family_hashes,
        "effective_date_policy": "ESTDATE < OWNED_EFFECTIVE_DATE <= PRICE_DATE",
        "adjustments_performed": 0})


def current_fper(eps, price, actions):
    value = {"contract": FPER, "metric": "CURRENT_PRICE_FY1_FPER",
        "source_kind": "THESIS_MONITOR_DERIVED_FROM_KIS_CLOSE_AND_KIS_RESEARCH_EPS",
        "label": "현재가 기준 fPER(FY1)", "allowed_roles": list(ALLOWED_ROLES), "prohibited_roles": list(PROHIBITED_ROLES),
        "overall_direction_use": False, "value": None, "display_value": None, "exact_quotient": None,
        "rounding_policy": ROUNDING, "proof_scope": "SEALED_EPS_OWNER_PROOF_NOT_FRESH_ESTIMATE"}
    if not eps or eps.get("state") != "KIS_FY1_EPS_ESTIMATE_SNAPSHOT":
        return sealed({**value, "state": "UNAVAILABLE_EPS"})
    denominator = eps_receipt(eps)
    value.update(security_code=eps["security_code"], fy1_period=eps["period"], fy1_eps=str(denominator),
        eps_estimate_date=eps["estdate"], eps_source_sha256=eps["estimate_sha256"],
        eps_receipt_sha256=eps["receipt_sha256"])
    if denominator <= 0:
        return sealed({**value, "state": "NOT_MEANINGFUL", "display_value": "N/M"})
    if not price:
        return sealed({**value, "state": "UNAVAILABLE_UNADJUSTED_COMPLETED_SESSION_CLOSE"})
    verified(price, PRICE)
    verify_calendar(price["calendar_owner_receipt"])
    if (price.get("state") != "QUALIFIED" or price.get("security_code") != eps["security_code"]
            or price.get("standard_code") != eps["security"]["standard_code"]
            or price.get("kis_product_identity") != eps["security"]["provider_product_number"]
            or price.get("currency") != "KRW" or price.get("market") != "KRX"
            or price.get("price_basis") != PRICE_BASIS or price.get("fid_org_adj_prc") != "0"
            or price.get("current_session_complete") is not True or price.get("overall_direction_use") is not False
            or price.get("session_date") != price["calendar_owner_receipt"]["latest_completed_session"]
            or price["session_date"] < eps["estdate"]):
        raise SemanticGap("FPER_PRICE_BASIS_GAP")
    value.update(canonical_security_id=price["canonical_security_id"], session_date=price["session_date"],
        unadjusted_close=price["close"], price_receipt_sha256=price["receipt_sha256"],
        currency="KRW", basis="KRW_CLOSE_DIVIDED_BY_KRW_PER_SHARE_FY1_EPS",
        source_age_days=(date.fromisoformat(price["calendar_owner_receipt"]["as_of"][:10])
                         - date.fromisoformat(eps["estdate"])).days)
    if not actions:
        return sealed({**value, "state": "UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE"})
    action_unresolved = False
    if actions.get("contract") == "CorporateActionCompatibilityReceiptV2":
        from scripts.kis_exact_action_guard import validate_compatibility
        validate_compatibility(actions, eps, price)
        action_clear = actions["state"] == "NO_RELEVANT_SHARE_UNIT_ACTION_FOUND_V1"
        action_event = actions["state"] == "POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT"
        action_unresolved = actions["state"] == "CORPORATE_ACTION_DATE_UNRESOLVED"
        value["corporate_action_policy"] = actions["policy"]
    else:
        verified(actions, ACTION)
        action_event = actions["state"] == "SHARE_UNIT_CHANGE_REQUIRES_ADJUSTMENT"
        action_clear = (actions["state"] == "NO_SHARE_UNIT_CHANGE_IN_WINDOW"
            and actions.get("share_unit_changing") is False and not actions.get("denial_reasons")
            and set(actions.get("queried_families", [])) == set(ROUTES))
    if (actions.get("security_code") != eps["security_code"]
            or actions.get("canonical_security_id") != price["canonical_security_id"]
            or actions.get("estimate_date") != eps["estdate"] or actions.get("price_date") != price["session_date"]):
        raise SemanticGap("FPER_ACTION_BINDING_GAP")
    value["corporate_action_receipt_sha256"] = actions["receipt_sha256"]
    if action_event:
        return sealed({**value, "state": "UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE"})
    if action_unresolved:
        return sealed({**value, "state": "UNAVAILABLE_CORPORATE_ACTION_DATE_UNRESOLVED"})
    if not action_clear:
        return sealed({**value, "state": "UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE"})
    numerator = _decimal(price["close"])
    if numerator <= 0:
        raise SemanticGap("FPER_NONPOSITIVE_PRICE")
    exact = Fraction(numerator) / Fraction(denominator)
    with localcontext() as ctx:
        ctx.prec = ROUNDING["decimal_precision"]
        quotient = numerator / denominator
        display = quotient.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return sealed({**value, "state": "QUALIFIED", "value": str(quotient), "display_value": str(display),
        "exact_quotient": {"numerator": str(exact.numerator), "denominator": str(exact.denominator)},
        "decimal_value_is_rounded_expansion": Fraction(quotient) != exact})


def validate_current_fper(receipt, eps, price, actions):
    verified(receipt, FPER)
    if receipt != current_fper(eps, price, actions):
        raise SemanticGap("FPER_REPRODUCTION_GAP")


def metric_set(trailing, provider_per, derived):
    """Keep three owners disjoint. Difference never repairs/rejects either input."""
    verified(derived, FPER)
    comparison = None
    if provider_per and provider_per.get("state") == "KIS_PROVIDER_FY1_PER_SNAPSHOT":
        verified(provider_per, SNAPSHOT)
        if derived.get("state") == "QUALIFIED":
            if (provider_per["security_code"] != derived["security_code"]
                    or provider_per["period"] != derived["fy1_period"]):
                raise SemanticGap("PROVIDER_PER_COMPARISON_IDENTITY_PERIOD_GAP")
            with localcontext() as ctx:
                ctx.prec = 50
                comparison = {"difference": str(_decimal(derived["value"]) - _decimal(provider_per["value"])),
                    "state": "DIAGNOSTIC_ONLY_DIFFERENT_PRICE_TIMES_NOT_AN_ERROR"}
    return {"current_trailing_per": deepcopy(trailing), "kis_provider_fy1_per": deepcopy(provider_per),
            "current_price_fy1_fper": deepcopy(derived), "provider_per_diagnostic": comparison}
