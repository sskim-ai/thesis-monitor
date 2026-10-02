"""Offline REV36 protocol calibration. Never a production provider or price owner.

The reviewed PDF table is a trusted operator input, not an AI-generated claim.
Historical display calibration establishes units, not current research freshness.
"""

from datetime import date, datetime
from fractions import Fraction
from hashlib import sha256
from itertools import permutations
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from scripts.kis_eps_wire_calibration import decimal_string, number, sealed, valid_full_layout, verified
from scripts.kis_fy1_semantic_owner import (
    ALLOWED_ROLES, LAYOUT, PROHIBITED_ROLES, SemanticGap, fiscal_owner,
    forecast_binding, period_pattern, security_binding,
)

PROTOCOL = "KISOutput3OfficialProtocolScaleV1"
PARTIAL = "KISOutput3UniqueEPSGrowthV1"
SNAPSHOT = "KISProtocolFY1SnapshotV1"
GATE = "KISProtocolStageBAdmissionV1"
PRECISION = {"contract": "REV36_EXPLICIT_GROWTH_PRECISION_POLICY",
    "percentage_point_quantum": "0.1", "rounding": "NEAREST_HALF_AWAY_FROM_ZERO",
    "authority": "USER_WORK_INSTRUCTION_NOT_OFFICIAL_ROUNDING_QUOTE",
    "signed_denominator": True, "first_growth_cell_used": False}
UNITS = {"EPS": "KRW_PER_SHARE", "PER": "MULTIPLE"}
STATES = {"EPS": "KIS_FY1_EPS_ESTIMATE_SNAPSHOT", "PER": "KIS_PROVIDER_FY1_PER_SNAPSHOT"}


def _rows(estimate):
    payload = estimate.payload()
    period_pattern(payload)
    rows = payload.get("output3")
    if (payload.get("rt_cd") != "0" or not isinstance(rows, list) or not 1 <= len(rows) <= 8
            or any(not isinstance(r, dict) or set(r) != {f"data{i}" for i in range(1, 6)} for r in rows)):
        raise SemanticGap("UNAVAILABLE_OUTPUT3_LAYOUT")
    return payload, rows


def _documentation(docs):
    if tuple(docs.review().get("output3_layout", [])) != LAYOUT:
        raise SemanticGap("UNAVAILABLE_OUTPUT3_LAYOUT")


def calibrate(pdf, extraction, docs, sources, identities, fiscals):
    """Use all reviewed historical controls; no price or reported-EPS series input."""
    _documentation(docs)
    review = extraction.payload()
    try:
        url = urlsplit(review["url"])
        official = (url.scheme == "https" and url.hostname == "file.truefriend.com"
            and url.port in {None, 443} and not url.username and not url.password
            and url.path.startswith("/Storage/research/") and url.path.endswith(".pdf")
            and not url.query and not url.fragment)
        date.fromisoformat(review["document_date"])
    except (KeyError, TypeError, ValueError):
        official = False
    if (not official or not pdf.raw.startswith(b"%PDF-")
            or sha256(pdf.raw).hexdigest() != pdf.sha256
            or review.get("kind") != "VISUAL_VERIFIED_OFFICIAL_HISTORICAL_TABLE"
            or review.get("artifact_sha256") != pdf.sha256
            or not review.get("title") or not review.get("analyst")
            or not isinstance(review.get("page"), int) or review["page"] < 1
            or not review.get("section") or review.get("units") != UNITS
            or review.get("all_selected_historical_controls_preserved") is not True
            or not isinstance(review.get("controls"), list)):
        raise SemanticGap("UNAVAILABLE_OFFICIAL_SCALE_ARTIFACT")
    controls = review["controls"]
    grouped, seen = {}, set()
    for item in controls:
        try:
            code, metric, label = item["security_code"], item["metric"], item["period"]
            key = code, metric, label
            if key in seen or metric not in UNITS or item.get("period_kind") != "ACTUAL":
                raise ValueError
            seen.add(key)
            display = number(item["value"])
            if display is None or not item.get("raw_token") or not item.get("bbox"):
                raise ValueError
            payload, rows = _rows(sources[code])
            security_binding(code, payload, identities[code])
            fiscal = fiscals[code]
            if fiscal.get("state") != "QUALIFIED" or fiscal.get("security_code") != code:
                raise ValueError
            periods = [p["dt"] for p in payload["output4"]]
            if label not in periods or label.endswith("E"):
                raise ValueError
            year, month = map(int, label.split("."))
            if month != fiscal["fiscal_end_month"] or year > fiscal["fiscal_year"]:
                raise ValueError
            grouped.setdefault((code, metric), []).append((periods.index(label) + 1, display, item))
        except (KeyError, TypeError, ValueError):
            raise SemanticGap("UNAVAILABLE_CALIBRATION_CONTROL") from None
    # Full layouts establish the transform before any shortened EPS row is searched.
    factors, pairs, selected_rows = {m: set() for m in UNITS}, [], {}
    for (code, metric), items in grouped.items():
        payload, rows = _rows(sources[code])
        if not valid_full_layout(rows):
            continue
        index = LAYOUT.index(metric)
        selected_rows[code + ":" + metric] = index
        for column, display, item in items:
            raw = number(rows[index][f"data{column}"])
            if raw in {None, 0} or display == 0:
                raise SemanticGap("UNAVAILABLE_OUTPUT3_SCALE_CONTRACT")
            factors[metric].add(display / raw)
    if any(len(v) != 1 or next(iter(v)) <= 0 for v in factors.values()):
        raise SemanticGap("UNAVAILABLE_OUTPUT3_SCALE_CONTRACT")
    scale = {m: next(iter(v)) for m, v in factors.items()}
    if any(v != Fraction(1, 10) for v in scale.values()):
        raise SemanticGap("UNAVAILABLE_OUTPUT3_SCALE_CONTRACT")
    for (code, metric), items in grouped.items():
        payload, rows = _rows(sources[code])
        if len(items) < 2:
            raise SemanticGap("UNAVAILABLE_CALIBRATION_CONTROL")
        key = code + ":" + metric
        if key not in selected_rows:
            if metric != "EPS":
                raise SemanticGap("UNAVAILABLE_NO_PER_ROW")
            matches = [i for i, row in enumerate(rows) if all(
                number(row[f"data{c}"]) is not None and number(row[f"data{c}"]) * scale[metric] == d
                for c, d, _ in items)]
            if len(matches) != 1:
                raise SemanticGap("UNAVAILABLE_PARTIAL_ABSOLUTE_EPS_BINDING")
            selected_rows[key] = matches[0]
        index = selected_rows[key]
        for column, display, item in items:
            raw = number(rows[index][f"data{column}"])
            if raw is None or raw * scale[metric] != display:
                raise SemanticGap("UNAVAILABLE_OUTPUT3_SCALE_CONTRACT")
            pairs.append({**item, "row_index": index, "column": column,
                "wire": rows[index][f"data{column}"], "factor": decimal_string(scale[metric]),
                "exact_match": True, "estimate_sha256": sources[code].sha256})
    eps_pairs = [p for p in pairs if p["metric"] == "EPS"]
    if (len(eps_pairs) < 4 or len({p["security_code"] for p in eps_pairs}) < 2
            or len([p for p in pairs if p["metric"] == "PER"]) < 2):
        raise SemanticGap("UNAVAILABLE_CALIBRATION_CONTROL")
    return sealed({"contract": PROTOCOL, "state": "QUALIFIED", "factors": {m: decimal_string(v) for m, v in scale.items()},
        "units": UNITS, "pairs": pairs, "selected_rows": selected_rows,
        "artifact_sha256": pdf.sha256, "extraction_sha256": extraction.sha256,
        "documentation_sha256": docs.evidence.sha256,
        "source_hashes": {c: sources[c].sha256 for c, _ in grouped},
        "identity_hashes": {c: identities[c].sha256 for c, _ in grouped},
        "fiscal_source_hashes": {c: fiscals[c]["source_sha256"] for c, _ in grouped},
        "scope": "PROTOCOL_SCALE_NOT_SAME_ANALYST_DATE_SNAPSHOT",
        "price_used": False, "financial_ratio_used": False, "dropped_disagreements": 0})


def _protocol(protocol, docs):
    verified(protocol, PROTOCOL)
    _documentation(docs)
    if (protocol.get("state") != "QUALIFIED" or protocol.get("factors") != {"EPS": "0.1", "PER": "0.1"}
            or protocol.get("documentation_sha256") != docs.evidence.sha256):
        raise SemanticGap("UNAVAILABLE_OUTPUT3_SCALE_CONTRACT")


def partial_binding(estimate, docs, protocol, *, stage_a=False):
    _protocol(protocol, docs)
    payload, rows = _rows(estimate)
    if len(rows) >= 8:
        raise SemanticGap("UNAVAILABLE_PARTIAL_ROW_SEMANTICS")
    code = payload.get("output1", {}).get("sht_cd", "")[1:]
    absolute = protocol.get("selected_rows", {}).get(code + ":EPS") if stage_a else None
    if stage_a and (protocol.get("source_hashes", {}).get(code) != estimate.sha256 or absolute is None):
        raise SemanticGap("UNAVAILABLE_PARTIAL_ABSOLUTE_EPS_BINDING")
    values = [[number(r[f"data{i}"]) for i in range(1, 6)] for r in rows]
    audits, matches = [], []
    for eps, growth in permutations(range(len(rows)), 2):
        transitions, consecutive, longest = [], 0, 0
        for i in range(1, 5):
            previous, current = values[eps][i - 1:i + 1]
            reported = values[growth][i]
            if previous in {None, 0} or current is None:
                consecutive = 0
                continue
            exact_wire = (current / previous - 1) * 1000
            magnitude = abs(exact_wire) + Fraction(1, 2)
            rounded = (magnitude.numerator // magnitude.denominator) * (-1 if exact_wire < 0 else 1)
            match = Fraction(rounded) == reported
            consecutive = consecutive + 1 if match else 0
            longest = max(longest, consecutive)
            transitions.append({"column": i + 1, "signed_exact_wire_fraction": str(exact_wire),
                "rounded_percentage_points": decimal_string(Fraction(rounded, 10)),
                "reported_wire": rows[growth][f"data{i + 1}"], "match": match})
        match = (longest >= (4 if stage_a else 2) and all(t["match"] for t in transitions)
                 and (not stage_a or eps == absolute))
        audits.append({"eps_row": eps, "growth_row": growth, "transitions": transitions,
                       "longest_consecutive": longest, "match": match})
        if match:
            matches.append([eps, growth])
    return sealed({"contract": PARTIAL, "state": "QUALIFIED" if len(matches) == 1 else "UNAVAILABLE_PARTIAL_ROW_SEMANTICS",
        "estimate_sha256": estimate.sha256, "protocol_sha256": protocol["receipt_sha256"],
        "documentation_sha256": docs.evidence.sha256, "precision_policy": PRECISION,
        "stage_a_absolute_eps_first": stage_a, "absolute_eps_row": absolute,
        "row_index": matches[0][0] if len(matches) == 1 else None,
        "growth_row_index": matches[0][1] if len(matches) == 1 else None,
        "matching_pairs": matches, "candidate_pairs": audits, "provider_per_qualified": False})


def snapshot(metric, estimate, identity, inventory, corp_code, cutoff, docs, controls, protocol,
             retrieval_time, as_of, *, stage_a=False):
    """Re-bind identity, fiscal and period from evidence, not caller-supplied booleans."""
    _protocol(protocol, docs)
    payload, rows = _rows(estimate)
    code = payload.get("output1", {}).get("sht_cd", "")[1:]
    security = security_binding(code, payload, identity)
    fiscal = fiscal_owner(code, corp_code, inventory, cutoff)
    forecast = forecast_binding(payload, fiscal, docs, controls)
    if metric not in UNITS:
        raise SemanticGap("UNAVAILABLE_METRIC")
    partial = None
    if valid_full_layout(rows):
        index = LAYOUT.index(metric)
    elif metric == "PER":
        raise SemanticGap("UNAVAILABLE_NO_PER_ROW")
    else:
        partial = partial_binding(estimate, docs, protocol, stage_a=stage_a)
        if partial["state"] != "QUALIFIED":
            raise SemanticGap(partial["state"])
        index = partial["row_index"]
    try:
        estdate = datetime.strptime(payload["output1"]["estdate"], "%Y%m%d").date()
        observed = datetime.fromisoformat(retrieval_time)
        if observed.tzinfo is None or not estdate <= observed.astimezone(ZoneInfo("Asia/Seoul")).date() <= as_of:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise SemanticGap("UNAVAILABLE_ESTDATE_OR_RETRIEVAL_TIME") from None
    raw = rows[index][f"data{forecast['fy1_column']}"]
    value = number(raw)
    if value is None:
        raise SemanticGap("UNAVAILABLE_WIRE_VALUE")
    return sealed({"contract": SNAPSHOT, "state": STATES[metric], "metric": metric,
        "security_code": code, "security": security, "fiscal": fiscal, "forecast": forecast,
        "raw": raw, "row_index": index, "column": forecast["fy1_column"], "period": forecast["fy1"],
        "factor": protocol["factors"][metric], "value": decimal_string(value * number(protocol["factors"][metric])),
        "unit": UNITS[metric], "estdate": estdate.isoformat(), "query_time": retrieval_time,
        "age_days": (as_of - estdate).days, "freshness": "RESEARCH_SNAPSHOT_NOT_CURRENT_SESSION",
        "estimate_sha256": estimate.sha256, "protocol_sha256": protocol["receipt_sha256"],
        "partial_binding": partial, "source_kind": "KIS_HOUSE_RESEARCH_NOT_CONSENSUS",
        "allowed_roles": list(ALLOWED_ROLES), "prohibited_roles": list(PROHIBITED_ROLES),
        "overall_direction_use": False, "current_price_used": False})


def qualify(code, estimate, identity, inventory, corp_code, cutoff, docs, controls, protocol,
            retrieval_time, as_of, *, stage_a=False):
    result = {"security_code": code, "source_failure": False}
    for metric, name in (("EPS", "eps"), ("PER", "provider_per")):
        try:
            if estimate is None:
                raise SemanticGap("UNAVAILABLE_NOT_QUERIED")
            payload = estimate.payload()
            if payload.get("rt_cd") != "0":
                raise SemanticGap("UNAVAILABLE_PROVIDER_ESTIMATE")
            if payload.get("output3") in (None, [], {}) or not payload.get("output1"):
                raise SemanticGap("UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE")
            if payload["output1"].get("sht_cd") != "A" + code:
                raise SemanticGap("UNAVAILABLE_SECURITY_IDENTITY")
            result[name] = snapshot(metric, estimate, identity, inventory, corp_code, cutoff, docs,
                controls, protocol, retrieval_time, as_of, stage_a=stage_a)
        except SemanticGap as exc:
            result[name] = {"state": str(exc), "value": None}
    eps = result["eps"]
    reason = "UNAVAILABLE_EPS"
    if eps["state"] == STATES["EPS"]:
        reason = ("UNAVAILABLE_NONPOSITIVE_EPS" if number(eps["value"]) <= 0
                  else "UNAVAILABLE_NO_CONFIGURED_KIS_KSD_CORPORATE_ACTION_OWNER")
    result["current_price_derived_fper"] = {"state": reason, "value": None,
        "security_valuation_basis": "DENIAL_ONLY_UNAVAILABLE_SECURITY_BASIS",
        "provider_snapshot_per_is_not_current_price_per": True}
    return result


def stage_b_gate(rows, protocol):
    verified(protocol, PROTOCOL)
    qualified = []
    for row in rows:
        eps = row.get("eps", {})
        if eps.get("state") == STATES["EPS"]:
            verified(eps, SNAPSHOT)
            if eps.get("protocol_sha256") != protocol["receipt_sha256"]:
                raise SemanticGap("UNAVAILABLE_STAGE_A_BINDING")
            if protocol["source_hashes"].get(eps["security_code"]) != eps["estimate_sha256"]:
                raise SemanticGap("UNAVAILABLE_STAGE_A_BINDING")
            qualified.append(eps)
    return sealed({"contract": GATE, "allow": bool(qualified), "protocol": protocol,
                   "qualified_stage_a_eps": qualified})


def verify_gate(gate):
    verified(gate, GATE)
    expected = stage_b_gate([{"eps": e} for e in gate.get("qualified_stage_a_eps", [])], gate["protocol"])
    if gate != expected or gate["allow"] is not True:
        raise SemanticGap("UNAVAILABLE_STAGE_A_GATE")


def action_window_guard(receipt, *, security_code, estdate, price_date):
    """Offline future-owner contract tests only; PASS does not enable current fPER."""
    families = {"MERGER", "SPLIT", "REVERSE_SPLIT", "BONUS", "PAID_IN"}
    try:
        start, end = date.fromisoformat(estdate), date.fromisoformat(price_date)
        valid = (start <= end and receipt.get("security_code") == security_code
            and receipt.get("from") == estdate and receipt.get("through") == price_date
            and set(receipt.get("families", [])) == families and receipt.get("complete") is True
            and receipt.get("source_kind") in {"KIS_OFFICIAL", "KSD_OFFICIAL"}
            and isinstance(receipt.get("events"), list))
    except (TypeError, ValueError):
        valid = False
    return {"state": "ACTION_WINDOW_CLEAR" if valid and not receipt["events"] else "UNAVAILABLE_CORPORATE_ACTION_BASIS",
            "metric_permission": False, "scope": "OFFLINE_INTERFACE_NOT_CONFIGURED_SOURCE_OWNER"}
