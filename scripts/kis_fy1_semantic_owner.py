"""Offline KIS estimate qualification. Not imported by production consumers.

Documentation reviews are trusted, frozen inputs, not model-provided claims.
No live scale is approved here: a unit label is not a wire conversion contract.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re


ENDPOINT = "/uapi/domestic-stock/v1/quotations/estimate-perform"
LAYOUT = ("EBITDA", "EPS", "EPS_CHANGE", "PER", "EV_EBITDA", "ROE", "DEBT_RATIO", "INTEREST_COVERAGE")
ALLOWED_ROLES = ("VALUATION", "NEW_BUYER_VALUATION", "HOLDER_VALUATION")
PROHIBITED_ROLES = ("OVERALL_DIRECTION", "FUNDAMENTAL_CORE", "PASS_A_DIRECTIONAL",
                    "SUPPORTING_BUSINESS_EVIDENCE", "CONTRADICTING_BUSINESS_EVIDENCE")
PERIOD = re.compile(r"([0-9]{4})\.(0[1-9]|1[0-2])(E?)")
ANNUAL = re.compile(r"(?:\[기재정정\])?사업보고서\s*\(([0-9]{4})\.(0[1-9]|1[0-2])\)")


class SemanticGap(ValueError):
    pass


@dataclass(frozen=True)
class Evidence:
    raw: bytes
    sha256: str

    def payload(self):
        if sha256(self.raw).hexdigest() != self.sha256:
            raise SemanticGap("UNAVAILABLE_SOURCE_HASH")
        try:
            value = json.loads(self.raw)
        except (ValueError, UnicodeError):
            raise SemanticGap("UNAVAILABLE_SOURCE_SHAPE") from None
        if not isinstance(value, dict):
            raise SemanticGap("UNAVAILABLE_SOURCE_SHAPE")
        return value


@dataclass(frozen=True)
class Documentation:
    evidence: Evidence
    endpoint: str = ENDPOINT

    def review(self):
        value = self.evidence.payload()
        if self.endpoint != ENDPOINT or value.get("endpoint") != ENDPOINT:
            raise SemanticGap("UNAVAILABLE_DOCUMENTATION_SCOPE")
        return value


def security_binding(code, estimate, identity):
    """Require the exact KIS product/short/standard-code tuple, not a name match."""
    if identity is None or not isinstance(estimate.get("output1"), dict):
        raise SemanticGap("UNAVAILABLE_SECURITY_IDENTITY")
    source = identity.payload()
    row = source.get("output", {})
    represented = estimate.get("output1", {}).get("sht_cd")
    if (not isinstance(row, dict) or not re.fullmatch(r"[0-9]{6}", code) or source.get("rt_cd") != "0"
            or represented != "A" + code or row.get("pdno") != "00000" + represented
            or row.get("shtn_pdno") != code or row.get("prdt_type_cd") != "300"
            or row.get("prdt_clsf_name") != "주권"
            or row.get("ivst_prdt_type_cd_name") != "주식"
            or not re.fullmatch(r"KR[A-Z0-9]{10}", row.get("std_pdno", ""))
            or not row.get("prdt_name")):
        raise SemanticGap("UNAVAILABLE_SECURITY_IDENTITY")
    return {"contract": "KISDomesticSecurityRepresentationBinding", "state": "QUALIFIED",
            "request_code": code, "estimate_sht_cd": represented,
            "provider_product_number": row["pdno"], "short_code": row["shtn_pdno"],
            "standard_code": row["std_pdno"], "security_name": row["prdt_name"],
            "product_type": row["prdt_type_cd"], "security_type": row["prdt_clsf_name"],
            "market_scope": "KIS_DOMESTIC_STOCK", "source_sha256": identity.sha256,
            "normalization": "Exact same response tuple: pdno == 00000 + estimate.sht_cd; shtn_pdno == request. No standalone prefix stripping."}


def fiscal_owner(code, corp_code, inventory, cutoff):
    if inventory is None:
        raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
    source = inventory.payload()
    rows = source.get("list", [])
    if (source.get("status") != "000" or not isinstance(rows, list)
            or source.get("page_no") != 1 or source.get("total_page") != 1
            or source.get("total_count") != len(rows) or not rows):
        raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
    annuals = []
    for row in rows:
        if not isinstance(row, dict) or row.get("stock_code") != code or row.get("corp_code") != corp_code:
            raise SemanticGap("UNAVAILABLE_FISCAL_IDENTITY")
        try:
            available = date.fromisoformat(row.get("rcept_dt", ""))
        except (ValueError, TypeError):
            raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD") from None
        if available > cutoff:
            continue
        match = ANNUAL.fullmatch(row.get("report_nm", ""))
        if match and re.fullmatch(r"[0-9]{14}", row.get("rcept_no", "")):
            period = tuple(map(int, match.groups()))
            if period >= (available.year, available.month):
                raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
            annuals.append((period, row["rcept_dt"], row))
    if not annuals:
        raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
    period, _, row = max(annuals, key=lambda item: (item[0], item[1], item[2]["rcept_no"]))
    return {"state": "QUALIFIED", "fiscal_year": period[0], "fiscal_end_month": period[1],
            "report_type": "ANNUAL", "report_name": row["report_nm"],
            "receipt_id": row["rcept_no"], "publication_date": row["rcept_dt"],
            "corp_code": corp_code, "security_code": code, "market_class": row.get("corp_cls"),
            "source_sha256": inventory.sha256, "as_of": cutoff.isoformat(),
            "latest_scope": "Latest annual in complete sealed filing inventory as of source cutoff"}


def period_pattern(payload):
    rows = payload.get("output4", [])
    if not isinstance(rows, list) or len(rows) != 5:
        raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
    parsed = []
    for row in rows:
        match = PERIOD.fullmatch(row.get("dt", "")) if isinstance(row, dict) else None
        if not match:
            raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
        year, month, marker = match.groups()
        parsed.append((int(year), int(month), marker))
    history = [p for p in parsed if not p[2]]
    forecasts = [p for p in parsed if p[2] == "E"]
    if (not history or not forecasts or parsed != history + forecasts
            or any(b[0] != a[0] + 1 or b[1] != a[1] for a, b in zip(parsed, parsed[1:]))):
        raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
    return parsed


def forecast_binding(estimate, fiscal, docs, controls):
    review = docs.review()
    if review.get("conflicting_marker_definition") is not False:
        raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
    if review.get("explicit_e_definition") is True:
        method = "OFFICIAL_DOCUMENTED_E"
    elif (review.get("official_estimate_endpoint") is True
          and review.get("analyst_estimates_description") is True
          and review.get("output4_data1_to_5_link") is True):
        patterns = []
        identities = set()
        for evidence in controls:
            payload = evidence.payload()
            if payload.get("rt_cd") != "0":
                raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
            identities.add(payload.get("output1", {}).get("sht_cd"))
            patterns.append(period_pattern(payload))
        if (len(identities) < 2 or None in identities or len(patterns) < 2
                or any(p != patterns[0] for p in patterns)):
            raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
        method = "KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS"
    else:
        raise SemanticGap("UNAVAILABLE_FORECAST_MARKER")
    parsed = period_pattern(estimate)
    annual = (fiscal["fiscal_year"], fiscal["fiscal_end_month"])
    history = [p[:2] for p in parsed if not p[2]]
    if any(p[1] != annual[1] for p in parsed) or max(history) != annual:
        raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
    forecasts = [i for i, p in enumerate(parsed) if p[2] == "E" and p[:2] > annual]
    if not forecasts:
        raise SemanticGap("UNAVAILABLE_NO_FORECAST_ROW")
    return {"state": "QUALIFIED", "method": method, "endpoint": ENDPOINT,
            "is_inference_not_official_quote": method == "KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS",
            "documentation_sha256": docs.evidence.sha256,
            "control_source_hashes": [e.sha256 for e in controls],
            "period_labels": [r["dt"] for r in estimate["output4"]],
            "fy1_column": forecasts[0] + 1,
            "fy1": estimate["output4"][forecasts[0]]["dt"],
            "fy2": estimate["output4"][forecasts[1]]["dt"] if len(forecasts) > 1 else None,
            "reason": "Earliest qualified forecast annual period strictly after independent completed annual owner"}


def metric_snapshot(metric, estimate, period, docs):
    review = docs.review()
    rows = estimate.get("output3", [])
    if not isinstance(rows, list) or len(rows) != 8:
        return {"state": "UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS", "value": None}
    if (tuple(review.get("output3_layout", [])) != LAYOUT
            or any(not isinstance(r, dict) or set(r) != {f"data{i}" for i in range(1, 6)} for r in rows)):
        return {"state": "UNAVAILABLE_OUTPUT3_LAYOUT", "value": None}
    index = LAYOUT.index(metric)
    raw = rows[index][f"data{period['fy1_column']}"]
    result = {"state": "UNAVAILABLE_WIRE_SCALE", "value": None, "raw_candidate": raw,
              "row_index": index, "column": period["fy1_column"], "period": period["fy1"],
              "documentation_sha256": docs.evidence.sha256}
    scale = review.get("wire_scales", {}).get(metric)
    unit = "KRW_PER_SHARE" if metric == "EPS" else "MULTIPLE"
    # Only an independently reviewed exact machine-to-display rule can enable a metric.
    if (not isinstance(scale, dict) or scale.get("unit") != unit
            or scale.get("kind") != "OFFICIAL_EXPLICIT_RAW_TO_DISPLAY"
            or not re.fullmatch(r"[a-f0-9]{64}", scale.get("source_sha256", ""))
            or not scale.get("definition")):
        return result
    try:
        number, multiplier = Decimal(raw), Decimal(scale["multiplier"])
        if not number.is_finite() or not multiplier.is_finite() or multiplier <= 0:
            raise InvalidOperation
        value = number * multiplier
    except (InvalidOperation, ValueError, TypeError, KeyError):
        return {**result, "state": "UNAVAILABLE_WIRE_VALUE"}
    return {**result, "state": "QUALIFIED_KIS_FY1_" + metric,
            "value": str(value), "unit": unit, "scale_evidence": scale,
            "allowed_roles": list(ALLOWED_ROLES), "prohibited_roles": list(PROHIBITED_ROLES),
            "estimate_kind": "KIS_ANALYST_ESTIMATE_NOT_CONSENSUS_AVERAGE"}


def qualify(code, corp_code, estimate, identity, inventory, cutoff, docs, controls=()):
    """No price parameter, network, production writes or automatic source failure."""
    result = {"security_code": code, "source_failure": False,
              "derived_fper": {"state": "UNAVAILABLE_PRICE_SHARE_SPLIT_BASIS", "value": None}}
    try:
        if estimate is None:
            raise SemanticGap("UNAVAILABLE_NOT_QUERIED_STAGE_A_GATE")
        payload = estimate.payload()
        result["estimate_sha256"] = estimate.sha256
        if payload.get("rt_cd") != "0":
            raise SemanticGap("UNAVAILABLE_PROVIDER_ESTIMATE")
        result["security"] = security_binding(code, payload, identity)
        result["fiscal"] = fiscal_owner(code, corp_code, inventory, cutoff)
        result["forecast"] = forecast_binding(payload, result["fiscal"], docs, controls)
        result["eps"] = metric_snapshot("EPS", payload, result["forecast"], docs)
        result["provider_per"] = metric_snapshot("PER", payload, result["forecast"], docs)
    except SemanticGap as exc:
        result["eps"] = {"state": str(exc), "value": None}
        result["provider_per"] = {"state": str(exc), "value": None}
    return result


def admitted_to_role(metric, role):
    return (metric.get("state") in {"QUALIFIED_KIS_FY1_EPS", "QUALIFIED_KIS_FY1_PER"}
            and role in ALLOWED_ROLES and role in metric.get("allowed_roles", []))
