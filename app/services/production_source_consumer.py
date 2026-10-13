"""Bind canonical consumer proofs to the scheduler's detached source envelope.

The local owner rows describe projection completeness, not an invented upstream
provider. Actual wire provider/routes remain in the separately admitted plan and
raw receipts. Numeric facts and typed denials in Monitoring are never rewritten.
"""
from datetime import datetime
import json

from app.services.production_source_execution import (
    ProductionCollection, ProductionRoleResolution, ProductionSourceExecutionEnvelopeV1,
    ProductionSourceRole, VALIDATORS, build_production_policy,
)
from app.services.unified_snapshot_contract import Role, SourceReceipt, ValidatorReceipt, digest
from app.services.unified_stock_acquisition import UNIVERSE

OWNER = "production-canonical-consumer-proof-v1"


def consumer_policy(*, market, session, code_config_sha256):
    roles = []
    for ticker in UNIVERSE[market]:
        for purpose in ("COMPLETED_CLOSE", "TECHNICAL", "FINANCIAL", "BUSINESS", "VALUATION"):
            key = ticker + ":" + purpose
            provider, route = "canonical_local", "source-owner"
            if purpose == "COMPLETED_CLOSE":
                provider, route = "kiwoom", "usa20590" if market == "us" else "ka10081"
            elif purpose == "TECHNICAL":
                provider, route = "kiwoom", "usa06012" if market == "us" else "ka10081"
            roles.append(ProductionSourceRole(role=Role(key=key, symbol=ticker, provider=provider, route=route,
                packet_pointer="/consumer_proofs/" + key, session_date=session, basis="CANONICAL_OWNER_PROOF"),
                owner_contract=OWNER, purpose=purpose, required=True))
    roles.append(ProductionSourceRole(role=Role(key="MARKET", symbol=market, provider="canonical_local",
        route="source-owner", packet_pointer="/consumer_proofs/MARKET", session_date=session,
        basis="CANONICAL_OWNER_PROOF"), owner_contract=OWNER, purpose="MARKET", required=True))
    roles.append(ProductionSourceRole(role=Role(key="NIGHT", symbol="KOSPI200", provider="krx_night_futures",
        route="fut_bydd_trd", packet_pointer="/consumer_proofs/NIGHT", session_date=None,
        basis="SEALED_CLOCK_CURRENT_FINAL_ROW"), owner_contract=OWNER, purpose="NIGHT", required=False))
    return build_production_policy(market=market, subjects=UNIVERSE[market], source_roles=roles,
                                   code_config_sha256=code_config_sha256)


def consumer_collection(*, request, policy, whole, monitoring, seal, finished_at):
    market = request["market"]
    generation = request["attempt_id"]
    if (whole["seed"]["contract"] != "production-source-run-binding-v1"
            or whole["seed"]["attempt_id"] != generation
            or whole["seed"]["runtime_source_policy_sha256"] != request["policy_sha256"]
            or seal["generation_id"] != generation
            or set(whole["packets"]) != {market}):
        raise ValueError("production_consumer_source_generation_mismatch")
    stocks = whole["packets"][market]["stocks"]
    if set(stocks) != set(UNIVERSE[market]):
        raise ValueError("production_consumer_cohort_mismatch")
    # These are compact proof identities, not model-visible financial values.
    proofs = {}
    source_fields = {"COMPLETED_CLOSE": ("completed_session_current_price", "current_price_state", "component_binding"),
        "TECHNICAL": ("component_binding",), "FINANCIAL": ("selected_financial_owner", "financial_state"),
        "BUSINESS": ("quality_view", "event_view", "context_fact_refs"), "VALUATION": ("valuation_view",)}
    for ticker, stock in stocks.items():
        if stock["status"] != "PASS" or stock["fresh_run_id"] != generation:
            raise ValueError("production_canonical_stock_not_qualified")
        for purpose, fields in source_fields.items():
            key = ticker + ":" + purpose
            proofs[key] = dict(kind="CANONICAL_CONSUMER_PROJECTION_COMPLETE", numeric_fact=False,
                canonical_owner_contract=stock["contract"], canonical_owner_sha256=digest(stock),
                projection_sha256=digest({k: stock.get(k) for k in fields}),
                typed_denials_preserved=True, field_names=list(fields))
    proofs["MARKET"] = dict(kind="CANONICAL_CONSUMER_PROJECTION_COMPLETE", numeric_fact=False,
        authority_graph_sha256=whole["authority_graph_sha256"],
        packet_sha256=whole["packet_hashes"][market], typed_denials_preserved=True)
    from app.services.canonical_market_projection import project_optional_night
    from app.services.night_futures import night_futures_context_row
    eligible, night = project_optional_night(whole["authority_graph"]["night"],
        seed=whole["seed"], cutoff=finished_at)
    proofs["NIGHT"] = json.loads(json.dumps(night_futures_context_row(eligible[0][1]), default=str)) if eligible else None
    packet = dict(stocks=[dict(ticker=t) for t in UNIVERSE[market]], consumer_proofs=proofs,
        monitoring_input=monitoring, source_collection_seal_sha256=seal["receipt_sha256"],
        canonical_whole_source_sha256=digest(whole))
    rows, receipts = [], []
    started = datetime.fromisoformat(request["started_at"])
    for spec in policy.source_roles:
        role = spec.role
        value = proofs[role.key]
        normalized = digest(value)
        available = role.key != "NIGHT" or bool(eligible)
        state = "AVAILABLE" if available else "TYPED_UNAVAILABLE"
        owner = dict(contract=OWNER, generation_id=generation, role=role.key,
            raw_receipt_sha256=seal["receipt_sha256"], normalized_sha256=normalized,
            state=state, current_eligible_count=int(available),
            claim="CURRENT_FINAL_NIGHT_ROW" if role.key == "NIGHT" else "ONE_COMPLETE_CANONICAL_PROJECTION_NOT_ONE_AVAILABLE_NUMERIC_FACT",
            source_authority_graph_sha256=whole["authority_graph_sha256"])
        if role.key == "NIGHT":
            owner["canonical_optional_ownership"] = night
        provenance = dict(generation_id=generation, attempt_id=generation, role=role.key,
            target_session=request["target_session"], raw_receipt_sha256=seal["receipt_sha256"],
            source_plan_sha256=seal["source_plan_sha256"], owner_sha256=digest(owner))
        rows.append(ProductionRoleResolution(role_key=role.key, provider=role.provider, route=role.route,
            owner_contract=OWNER, state=state, raw_receipt_sha256=seal["receipt_sha256"],
            normalized_sha256=normalized, owner_result_sha256=digest(owner), provenance_sha256=digest(provenance),
            observed_at=finished_at, current_eligible_count=int(available), value=value,
            reason_codes=() if available else (night["state"],), owner_result=owner, provenance=provenance))
        receipts.append(SourceReceipt(role=role.key, attempt_id=generation, provider=role.provider,
            route=role.route, symbol=role.symbol, session_date=role.session_date, basis=role.basis,
            observed_at=finished_at, raw_sha256=seal["receipt_sha256"], normalized_sha256=normalized, status="PASS"))
    envelope = ProductionSourceExecutionEnvelopeV1(market=market, run_id=request["run_id"], attempt_id=generation,
        generation_id=generation, subjects=UNIVERSE[market], source_policy_sha256=request["policy_sha256"],
        code_config_sha256=policy.code_config_sha256, started_at=started, completed_at=finished_at,
        target_session=request["target_session"], required_roles=tuple(r.role.key for r in policy.source_roles if r.required),
        optional_roles=tuple(r.role.key for r in policy.source_roles if not r.required), resolutions=tuple(rows), packet_sha256=digest(packet))
    return ProductionCollection(run_id=request["run_id"], attempt_id=generation, market=market,
        started_at=started, completed_at=finished_at, packet=packet, receipts=tuple(receipts),
        validators=tuple(ValidatorReceipt(contract=v, packet_sha256=digest(packet), status="PASS") for v in VALIDATORS),
        policy_sha256=request["policy_sha256"], production_envelope=envelope)
