"""Subordinate historical news lineage; never a fresh acquisition role."""
import base64
from copy import deepcopy
from datetime import datetime
import json

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_event_input import BoundNewsInput, make_read, replay_news
from app.services.unified_stock_owner import assemble_stock, reject_downstream, validate_assembled

CONTRACT = "persisted-source-owned-business-event-v1"
FILES = frozenset({"plan.json", "read-0001.body", "read-0001.intent.json",
                  "read-0001.response.json", "logical-receipt.json", "normalization.json"})
STATE = "PERSISTED_SOURCE_OWNED_BUSINESS_EVENT"


def replay_persisted_event(*, artifacts, hashes, security_records, ticker, market,
                           current_run_id, cutoff, current_news_denial, policy):
    if set(artifacts) != FILES or set(hashes) != FILES:
        raise ValueError("persisted_event_exact_source_set_required")
    if any(sha256_bytes(artifacts[n]) != hashes[n] for n in FILES):
        raise ValueError("persisted_event_source_hash_mismatch")
    if (set(current_news_denial) != {"role", "run_id", "acquisition_class", "denial"}
            or current_news_denial.get("acquisition_class") != "OPTIONAL_UNAVAILABLE"
            or current_news_denial.get("role") != "news_and_filing_events"
            or current_news_denial.get("run_id") != current_run_id
            or not current_news_denial.get("denial")):
        raise ValueError("persisted_event_current_acquisition_relabel_denied")
    documents = {n: json.loads(artifacts[n]) for n in FILES if n.endswith(".json")}
    reject_downstream(documents)
    plan, response, intent, norm, logical = (documents[n] for n in (
        "plan.json", "read-0001.response.json", "read-0001.intent.json",
        "normalization.json", "logical-receipt.json"))
    original = (plan["run_id"], plan["acquisition_id"], plan["provider"])
    if original[0] == current_run_id or plan["mode"] != "WIRE" or plan["max_requests"] != 1:
        raise ValueError("persisted_event_historical_source_required")
    for row in (plan, response, intent, norm):
        if ((row.get("run_id"), row.get("acquisition_id"), row.get("provider")) != original
                or row.get("role") != "news_and_filing_events"
                or row.get("acquisition_class") != "RUN_FRESH_ONCE"):
            raise ValueError("persisted_event_original_acquisition_mismatch")
    if logical != dict(HTTP_attempts=1, logical_attempts=1, owner_error=None,
                       provider=plan["provider"], subject=ticker):
        raise ValueError("persisted_event_logical_receipt_mismatch")
    if any(intent.get(k) != response.get(k) for k in
           ("ordinal", "request", "request_sha256", "requested_at")):
        raise ValueError("persisted_event_intent_response_mismatch")
    security = [r for r in security_records if r["ticker"] == ticker]
    if len(security) != 1:
        raise ValueError("persisted_event_current_identity_ambiguous")
    read = make_read(security=security[0], market=market, run_id=original[0],
                     lookback_days=norm["lookback_days"], security_records=security_records)
    if read.acquisition_id != original[1]:
        raise ValueError("persisted_event_original_subject_mismatch")
    source = BoundNewsInput(read=read, security_records=tuple(security_records),
        response_receipt_b64=base64.b64encode(artifacts["read-0001.response.json"]).decode(),
        normalization_b64=base64.b64encode(artifacts["normalization.json"]).decode(),
        raw_response_b64=base64.b64encode(artifacts["read-0001.body"]).decode())
    replayed = replay_news(source, security=security[0], business_cutoff=cutoff, policy=policy)
    # The existing source query lookback remains the temporal policy. Never
    # extend a frozen query window to make a historical article pass.
    from datetime import timedelta
    earliest = cutoff.date() - timedelta(days=read.lookback_days)
    selected = [r for r in replayed["selected"] if r["status"] == "PASS"]
    if any(not earliest <= datetime.fromisoformat(r["published_at"]).date() <= cutoff.date()
           for r in selected):
        raise ValueError("persisted_event_current_lookback_ineligible")
    receipt = {"contract": CONTRACT, "state": STATE, "ticker": ticker, "market": market,
        "original_run_id": original[0], "original_acquisition_id": original[1],
        "original_acquisition_class": "RUN_FRESH_ONCE", "provider": original[2],
        "original_source_hashes": dict(hashes), "current_run_id": current_run_id,
        "current_eligibility_cutoff": cutoff.isoformat(),
        "current_news_denial": deepcopy(current_news_denial),
        "current_class_b_claimed": False, "new_acquisition_role": False,
        "old_price_technical_or_pass_consumed": False,
        "source_strength": "linked_headline_requires_review_not_official_or_confirmed_contract",
        "selected": deepcopy(selected), "replay_sha256": digest(replayed)}
    return source, receipt


def bind_persisted_event(*, stock_inputs, event_inputs):
    plan, ticker = stock_inputs["plan"], stock_inputs["ticker"]
    if (event_inputs["current_run_id"] != plan.run_id or event_inputs["cutoff"] != plan.frozen_at
            or event_inputs["ticker"] != ticker
            or event_inputs["market"] != next(r.market for r in plan.reads if r.subject == ticker)):
        raise ValueError("persisted_event_current_stock_binding_mismatch")
    source, receipt = replay_persisted_event(**event_inputs)
    params = {**stock_inputs, "event_source": source, "business_cutoff": plan.frozen_at,
        "expected_hashes": {**stock_inputs["expected_hashes"],
            "events": digest(source.model_dump(mode="json")),
            "business_cutoff": digest(plan.frozen_at.isoformat())}}
    result = assemble_stock(**params)
    validate_assembled(result, expected_result_sha256=digest(result))
    baseline = assemble_stock(**stock_inputs)
    fields = ("price_and_positioning", "technical_context", "chart_context", "current_price_context")
    if any(result["packet"]["stocks"][0][k] != baseline["packet"]["stocks"][0][k] for k in fields):
        raise ValueError("persisted_event_changed_current_price_or_technical")
    # Keep existing canonical event facts and permissions untouched. Acquisition
    # provenance belongs to their source graph, not to the headline's economics.
    for row in result["observed_business_union"]:
        if row.get("source_kind") == "BUSINESS_EVENT":
            row.update(source_kind="PERSISTED_BUSINESS_EVENT",
                       persisted_source_receipt_sha256=digest(receipt))
    result["persisted_event_receipt"] = receipt
    return {"contract": CONTRACT, "binding_kind": STATE, "result": result,
            "fresh_price_technical_unchanged": True}


def validate_persisted_event(bound, *, stock_inputs, event_inputs):
    expected = bind_persisted_event(stock_inputs=stock_inputs, event_inputs=event_inputs)
    if expected != bound:
        raise ValueError("persisted_event_stock_source_replay_mismatch")
    return expected["result"]["status"] == "PASS"
