"""Whole-source composition over existing independently replayed owners.

This does not accept a caller's PASS flag as source authority. Market components
are replayed by unified_source_composition and stock authority by its existing
stock/financial builders. No network or production registration lives here.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_composition import compose_attempt
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_stock_owner import assemble_stock
from scripts.m12dr_financial_source_authority import build_source_authority


class FullSourceRunSeed(ContractModel):
    contract: Literal["full-source-run-seed-v1"] = "full-source-run-seed-v1"
    proof_mode: Literal["AD_HOC_LIVE_SOURCE_PROOF", "SCHEDULED_ELIGIBLE_PROOF"]
    packet_scope: Literal["LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION"]
    parent_run_id: str = Field(min_length=1)
    started_at: datetime
    source_policy_sha256: str
    inventory_sha256: str
    code_config_sha256: str
    universe_sha256: str
    attempts: dict[str, str]
    attempt_hashes: dict[str, str]
    run_acquisitions: dict[str, str]
    class_c_version_set_sha256: str
    stock_cohort_hashes: dict[str, str]
    night_publication_receipt_sha256: str
    optional_denial_set_sha256: str
    skhy_issuer_bridge_sha256: str
    source_authority_contract_sha256: str

    @model_validator(mode="after")
    def explicit_bindings(self):
        if self.started_at.utcoffset() is None:
            raise ValueError("aware_proof_time_required")
        for mapping in (self.attempts, self.attempt_hashes, self.stock_cohort_hashes):
            if set(mapping) != {"us", "kr"} or not all(mapping.values()):
                raise ValueError("exact_two_market_bindings_required")
        if len(set(self.attempts.values())) != 2 or not self.run_acquisitions:
            raise ValueError("distinct_attempts_and_run_acquisition_required")
        values = self.model_dump()
        hashes = [v for k, v in values.items() if k.endswith("sha256")]
        hashes += list(self.attempt_hashes.values()) + list(self.stock_cohort_hashes.values())
        hashes += list(self.run_acquisitions.values())
        if any(not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h) for h in hashes):
            raise ValueError("non_null_exact_hash_required")
        return self

    @property
    def sha256(self):
        return digest(self.model_dump(mode="json"))


def compose_full_source(*, seed: FullSourceRunSeed, market_inputs, stock_inputs,
                        authority_inputs, version_set, optional_denials, issuer_bridge):
    """All external artifact resolvers are already owned by compose_attempt."""
    if (digest(version_set) != seed.class_c_version_set_sha256 or
            digest(optional_denials) != seed.optional_denial_set_sha256 or
            digest(issuer_bridge) != seed.skhy_issuer_bridge_sha256):
        raise ValueError("run_component_hash_mismatch")
    if issuer_bridge.get("security_valuation_transfer") or issuer_bridge.get("per_share_transfer"):
        raise ValueError("issuer_bridge_security_transfer_denied")
    expected = {t for tickers in UNIVERSE.values() for t in tickers}
    if set(stock_inputs) != expected or set(authority_inputs) != expected or set(market_inputs) != {"us", "kr"}:
        raise ValueError("whole_universe_required")
    markets, stocks, authorities = {}, {}, {}
    for market in ("us", "kr"):
        params = market_inputs[market]
        if params["attempt_id"] != seed.attempts[market] or params["started_at"] < seed.started_at:
            raise ValueError("market_attempt_generation_mismatch")
        packet = compose_attempt(**params)
        if packet["run_id"] != seed.parent_run_id or digest(packet) != seed.attempt_hashes[market]:
            raise ValueError("market_replayed_packet_mismatch")
        markets[market] = packet
        current = {}
        for ticker in UNIVERSE[market]:
            inputs = stock_inputs[ticker]
            plan = inputs["plan"]
            if plan.run_id != seed.parent_run_id or plan.frozen_at != seed.started_at:
                raise ValueError("inherited_class_a_stock_denied")
            stock = assemble_stock(**inputs)
            if stock["status"] != "PASS" or stock["market"] != market:
                raise ValueError("current_complete_stock_required:" + ticker)
            authority = authority_inputs[ticker]
            if authority["source_packet"] != stock["packet"] or authority["ticker"] != ticker:
                raise ValueError("authority_stock_packet_mismatch")
            # Existing financial/current-source authority is the only allocator.
            resolved = build_source_authority(**authority)
            if any(r.get("errors") for r in resolved["family_receipts"]):
                raise ValueError("stock_authority_unresolved:" + ticker)
            current[ticker] = stock
            authorities[ticker] = resolved
        if digest(current) != seed.stock_cohort_hashes[market]:
            raise ValueError("current_stock_cohort_hash_mismatch")
        stocks[market] = current
    graph = {"contract": "full-source-authority-graph-v1", "run_seed_sha256": seed.sha256,
        "markets": markets, "stocks": authorities, "issuer_bridge": issuer_bridge,
        "class_c": version_set, "optional_denials": optional_denials}
    output = {m: {"run_seed_sha256": seed.sha256, "market": m,
                  "market_sources": markets[m], "stocks": stocks[m],
                  "authority_graph_sha256": digest(graph)} for m in markets}
    combined = {"contract": "full-source-cohort-v1", "seed": seed.model_dump(mode="json"),
                "packets": output, "authority_graph": graph,
                "model_dispatch_qualified": False, "production_dispatch_enabled": False}
    return {"seed": seed.model_dump(mode="json"), "seed_sha256": seed.sha256,
            "packets": output, "packet_hashes": {m: digest(p) for m, p in output.items()},
            "combined": combined, "combined_sha256": digest(combined),
            "authority_graph": graph, "authority_graph_sha256": digest(graph)}
