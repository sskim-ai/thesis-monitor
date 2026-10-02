"""Read declared frozen source packets, never AI outputs or implicit storage.

Historical field reachability is NOT a newly assembled unified source packet.
This audit deliberately leaves its full-packet proof false.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.packet_owned_technical_context_service import packet_owned_context_for_stock
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from scripts.m12ds_r4_r4_market import market_context


CHART_TYPES = frozenset({"price", "positioning", "chart_timeframe", "chart_transition",
    "chart_structure_atr", "chart_support_zone", "chart_resistance_zone", "chart_active_zone",
    "chart_box", "chart_major_swing", "chart_fibonacci", "chart_invalidation", "chart_state",
    "chart_price_structure_v3_zone", "chart_risk_reward_current_price", "chart_risk_reward_support_entry"})
FINANCIAL_TYPES = frozenset({"earnings", "financial_quality", "valuation", "valuation_quality",
                           "valuation_interpretation", "valuation_multiple_relation"})
MACRO_TYPES = frozenset({"market_credit_spread", "market_nominal_yield", "market_real_yield",
                        "market_volatility", "market_breakeven_inflation"})


def field_role(fact, market):
    kind = fact.get("fact_type", "")
    if kind in CHART_TYPES:
        return "stock_chart_adjusted_daily_weekly_monthly"
    if kind == "chart_price_rules":
        return "stored_thesis_and_business_metadata"
    if kind in {"security_identity", "security_basis"}:
        return "security_identity"
    if kind in FINANCIAL_TYPES:
        if "consensus_forward" in fact.get("fact_id", ""):
            return "eligible_valuation_estimates"
        return "sec_financial_fundamental_domains" if market == "us" else "opendart_financial_fundamental_domains"
    if kind in {"working_capital_inventory_relation", "working_capital_lineage_input",
                "cash_flow_ocf", "cash_flow_ppe_capex", "cash_flow_fcf_ppe"}:
        return "canonical_cashflow_working_capital"
    if kind in MACRO_TYPES:
        return "rates_credit_liquidity_risk"
    if kind == "market_oil":
        return "energy"
    return None


def audit_packet(packet, *, expected_subjects):
    subjects = [s["ticker"] for s in packet["stocks"]]
    if subjects != list(expected_subjects) or len(set(subjects)) != len(subjects):
        raise ValueError("consumed_graph_population_mismatch")
    inventory = json.loads(Path("docs/operations/UNIFIED_ACQUISITION_CLASSES.json").read_bytes())
    roles = {r["role"]: r for r in inventory["roles"]}
    rows, subject_rows = [], []
    for stock in packet["stocks"]:
        ep = build_decision_evidence_packet(packet=packet, stock=stock,
            technical_context=packet_owned_context_for_stock(packet=packet, stock=stock))
        owned = build_owned_evidence_packet(ep, stock=stock)
        facts = {f["fact_id"]: f for f in stock.get("fact_catalog", [])}
        for ref in ep.evidence:
            if not ref.source_ref or not ref.source_ref.startswith("stock.fact_catalog."):
                continue
            fid = ref.source_ref.removeprefix("stock.fact_catalog.")
            fact = facts[fid]
            family = field_role(fact, packet["market"])
            specification = roles.get(family, {})
            fields = fact.get("fields") or {}
            rows.append({"ticker": stock["ticker"], "ref_id": ref.ref_id,
                "fact_id": fid, "fact_type": fact.get("fact_type"),
                "stage": "CORE_A_B" if ref.ref_id in owned.core_refs else "TIMING_A_B",
                "field_paths": ["stock.fact_catalog." + fid + ".fields." + key for key in sorted(fields)],
                "source_role": family, "owner": specification.get("owner"),
                "provider_registry": specification.get("provider"),
                "acquisition_class": specification.get("acquisition_class"),
                "role_mandatory": specification.get("mandatory"),
                "absence_policy": "EMPTY_CORE_OBSERVED_UNION_BLOCKS" if fact.get("fact_type") == "earnings"
                    else "OWNER_GATED_OPTIONAL_FIELD",
                "source_validator": specification.get("freshness_rule"),
                "fallback": specification.get("fallback_policy"),
                "fact_sha256": digest(fact), "metadata_sha256": digest(ref.model_dump(mode="json")),
                "financial_context_present": ref.financial_context is not None,
                "mapping_status": "OWNER_FAMILY_MAPPED_NOT_SOURCE_QUALIFIED" if family else "UNMAPPED"})
        subject_rows.append({"ticker": stock["ticker"], "core_ref_count": len(owned.core_refs),
            "timing_ref_count": len(owned.timing_refs), "fact_count": len(facts),
            "evidence_sha256": ep.evidence_sha256, "historical_packet_only": True})
    market_input = market_context(packet)
    market_rows = []
    for ref, fact in market_input["facts"].items():
        kind = fact.get("fact_type") or fact.get("kind")
        family = field_role(fact, packet["market"])
        if kind in {"night_futures", "night_futures_timeframe"}:
            family = "night_and_publication_context"
        elif kind in {"market_index", "market_sector", "market_style", "market_growth_relative",
                "market_small_cap_relative", "market_sector_relative", "market_style_relative", "relative_returns"}:
            family = "us_market_prices" if packet["market"] == "us" else "kr_overnight_cross_assets"
        elif kind in {"indices", "sectors", "size_context", "breadth", "market_cross_section_index",
                "market_breadth_activity", "market_breadth_counts", "market_breadth_returns"}:
            family = "kr_local_indices_sectors_breadth" if packet["market"] == "kr" else "us_exchange_breadth"
        elif kind == "market_flows":
            family = "kr_market_investor_flows"
        elif kind == "market_fx":
            # Mapping is not source qualification. A generic verified_macro_briefing
            # label does not establish a permitted underlying FX provider.
            family = "excluded_kr_fx" if packet["market"] == "kr" else "rates_credit_liquidity_risk"
        specification = roles.get(family, {})
        market_rows.append({"stage": "MARKET", "ref_id": ref, "fact_type": kind,
            "source_role": family, "owner": specification.get("owner"),
            "provider_registry": specification.get("provider"),
            "acquisition_class": specification.get("acquisition_class"),
            "source_validator": specification.get("freshness_rule"),
            "role_mandatory": specification.get("mandatory"),
            "field_paths": sorted((fact.get("fields") or fact).keys()),
            "fact_sha256": digest(fact), "source_qualified": False})
    return {"contract": "unified-consumed-field-reachability-audit-v1", "market": packet["market"],
        "subjects": subject_rows, "rows": rows, "unmapped": [r for r in rows if r["source_role"] is None],
        "market_rows": market_rows, "market_parity": market_input["parity_matrix"],
        "market_unmapped": [r for r in market_rows if r["source_role"] is None],
        "observed_type_counts": dict(sorted(Counter(r["fact_type"] for r in rows).items())),
        "source_packet_content_sha256": digest(packet), "new_unified_packet_assembled": False,
        "all_values_source_qualified": False, "interpretation": "HISTORICAL_REACHABILITY_ONLY"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("immutable_consumption_audit_exists")
    preflight = json.loads(args.preflight.read_bytes())
    references = [r for r in preflight["archives"] if r["archive"] == str(args.archive)]
    if len(references) != 1:
        raise ValueError("declared_source_archive_required")
    manifest_path = args.archive / "report/source-snapshot-manifest.json"
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != references[0]["source_manifest_sha256"]:
        raise ValueError("historical_source_manifest_drift")
    manifest = json.loads(manifest_path.read_bytes())
    for market in ("us", "kr"):
        raw = (args.archive / f"snapshot/{market}-packet.json").read_bytes()
        source_sha = hashlib.sha256(raw).hexdigest()
        if source_sha != next(r for r in manifest["rows"] if r["market"] == market)["projected_sha256"]:
            raise ValueError("historical_source_packet_drift")
        result = audit_packet(json.loads(raw), expected_subjects=preflight["universe"][market]["eligible_subjects"])
        result["source_file_sha256"] = source_sha
        durable_json(args.output / f"{market}-consumption.json", result, exclusive=True)
        print(json.dumps({"market": market, "subjects": len(result["subjects"]),
            "consumed_rows": len(result["rows"]), "unmapped": len(result["unmapped"])}))


if __name__ == "__main__":
    main()
