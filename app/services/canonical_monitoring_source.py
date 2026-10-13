"""Deterministic same-generation inputs for canonical Monitoring stages."""
from copy import deepcopy

from app.services.canonical_subject_preflight import preflight_subject
from app.services.canonical_monitoring_io import require
from app.services.canonical_market_projection import project_production_market_context
from app.services.unified_snapshot_contract import digest
from scripts.fresh_source_only_export import source_only_fresh_stock


def prepare_monitoring_source(*, whole, local_seeds, valuation_contexts, generation,
                              coverage, census, market_projector=project_production_market_context):
    prepared, stocks = {}, {}
    for market, packet in whole["packets"].items():
        for ticker, stock in packet["stocks"].items():
            authority = whole["authority_graph"]["stocks"][ticker]
            source_only_fresh_stock(stock, authority)
            readiness, data = preflight_subject(stock, authority, local_seeds[ticker],
                generation=generation, cutoff=stock["packet"]["generated_at"])
            require(readiness["status"] == "PASS" and data["mode"] == "EVIDENCE_BASED",
                    "STRICT_NATIVE_SOURCE_PREFLIGHT_GAP:" + ticker)
            prepared[ticker], stocks[ticker] = data, deepcopy(stock)
    markets = {market: market_projector(packet, whole["seed"], whole["authority_graph"],
        expected_authority_sha256=whole["authority_graph_sha256"])
        for market, packet in whole["packets"].items()}
    return dict(prepared=prepared, stocks=stocks, markets=markets,
        valuation_contexts=deepcopy(valuation_contexts),
        source_generation_id=whole["seed"]["parent_run_id"], coverage=deepcopy(coverage),
        census=deepcopy(census), whole_source_sha256=digest(whole))
