"""Offline, exact KIS EPS calibration. No production source or valuation hook.

Raw-to-raw overlap diagnostics are not display EPS authority. A separately
reviewed reference unit and all-period agreement are both mandatory.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re

from scripts.kis_fy1_semantic_owner import (
    ALLOWED_ROLES, ENDPOINT, LAYOUT, PROHIBITED_ROLES, Evidence, SemanticGap,
    fiscal_owner, forecast_binding, period_pattern, security_binding,
)

RATIO_PATH = "/uapi/domestic-stock/v1/finance/financial-ratio"
RATIO_TR = "FHKST66430300"


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sealed(value):
    return {**value, "receipt_sha256": digest(value)}


def verified(value, contract):
    body = {k: v for k, v in value.items() if k != "receipt_sha256"}
    if value.get("contract") != contract or value.get("receipt_sha256") != digest(body):
        raise SemanticGap("UNAVAILABLE_RECEIPT_BINDING")
    return body


def number(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise SemanticGap("UNAVAILABLE_WIRE_VALUE")
    try:
        result = Decimal(value)
        if not result.is_finite():
            raise InvalidOperation
        return Fraction(result)
    except (InvalidOperation, ValueError):
        raise SemanticGap("UNAVAILABLE_WIRE_VALUE") from None


def decimal_string(value):
    """Serialize only terminating decimals without Decimal context rounding."""
    divisor, twos, fives = value.denominator, 0, 0
    while divisor % 2 == 0:
        divisor //= 2
        twos += 1
    while divisor % 5 == 0:
        divisor //= 5
        fives += 1
    if divisor != 1:
        raise SemanticGap("UNAVAILABLE_NON_DECIMAL_SCALE")
    places = max(twos, fives)
    integer = value.numerator * 2 ** (places - twos) * 5 ** (places - fives)
    sign = "-" if integer < 0 else ""
    digits = str(abs(integer)).zfill(places + 1)
    return sign + (digits[:-places] + "." + digits[-places:] if places else digits)


def annual_reference(code, estimate, identity, ratio, transport, fiscal, unit_review):
    security = security_binding(code, estimate.payload(), identity)
    payload, receipt, review = ratio.payload(), transport.payload(), unit_review.payload()
    request = receipt.get("request", {})
    expected = {"FID_DIV_CLS_CODE": "0", "fid_cond_mrkt_div_code": "J", "fid_input_iscd": code}
    if (receipt.get("security_code") != code or request.get("params") != expected
            or request.get("method") != "GET" or request.get("path") != RATIO_PATH
            or request.get("tr_id") != RATIO_TR or receipt.get("raw_sha256") != ratio.sha256
            or receipt.get("http_status") != 200 or payload.get("rt_cd") != "0"
            or receipt.get("response_headers", {}).get("tr_cont") in {"M", "F"}):
        raise SemanticGap("UNAVAILABLE_REFERENCE_SOURCE_BINDING")
    try:
        retrieved = datetime.fromisoformat(receipt["ended_at"])
        if retrieved.tzinfo is None:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        raise SemanticGap("UNAVAILABLE_REFERENCE_RETRIEVAL_TIME") from None
    if (fiscal.get("state") != "QUALIFIED" or fiscal.get("security_code") != code
            or review.get("endpoint") != RATIO_PATH or review.get("eps_field") != "eps"
            or review.get("annual_selector") != expected["FID_DIV_CLS_CODE"]):
        raise SemanticGap("UNAVAILABLE_REFERENCE_SEMANTICS")
    values, excluded = {}, []
    rows = payload.get("output")
    if not isinstance(rows, list) or not rows:
        raise SemanticGap("UNAVAILABLE_REFERENCE_EPS")
    for row in rows:
        period = row.get("stac_yymm", "") if isinstance(row, dict) else ""
        if not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", period):
            raise SemanticGap("UNAVAILABLE_REFERENCE_PERIOD")
        # The annual selector can also return a current interim row. Never
        # promote it to an annual merely because the query requested years.
        if int(period[4:]) != fiscal["fiscal_end_month"] or int(period[:4]) > fiscal["fiscal_year"]:
            excluded.append({"stac_yymm": period, "reason": "NOT_COMPLETED_ANNUAL_FISCAL_END"})
            continue
        label = period[:4] + "." + period[4:]
        if label in values:
            raise SemanticGap("UNAVAILABLE_DUPLICATE_REFERENCE_PERIOD")
        number(row.get("eps"))
        values[label] = row.get("eps")
    wire = review.get("wire_to_display", {})
    display_factor = None
    if (wire.get("kind") == "OFFICIAL_EXPLICIT_RAW_TO_DISPLAY"
            and wire.get("unit") == "KRW_PER_SHARE" and wire.get("definition")
            and re.fullmatch(r"[a-f0-9]{64}", wire.get("source_sha256", ""))):
        display_factor = number(wire.get("multiplier"))
        if display_factor is None or display_factor <= 0:
            raise SemanticGap("UNAVAILABLE_REFERENCE_WIRE_SCALE")
        decimal_string(display_factor)
    return sealed({"contract": "KISAnnualEPSReference", "security_code": code,
        "state": "QUALIFIED" if display_factor else "UNAVAILABLE_REFERENCE_WIRE_SCALE",
        "security": security, "fiscal": fiscal, "annual_selector": "0", "endpoint": RATIO_PATH,
        "tr_id": RATIO_TR, "raw_eps_by_period": values, "excluded_periods": excluded,
        "source_sha256": ratio.sha256, "transport_sha256": transport.sha256,
        "estimate_source_sha256": estimate.sha256,
        "retrieved_at": receipt["ended_at"], "unit_review_sha256": unit_review.sha256,
        "display_factor": decimal_string(display_factor) if display_factor else None,
        "unit": "KRW_PER_SHARE" if display_factor else None})


def overlaps(estimate, row_index, reference):
    payload = estimate.payload()
    periods = period_pattern(payload)
    row = payload["output3"][row_index]
    if not isinstance(row, dict) or set(row) != {f"data{i}" for i in range(1, 6)}:
        raise SemanticGap("UNAVAILABLE_OUTPUT3_LAYOUT")
    pairs = []
    for index, (year, month, marker) in enumerate(periods, 1):
        label = f"{year:04}.{month:02}"
        if marker or label not in reference["raw_eps_by_period"]:
            continue
        left, right = number(row[f"data{index}"]), number(reference["raw_eps_by_period"][label])
        if left is None or right is None:
            continue
        pairs.append({"period": label, "estimate_raw": row[f"data{index}"],
                      "reference_raw": reference["raw_eps_by_period"][label],
                      "ratio": str(right / left) if left else None,
                      "zero_conflict": not left and bool(right)})
    return pairs


def calibrate(estimate, docs, reference):
    verified(reference, "KISAnnualEPSReference")
    payload = estimate.payload()
    review = docs.review()
    if (estimate.sha256 != reference["estimate_source_sha256"]
            or payload.get("rt_cd") != "0" or payload.get("output1", {}).get("sht_cd") != "A" + reference["security_code"]
            or tuple(review.get("output3_layout", [])) != LAYOUT
            or not valid_full_layout(payload.get("output3"))):
        raise SemanticGap("UNAVAILABLE_CALIBRATION_CONTROL")
    pairs = overlaps(estimate, 1, reference)
    ratios = {Fraction(p["ratio"]) for p in pairs if p["ratio"] is not None}
    state, factor = "UNAVAILABLE_CROSS_ENDPOINT_SCALE_GAP", None
    if any(p["zero_conflict"] for p in pairs) or len(ratios) > 1 or any(r <= 0 for r in ratios):
        state = "UNAVAILABLE_CROSS_ENDPOINT_SCALE_CONFLICT"
    elif len(pairs) >= 2 and len(ratios) == 1:
        if reference["state"] != "QUALIFIED":
            state = "UNAVAILABLE_REFERENCE_WIRE_SCALE"
        else:
            try:
                factor = decimal_string(next(iter(ratios)) * number(reference["display_factor"]))
                state = "QUALIFIED"
            except SemanticGap as exc:
                state = str(exc)
    return sealed({"contract": "KISEstimatePerformEPSWireCalibration", "state": state,
        "control_security": reference["security_code"], "estimate_endpoint": ENDPOINT,
        "reference_endpoint": RATIO_PATH, "estimate_source_sha256": estimate.sha256,
        "reference_source_sha256": reference["source_sha256"],
        "reference_receipt_sha256": reference["receipt_sha256"],
        "documentation_sha256": docs.evidence.sha256, "row_index": 1,
        "all_non_null_overlaps": pairs, "matched_period_count": len(pairs),
        "reference_display_state": reference["state"], "wire_to_krw_per_share": factor,
        "raw_ratio_diagnostic_only": reference["state"] != "QUALIFIED",
        "periods_dropped_for_disagreement": 0, "price_per_used": False})


def partial_binding(estimate, reference, calibration):
    verified(reference, "KISAnnualEPSReference")
    verified(calibration, "KISEstimatePerformEPSWireCalibration")
    payload = estimate.payload()
    if (calibration["state"] != "QUALIFIED" or reference["state"] != "QUALIFIED"
            or estimate.sha256 != reference["estimate_source_sha256"]
            or payload.get("output1", {}).get("sht_cd") != "A" + reference["security_code"]
            or payload.get("rt_cd") != "0" or not isinstance(payload.get("output3"), list)
            or len(payload["output3"]) != 3):
        raise SemanticGap("UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS")
    matches, audits = [], []
    for index in range(len(payload["output3"])):
        pairs = overlaps(estimate, index, reference)
        match = len(pairs) >= 2 and all(
            number(p["estimate_raw"]) * number(calibration["wire_to_krw_per_share"])
            == number(p["reference_raw"]) * number(reference["display_factor"]) for p in pairs)
        audits.append({"row_index": index, "all_non_null_overlaps": pairs, "match": match})
        if match:
            matches.append(index)
    return sealed({"contract": "KISPartialOutput3EPSCrossEndpointBinding",
        "state": "QUALIFIED" if len(matches) == 1 else "UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS",
        "security_code": reference["security_code"], "estimate_source_sha256": estimate.sha256,
        "reference_source_sha256": reference["source_sha256"], "calibration_sha256": calibration["receipt_sha256"],
        "candidate_rows": audits, "matching_rows": matches, "row_index": matches[0] if len(matches) == 1 else None,
        "provider_per_qualified": False})


def valid_full_layout(rows):
    return (isinstance(rows, list) and len(rows) == 8
            and all(isinstance(r, dict) and set(r) == {f"data{i}" for i in range(1, 6)} for r in rows))


def qualify_eps(code, corp, estimate, identity, inventory, cutoff, docs, controls,
                calibration, reference=None, estimate_transport=None):
    """Revalidate independent identity/fiscal owners before exposing any FY1 value."""
    result = {"security_code": code, "value": None, "state": "UNAVAILABLE_CROSS_ENDPOINT_SCALE_GAP",
              "provider_per": "UNAVAILABLE_WIRE_SCALE", "derived_fper": "UNAVAILABLE_PRICE_SHARE_SPLIT_BASIS",
              "overall_direction_use": False, "source_failure": False}
    try:
        if estimate is None:
            raise SemanticGap("UNAVAILABLE_NO_ESTIMATE")
        if estimate.payload().get("rt_cd") != "0":
            raise SemanticGap("UNAVAILABLE_PROVIDER_ESTIMATE")
        verified(calibration, "KISEstimatePerformEPSWireCalibration")
        if calibration["state"] != "QUALIFIED":
            raise SemanticGap(calibration["state"])
        if docs.evidence.sha256 != calibration["documentation_sha256"]:
            raise SemanticGap("UNAVAILABLE_CALIBRATION_DOCUMENTATION_CHANGED")
        transport = estimate_transport.payload() if estimate_transport is not None else {}
        if (transport.get("raw_sha256") != estimate.sha256 or transport.get("http_status") != 200
                or transport.get("SHT_CD") != code):
            raise SemanticGap("UNAVAILABLE_ESTIMATE_TRANSPORT")
        try:
            if datetime.fromisoformat(transport["ended_at"]).tzinfo is None:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise SemanticGap("UNAVAILABLE_ESTIMATE_TRANSPORT") from None
        security = security_binding(code, estimate.payload(), identity)
        fiscal = fiscal_owner(code, corp, inventory, cutoff)
        forecast = forecast_binding(estimate.payload(), fiscal, docs, controls)
        rows = estimate.payload().get("output3", [])
        binding = None
        if valid_full_layout(rows) and tuple(docs.review().get("output3_layout", [])) == LAYOUT:
            index = 1
        elif reference is not None:
            binding = partial_binding(estimate, reference, calibration)
            if binding["state"] != "QUALIFIED":
                raise SemanticGap(binding["state"])
            index = binding["row_index"]
        else:
            raise SemanticGap("UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS")
        if (code == calibration["control_security"] and estimate.sha256 != calibration["estimate_source_sha256"]):
            raise SemanticGap("UNAVAILABLE_CALIBRATION_SOURCE_CHANGED")
        raw = rows[index][f"data{forecast['fy1_column']}"]
        value = number(raw)
        if value is None:
            raise SemanticGap("UNAVAILABLE_WIRE_VALUE")
        result.update({"contract": "KIS_FY1_EPS_ESTIMATE_SNAPSHOT", "state": "QUALIFIED_KIS_FY1_EPS",
            "security": security, "fiscal": fiscal, "forecast": forecast, "raw_value": raw,
            "value": decimal_string(value * number(calibration["wire_to_krw_per_share"])),
            "unit": "KRW_PER_SHARE", "currency": "KRW", "provider": "KIS", "endpoint": ENDPOINT,
            "period": forecast["fy1"], "provider_estimate_date": None,
            "retrieved_at": transport["ended_at"], "transport_sha256": estimate_transport.sha256,
            "source_sha256": estimate.sha256, "calibration_sha256": calibration["receipt_sha256"],
            "reference_source_sha256": calibration["reference_source_sha256"], "partial_binding": binding,
            "allowed_roles": list(ALLOWED_ROLES), "prohibited_roles": list(PROHIBITED_ROLES),
            "label": "FY1 EPS (KIS estimate snapshot)"})
    except SemanticGap as exc:
        result["state"] = str(exc)
    return sealed(result)


def verify_stage_b_gate(decision):
    """Bind an explicit offline gate to the frozen tested implementation and receipt."""
    owner = Path(__file__)
    if (decision.get("owner_sha256") != sha256(owner.read_bytes()).hexdigest()
            or decision.get("focused_tests") != "PASS"):
        raise SemanticGap("UNAVAILABLE_STAGE_B_OWNER_GATE")
    raw = Path(decision["qualification_path"]).read_bytes()
    payload = Evidence(raw, decision["qualification_sha256"]).payload()
    verified(payload, "KIS_FY1_EPS_ESTIMATE_SNAPSHOT")
    if payload.get("state") != "QUALIFIED_KIS_FY1_EPS" or payload.get("security_code") not in {"005930", "000660"}:
        raise SemanticGap("UNAVAILABLE_STAGE_B_EPS_GATE")
