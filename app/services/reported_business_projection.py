"""Opt-in R2 producer projection after original raw/quality replay, not a stance."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.unified_snapshot_contract import digest, encoded

CONTRACT = "reported-business-native-projection-v1"
ISSUER_CONTRACT = "reported-issuer-context-native-projection-v2"
COMPARISON_USES = ("BUSINESS_CONTEXT", "CONTEXT", "OVERALL_DIRECTION", "PASS_A_ARCHETYPE")
_BUILDER_PERMIT = object()
_KEY = secrets.token_bytes(32)
_PID = os.getpid()


class ReportedBusinessProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["reported-business-native-projection-v1", "reported-issuer-context-native-projection-v2"] = CONTRACT
    kind: Literal["COMPARISON", "QUALITY", "ISSUER_CONTEXT"]
    ticker: str
    market: Literal['kr', 'us']
    security_id: str
    issuer_id: str
    source_generation: str
    packet_id: str
    projection_at: str
    fact_id: str
    fact_sha256: str
    acquisition_sha256: str
    selected_owner_sha256: str
    projection_sha256: str
    quality_sha256: str
    source_window_sha256: str
    allowed_uses: tuple[str, ...]
    recurrence_verified: Literal[False] = False
    security_valuation_transfer: Literal[False] = False


def comparative_admission_errors(*, fact, expected, statement, expected_statement,
                                 category, as_of, source_family):
    """The existing M12DR field-local gate, shared without recursive assembly."""
    errors = []
    if not expected or fact != expected or statement != expected_statement:
        errors.append("comparative_fact_frozen_derivation_mismatch")
    if category != "earnings" or (expected and as_of != expected["as_of_date"]):
        errors.append("comparative_fact_typed_period_mismatch")
    if source_family != "unclassified":
        errors.append("existing_restrictive_family_cannot_be_rebound")
    return errors


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _stock_hash(stock):
    return digest({k: v for k, v in stock.items() if k != "reported_business_projection"})


def _signature(value):
    return hmac.new(_KEY, encoded(value), hashlib.sha256).hexdigest()


def _packet_metadata(packet):
    return {k: v for k, v in packet.items() if k != 'stocks'}


def validate_packet_binding(stock, packet):
    envelope = stock.get('reported_business_projection')
    if envelope is not None:
        _require(envelope['payload']['packet_metadata_sha256'] == digest(_packet_metadata(packet)),
                 'business_outer_packet_binding')


def issue(*, stock, packet, facts, plan, acquisition, projection, selected_owner,
          quality, bridge, financial_inputs=None, _permit=None):
    """Called only at the end of the fresh owner; public envelopes cannot issue."""
    _require(_permit is _BUILDER_PERMIT and os.getpid() == _PID, "business_backend_replay_permit_required")
    _require(not stock.get("reported_comparison_context"), "business_historical_context_not_direction")
    from app.services.selected_financial_owner import validate
    from app.services.canonical_business_quality_owner import derive_fresh
    from app.services.bounded_financial_stock_owner import reported_comparisons
    from app.services.cross_market_decision_engine_service import _compact

    source_ticker, issuer_id, contract = plan['ticker'], plan['issuer'], CONTRACT
    acquisition_sha = digest(acquisition)
    if bridge is not None:
        from app.services.bounded_financial_stock_owner import _issuer_business_facts
        _require(financial_inputs is not None and financial_inputs.get('plan') == plan
                 and financial_inputs.get('acquisition') == acquisition
                 and financial_inputs.get('issuer_business') is not None,
                 'business_issuer_original_inputs_required')
        # Replay the original raw owner and independent SEC/DART identity chain;
        # a rehashed bridge or comparison is not an issuing capability.
        expected_bridge, expected, origin = _issuer_business_facts(plan, financial_inputs['issuer_business'])
        _require(expected_bridge == bridge and origin['projection'] == projection,
                 'business_issuer_original_owner_mismatch')
        source_ticker, issuer_id, contract = bridge['underlying_ticker'], bridge['issuer_id'], ISSUER_CONTRACT
        acquisition_sha = origin['input_hashes']['acquisition']
    else:
        expected, denials = reported_comparisons(plan, projection)
        denied_metrics = {row['metric'] for row in denials}
        _require(not any(f['fields']['metric'] in denied_metrics for f in facts),
                 'business_original_comparison_replay_mismatch')
    _require(expected == facts, 'business_original_comparison_replay_mismatch')
    validate(selected_owner, projection=projection, facts=facts, bridge=bridge,
        current_financial_parent=(financial_inputs or {}).get('current_financial_parent'),
        current_purpose_intake=(financial_inputs or {}).get('current_purpose_intake'))
    _require(selected_owner["selected_acquisition_sha256"] == acquisition_sha,
             "business_acquisition_binding_mismatch")
    derived = derive_fresh(projection=projection, facts=facts, ticker=plan["ticker"],
        security_id=plan["security"]["canonical_security_id"], run_id=plan["run_id"],
        source_ticker=source_ticker, bridge=bridge)
    _require(quality == derived, "business_quality_owner_mismatch")
    catalog = {f["fact_id"]: f for f in stock["fact_catalog"]}
    entries = {}
    for fact in facts:
        _require(not comparative_admission_errors(fact=catalog.get(fact["fact_id"]), expected=fact,
            statement=_compact(catalog.get(fact["fact_id"], {}).get("fields", {})),
            expected_statement=_compact(fact["fields"]), category="earnings", as_of=fact["as_of_date"],
            source_family="unclassified"), "business_source_fact_mismatch")
        entries[fact["fact_id"]] = ((fact, "ISSUER_CONTEXT", ("CONTEXT",)) if bridge else
                                    (fact, "COMPARISON", COMPARISON_USES))
    qfact = quality["fact"]
    if qfact is not None:
        _require(catalog.get(qfact["fact_id"]) == qfact, "business_quality_fact_mismatch")
        entries[qfact["fact_id"]] = (qfact, "QUALITY", ("CONTEXT",))
    payload = dict(contract=contract, stock_sha256=_stock_hash(stock), packet_id=packet["packet_id"],
        assessment_date=packet["assessment_date"], packet_metadata_sha256=digest(_packet_metadata(packet)), entries={})
    for key, (fact, kind, uses) in entries.items():
        payload["entries"][key] = ReportedBusinessProjection(contract=contract, kind=kind, ticker=plan["ticker"], market=packet['market'],
            security_id=plan["security"]["canonical_security_id"], issuer_id=issuer_id,
            source_generation=plan["run_id"], packet_id=packet["packet_id"], projection_at=packet["generated_at"],
            fact_id=key, fact_sha256=digest(fact), acquisition_sha256=acquisition_sha,
            selected_owner_sha256=selected_owner["envelope_sha256"], projection_sha256=digest(projection),
            quality_sha256=digest(quality), allowed_uses=uses,
            source_window_sha256=digest(packet['source_time_domains']['business_window'])).model_dump(mode="json")
    return dict(payload=payload, signature=_signature(payload))


def projection_for_fact(stock, fact, *, ticker, packet_id, assessment_date, market):
    envelope = stock.get("reported_business_projection")
    if envelope is None:
        return None
    _require(isinstance(envelope, dict) and set(envelope) == {"payload", "signature"},
             "business_projection_envelope_shape")
    payload = envelope["payload"]
    _require(os.getpid() == _PID and isinstance(envelope["signature"], str)
             and hmac.compare_digest(envelope["signature"], _signature(payload)),
             "business_projection_unissued_or_changed")
    _require(payload["contract"] in {CONTRACT, ISSUER_CONTRACT} and payload["stock_sha256"] == _stock_hash(stock)
             and payload["packet_id"] == packet_id and payload["assessment_date"] == assessment_date,
             "business_projection_native_binding")
    value = payload["entries"].get(fact["fact_id"])
    if value is None:
        return None
    result = ReportedBusinessProjection.model_validate(value)
    _require(result.contract == payload['contract']
             and (result.kind != 'ISSUER_CONTEXT' or result.contract == ISSUER_CONTRACT)
             and (result.contract != ISSUER_CONTRACT or result.kind in {'ISSUER_CONTEXT', 'QUALITY'})
             and result.ticker == ticker and result.market == market and result.packet_id == packet_id and result.fact_sha256 == digest(fact)
             and result.allowed_uses == (COMPARISON_USES if result.kind == "COMPARISON" else ("CONTEXT",)),
             "business_projection_fact_or_use_mismatch")
    return result
