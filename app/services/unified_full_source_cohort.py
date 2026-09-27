"""Whole-source composition over existing independently replayed owners.

This does not accept a caller's PASS flag as source authority. Market components
are replayed by unified_source_composition and stock authority by its existing
stock/financial builders. No network or production registration lives here.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest, encoded
from app.services.unified_source_composition import compose_attempt, _resolve
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
    persisted_event_evidence_sha256: str | None = None

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
        hashes = [v for k, v in values.items() if k.endswith("sha256") and v is not None]
        hashes += list(self.attempt_hashes.values()) + list(self.stock_cohort_hashes.values())
        hashes += list(self.run_acquisitions.values())
        if any(not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h) for h in hashes):
            raise ValueError("non_null_exact_hash_required")
        return self

    @property
    def sha256(self):
        return digest(self.model_dump(mode="json"))


def compose_full_source(*, seed: FullSourceRunSeed, market_inputs, stock_inputs,
                        authority_inputs, version_set, optional_denials, issuer_bridge,
                        publication_inputs=None, night_inputs=None, composition_metadata=None):
    """All external artifact resolvers are already owned by compose_attempt."""
    if (digest(version_set) != seed.class_c_version_set_sha256 or
            digest(optional_denials) != seed.optional_denial_set_sha256 or
            digest(issuer_bridge) != seed.skhy_issuer_bridge_sha256):
        raise ValueError("run_component_hash_mismatch")
    if issuer_bridge.get("security_valuation_transfer") or issuer_bridge.get("per_share_transfer"):
        raise ValueError("issuer_bridge_security_transfer_denied")
    if publication_inputs is not None or night_inputs is not None:
        from pathlib import Path
        import json
        from app.services.unified_run_artifacts import sha256_bytes
        root = Path(__file__).resolve().parents[2]
        inventory = json.loads((root / 'docs/operations/UNIFIED_ACQUISITION_CLASSES.json').read_bytes())
        if (composition_metadata is None or composition_metadata.get('inventory') != inventory
                or len(inventory['roles']) != 24 or digest(inventory) != seed.inventory_sha256
                or digest(UNIVERSE) != seed.universe_sha256
                or digest(composition_metadata.get('allowed_providers')) != seed.source_policy_sha256):
            raise ValueError('whole_source_inventory_policy_identity_mismatch')
        code = composition_metadata.get('code_fingerprints', {})
        required = {'app/services/unified_full_source_cohort.py', 'app/services/unified_sealed_context.py',
            'app/services/persisted_business_event_owner.py', 'scripts/m12dr_financial_source_authority.py'}
        if (set(code) != required or any(sha256_bytes((root / n).read_bytes()) != h for n, h in code.items())
                or digest(code) != seed.code_config_sha256 or digest(code) != seed.source_authority_contract_sha256):
            raise ValueError('whole_source_code_contract_identity_mismatch')
    expected = {t for tickers in UNIVERSE.values() for t in tickers}
    if set(stock_inputs) != expected or set(authority_inputs) != expected or set(market_inputs) != {"us", "kr"}:
        raise ValueError("whole_universe_required")
    markets, stocks, authorities = {}, {}, {}
    persisted_events = {}
    for market in ("us", "kr"):
        params = market_inputs[market]
        native = params.get("native_aggregate")
        attempt = native["attempt_id"] if native is not None else params["attempt_id"]
        started = native["start"] if native is not None else params["started_at"]
        if attempt != seed.attempts[market] or started < seed.started_at:
            raise ValueError("market_attempt_generation_mismatch")
        if native is not None:
            role_key = {'us': 'us_market_prices', 'kr': 'kr_local_indices_sectors_breadth'}[market]
            if (native["role"].market != market or native["run_id"] != seed.parent_run_id
                    or native["role"].key != role_key):
                raise ValueError("native_market_run_or_market_mismatch")
            packet = {"run_id": native["run_id"], "attempt_id": attempt,
                "attempt_started_at": started.isoformat(), "cutoff": native["cutoff"].isoformat(),
                "component": _resolve(**native)}
        else:
            packet = compose_attempt(**params)
        if packet["run_id"] != seed.parent_run_id or digest(packet) != seed.attempt_hashes[market]:
            raise ValueError("market_replayed_packet_mismatch")
        markets[market] = packet
        current = {}
        for ticker in UNIVERSE[market]:
            inputs = stock_inputs[ticker]
            versioned = inputs.get("versioned_binding")
            persisted = inputs.get("persisted_binding")
            if versioned is not None and persisted is not None:
                raise ValueError("ambiguous_stock_business_owner")
            direct = (versioned or persisted or {}).get("stock_inputs", inputs)
            plan = direct["plan"]
            if plan.run_id != seed.parent_run_id or plan.frozen_at != seed.started_at:
                raise ValueError("inherited_class_a_stock_denied")
            if composition_metadata is not None:
                if seed.run_acquisitions.get('stock') != digest(plan.model_dump(mode='json')):
                    raise ValueError('stock_acquisition_seed_mismatch')
                for name, value in ((f'class-c/local-{market}.json', direct['local_seed']),
                                    (f'class-c/financial-{ticker}.json', direct['financial'])):
                    if sha256_bytes(encoded(value) + b'\n') != version_set.get(name):
                        raise ValueError('stock_persisted_version_seed_mismatch')
            if versioned is not None:
                from app.services.versioned_business_stock_owner import bind_current_stock
                stock = bind_current_stock(**versioned)["result"]
            elif persisted is not None:
                from app.services.persisted_business_event_owner import bind_persisted_event
                stock = bind_persisted_event(**persisted)["result"]
                persisted_events[ticker] = stock["persisted_event_receipt"]
            else:
                stock = assemble_stock(**inputs)
            if stock["status"] != "PASS" or stock["market"] != market:
                raise ValueError("current_complete_stock_required:" + ticker)
            authority = authority_inputs[ticker]
            if (authority["source_packet"] != stock["packet"] or authority["ticker"] != ticker
                    or authority["evidence_packet"] != stock["evidence_packet"]):
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
    if seed.persisted_event_evidence_sha256 is not None:
        if not persisted_events or digest(persisted_events) != seed.persisted_event_evidence_sha256:
            raise ValueError("persisted_event_seed_binding_mismatch")
    elif persisted_events:
        raise ValueError("persisted_event_seed_binding_required")
    publications, night = None, None
    if publication_inputs is not None or night_inputs is not None:
        if publication_inputs is None or night_inputs is None:
            raise ValueError("complete_publication_and_night_inputs_required")
        from app.services.unified_sealed_context import replay_night, replay_publications
        if publication_inputs["cutoff"] != seed.started_at:
            raise ValueError("publication_cutoff_seed_mismatch")
        expected_publications = {n for n in version_set
            if not any(part in n for part in ('/local-', '/financial-', '/business-versioned-'))}
        if set(publication_inputs['documents']) != expected_publications:
            raise ValueError('publication_complete_version_set_required')
        if any(digest(sorted(inputs['policy'].allowed_providers)) != seed.source_policy_sha256
               for inputs in (publication_inputs, night_inputs)):
            raise ValueError('context_policy_seed_mismatch')
        if any(version_set.get(k) != v for k, v in publication_inputs["hashes"].items()):
            raise ValueError("publication_version_seed_mismatch")
        publications = replay_publications(**publication_inputs)
        night = replay_night(**night_inputs)
        if (digest(night["original_receipts"]) != seed.night_publication_receipt_sha256
                or night["original_run_id"] != seed.parent_run_id
                or night["value_sha256"] != seed.run_acquisitions.get("night")):
            raise ValueError("night_run_seed_binding_mismatch")
    graph = {"contract": "full-source-authority-graph-v1", "run_seed_sha256": seed.sha256,
        "markets": markets, "stocks": authorities, "issuer_bridge": issuer_bridge,
        "class_c": version_set, "optional_denials": optional_denials,
        "persisted_business_events": persisted_events, "publication_context": publications, "night": night}
    if composition_metadata is not None:
        graph["source_contract"] = composition_metadata
    output = {m: {"run_seed_sha256": seed.sha256, "market": m,
                  "market_sources": markets[m], "stocks": stocks[m],
                  "authority_graph_sha256": digest(graph)} for m in markets}
    for market, packet in output.items():
        packet.update(class_c_versions=version_set, publication_context=publications,
            optional_denials=optional_denials,
            authority_subset={t: authorities[t] for t in UNIVERSE[market]},
            persisted_business_events={t: persisted_events[t] for t in UNIVERSE[market] if t in persisted_events})
        if market == "us":
            packet["night_and_publication_context"] = night
    combined = {"contract": "full-source-cohort-v1", "seed": seed.model_dump(mode="json"),
                "packets": output, "authority_graph": graph,
                "model_dispatch_qualified": False, "production_dispatch_enabled": False}
    return {"seed": seed.model_dump(mode="json"), "seed_sha256": seed.sha256,
            "packets": output, "packet_hashes": {m: digest(p) for m, p in output.items()},
            "combined": combined, "combined_sha256": digest(combined),
            "authority_graph": graph, "authority_graph_sha256": digest(graph)}
