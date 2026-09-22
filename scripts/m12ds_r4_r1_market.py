"""Add only typed official night eligibility to the unchanged R3 market owner."""
from copy import deepcopy

from app.services.official_night_market_eligibility_service import night_market_eligibility, night_catalog_matches
from scripts import m12ds_r3_market as r3

PROMPT = r3.PROMPT
market_schema = r3.market_schema
validate_market = r3.validate_market


def market_context(packet):
    context = r3.market_context(packet)
    source = packet["market_context"]
    session = source.get("session") or {}
    rows = {r["fact_id"]: r for r in source.get("night_futures") or []}
    matrix = {r["ref"]: r for r in context["parity_matrix"]}
    for fact in source.get("fact_catalog") or []:
        ref = fact["fact_id"]
        if fact.get("fact_type") != "night_futures" or ref not in rows:
            continue
        receipt = night_market_eligibility(rows[ref], market=packet["market"],
            assessment_date=packet["assessment_date"],
            completed_session_date=session.get("latest_completed_regular_session_date"))
        if not night_catalog_matches(fact, rows[ref]):
            receipt["eligible"] = False
            receipt["errors"].append("night_catalog_context_mismatch")
        matrix[ref].update(eligible=receipt["eligible"], reasons=receipt["errors"],
                           night_eligibility=receipt)
        if receipt["eligible"]:
            context["facts"][ref] = {**deepcopy(fact), "consumer_eligibility": receipt,
                                     "consumer_scopes": receipt["consumer_scopes"],
                                     "night_timeframes": deepcopy(rows[ref].get("night_timeframes"))}
        else:
            context["facts"].pop(ref, None)
    context["parity_matrix"] = [matrix[r] for r in sorted(matrix)]
    context["packet_eligible_refs"] = sorted(r for r in matrix if matrix[r]["eligible"])
    context["request_eligible_refs"] = sorted(context["facts"])
    context["suppressed_refs"] = sorted(set(matrix) - set(context["facts"]))
    context["parity_status"] = "PASS" if context["packet_eligible_refs"] == context["request_eligible_refs"] else "FAIL"
    return context
