from copy import deepcopy
from datetime import date
import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.unified_class_c_owners import project_reported_financial, project_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_composition import C, SourceRole
from app.services.unified_stock_anomaly_scope import materialize_source_components
from app.services.unified_stock_owner import assemble_stock, validate_assembled, reject_downstream
from scripts.unified_stock_owner_proof import POLICY
from test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
from test_unified_stock_acquisition import plan as acquisition_plan
from test_unified_stock_anomaly_scope import bars, bad


def freeze_hashes(params):
    params["expected_hashes"] = {"plan": digest(params["plan"].model_dump(mode="json")),
        **{k: digest(params[v]) for k, v in {"local": "local_seed", "financial": "financial",
            "components": "components", "receipts": "receipts"}.items()}}
    for key in ('completed_close_source', 'completed_price_source'):
        if key in params:
            params['expected_hashes'][key] = digest(params[key])
    return params


@pytest.fixture
def source():
    plan = acquisition_plan.__wrapped__()
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    at = plan.frozen_at
    with Session(engine) as session:
        session.add(WatchlistItem(ticker="CORZ", company_name="Fixture", exchange="NASDAQ",
            created_at=at, activated_at=at))
        session.add(SecurityMaster(ticker="CORZ", company_name="Fixture", canonical_company_id="issuer:fixture",
            canonical_security_id="security-CORZ", exchange="NASDAQ", country="US", cik="1234",
            issuer_type="domestic_us", identity_provider="sec_edgar", updated_at=at))
        session.add(InvestmentThesis(ticker="CORZ", version=1, core_thesis="Configured business", created_at=at))
        entry = {**_companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01"),
            "accn": "0000001234-26-000001"}
        payload = _companyfacts_payload("us-gaap", {"Revenues": [dict(entry, val=100)],
            "OperatingIncomeLoss": [entry]})
        payload["cik"] = 1234
        session.add_all(_companyfacts_snapshots(payload, "CORZ"))
        session.commit()
        local = project_local_seed(session, market="us", session_key="2026-09-25", cutoff=at, policy=POLICY)
        projection = project_reported_financial(session, role="sec_financial_fundamental_domains",
            ticker="CORZ", cutoff=at, policy=POLICY)
    engine.dispose()
    role = SourceRole(key="sec_financial_fundamental_domains:CORZ", owner="project_reported_financial",
        market="us", symbol="CORZ", acquisition_class=C, mandatory=False,
        provider="sec_companyfacts", basis="direct_reported_issuer_financial", session="2026-09-25")
    financial = {"contract": "unified-persisted-owner-input-v1", "role": role.model_dump(mode="json"),
        "family": "sec_financial_fundamental_domains", "projection": projection}
    receipts, artifacts, roles = {}, {}, {}
    for read in plan.reads[:4]:
        rows = bars(400)
        roles[read.role] = rows
        raw = encoded({"return_code": 0, "result_list": rows})
        normalized = encoded(rows)
        name = read.role
        artifacts[name + ".body"], artifacts[name + ".json"] = raw, normalized
        request = {"method": "POST", "route": read.route, "api_id": read.api_id,
            "payload": {"stk_cd": read.subject, "upd_stkpc_tp": str(int(read.adjusted)), "stex_tp": read.exchange}}
        page = {"provider": "kiwoom", "entry_id": read.entry_id, "page_ordinal": 1,
            "request": request, "request_sha256": digest(request), "requested_at": "2026-09-26T00:00:01+00:00",
            "received_at": "2026-09-26T00:00:02+00:00", "artifact": name + ".body",
            "source_sha256": digest(json.loads(raw)), "http_status": 200}
        from app.services.unified_run_artifacts import sha256_bytes
        page["source_sha256"] = sha256_bytes(raw)
        receipts[name] = {"run_id": plan.run_id, "acquisition_id": plan.acquisition_id,
            "plan_sha256": digest(plan.model_dump(mode="json")), "entry": read.model_dump(mode="json"),
            "started_at": "2026-09-26T00:00:00+00:00", "completed_at": "2026-09-26T00:00:03+00:00",
            "status": "CAPTURED", "pages": [page], "normalized_artifact": name + ".json",
            "normalized_sha256": sha256_bytes(normalized)}
    components = materialize_source_components(ticker="CORZ", market="us", cutoff=date(2026, 9, 25),
        observed_at=at.isoformat(), roles=roles)
    return freeze_hashes(dict(plan=plan, ticker="CORZ", receipts=receipts, artifacts=artifacts,
        local_seed=local, financial=financial, components=components, policy=POLICY))


def test_actual_existing_owners_deterministic_and_optional_absence(source):
    before = deepcopy(source)
    first = assemble_stock(**source)
    assert first == assemble_stock(**source)
    assert source == before
    assert first["status"] == "PASS", first["mandatory_missing"]
    assert first["observed_business_cardinality"] > 0
    stock = first["packet"]["stocks"][0]
    assert stock["technical_context"]["contract"] == "packet-owned-technical-context-v1"
    assert "cash_flow_user_visible" not in stock and "working_capital_user_visible" not in stock
    assert "forward_eps" not in stock["valuation"]
    for component in first["component_binding"]:
        if component["eligible"] and component["consumer"] in {"v3_long_cycle", "valuation_weekly_close_history"}:
            assert component["behavior"] == "SOURCE_AVAILABLE_CONSUMER_NOT_MATERIALIZED"
            assert not component["selected_value_in_packet"]
    assert validate_assembled(first, expected_result_sha256=digest(first))


@pytest.mark.parametrize("key", ["previous_assessment", "rendered_prose", "ai_verdict", "monitoring_state"])
def test_downstream_output_injection_rejected(source, key):
    source["local_seed"][key] = "not source evidence"
    freeze_hashes(source)
    with pytest.raises(ValueError, match="downstream_output_forbidden"):
        assemble_stock(**source)


@pytest.mark.parametrize("mutation", ["raw_hash", "wrong_subject", "wrong_basis", "prior_attempt", "prior_run"])
def test_source_ownership_failures(source, mutation):
    receipt = source["receipts"]["adjusted_daily"]
    if mutation == "raw_hash":
        source["artifacts"][receipt["pages"][0]["artifact"]] += b" "
    elif mutation == "wrong_subject":
        receipt["entry"]["subject"] = "CPNG"
    elif mutation == "wrong_basis":
        receipt["entry"]["adjusted"] = False
    elif mutation == "prior_attempt":
        receipt["acquisition_id"] = "prior"
    else:
        receipt["run_id"] = "prior"
    freeze_hashes(source)
    with pytest.raises(ValueError):
        assemble_stock(**source)


@pytest.mark.parametrize("mutation", ["future", "tainted", "unowned", "empty"])
def test_financial_cannot_promote_modified_input(source, mutation):
    projection = source["financial"]["projection"]
    if mutation == "empty":
        projection["values"] = []
    else:
        value = next(r["record"] for r in projection["records"] if r["table"] == "financialsnapshot")
        if mutation == "future":
            value["filing_date"] = "2027-01-01"
        elif mutation == "tainted":
            value["financial_hard_errors"] = '["gross_margin_out_of_range"]'
        else:
            value["ticker"] = "CPNG"
    projection["version"] = digest(projection["records"])
    projection["projection_sha256"] = digest({k: v for k, v in projection.items() if k != "projection_sha256"})
    freeze_hashes(source)
    with pytest.raises(ValueError):
        assemble_stock(**source)


def test_missing_business_is_not_replaced_by_thesis(source):
    from app.services.unified_persisted_owner_bridge import MODELS, project
    document = source["financial"]
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        record = next(r for r in document["projection"]["records"] if r["table"] == "securitymaster")
        session.add(MODELS[record["table"]].model_validate(record["record"]))
        session.commit()
        document["projection"] = project(session, role=document["family"], ticker="CORZ",
            cutoff=source["plan"].frozen_at, policy=POLICY)
    engine.dispose()
    freeze_hashes(source)
    result = assemble_stock(**source)
    assert result["status"] == "BLOCKED"
    assert result["observed_business_cardinality"] == 0
    assert result["packet_sha256"] is None


@pytest.mark.parametrize("mutation", ["numeric", "wrong_stock_ref", "fact", "typed_evidence", "technical_identity", "missing_graph"])
def test_final_packet_binding_mismatch(source, mutation):
    result = assemble_stock(**source)
    stock = result["packet"]["stocks"][0]
    if mutation == "numeric":
        stock["numeric_registry"][0]["value"] += 1
    elif mutation == "wrong_stock_ref":
        next(iter(result["source_graph"].values()))["ticker"] = "CPNG"
    elif mutation == "fact":
        stock["fact_catalog"][0]["fields"]["unexpected"] = 1
    elif mutation == "typed_evidence":
        result["evidence_packet"]["evidence"][0]["statement"] = "unbound replacement"
    elif mutation == "technical_identity":
        stock["technical_context"]["ticker"] = "CPNG"
    else:
        result["evidence_reference_graph"].pop(next(iter(result["evidence_reference_graph"])))
    with pytest.raises(ValueError):
        validate_assembled(result, expected_result_sha256=digest(result))


def mutate_bars(source, index):
    from app.services.unified_run_artifacts import sha256_bytes
    role = "adjusted_daily"
    rows = json.loads(source["artifacts"][role + ".json"])
    bad(rows, index)
    source["artifacts"][role + ".json"] = encoded(rows)
    source["receipts"][role]["normalized_sha256"] = sha256_bytes(encoded(rows))
    source["artifacts"][role + ".body"] = encoded({"return_code": 0, "result_list": rows})
    source["receipts"][role]["pages"][0]["source_sha256"] = sha256_bytes(source["artifacts"][role + ".body"])
    roles = {r: json.loads(source["artifacts"][r + ".json"]) for r in source["receipts"]}
    source["components"] = materialize_source_components(ticker="CORZ", market="us", cutoff=date(2026, 9, 25),
        observed_at=source["plan"].frozen_at.isoformat(), roles=roles)
    freeze_hashes(source)


def test_preserved_historical_anomaly_is_optional_not_whole_stock_failure(source):
    mutate_bars(source, 1)
    before = deepcopy(source["artifacts"])
    result = assemble_stock(**source)
    assert result["status"] == "PASS", result["mandatory_missing"]
    assert any(r["behavior"] == "UNAVAILABLE_SOURCE_ANOMALY_RELEVANT" for r in result["component_binding"])
    assert source["artifacts"] == before


def test_mandatory_current_anomaly_fails(source):
    mutate_bars(source, -1)
    before = deepcopy(source["artifacts"])
    result = assemble_stock(**source)
    assert result["status"] == "BLOCKED"
    assert "price_and_positioning.price.current_price" in result["mandatory_missing"]
    assert result["packet_sha256"] is None
    stock = result["packet"]["stocks"][0]
    assert stock["price_and_positioning"]["price"]["current_price"] is None
    assert stock["technical_context"]["features"]["daily"]["facts"] == []
    assert source["components"]["features"]["daily"]["source_invalid_rows"]
    assert source["components"]["historical_technical_inventory"]["current_authority"] is False
    assert source["artifacts"] == before
    assert result == assemble_stock(**source)


def test_encoded_prior_model_injection():
    with pytest.raises(ValueError, match="forbidden"):
        reject_downstream({"nested": '{"previous_assessment": "forbidden"}'})


def test_field_audit_covers_actual_stock_contract_and_banned_surface(source):
    from pathlib import Path
    from scripts.m12ds_r4_r1_project_source import STOCK_FIELDS, BANNED
    from app.services.unified_stock_owner import FORBIDDEN
    audit = (Path(__file__).parents[1] / "docs/operations/UNIFIED_STOCK_OWNER_BINDING.md").read_text()
    assert all(name in audit for name in STOCK_FIELDS)
    assert BANNED <= FORBIDDEN
    stock = assemble_stock(**source)["packet"]["stocks"][0]
    assert set(stock) <= set(STOCK_FIELDS)
    assert {"ticker", "company_name", "thesis_version", "thesis", "fact_catalog", "numeric_registry"} <= set(stock)


def test_pure_catalog_extraction_preserves_existing_assessment_owner(source):
    from types import SimpleNamespace
    from app.services.ai_review_service import _fact_catalog, build_source_fact_catalog
    kwargs = dict(evidence=[], valuation={}, price={"price": {"current_price": 3, "currency": "USD"}},
        chart={}, monitoring_state={})
    at = source["plan"].frozen_at.date()
    assessment = SimpleNamespace(assessment_date=at, thesis_snapshot="{}")
    assert _fact_catalog(assessment, **kwargs) == build_source_fact_catalog(
        assessment_date=at, capital_actions=[], **kwargs)
