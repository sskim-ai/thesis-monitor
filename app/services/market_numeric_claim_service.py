"""Typed deterministic market numbers, separate from numeric-free model prose."""
from datetime import date
from hashlib import sha256
import json
from math import isclose, isfinite

from app.services.official_night_market_eligibility_service import night_market_eligibility, night_catalog_matches
from app.services.us_full_message_service import _night_timeframe_block

CONTRACT = "market-numeric-claim-v1"
FORMATTER = "market-numeric-formatter-v1"
PROSE_FIELDS = ("breadth_state", "leadership", "flows_or_participation", "rates_or_macro_context")
NUMERIC_FREE_RULE = """Market narrative must be qualitative Korean with no numeric literals, dates,
tenors, maturity codes or instrument names containing digits. Do not spell quantities out
in words as a workaround. The backend separately renders typed eligible numeric facts,
including their dates and instruments. Cite source refs in structured ref arrays only.
Do not quote non-prose-eligible previous levels or calculate new numeric changes."""


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def narrative_errors(row):
    return ["untyped_market_numeric_literal:"+key for key in PROSE_FIELDS
            if any(c.isnumeric() for c in str(row.get(key, "")))]


def number(value):
    return not isinstance(value,bool) and isinstance(value,(int,float)) and isfinite(value)


def component(ref, path, value, role, unit, observed, *, scope="MARKET_RENDERER"):
    return dict(source_fact_ref=ref, field_path=path, exact_value=value, value_role=role,
                display_unit=unit, observation_date=observed, prose_eligible=True,
                consumer_scope=scope, formatter=FORMATTER)


def claim(kind, components, text, *, parents=(), formula=None, metadata=None):
    payload = dict(contract=CONTRACT, claim_type=kind, components=components,
                   input_fact_refs=list(parents), derivation_formula=formula,
                   formatter=FORMATTER, rendered_text=text, metadata=metadata or {})
    return {**payload, "claim_id":"market-claim:"+digest(payload)}


def _eligible(fact, completed, assessed):
    fields = fact.get("fields") or {}
    try:
        observed = date.fromisoformat(fact["as_of_date"])
        if observed > date.fromisoformat(assessed):
            return False
    except (ValueError, KeyError, TypeError):
        return False
    if (any(fields.get(k) is True for k in ("source_unavailable","renderer_only"))
            or fields.get("today_signal_eligible") is False):
        return False
    if fields.get("structured_state") in {"UNAVAILABLE","SOURCE_UNAVAILABLE","REFERENCE_LAGGING"}:
        return False
    if fact.get("fact_type") in {"market_index","market_sector","market_style","market_relative_return"}:
        return fact["as_of_date"] == completed and fields.get("quality") in {"fresh","verified"}
    return fields.get("today_signal_eligible") is True and fields.get("temporal_role") == "CURRENT_OBSERVATION"


def numeric_catalog(source, *, market, assessment_date, eligible_refs):
    """Registry permissions and selected-source/session permissions must both pass."""
    session = source.get("session") or {}
    completed = session.get("latest_completed_regular_session_date")
    date.fromisoformat(assessment_date)
    date.fromisoformat(completed)
    if (market not in {"us", "kr"} or completed > assessment_date
            or session.get("market", market) != market
            or session.get("assessment_date", assessment_date) != assessment_date):
        raise ValueError("market_numeric_session_identity_invalid")
    by_id = {f["fact_id"]:f for f in source.get("fact_catalog") or []}
    if len(by_id) != len(source.get("fact_catalog") or []):
        raise ValueError("market_numeric_duplicate_fact")
    eligible = set(eligible_refs)
    claims, suppressed = [], []
    temporal = [component("market-session", "assessment_date",assessment_date,"DATE","ISO_DATE",assessment_date),
                component("market-session", "latest_completed_regular_session_date",completed,"DATE","ISO_DATE",completed)]
    heading = ("미국" if market == "us" else "한국")+f" 시장 점검 · 판단 {assessment_date}\n완료 정규장 기준: {completed}"
    claims.append(claim("SESSION",temporal,heading,metadata={"source_session_sha256":digest(session)}))
    accepted_keys = set()
    for row in source.get("numeric_registry") or []:
        ref, path = row.get("fact_id"), row.get("field_path")
        if path not in {"fields.return_pct","fields.relative_return_pct","fields.level_pct"}:
            continue
        fact = by_id.get(ref)
        fields = (fact or {}).get("fields") or {}
        key = path.removeprefix("fields.")
        if (ref not in eligible or not fact or not _eligible(fact,completed,assessment_date)
                or row.get("registered") is not True or row.get("prose_allowed") is not True
                or row.get("scope") not in {"market","both"}
                or not number(row.get("value")) or row["value"] != fields.get(key)):
            suppressed.append(dict(ref=ref,path=path,reason="source_or_registry_permission_denied"))
            continue
        allowed_units = {"pct", "percent", "percentage_point", "pp"} if key == "relative_return_pct" else {"pct", "percent"}
        if row.get("unit") not in allowed_units:
            suppressed.append(dict(ref=ref,path=path,reason="numeric_unit_mismatch"))
            continue
        if (ref,path) in accepted_keys:
            raise ValueError("duplicate_market_numeric_registry_key")
        accepted_keys.add((ref,path))
        parents, formula, components = [], None, []
        if key == "relative_return_pct":
            parents = fields.get("source_fact_ids") or []
            inputs = [by_id.get(r) for r in parents]
            if (len(inputs)!=2 or any(not f or f["fact_id"] not in eligible or not _eligible(f,completed,assessment_date) or f['as_of_date'] != completed for f in inputs)
                    or any(not number(f["fields"].get("return_pct")) for f in inputs)
                    or not isclose(inputs[0]["fields"]["return_pct"]-inputs[1]["fields"]["return_pct"],row["value"],abs_tol=1e-9)):
                suppressed.append(dict(ref=ref,path=path,reason="derived_return_parent_binding_failed"))
                continue
            components += [component(f["fact_id"],"fields.return_pct",f["fields"]["return_pct"],"RETURN","pct",f["as_of_date"]) for f in inputs]
            formula = "parent[0].return_pct - parent[1].return_pct"
        observed = fact["as_of_date"]
        if key == "relative_return_pct" and fields.get("subject_label") and fields.get("benchmark_label"):
            label = f"{fields['benchmark_label']} 대비 {fields['subject_label']}"
            components += [component(ref, "fields."+k, fields[k], "INSTRUMENT", "TEXT", observed)
                           for k in ("subject_label", "benchmark_label")]
        elif fields.get("label") or fields.get("series_code"):
            label_path = "label" if fields.get("label") else "series_code"
            label = str(fields[label_path])
            components.append(component(ref,"fields."+label_path,label,"INSTRUMENT","TEXT",observed))
        else:
            suppressed.append(dict(ref=ref,path=path,reason="numeric_instrument_owner_missing"))
            continue
        role = "YIELD" if key=="level_pct" else "RETURN"
        unit = "pp" if key=="relative_return_pct" else "pct"
        components += [component(ref,path,row["value"],role,unit,observed),
                       component(ref,"as_of_date",observed,"DATE","ISO_DATE",observed)]
        value = f"{row['value']:.2f}%" if key=="level_pct" else f"{row['value']:+.2f}{'pp' if unit=='pp' else '%'}"
        claims.append(claim("OBSERVED_MARKET_VALUE",components,f"• {label}: {value} ({observed} 관측)",
                            parents=parents,formula=formula,metadata={"registry_row_sha256":digest(row),"fact_sha256":digest(fact)}))
    for row in source.get("night_futures") or []:
        receipt = night_market_eligibility(row,market=market,assessment_date=assessment_date,completed_session_date=completed)
        if not receipt["eligible"]:
            suppressed.append(dict(ref=row.get("fact_id"),reason="night_scope_or_session_denied",receipt=receipt))
            continue
        ref = row["fact_id"]
        fact = by_id.get(ref)
        if ref not in eligible or not fact or not night_catalog_matches(fact,row):
            raise ValueError("night_numeric_catalog_binding_mismatch")
        block = _night_timeframe_block(row,series=row["series_code"])
        if not block:
            raise ValueError("night_numeric_formatter_unavailable")
        day = row["session_date"]
        parts = [component(ref,k,row[k],role,unit,day,scope="NIGHT_FUTURES_MODULE") for k,role,unit in (
            ("series_code","INSTRUMENT","TEXT"),("contract_maturity","CONTRACT_MATURITY","YYYY_MM"),
            ("session_date","DATE","ISO_DATE"),("reference_date","DATE","ISO_DATE"),
            ("value","LEVEL","point"),("reference_price","LEVEL","point"),
            ("change_value","DELTA","point"),("change_pct","RETURN","pct"))]
        for name in ("daily","weekly","monthly"):
            frame = row["night_timeframes"][name]
            for key,role,unit in (("open","LEVEL","point"),("close","LEVEL","point"),("gap_pct","RETURN","pct"),("return_pct","RETURN","pct")):
                if frame.get(key) is not None:
                    parts.append(component(frame["fact_id"],key,frame[key],role,unit,frame["reference_date"],scope="NIGHT_FUTURES_MODULE"))
            for key,numerator,baseline in (("return_pct","close","return_baseline_close"),("gap_pct","open","gap_baseline_close")):
                if frame.get(key) is not None:
                    if not number(frame.get(numerator)) or not number(frame.get(baseline)) or frame[baseline]<=0 or not isclose((frame[numerator]/frame[baseline]-1)*100,frame[key],abs_tol=1e-6):
                        raise ValueError("night_timeframe_derived_arithmetic_invalid")
                    parts.append(component(frame['fact_id'],baseline,frame[baseline],"DERIVATION_BASELINE","point",frame['reference_date'],scope="NIGHT_FUTURES_MODULE"))
        exact = (f"한국 야간선물 · 기준 {day}\n"+block[0]+f"\n  종가 {row['value']:,.2f} · 직전 정규장({row['reference_date']}) {row['reference_price']:,.2f}"
                 +f" · 차이 {row['change_value']:+.2f}pt / {row['change_pct']:+.2f}%")
        claims.append(claim("OFFICIAL_NIGHT",parts,exact,
            parents=[row["night_source_record_id"],row["reference_source_record_id"],*block[1]],
            formula="night_close - same_contract_regular_close; change / regular_close * 100",
            metadata={"eligibility":receipt,"row_sha256":digest(row),"timeframes":row["night_timeframes"],
                      "night_source_sha256":row["night_source_payload_sha256"],"baseline_source_sha256":row["reference_source_payload_sha256"]}))
    payload = dict(contract=CONTRACT,market=market,assessment_date=assessment_date,source_sha256=digest(source),
                   eligible_refs=sorted(eligible),claims=claims,suppressed=suppressed)
    return {**payload,"catalog_sha256":digest(payload)}


def validate_catalog(catalog,source):
    try:
        expected = numeric_catalog(source,market=catalog["market"],assessment_date=catalog["assessment_date"],eligible_refs=catalog["eligible_refs"])
        return {"status":"PASS" if catalog==expected else "FAIL","errors":[] if catalog==expected else ["market_numeric_catalog_drift"]}
    except (KeyError,ValueError,TypeError):
        return {"status":"FAIL","errors":["market_numeric_source_invalid"]}


def render_typed_market_facts(catalog,source):
    if validate_catalog(catalog,source)["status"] != "PASS":
        raise ValueError("market_numeric_catalog_invalid")
    return "\n\n".join(c["rendered_text"] for c in catalog["claims"])


def final_market_numeric_audit(text,catalog,source,narrative):
    expected = render_typed_market_facts(catalog,source)+"\n\n"+narrative
    errors = []
    if text != expected:
        errors.append("final_market_numeric_render_binding_mismatch")
    if any(c.isnumeric() for c in narrative):
        errors.append("untyped_market_narrative_number")
    return dict(contract=CONTRACT,status="FAIL" if errors else "PASS",errors=errors,
                catalog_sha256=catalog["catalog_sha256"],claim_ids=[c["claim_id"] for c in catalog["claims"]],
                exact_text_sha256=sha256(text.encode()).hexdigest())
