from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.macro import MacroEvent, MacroObservation
from app.models.security import ConsensusEstimate, SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.unified_class_c_owners import (
    CLASS_C_ROLES, MACRO_ROLES, class_c_owner_inventory, project_reported_financial,
    project_macro_records, project_estimate_inventory, project_published_events, project_canonical_catalog,
)
from app.services.unified_local_seed_bridge import capture_local_seed
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import durable_json
from app.services.unified_source_composition import freeze_run, compose_attempt
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from test_kr_financial_lineage_service import _item, _row
from app.services.kr_financial_lineage_service import opendart_lineage_records


CUTOFF = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({"canonical_local", "sec_edgar", "sec_companyfacts", "opendart",
    "finnhub", "fred", "ecos", "eia", "federal_reserve", "ohlcv_analyst", "official_fixture"}))


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(WatchlistItem(ticker="FIX", company_name="Fixture", exchange="NASDAQ",
            created_at=CUTOFF, activated_at=CUTOFF, latest_status="MUST_NOT_BE_A_SOURCE"))
        session.add(SecurityMaster(ticker="FIX", company_name="Fixture", canonical_company_id="issuer:fix",
            canonical_security_id="security:fix", exchange="NASDAQ", country="US", cik="1234", corp_code="00123456",
            issuer_type="domestic_us", identity_provider="sec_edgar", updated_at=CUTOFF))
        session.add(InvestmentThesis(ticker="FIX", version=1, core_thesis="Configured thesis", created_at=CUTOFF))
        session.commit()
        yield session
    engine.dispose()


def clean(session):
    assert not session.dirty and not session.new and not session.deleted


def test_twelve_roles_exact_no_prequalification_by_count():
    frozen = json.loads(Path("docs/operations/UNIFIED_ACQUISITION_CLASSES.json").read_bytes())
    expected = {r["role"] for r in frozen["roles"] if r["acquisition_class"] == "VERSIONED_PERSISTED_ALLOWED"}
    assert set(CLASS_C_ROLES) == expected and len(CLASS_C_ROLES) == 12
    assert class_c_owner_inventory()["network_free_source_adapter_prequalified"] is False


def test_local_mandatory_seed_real_owner_replay_no_prior_ai_or_price(tmp_path, session):
    roles, inputs, owners = capture_local_seed(session, root=tmp_path, run_id="fixture",
        market="us", session_key="2026-08-25", cutoff=CUTOFF, policy=POLICY)
    assert "MUST_NOT_BE_A_SOURCE" not in (tmp_path / "local-us.json").read_text()
    frozen = freeze_run(root=tmp_path, run_id="fixture", run_started_at=CUTOFF, cutoff=CUTOFF,
                        roles=roles, inputs=inputs, owners=owners, policy=POLICY)
    first = compose_attempt(frozen=frozen, expected_run_sha256=frozen.sha256, root=tmp_path,
        attempt_id="A", started_at=CUTOFF, cutoff=CUTOFF, inputs=(), owners=owners)
    again = compose_attempt(frozen=frozen, expected_run_sha256=frozen.sha256, root=tmp_path,
        attempt_id="A", started_at=CUTOFF, cutoff=CUTOFF, inputs=(), owners=owners)
    assert first == again
    durable_json(tmp_path / "local-seed-only-composition.json", first)
    assert len(first["run_components"]) == 3
    assert not first["model_dispatch_qualified"]
    clean(session)


def test_local_future_cutoff_owner_negative(tmp_path, session):
    roles, inputs, owners = capture_local_seed(session, root=tmp_path, run_id="fixture",
        market="us", session_key="2026-08-25", cutoff=CUTOFF, policy=POLICY)
    with pytest.raises(ValueError, match="changed|eligibility"):
        freeze_run(root=tmp_path, run_id="fixture", run_started_at=CUTOFF - timedelta(days=1),
            cutoff=CUTOFF - timedelta(days=1), roles=roles, inputs=inputs, owners=owners, policy=POLICY)


def test_sec_direct_selected_field_lineage_and_ambiguity_preserved(session, tmp_path):
    entry = {**_companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01"),
             "accn": "0000001234-26-000001"}
    payload = _companyfacts_payload("us-gaap", {"Revenues": [dict(entry, val=100)],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [dict(entry, val=10)],
        "OperatingIncomeLoss": [entry]})
    payload["cik"] = 1234
    rows = _companyfacts_snapshots(payload, "FIX")
    session.add_all(rows)
    session.commit()
    result = project_reported_financial(session, role="sec_financial_fundamental_domains", ticker="FIX",
                                       cutoff=CUTOFF, policy=POLICY)
    assert [r["metric"] for r in result["values"]] == ["operating_income"]
    value = result["values"][0]
    assert value["lineage"]["source_document_id"]
    assert value["lineage"]["source_row_identity"]
    assert value["record_id"] and value["record_sha256"]
    assert result["source_receipt"] is None
    durable_json(tmp_path / "sec-selected-field-projection.json", result)
    assert result == project_reported_financial(session, role="sec_financial_fundamental_domains", ticker="FIX",
                                               cutoff=CUTOFF, policy=POLICY)
    clean(session)


def test_opendart_exact_occurrence_not_freshness_only(session, tmp_path):
    records = opendart_lineage_records(_item(), logical_field="revenue", report_code="11012", selected=True)
    row = _row(records)
    row.ticker = "FIX"
    row.unit_scale = 1
    session.add(row)
    session.commit()
    result = project_reported_financial(session, role="opendart_financial_fundamental_domains", ticker="FIX",
                                       cutoff=CUTOFF, policy=POLICY)
    assert len(result["values"]) == 1
    assert result["values"][0]["lineage"]["source_row_identity"]
    durable_json(tmp_path / "opendart-selected-field-projection.json", result)
    clean(session)


@pytest.mark.parametrize("role", list(MACRO_ROLES))
@pytest.mark.parametrize("state", ["valid", "future", "stale", "prohibited"])
def test_macro_role_original_date_and_current_temporal_owner(session, role, state, tmp_path):
    provider = MACRO_ROLES[role][0]
    observed = CUTOFF - timedelta(days=1)
    row = MacroObservation(dedupe_key="fixture", series_code="SPY" if role == "kr_overnight_cross_assets" else "DGS10",
        category="fixture", provider=provider, observed_at=observed, retrieved_at=CUTOFF,
        value=4.0, unit="percent", quality_status="fresh", source_url="https://example.test")
    if state == "future":
        row.retrieved_at = CUTOFF + timedelta(seconds=1)
    if state == "stale":
        row.quality_status = "stale"
    if state == "prohibited":
        row.raw_payload = json.dumps({"source_provider": "alpha_vantage"})
    session.add(row)
    session.commit()
    if state == "prohibited":
        with pytest.raises(ValueError, match="not_authorized"):
            project_macro_records(session, role=role, cutoff=CUTOFF, policy=POLICY)
    else:
        result = project_macro_records(session, role=role, cutoff=CUTOFF, policy=POLICY)
        assert result["eligible"] == (state == "valid")
        durable_json(tmp_path / f"{role}-{state}.json", result)
        assert result == project_macro_records(session, role=role, cutoff=CUTOFF, policy=POLICY)
        if state == "valid":
            assert result["values"][0]["observation"]["observed_at"].startswith("2026-08-25")
            assert result["version"] == digest(result["records"])
    clean(session)


@pytest.mark.parametrize("future", [False, True])
def test_released_fed_context_not_prior_ai_output(session, future, tmp_path):
    session.add(MacroEvent(event_key="fixture", event_type="speech", category="policy", title="Fixture speech",
        provider="federal_reserve", source_url="https://www.federalreserve.gov/fixture",
        released_at=CUTOFF + timedelta(days=int(future)), retrieved_at=CUTOFF,
        inferred_implications='["NOT_INPUT"]', unknowns='["NOT_INPUT"]'))
    session.commit()
    result = project_published_events(session, cutoff=CUTOFF, policy=POLICY)
    assert result["eligible"] is (not future)
    assert "NOT_INPUT" not in json.dumps(result)
    durable_json(tmp_path / "fed-context.json", result)
    clean(session)


def test_estimate_inventory_does_not_forge_unavailable_basis(session, tmp_path):
    session.add(ConsensusEstimate(ticker="FIX", provider="finnhub", estimate_as_of=CUTOFF,
        estimate_period="provider-defined forward consensus", metric="forward_pe", value=10))
    session.commit()
    result = project_estimate_inventory(session, ticker="FIX", cutoff=CUTOFF, policy=POLICY)
    assert result["records"] and not result["eligible"]
    assert result["qualification"] == "GAP_PERSISTED_ESTIMATE_OWNER_NOT_IMPLEMENTED"
    durable_json(tmp_path / "estimate-owner-gap.json", result)
    clean(session)


@pytest.mark.parametrize("as_of", [CUTOFF, CUTOFF + timedelta(hours=7, minutes=13, seconds=17)])
def test_estimate_utc_datetime_persistence_preserves_metadata_and_ineligibility(session, as_of):
    assert ConsensusEstimate.model_fields["estimate_as_of"].annotation is datetime
    assert as_of.utcoffset() == timedelta(0)
    period = "provider-defined forward consensus"
    estimate = ConsensusEstimate(ticker="FIX", provider="finnhub", estimate_as_of=as_of,
        estimate_period=period, basis="provider-defined", metric="forward_pe", value=10)
    session.add(estimate)
    session.commit()
    identity = estimate.id
    session.expunge(estimate)

    stored = session.get(ConsensusEstimate, identity)
    assert stored is not None
    assert isinstance(stored.estimate_as_of, datetime)
    persisted = stored.estimate_as_of
    # Older SQLite adapters return the stored UTC wall time without tzinfo.
    if persisted.tzinfo is None:
        persisted = persisted.replace(tzinfo=timezone.utc)
    assert persisted.astimezone(timezone.utc) == as_of
    assert (stored.estimate_period, stored.basis, stored.metric, stored.value) == (
        period, "provider-defined", "forward_pe", 10)
    result = project_estimate_inventory(session, ticker="FIX", cutoff=as_of, policy=POLICY)
    assert result["records"] and result["values"] == [] and not result["eligible"]
    assert result["qualification"] == "GAP_PERSISTED_ESTIMATE_OWNER_NOT_IMPLEMENTED"
    clean(session)


def test_canonical_lineage_reuses_adapter_and_never_claims_freshness(tmp_path):
    from test_financial_lineage_projection_service import _project, _reported_pair, _period
    from app.services.cash_flow_capital_efficiency_service import PeriodType
    rows = _project(list(_reported_pair(_period(PeriodType.YTD, 2026, 2), prefix="fixture")))
    result = project_canonical_catalog(rows, cutoff=CUTOFF, policy=POLICY)
    assert result["lineage_eligible"] and not result["consumption_eligible"]
    assert result["records"][0]["fact_id"] == rows[0]["fact_id"]
    assert project_canonical_catalog(rows, cutoff=CUTOFF, policy=POLICY) == result
    durable_json(tmp_path / "canonical-lineage-only-projection.json", result)
    rows[0]["canonical_financial_lineage"]["source_provider"] = "alpha_vantage"
    with pytest.raises(ValueError, match="not_authorized"):
        project_canonical_catalog(rows, cutoff=CUTOFF, policy=POLICY)
