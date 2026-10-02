"""Pure source-only stock assembly. Not registered in production dispatch.

The stock dictionary is the existing source packet, not a new AI schema.
Input replays use only private in-memory SQLite owners and supplied bytes.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import json

from app.models.financial import FinancialSnapshot
from app.models.event import Event
from app.services.ai_review_service import (
    _chart_knowledge_routing, _compact_chart_structure, build_source_fact_catalog,
    investment_framework_routing,
)
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.current_price_context_service import select_current_price_context
from app.services.direction_timing_ownership_service import build_owned_evidence_packet, stage_alias_catalogs
from app.services.financial_amount_period_service import AMOUNT_PERIOD_CONTRACT
from app.services.financial_quality_service import build_financial_quality_state
from app.services.financial_freshness_service import evaluate_financial_freshness_records
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.ohlcv_client import _chart_timeframe_context, _summarize_bars
from app.services.ohlcv_structure_service import analyze_chart_structure
from app.services.packet_owned_technical_context_service import (
    PacketOwnedTechnicalContext, build_packet_owned_technical_context,
)
from app.services.sec_business_field_quality_service import field_errors
from app.services.unified_local_seed_bridge import local_owner
from app.services.unified_persisted_owner_bridge import persisted_owner
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import SourceRole
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import ROLES, StockPlan, decode_owned_role
from app.services.unified_stock_anomaly_scope import materialize_source_components
from app.services.unified_stock_event_input import BoundNewsInput, replay_news


CONTRACT = "unified-complete-stock-owner-v1"
FORBIDDEN = frozenset({"previous_assessment", "deterministic_assessment", "monitoring_state",
    "rendered_message", "rendered_prose", "model_output", "ai_verdict", "overall_direction",
    "directional_balance", "accepted_decision_id", "thesisassessment", "notificationdelivery",
    "prior_accepted", "latest_assessment", "runtime_specificity_plan", "industry_reasoning_plan",
    "state_grounding_requirements", "buy_drivers", "sell_drivers", "balance_summary",
    "archetype_rationale", "tier_rationale", "decisive_reason", "holder_axis", "new_buyer_axis",
    "overall_axis", "model_summary", "model_recommendation", "accepted_plan",
    "frozen_pass_a_classification", "previous_decision", "ai_entry_recommendation",
    "buy_sell_balance", "overall_maturity", "driver_maturity", "model_scores", "model_score",
    "ai_score", "decision_label", "recommendation"})


def reject_downstream(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN or key.lower().startswith(("ai_verdict", "model_recommendation")):
                raise ValueError("downstream_output_forbidden:" + key)
            reject_downstream(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_downstream(child)
    elif isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            decoded = json.loads(value)
        except ValueError:
            return
        reject_downstream(decoded)


def _exact(document, expected):
    if digest(document) != expected:
        raise ValueError("frozen_input_hash_mismatch")
    reject_downstream(document)


def _local(document, *, market, session_key, cutoff, ticker, policy):
    for role in document["roles"]:
        projection = local_owner(role=role, market=market, session_key=session_key,
            policy=policy).project_and_validate(json.dumps(document).encode(), cutoff)
        if not projection.eligible:
            raise ValueError("mandatory_local_seed_ineligible:" + role)
    tables = {}
    for component in document["roles"].values():
        for record in component["records"]:
            if record["record"].get("ticker") == ticker:
                if record["table"] in tables:
                    raise ValueError("duplicate_subject_local_record")
                tables[record["table"]] = record["record"]
    for table in ("watchlistitem", "securitymaster", "investmentthesis"):
        if table not in tables:
            raise ValueError("mandatory_local_record_missing:" + table)
    return tables


def _financial(document, *, ticker, market, cutoff, policy):
    role = SourceRole.model_validate(document["role"])
    if role.symbol != ticker or role.market != market:
        raise ValueError("financial_subject_mismatch")
    replay = persisted_owner(role=role, family=document["family"], policy=policy).project_and_validate(
        json.dumps(document).encode(), cutoff)
    selected = replay.value if replay.eligible else []
    original = document["projection"]
    if digest(original["values"]) != original["normalized_sha256"]:
        raise ValueError("financial_projection_value_hash_mismatch")
    records = {r["record_id"]: r["record"] for r in original["records"]
        if r["table"] == "financialsnapshot"}
    # Reuse the exact detached-copy revalidation used by the Class-C selector.
    # Stored historical quality annotations are not the selected owner's verdict.
    _, _, validated = evaluate_financial_freshness_records(
        [Event.model_validate(r["record"]) for r in original["records"] if r["table"] == "event"],
        [FinancialSnapshot.model_validate(r) for r in records.values()], as_of=cutoff.date())
    validated_by_id = {str(r.id): r for r in validated}
    # Only reported revenue/operating income have direct fact-catalog owners.
    # No new margin, growth, per-share or valuation formula is introduced.
    fields, sources, bindings = {}, {}, {}
    selected_rows = []
    for item in selected:
        if item["metric"] not in {"revenue", "operating_income"}:
            continue
        raw = records[item["record_id"]]
        if raw["ticker"] != ticker or digest(raw) != item["record_sha256"]:
            raise ValueError("financial_record_binding_mismatch")
        row = validated_by_id[item["record_id"]]
        logical = "latest_" + item["metric"]
        metadata = {"period": item["period_end"], "period_type": row.period_type,
            "source_type": row.snapshot_type, "provider": row.provider,
            "filing_date": item["filing_date"], "hard_errors": field_errors(row, logical),
            "soft_outliers": json.loads(row.financial_soft_outliers),
            "fiscal_year": row.fiscal_year, "period_scope": row.period_scope, "is_cumulative": row.is_cumulative,
            "financial_statement_basis_warning": row.financial_statement_basis_warning,
            "period_mapping_validation_failed": row.period_mapping_validation_failed,
            "margin_quality_review": row.margin_quality_review,
            "lineage_verified": True}
        if row.provider == "opendart":
            metadata.update(item["lineage"])
        fields[logical] = item["value"]
        sources[logical] = [metadata]
        bindings[logical] = item
        selected_rows.append(row)
    if not fields:
        return {}, {}, {"status": "UNAVAILABLE", "denials": original["denials"],
            "owner": "project_reported_financial", "version": original["version"]}
    tuples = {(r.financial_period_end, r.currency, r.period_type, r.provider,
               r.source_filing_id) for r in selected_rows}
    if len(tuples) != 1:
        raise ValueError("financial_selected_tuple_mismatch")
    row = selected_rows[0]
    metadata = {**next(iter(sources.values()))[0], "direct_field_sources": sources,
                "financial_amount_period_contract": AMOUNT_PERIOD_CONTRACT}
    valuation = {**fields, "financial_currency": row.currency,
        "latest_earnings_period": str(row.financial_period_end),
        "latest_earnings_period_type": row.period_type,
        "latest_earnings_fiscal_year": row.fiscal_year,
        "latest_earnings_period_scope": row.period_scope,
        "latest_earnings_is_cumulative": row.is_cumulative,
        "earnings_context_is_preliminary": row.snapshot_type == "preliminary_earnings"}
    valuation["financial_quality"] = build_financial_quality_state(valuation, source_metadata=metadata)
    return valuation, bindings, {"status": "SELECTED_OWNER_REPLAYED",
        "owner": "project_reported_financial", "version": original["version"],
        "selected_metrics": sorted(bindings), "denials": original["denials"]}


def _technical(components, roles, *, ticker, market, cutoff, observed_at):
    if "completed_close_projection_sha256" in components:
        from app.services.kiwoom_completed_close_owner import historical_only_roles
        roles = historical_only_roles(roles, cutoff=cutoff)
    if "completed_session_bar_set" in components:
        from app.services.eligible_completed_session_bars import eligible_completed_roles
        roles, receipt = eligible_completed_roles(roles, ticker=ticker, market=market,
            cutoff=cutoff, observed_at=observed_at)
        if receipt != components["completed_session_bar_set"]:
            raise ValueError("completed_bar_set_receipt_mismatch")
    periods = {}
    for tf in ("daily", "weekly", "monthly"):
        states = {r["date"]: r["bar_state"] for r in components["analysis_view_finality"][tf]["rows"]}
        periods[tf] = [{**r, "bar_state": states[str(r["date"])[:10]]}
            if str(r["date"])[:10] in states else dict(r) for r in roles["adjusted_" + tf]]
    context = build_packet_owned_technical_context(ticker=ticker, market=market, session="closed",
        as_of=observed_at, periods=periods, cutoff=cutoff, expected_daily_completed=str(cutoff),
        source="sealed_r2b0_kiwoom", source_version="one-shot-stock-source-acquisition-v1")
    if "completed_session_bar_set" in components and digest(periods) != components["technical_input_sha256"]:
        raise ValueError("completed_technical_input_mismatch")
    from app.services.current_effective_technical import project
    historical = components["historical_technical_inventory"]
    if (historical["current_authority"] is not False or historical["context_id"] != context.technical_context_id
            or historical["features_sha256"] != digest(context.features.model_dump(mode="json"))
            or historical["facts"] != {tf: [f.model_dump(mode="json") for f in getattr(context.features, tf).facts] for tf in periods}):
        raise ValueError("historical_technical_inventory_mismatch")
    context = project(context, components["features"])
    if context.technical_context_id != components["technical_context_id"]:
        raise ValueError("technical_component_identity_mismatch")
    for tf in periods:
        if [f.model_dump(mode="json") for f in getattr(context.features, tf).facts] != components["features"][tf]["facts"]:
            raise ValueError("technical_component_fact_parity_mismatch:" + tf)
    return context, periods


def component_binding(components, price_projection=None):
    result = []
    for role, rows in components["role_consumer_matrix"].items():
        for c in rows:
            feature = "owner_dependency" in c
            requirement = "MANDATORY" if c["requirement"] == "MANDATORY_CURRENT_PRICE" else "OPTIONAL"
            if requirement == "MANDATORY" and price_projection is not None:
                eligible = price_projection.availability == "AVAILABLE"
                result.append(dict(role=role, consumer=c["consumer"],
                    packet_path="price_and_positioning.price.current_price", requirement=requirement,
                    Core=False, A=False, B=True, renderer_requires=True, eligible=eligible,
                    selected_value_in_packet=eligible, behavior="INCLUDE" if eligible else "COMPLETED_SESSION_PRICE_UNAVAILABLE",
                    owner=price_projection.contract, projection_sha256=price_projection.projection_sha256,
                    dependency_span=[price_projection.target_session], anomalies=price_projection.target_integrity["issues"]))
                continue
            path = ("technical_context.features." + role.removeprefix("adjusted_") + ".facts:" + c["consumer"]
                if feature else "price_and_positioning.price.current_price" if requirement == "MANDATORY"
                else "chart_context:" + role + ":" + c["consumer"])
            source_only = c["consumer"] in {"v3_long_cycle", "valuation_weekly_close_history"}
            if source_only:
                path = ("valuation" if c["consumer"] == "valuation_weekly_close_history"
                        else "chart_context.structure.price_structure_v3")
            result.append({"role": role, "consumer": c["consumer"], "packet_path": path,
                "requirement": requirement, "Core": False, "A": False, "B": True,
                "renderer_requires": requirement == "MANDATORY", "eligible": c["eligible"],
                "selected_value_in_packet": c["eligible"] and not source_only,
                "behavior": "SOURCE_AVAILABLE_CONSUMER_NOT_MATERIALIZED" if c["eligible"] and source_only
                    else "INCLUDE" if c["eligible"] else
                    "MANDATORY_FIELD_UNAVAILABLE_SOURCE_ANOMALY" if requirement == "MANDATORY" else
                    "UNAVAILABLE_SOURCE_ANOMALY_RELEVANT" if c["reason"] == "SOURCE_ANOMALY_RELEVANT_TO_CONSUMER"
                    else "UNAVAILABLE_" + c["reason"],
                "owner": c["owner"], "dependency_span": c["dependency_span"], "anomalies": c["anomalies"]})
    return result


def assemble_stock(*, plan: StockPlan, ticker: str, receipts: dict, artifacts: dict[str, bytes],
                   local_seed: dict, financial: dict | None, components: dict,
                   expected_hashes: dict, policy: UnifiedSourcePolicy,
                   event_source: BoundNewsInput | None = None,
                   business_cutoff: datetime | None = None,
                   financial_tuple_denial: bool = False,
                   fresh_financial_pending: bool = False,
                   completed_close_source: dict | None = None) -> dict:
    """No path lookup, providers, prior assessments or downstream model output."""
    for key, value in (("local", local_seed), ("financial", financial), ("components", components),
                       ("receipts", receipts), ("plan", plan.model_dump(mode="json"))):
        _exact(value, expected_hashes[key])
    event_binding = None
    if fresh_financial_pending and (financial is not None or event_source is not None):
        raise ValueError('fresh_technical_baseline_must_not_import_financial_or_event_state')
    if (event_source is None) != (business_cutoff is None):
        raise ValueError("event_source_and_business_cutoff_required_together")
    if event_source is not None:
        if business_cutoff.utcoffset() is None or business_cutoff < plan.frozen_at:
            raise ValueError("business_cutoff_before_sealed_price_or_naive")
        _exact(event_source.model_dump(mode="json"), expected_hashes["events"])
        _exact(business_cutoff.isoformat(), expected_hashes["business_cutoff"])
    reads = [r for r in plan.reads if r.subject == ticker]
    if len(reads) != 4 or set(receipts) != set(ROLES):
        raise ValueError("exact_four_subject_roles_required")
    market, session_key = reads[0].market, reads[0].latest_completed_session
    if any((r.market, r.latest_completed_session, r.canonical_security_id) !=
           (market, session_key, reads[0].canonical_security_id) for r in reads):
        raise ValueError("stock_role_session_identity_mismatch")

    def artifact(path, expected):
        raw = artifacts[path]
        if sha256_bytes(raw) != expected:
            raise ValueError("stock_artifact_hash_mismatch")
        return raw

    roles = {r.role: decode_owned_role(plan, r, receipts[r.role], artifact) for r in reads}
    cutoff = date.fromisoformat(session_key)
    params = dict(ticker=ticker, market=market, cutoff=cutoff, observed_at=plan.frozen_at.isoformat(), roles=roles)
    tables = _local(local_seed, market=market, session_key=session_key, cutoff=plan.frozen_at,
        ticker=ticker, policy=policy)
    security, watch, thesis = (tables[k] for k in ("securitymaster", "watchlistitem", "investmentthesis"))
    if security["canonical_security_id"] != reads[0].canonical_security_id:
        raise ValueError("stock_local_security_receipt_mismatch")
    price_projection = None
    if completed_close_source is not None:
        from app.services.kiwoom_completed_close_owner import project, materialize
        if not fresh_financial_pending or market != "us":
            raise ValueError("completed_close_requires_fresh_us_owner")
        _exact(completed_close_source, expected_hashes["completed_close_source"])
        price_projection = project(source=completed_close_source, plan=plan,
            read=next(r for r in reads if r.role == "adjusted_daily"), security=security, artifact_reader=artifact)
        replayed_components = materialize(projection=price_projection, **params)
    else:
        if "completed_close_projection_sha256" in components:
            raise ValueError("completed_close_source_required")
        replayed_components = materialize_source_components(**params,
            completed_session="completed_session_bar_set" in components)
    if digest(replayed_components) != digest(components):
        raise ValueError("sealed_component_replay_mismatch")
    if fresh_financial_pending and price_projection is None:
        from app.services.completed_session_current_price import project_completed_price
        daily = next(r for r in reads if r.role == "adjusted_daily")
        price_projection = project_completed_price(plan=plan, read=daily, receipt=receipts[daily.role],
            artifact_reader=artifact, security=security, currency="USD" if market == "us" else "KRW")
    binding = component_binding(components, price_projection)
    missing = [r["packet_path"] for r in binding if r["requirement"] == "MANDATORY" and not r["eligible"]]
    if event_source is not None:
        if event_source.read.market != market:
            raise ValueError("event_stock_market_mismatch")
        event_binding = replay_news(event_source, security=security, business_cutoff=business_cutoff, policy=policy)
    try:
        if fresh_financial_pending:
            valuation, financial_refs = {}, {}
            financial_state = {'status': 'UNAVAILABLE', 'owner': 'fresh_financial_pending',
                               'run_id': plan.run_id}
        else:
            valuation, financial_refs, financial_state = _financial(financial, ticker=ticker, market=market,
                cutoff=plan.frozen_at, policy=policy)
    except ValueError as exc:
        if (event_source is None and not financial_tuple_denial) or str(exc) != "financial_selected_tuple_mismatch":
            raise
        valuation, financial_refs = {}, {}
        financial_state = {"status": "DENIED", "denials": [str(exc)],
            "owner": "project_reported_financial", "version": financial["projection"]["version"]}
    technical, periods = _technical(components, roles, **{k: params[k] for k in ("ticker", "market", "cutoff", "observed_at")})
    currency = technical.currency
    decision = {"current_price": components["current_price"], "currency": currency,
        "price_as_of": session_key, "price_basis": "adjusted_close"}
    if price_projection is not None:
        decision.update(current_price=price_projection.current_price, currency=price_projection.currency,
                        price_as_of=price_projection.price_as_of, price_basis=price_projection.adjustment_basis)
    timeframes = {}
    for tf in periods:
        consumers = {c["consumer"]: c for c in components["role_consumer_matrix"]["adjusted_" + tf]}
        # Native embedded indicators are not canonical dependency-owned features.
        rows = [{k: r[k] for k in ("date", "open", "high", "low", "close", "volume", "value") if k in r}
                for r in periods[tf]]
        if not consumers["latest_candle_volume_value"]["eligible"]:
            timeframes[tf] = {"quality": "unavailable"}
            continue
        summary = _summarize_bars(len(rows), rows) if consumers["period_range_position"]["eligible"] else _summarize_bars(1, rows[-1:])
        value = _chart_timeframe_context(tf, rows[-1:], summary).model_dump(mode="json")
        if not consumers["period_range_position"]["eligible"]:
            value["range_position_pct"] = None
            value["period_return_pct"] = None
        timeframes[tf] = value
    structure_ready = all(c["eligible"] for rows in components["role_consumer_matrix"].values() for c in rows
        if c["consumer"] in {"legacy_local_pivots", "legacy_major_swings_atr", "legacy_boxes"})
    structure = analyze_chart_structure(periods, timeframe_contexts=timeframes) if structure_ready else {}
    chart = {"available": False if completed_close_source is not None else bool(timeframes),
        "quality": "unavailable" if completed_close_source is not None else "fresh", "source": "kiwoom",
        "timeframes": timeframes, "structure": _compact_chart_structure(structure) if structure else {},
        "stored_price_rules": json.loads(thesis["price_rules"])}
    event_evidence = event_binding["evidence"] if event_binding else []
    at = business_cutoff or plan.frozen_at
    facts = build_source_fact_catalog(assessment_date=at.date(), capital_actions=[], evidence=event_evidence,
        valuation=valuation, price={"price": decision}, chart=chart, monitoring_state={})
    # Empty auto-generated earnings envelopes are not observed evidence.
    facts = [f for f in facts if f["fact_type"] != "earnings" or financial_refs]
    company = tables.get("company", {})
    stock = {"ticker": ticker, "company_name": watch["company_name"], "thesis_version": thesis["version"],
        "industry": company.get("industry"), "sector": company.get("sector"),
        "business_model": company.get("business_units"), "revenue_sources": company.get("revenue_sources"),
        "thesis": {"core_thesis": thesis["core_thesis"], "time_horizon": thesis.get("time_horizon"),
            **{k: json.loads(thesis[k]) for k in ("thesis_drivers", "validation_metrics", "strengthen_signals",
                "weaken_signals", "invalidation_signals", "market_expectations", "valuation_framework", "macro_exposures")}},
        "evidence": event_evidence, "valuation": valuation, "price_and_positioning": {"price": decision},
        "chart_context": chart, "fact_catalog": facts, "numeric_registry": build_numeric_registry(facts),
        "current_price_context": select_current_price_context({"decision": decision}),
        "technical_context": technical.model_dump(mode="json"),
        "data_cautions": sorted({r["behavior"] + ":" + r["role"] + ":" + r["consumer"]
            for r in binding if not r["eligible"]} | {"OPTIONAL_ESTIMATE_UNAVAILABLE", "OPTIONAL_CF_WC_UNAVAILABLE",
                "QUERY_TIME_SOURCE_NOT_OFFICIAL_REGULAR_CLOSE_AUTHORITY"})}
    if completed_close_source is not None:
        stock["data_cautions"].remove("QUERY_TIME_SOURCE_NOT_OFFICIAL_REGULAR_CLOSE_AUTHORITY")
        stock["data_cautions"].append("COMPLETED_REGULAR_SESSION_CLOSE_NOT_REALTIME")
    stock["knowledge_routing"] = investment_framework_routing(stock["industry"], stock["business_model"],
        thesis["core_thesis"], sector=stock["sector"], revenue_sources=stock["revenue_sources"],
        has_earnings=bool(financial_refs), has_price_context=bool(decision["current_price"]),
        preliminary_earnings=bool(valuation.get("earnings_context_is_preliminary")),
        has_adr_basis_risk=security.get("security_type") in {"adr", "gdr"})
    stock["chart_knowledge_routing"] = _chart_knowledge_routing(chart)
    packet = {"packet_id": plan.run_id + ":" + market, "market": market,
        "assessment_date": at.date().isoformat(), "generated_at": at.isoformat(),
        "schema_version": 4, "stocks": [stock]}
    if event_source is not None:
        packet["source_time_domains"] = {"price_source_frozen_at": plan.frozen_at.isoformat(),
            "price_session": session_key, "business_cutoff": business_cutoff.isoformat(),
            "financial_projection_cutoff": financial["projection"]["cutoff"],
            "scope": "MIXED_TIME_MATERIALIZER_PROOF_NOT_HISTORICAL_PRODUCTION_DECISION"}
    # Consume the serialized packet through its real loader. Producer-only
    # Decimal instances must not grant permissions lost at the JSON boundary.
    serialized_technical = PacketOwnedTechnicalContext.model_validate(stock["technical_context"])
    evidence = build_decision_evidence_packet(packet=packet, stock=stock, technical_context=serialized_technical)
    from scripts.m12dk_current_source_authority import earnings_lineage_receipt
    business = [earnings_lineage_receipt(ref.model_dump(mode="json"), stock, packet)
        for ref in evidence.evidence if ref.source_ref and ref.source_ref.startswith("stock.fact_catalog.earnings:")]
    if event_source is not None:
        financial_state = {**financial_state, "earnings_qualification": deepcopy(business)}
        denied = [r for r in business if r["status"] != "PASS"]
        if denied:
            financial_state.update(status="DENIED", denial_reason="existing_earnings_owner_rejected")
            facts[:] = [f for f in facts if f["fact_type"] not in {"earnings", "financial_quality"}]
            stock["valuation"] = {}
            stock["numeric_registry"] = build_numeric_registry(facts)
            evidence = build_decision_evidence_packet(packet=packet, stock=stock, technical_context=serialized_technical)
        if financial_state["status"] in {"DENIED", "UNAVAILABLE"}:
            stock["data_cautions"].append("REPORTED_FINANCIAL_UNAVAILABLE_OR_DENIED_SEE_FINANCIAL_STATE")
        selected = {r["event_fingerprint"]: r for r in event_binding["selected"] if r["status"] == "PASS"}
        for ref in evidence.evidence:
            if not ref.source_ref.startswith("stock.fact_catalog.event:"):
                continue
            fp = ref.source_ref.removeprefix("stock.fact_catalog.event:").split(":", 1)[0]
            if fp not in selected:
                raise ValueError("event_typed_ref_not_selected_by_owner")
            business.append({"status": "PASS", "source_kind": "BUSINESS_EVENT", "ref_id": ref.ref_id,
                "ticker": ticker, "event_fingerprint": fp, "source_receipt_sha256": event_binding["source_receipt_sha256"],
                "raw_sha256": event_binding["raw_sha256"], "event": selected[fp]})
        # Cautions participate in the typed evidence identity too.
        evidence = build_decision_evidence_packet(packet=packet, stock=stock, technical_context=serialized_technical)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    stage_alias_catalogs(owned)
    usable = [r for r in business if r["status"] == "PASS"]
    if not usable:
        missing.append("observed_business_union:eligible_reported_financial_or_event")
    registry_errors = [r for r in stock["numeric_registry"] if not r["registered"]]
    if registry_errors:
        missing.append("numeric_registry:unregistered_fields")
    graph = {f["fact_id"]: {"ticker": ticker, "fact_sha256": digest(f),
        "source": "business_events" if f["fact_id"].startswith("event:") else
            "selected_financial" if f["fact_type"] in {"earnings", "financial_quality"}
            else "local_seed" if f["fact_type"] in {"security_identity", "security_basis", "chart_price_rules"}
            else "sealed_stock_roles",
        "input_sha256": expected_hashes["events"] if f["fact_id"].startswith("event:") else
            expected_hashes["financial"] if f["fact_type"] in {"earnings", "financial_quality"}
            else expected_hashes["local"] if f["fact_type"] in {"security_identity", "security_basis", "chart_price_rules"}
            else expected_hashes["receipts"]} for f in facts}
    for node in graph.values():
        if node["source"] == "business_events":
            node["event_binding"] = deepcopy(event_binding)
        elif node["source"] == "selected_financial":
            node["records"] = deepcopy(financial_refs)
        elif node["source"] == "local_seed":
            node["records"] = {table: {"record_id": str(row["id"]), "record_sha256": digest(row)}
                for table, row in tables.items()}
        else:
            node["roles"] = {role: {"receipt_sha256": digest(receipt),
                "normalized_sha256": receipt["normalized_sha256"],
                "raw_sha256": [page["source_sha256"] for page in receipt["pages"]]}
                for role, receipt in receipts.items()}
            node["component_projection_sha256"] = expected_hashes["components"]
            if price_projection is not None:
                node["completed_price_projection_sha256"] = price_projection.projection_sha256
    numeric_graph = [{"fact_id": r["fact_id"], "field_path": r["field_path"],
        "registry_entry_sha256": digest(r), "source_node_sha256": digest(graph[r["fact_id"]])}
        for r in stock["numeric_registry"]]
    evidence_graph = {r.ref_id: {"ticker": ticker, "source_ref": r.source_ref,
        "evidence_sha256": digest(r.model_dump(mode="json")),
        "input_hashes": deepcopy(expected_hashes),
        "technical_context_id": technical.technical_context_id}
        for r in evidence.evidence}
    return {"contract": CONTRACT, "ticker": ticker, "market": market,
        "status": "PASS" if not missing else "BLOCKED", "mandatory_missing": missing,
        "packet": packet, "packet_sha256": digest(packet) if not missing else None,
        "diagnostic_packet_sha256": digest(packet), "evidence_packet": evidence.model_dump(mode="json"),
        "ownership": owned.model_dump(mode="json"), "component_binding": binding,
        "source_graph": graph, "financial_bindings": financial_refs, "financial_state": financial_state,
        "numeric_registry_graph": numeric_graph, "evidence_reference_graph": evidence_graph,
        "observed_business_union": business, "observed_business_cardinality": len(usable),
        "numeric_registry_unregistered": registry_errors, "input_hashes": deepcopy(expected_hashes),
        "complete_source_adapter_qualified": False,
        **({"completed_session_current_price": price_projection.model_dump(mode="json")} if price_projection else {}),
        **({"event_binding": event_binding, "event_source": event_source.model_dump(mode="json"),
            "business_cutoff": business_cutoff.isoformat(), "event_policy": sorted(policy.allowed_providers)}
           if event_source is not None else {})}


def validate_assembled(result, *, expected_result_sha256, versioned_business_inputs=None):
    """Detect post-owner mutation without trusting packet or PASS labels."""
    if digest(result) != expected_result_sha256:
        raise ValueError("assembled_result_hash_mismatch")
    stock = result["packet"]["stocks"][0]
    if "completed_session_current_price" in result:
        from app.services.completed_session_current_price import CompletedSessionCurrentPriceProjection
        from app.services.kiwoom_completed_close_owner import KiwoomCompletedClose, CONTRACT as CLOSE_V2
        projection_type = (KiwoomCompletedClose if result["completed_session_current_price"]["contract"] == CLOSE_V2
            else CompletedSessionCurrentPriceProjection)
        price = projection_type.model_validate(result["completed_session_current_price"])
        if projection_type is KiwoomCompletedClose and (
                price.supplement_source_sha256 != result["input_hashes"].get("completed_close_source")):
            raise ValueError("completed_close_supplement_binding_mismatch")
        context = stock["current_price_context"]
        decision = stock["price_and_positioning"]["price"]
        if (price.ticker != stock["ticker"] or price.market != result["market"]
                or price.source_plan_sha256 != result["input_hashes"]["plan"]
                or (context["current_price"], context["as_of_date"], context["currency"], context["price_basis"]) !=
                    (price.current_price, price.price_as_of, price.currency, price.adjustment_basis)
                or (decision["current_price"], decision["price_as_of"]) != (price.current_price, price.price_as_of)):
            raise ValueError("completed_price_packet_binding_mismatch")
    versioned = None
    if 'versioned_business' in result['input_hashes']:
        from app.services.versioned_business_stock_owner import replay_version
        if versioned_business_inputs is None:
            raise ValueError('versioned_business_source_replay_required')
        versioned = replay_version(**versioned_business_inputs)
        if (versioned['ticker'] != stock['ticker']
                or versioned['current_cutoff'] != result['packet']['generated_at']
                or versioned['version_sha256'] != result['input_hashes']['versioned_business']
                or [f for f in stock['fact_catalog'] if f.get('fact_type') == 'earnings_comparison'] != versioned['facts']):
            raise ValueError('versioned_business_source_binding_mismatch')
    if "event_source" in result:
        event_source = BoundNewsInput.model_validate(result["event_source"])
        if event_source.read.market != result["market"] or event_source.read.subject != stock["ticker"]:
            raise ValueError("event_stock_market_or_subject_mismatch")
        cutoff = datetime.fromisoformat(result["business_cutoff"])
        if digest(result["event_source"]) != result["input_hashes"]["events"] or digest(cutoff.isoformat()) != result["input_hashes"]["business_cutoff"]:
            raise ValueError("event_input_hash_mismatch")
        replayed = replay_news(event_source, security=event_source.read.security,
            business_cutoff=cutoff, policy=UnifiedSourcePolicy(frozenset(result["event_policy"])))
        if replayed != result["event_binding"] or stock["evidence"] != replayed["evidence"]:
            raise ValueError("event_source_replay_mismatch")
        from app.services.canonical_fact_service import canonical_event_fact
        expected_events = [canonical_event_fact(item) for item in replayed["evidence"]]
        if [f for f in stock["fact_catalog"] if f["fact_id"].startswith("event:")] != expected_events:
            raise ValueError("event_catalog_not_owned_by_source")
        domains = result["packet"].get("source_time_domains", {})
        if domains.get("business_cutoff") != cutoff.isoformat() or result["packet"]["generated_at"] != cutoff.isoformat():
            raise ValueError("business_time_domain_mismatch")
    reject_downstream(stock)
    registry_builder = build_numeric_registry
    if versioned is not None:
        from app.services.bounded_financial_stock_owner import build_shadow_numeric_registry
        registry_builder = build_shadow_numeric_registry
    if stock["ticker"] != result["ticker"] or stock["numeric_registry"] != registry_builder(stock["fact_catalog"]):
        raise ValueError("numeric_registry_or_subject_mismatch")
    if digest(result["packet"]) != result["diagnostic_packet_sha256"]:
        raise ValueError("packet_hash_mismatch")
    if result["status"] == "PASS" and result["packet_sha256"] != digest(result["packet"]):
        raise ValueError("qualified_packet_hash_mismatch")
    technical = PacketOwnedTechnicalContext.model_validate(stock["technical_context"])
    if technical.ticker != stock["ticker"] or technical.market != result["market"]:
        raise ValueError("technical_subject_mismatch")
    evidence = build_decision_evidence_packet(packet=result["packet"], stock=stock, technical_context=technical)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    if evidence.model_dump(mode="json") != result["evidence_packet"] or owned.model_dump(mode="json") != result["ownership"]:
        raise ValueError("typed_evidence_binding_mismatch")
    if set(result["evidence_reference_graph"]) != {r.ref_id for r in evidence.evidence}:
        raise ValueError("evidence_graph_coverage_mismatch")
    for ref in evidence.evidence:
        node = result["evidence_reference_graph"][ref.ref_id]
        if (node["ticker"] != stock["ticker"] or node["source_ref"] != ref.source_ref
                or node["evidence_sha256"] != digest(ref.model_dump(mode="json"))
                or node["input_hashes"] != result["input_hashes"]
                or node["technical_context_id"] != technical.technical_context_id):
            raise ValueError("evidence_reference_mismatch")
    if set(result["source_graph"]) != {f["fact_id"] for f in stock["fact_catalog"]}:
        raise ValueError("source_graph_coverage_mismatch")
    for fact in stock["fact_catalog"]:
        binding = result["source_graph"][fact["fact_id"]]
        if binding["ticker"] != stock["ticker"] or binding["fact_sha256"] != digest(fact):
            raise ValueError("source_reference_mismatch")
        key = {"selected_financial": "financial", "local_seed": "local", "sealed_stock_roles": "receipts",
               "business_events": "events", "versioned_reported_business": "versioned_business"}[binding["source"]]
        if binding["input_sha256"] != result["input_hashes"][key]:
            raise ValueError("source_input_hash_mismatch")
        if binding['source'] == 'versioned_reported_business':
            if (versioned is None or binding['original_source_artifact_sha256'] != versioned['original_source_artifact_sha256']
                    or binding['current_eligibility_sha256'] != digest(versioned['eligibility'])
                    or binding['original_occurrence_graph'] != versioned['source_graph'][fact['fact_id']]
                    or binding['source_scope'] != 'issuer_business_only_no_current_price_or_security_valuation'):
                raise ValueError('versioned_business_source_graph_mismatch')
    if result["numeric_registry_graph"] != [{"fact_id": r["fact_id"], "field_path": r["field_path"],
            "registry_entry_sha256": digest(r), "source_node_sha256": digest(result["source_graph"][r["fact_id"]])}
            for r in stock["numeric_registry"]]:
        raise ValueError("numeric_source_graph_mismatch")
    if "event_source" in result or versioned is not None:
        from scripts.m12dk_current_source_authority import earnings_lineage_receipt
        refs = {r.ref_id for r in evidence.evidence if r.source_ref.startswith("stock.fact_catalog.event:")}
        refs.update(r.ref_id for r in evidence.evidence if r.source_ref.startswith("stock.fact_catalog.earnings:")
            and earnings_lineage_receipt(r.model_dump(mode="json"), stock, result["packet"])["status"] == "PASS")
        if versioned is not None:
            refs.update('canonical:' + f['fact_id'] for f in versioned['facts'])
        actual = [r["ref_id"] for r in result["observed_business_union"] if r["status"] == "PASS"]
        if set(actual) != refs or len(actual) != len(refs) or result["observed_business_cardinality"] != len(refs):
            raise ValueError("observed_business_union_replay_mismatch")
    if result["status"] == "PASS" and (result["mandatory_missing"] or not result["observed_business_cardinality"]):
        raise ValueError("mandatory_stock_contract_failed")
    return result["status"] == "PASS"
