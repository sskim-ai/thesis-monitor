"""Offline research-family qualification; no production imports or live defaults.

Extraction reviews are frozen, operator-reviewed evidence, never model claims.
No live transform or growth rounding rule is approved by this module.
"""

from datetime import datetime
from fractions import Fraction
from hashlib import sha256
from itertools import permutations
from urllib.parse import urlsplit

from scripts.kis_eps_wire_calibration import (
    decimal_string, number, sealed, valid_full_layout, verified,
)
from scripts.kis_fy1_semantic_owner import (
    ALLOWED_ROLES, LAYOUT, PERIOD, PROHIBITED_ROLES, SemanticGap,
    period_pattern, security_binding,
)


OFFICIAL_HOSTS = {"truefriend.com", "www.truefriend.com", "securities.koreainvestment.com"}
BINDING = "KISResearchEstimateSnapshotBinding"
WIRE = "KISEstimatePerformResearchWireSemantics"
PARTIAL = "KISPartialOutput3EPSGrowthBinding"
UNITS = {"EPS": "KRW_PER_SHARE", "PER": "MULTIPLE"}


def official_url(value):
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS
                and not parsed.username and not parsed.password and parsed.port in {None, 443})
    except (TypeError, ValueError):
        return False


def blob(evidence):
    if evidence is None or not evidence.raw or sha256(evidence.raw).hexdigest() != evidence.sha256:
        raise SemanticGap("UNAVAILABLE_RESEARCH_ARTIFACT")


def bind_research(code, estimate, identity, page, attachment, extraction):
    """Require preserved artifacts plus a reviewed same-snapshot extraction."""
    blob(page)
    blob(attachment)
    if extraction is None:
        raise SemanticGap("UNAVAILABLE_RESEARCH_REPORT_BINDING")
    payload, review = estimate.payload(), extraction.payload()
    security = security_binding(code, payload, identity)
    metadata, document = review.get("page_metadata", {}), review.get("document_metadata", {})
    output = payload["output1"]
    if (payload.get("rt_cd") != "0" or review.get("kind") != "REVIEWED_OFFICIAL_RESEARCH_EXTRACTION"
            or review.get("page_sha256") != page.sha256
            or review.get("attachment_sha256") != attachment.sha256
            or not official_url(review.get("page_url")) or not official_url(review.get("attachment_url"))
            or review.get("attachment_linked_by_page") is not True
            or review.get("all_metric_periods_preserved") is not True
            or review.get("method") not in {"PDF_TEXT", "PDF_TABLE", "VISUAL_VERIFIED_TEXT"}):
        raise SemanticGap("UNAVAILABLE_RESEARCH_REPORT_BINDING")
    expected = {"security_code": code, "analyst": output.get("name1"),
                "date": output.get("estdate"), "recommendation": output.get("rcmd_name")}
    try:
        datetime.strptime(expected["date"], "%Y%m%d")
    except (TypeError, ValueError):
        raise SemanticGap("UNAVAILABLE_ESTDATE") from None
    fields = (*expected, "title", "report_type", "report_id")
    if (any(not metadata.get(k) or metadata.get(k) != document.get(k) for k in fields)
            or any(not v or metadata.get(k) != v for k, v in expected.items())):
        raise SemanticGap("UNAVAILABLE_RESEARCH_SNAPSHOT_BINDING")
    tables = review.get("tables", {})
    if not isinstance(tables, dict) or not tables or set(tables) - set(UNITS):
        raise SemanticGap("UNAVAILABLE_RESEARCH_TABLE")
    for metric, table in tables.items():
        rows = table.get("rows")
        if (table.get("unit") != UNITS[metric] or type(table.get("page")) is not int
                or table["page"] < 1 or not table.get("section") or not isinstance(rows, list) or not rows):
            raise SemanticGap("UNAVAILABLE_RESEARCH_TABLE")
        seen = set()
        for row in rows:
            label = row.get("period", "")
            if not PERIOD.fullmatch(label) or label in seen or number(row.get("value")) is None:
                raise SemanticGap("UNAVAILABLE_RESEARCH_TABLE")
            seen.add(label)
    return sealed({"contract": BINDING, "state": "QUALIFIED", "security_code": code,
        "security": security, "metadata": metadata, "tables": tables,
        "estimate_sha256": estimate.sha256, "extraction_sha256": extraction.sha256,
        "page_sha256": page.sha256, "attachment_sha256": attachment.sha256,
        "source_family": "KIS_RESEARCH_ESTIMATE", "not_consensus": True,
        "identity_scope": "SAME_SECURITY_ANALYST_DATE_SNAPSHOT_FAMILY_NOT_PROVEN_PDF_GENERATOR"})


def partial_eps_binding(estimate, docs, rounding=None):
    """All ordered row pairs, signed denominator, documented rounding only."""
    payload = estimate.payload()
    rows = payload.get("output3")
    if (tuple(docs.review().get("output3_layout", [])) != LAYOUT
            or not isinstance(rows, list) or len(rows) != 3
            or any(not isinstance(r, dict) or set(r) != {f"data{i}" for i in range(1, 6)} for r in rows)):
        raise SemanticGap("UNAVAILABLE_PARTIAL_ROW_SEMANTICS")
    period_pattern(payload)
    values = [[number(r[f"data{i}"]) for i in range(1, 6)] for r in rows]
    result = {"contract": PARTIAL, "state": "UNAVAILABLE_DOCUMENTED_GROWTH_ROUNDING",
              "estimate_sha256": estimate.sha256, "row_index": None, "matching_pairs": [],
              "candidate_pairs": [], "documentation_sha256": docs.evidence.sha256,
              "signed_denominator": True, "provider_per_qualified": False}
    if rounding is None:
        return sealed(result)
    policy = rounding.payload()
    rule = policy.get("rule", {})
    if (policy.get("kind") != "OFFICIAL_DOCUMENTED_GROWTH_ROUNDING"
            or policy.get("documentation_sha256") != docs.evidence.sha256
            or not rule or rule != docs.review().get("growth_rounding")):
        return sealed(result)
    factor = number(rule.get("wire_to_percentage_points"))
    if factor is None or factor <= 0 or rule.get("rounding") not in {"HALF_AWAY_FROM_ZERO", "TRUNCATE_TOWARD_ZERO"}:
        return sealed(result)
    audits, matches = [], []
    for eps, growth in permutations(range(3), 2):
        transitions = []
        complete = all(v is not None for v in values[eps] + values[growth])
        for i in range(1, 5):
            previous, current = values[eps][i - 1:i + 1]
            if previous in {None, 0} or current is None:
                continue
            exact = (current / previous - 1) * 100 / factor
            magnitude = abs(exact)
            if rule["rounding"] == "HALF_AWAY_FROM_ZERO":
                magnitude += Fraction(1, 2)
            rounded = magnitude.numerator // magnitude.denominator
            rounded *= -1 if exact < 0 else 1
            transitions.append({"column": i + 1, "exact_wire_fraction": str(exact),
                "rounded_wire": str(rounded), "actual_wire": rows[growth][f"data{i + 1}"],
                "match": Fraction(rounded) == values[growth][i]})
        match = complete and len(transitions) >= 2 and all(t["match"] for t in transitions)
        audits.append({"eps_row": eps, "growth_row": growth, "transitions": transitions, "match": match})
        if match:
            matches.append([eps, growth])
    return sealed({**result, "state": "QUALIFIED" if len(matches) == 1 else "UNAVAILABLE_PARTIAL_ROW_SEMANTICS",
        "rounding_review_sha256": rounding.sha256, "candidate_pairs": audits,
        "matching_pairs": matches, "row_index": matches[0][0] if len(matches) == 1 else None})


def metric_row(metric, estimate, docs, partial=None):
    payload = estimate.payload()
    if metric not in UNITS or tuple(docs.review().get("output3_layout", [])) != LAYOUT:
        raise SemanticGap("UNAVAILABLE_OUTPUT3_LAYOUT")
    if valid_full_layout(payload.get("output3")):
        return LAYOUT.index(metric)
    if metric == "PER":
        raise SemanticGap("UNAVAILABLE_NO_PER_ROW")
    if partial is not None:
        verified(partial, PARTIAL)
        if partial["state"] == "QUALIFIED" and partial["estimate_sha256"] == estimate.sha256:
            return partial["row_index"]
    raise SemanticGap("UNAVAILABLE_PARTIAL_ROW_SEMANTICS")


def calibrate(metric, estimate, docs, binding, partial=None):
    verified(binding, BINDING)
    if binding["state"] != "QUALIFIED" or binding["estimate_sha256"] != estimate.sha256:
        raise SemanticGap("UNAVAILABLE_RESEARCH_SNAPSHOT_BINDING")
    index = metric_row(metric, estimate, docs, partial)
    payload = estimate.payload()
    period_pattern(payload)
    table = binding["tables"].get(metric)
    if not table:
        raise SemanticGap("UNAVAILABLE_RESEARCH_TABLE")
    wire = dict(zip([r["dt"] for r in payload["output4"]],
                    [payload["output3"][index][f"data{i}"] for i in range(1, 6)]))
    pairs, outside, factors = [], [], set()
    for row in table["rows"]:
        label, display = row["period"], number(row["value"])
        if label not in wire:
            outside.append({**row, "reason": "NO_API_PERIOD_EXACT_MATCH"})
            continue
        raw = number(wire[label])
        if raw is None:
            raise SemanticGap("UNAVAILABLE_WIRE_VALUE")
        factor = display / raw if raw else None
        if factor is not None:
            factors.add(factor)
        pairs.append({"period": label, "raw": wire[label], "display": row["value"],
                      "factor": str(factor) if factor is not None else None,
                      "zero_conflict": not raw and bool(display)})
    state, factor = "UNAVAILABLE_RESEARCH_WIRE_SCALE", None
    if any(p["zero_conflict"] for p in pairs) or len(factors) > 1 or any(f <= 0 for f in factors):
        state = "UNAVAILABLE_RESEARCH_SNAPSHOT_MISMATCH"
    elif len(pairs) >= 2 and len(factors) == 1:
        factor = decimal_string(next(iter(factors)))
        state = "QUALIFIED"
    return sealed({"contract": WIRE, "state": state, "metric": metric, "unit": UNITS[metric],
        "factor": factor, "pairs": pairs, "outside_api_periods": outside,
        "binding_sha256": binding["receipt_sha256"], "estimate_sha256": estimate.sha256,
        "attachment_sha256": binding["attachment_sha256"], "documentation_sha256": docs.evidence.sha256,
        "periods_dropped_for_disagreement": 0, "price_used": False, "reference_ratio_used": False})


def snapshot(metric, estimate, security, forecast, docs, calibration, partial=None):
    """Stage B consumes one frozen global transform, with no per-ticker fitting."""
    verified(calibration, WIRE)
    payload = estimate.payload()
    try:
        datetime.strptime(payload.get("output1", {}).get("estdate", ""), "%Y%m%d")
    except (TypeError, ValueError):
        raise SemanticGap("UNAVAILABLE_ESTDATE") from None
    if (calibration["state"] != "QUALIFIED" or calibration["metric"] != metric
            or calibration["documentation_sha256"] != docs.evidence.sha256
            or payload.get("rt_cd") != "0" or security.get("state") != "QUALIFIED"
            or payload.get("output1", {}).get("sht_cd") != "A" + security.get("request_code", "")
            or forecast.get("state") != "QUALIFIED"):
        raise SemanticGap("UNAVAILABLE_RESEARCH_WIRE_SCALE")
    periods = [r["dt"] for r in payload["output4"]]
    if (periods != forecast.get("period_labels") or forecast.get("fy1") not in periods
            or not forecast["fy1"].endswith("E")
            or periods.index(forecast["fy1"]) + 1 != forecast.get("fy1_column")):
        raise SemanticGap("UNAVAILABLE_FISCAL_PERIOD")
    index = metric_row(metric, estimate, docs, partial)
    raw = payload["output3"][index][f"data{forecast['fy1_column']}"]
    value, factor = number(raw), number(calibration["factor"])
    if value is None or factor is None or factor <= 0:
        raise SemanticGap("UNAVAILABLE_WIRE_VALUE")
    return sealed({"contract": "KISResearchFY1Snapshot", "state": "QUALIFIED_KIS_RESEARCH_FY1_" + metric,
        "metric": metric, "security_code": security["request_code"], "period": forecast["fy1"],
        "raw": raw, "value": decimal_string(value * factor), "unit": UNITS[metric],
        "estdate": payload["output1"].get("estdate"), "estimate_sha256": estimate.sha256,
        "calibration_sha256": calibration["receipt_sha256"], "source_kind": "KIS_HOUSE_RESEARCH_NOT_CONSENSUS",
        "allowed_roles": list(ALLOWED_ROLES), "prohibited_roles": list(PROHIBITED_ROLES),
        "overall_direction_use": False, "current_session_metric": False})


def freshness(estimate, retrieval_time, as_of):
    row = estimate.payload().get("output1", {})
    result = {"contract": "KISResearchEstimateFreshness", "query_time": retrieval_time,
              "estdate": row.get("estdate"), "age_days": None, "as_of": as_of.isoformat(),
              "estimate_sha256": estimate.sha256, "new_query_in_this_task": False,
              "newer_snapshot_returned": None, "latest_available_verified": False}
    try:
        observed = datetime.fromisoformat(retrieval_time)
        estdate = datetime.strptime(row.get("estdate", ""), "%Y%m%d").date()
        if observed.tzinfo is None or not estdate <= observed.date() <= as_of:
            raise ValueError
    except (TypeError, ValueError):
        return {**result, "state": "UNAVAILABLE_ESTDATE_OR_RETRIEVAL_TIME"}
    return {**result, "state": "SEALED_KIS_RESEARCH_SNAPSHOT_CURRENT_LATEST_UNVERIFIED",
            "age_days": (as_of - estdate).days, "arbitrary_stale_threshold": None}


def current_fper_denial(eps=None):
    """No configured KIS/KSD action-window owner exists in this revision.

    A caller-supplied 'no actions' flag cannot enable current per-share basis.
    A future source-qualified action owner needs a separately reviewed contract.
    """
    if eps is None:
        return {"state": "UNAVAILABLE_EPS", "value": None}
    verified(eps, "KISResearchFY1Snapshot")
    if eps.get("state") != "QUALIFIED_KIS_RESEARCH_FY1_EPS":
        return {"state": "UNAVAILABLE_EPS", "value": None}
    if number(eps["value"]) <= 0:
        return {"state": "NOT_MEANINGFUL", "value": None}
    return {"state": "UNAVAILABLE_CORPORATE_ACTION_BASIS", "value": None,
            "completed_session_price_used": False, "intraday_price_used": False}


def stage_b_admitted(metrics):
    for metric in metrics:
        try:
            verified(metric, "KISResearchFY1Snapshot")
        except SemanticGap:
            continue
        if metric.get("state") in {"QUALIFIED_KIS_RESEARCH_FY1_EPS", "QUALIFIED_KIS_RESEARCH_FY1_PER"}:
            return True
    return False
