from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.macro import MacroObservation, MacroEvent
from app.services.unified_consumption_projection import (
    project_cash_flow_consumption, project_working_capital_consumption,
)
from app.services.unified_persisted_owner_bridge import capture_persisted_owner
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import C, OwnerAdapter, SourceInput, SourceRole, freeze_run
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_cash_flow_shadow_consumption_service import _full_facts
from test_working_capital_shadow_consumption_service import _snapshot


AT = datetime(2026, 8, 21, 0, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({"fred", "eia", "ecos", "ohlcv_analyst", "finnhub",
    "federal_reserve", "sec_companyfacts", "sec_edgar_companyfacts", "canonical_derivation"}))


def cash(facts=None, **options):
    return project_cash_flow_consumption(facts=tuple(facts or _full_facts()), issuer_id="issuer-1",
        ticker="EXAMPLE", industry="cloud_platform", financial_type="non_financial",
        core_status="ELIGIBLE", cutoff=AT, policy=POLICY,
        latest_formal_period=options.get("formal", date(2026, 6, 30)),
        latest_provisional_period=options.get("provisional"))


def test_cash_flow_actual_owner_verdict_lineage_deterministic_no_render(monkeypatch):
    from app.services import cash_flow_user_visible_service, cash_flow_shadow_consumption_service
    monkeypatch.setattr(cash_flow_user_visible_service, "_render", lambda *_: pytest.fail("render"))
    monkeypatch.setattr(cash_flow_shadow_consumption_service, "render_shadow_reasoning", lambda *_: pytest.fail("render"))
    result = cash()
    assert result == cash()
    assert result["consumption_eligible"]
    assert result["existing_owner_verdict"]["freshness_state"] == "CURRENT_FORMAL"
    assert set(result["selected_fact_ids"]) <= set(result["input_fact_ids"])
    assert all(result["fact_versions"][f["fact_id"]] == digest(f) for f in result["facts"])


@pytest.mark.parametrize("case", ["stale", "formal_missing", "future", "taint", "currency", "source_date"])
def test_cash_flow_denial_does_not_expose_values(case):
    facts = list(_full_facts())
    options = {}
    if case == "stale":
        options["formal"] = date(2026, 9, 30)
    elif case == "formal_missing":
        options["formal"] = None
    else:
        facts = [replace(f, **{
            "future": {"filing_date": date(2026, 9, 1)},
            "taint": {"quality": "TAINTED"},
            "currency": {"currency": "TWD" if f.metric.value == "operating_cash_flow" else "USD"},
            "source_date": {"source_available_at": date(2026, 9, 1)},
        }[case]) for f in facts]
    result = cash(facts, **options)
    assert not result["consumption_eligible"]
    assert result["facts"] == []


@pytest.mark.parametrize("case", ["duplicate", "issuer", "unowned", "prohibited"])
def test_cash_flow_conflicting_ownership_rejected(case):
    facts = list(_full_facts())
    if case == "duplicate":
        facts.append(facts[0])
    else:
        facts[0] = replace(facts[0], **{
            "issuer": {"issuer_id": "another"}, "unowned": {"source_occurrence_id": ""},
            "prohibited": {"source_provider": "alpha_vantage"},
        }[case])
    with pytest.raises(ValueError):
        cash(facts)


def test_lagging_provisional_does_not_become_current():
    result = cash(provisional=date(2026, 9, 30))
    assert result["consumption_eligible"]
    assert result["existing_owner_verdict"]["usage_mode"] == "LATEST_FORMAL_CONTEXT_ONLY"


@pytest.mark.parametrize("formal,eligible", [(date(2026, 6, 30), True), (date(2026, 9, 30), False), (None, False)])
def test_working_capital_existing_consumption_owner(formal, eligible, monkeypatch):
    from app.services import working_capital_shadow_consumption_service
    monkeypatch.setattr(working_capital_shadow_consumption_service, "render_working_capital_reasoning",
                        lambda *_: pytest.fail("render"))
    result = project_working_capital_consumption(snapshot=_snapshot(), issuer_id="sec:0000000001",
        ticker="EXAMPLE", market="us", packet_id="offline", industry="memory_semiconductor",
        cutoff=AT, latest_formal_balance_date=formal, policy=POLICY, monitoring_text="inventory")
    assert result["consumption_eligible"] is eligible
    assert result["facts"] or not eligible


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def role(family, *, mandatory=False, provider="fred"):
    return SourceRole(key=family, owner="read_only_" + family, market="us", symbol="*",
        acquisition_class=C, mandatory=mandatory, provider=provider,
        basis="published_context", session="2026-08-20")


def frozen(tmp_path, db, family="rates_credit_liquidity_risk", **options):
    specification = role(family, **options)
    item, owner = capture_persisted_owner(db, root=tmp_path, run_id="offline", role=specification,
        family=family, cutoff=AT, policy=POLICY)
    result = freeze_run(root=tmp_path, run_id="offline", run_started_at=AT, cutoff=AT,
        roles=(specification,), inputs=(item,), policy=POLICY, owners={specification.owner: owner})
    return result, item, owner


def test_optional_c_retains_class_with_bound_empty_selection(db, tmp_path):
    result, item, _ = frozen(tmp_path, db)
    row = json.loads(result.content)["components"][0]
    assert row["source"]["acquisition_class"] == C
    assert row["availability"] == "UNAVAILABLE"
    assert row["value"] is None and item.original_record_id and item.version


def test_mandatory_c_never_accepts_empty_selection(db, tmp_path):
    with pytest.raises(ValueError, match="optional_persisted_denial"):
        frozen(tmp_path, db, mandatory=True)


def test_c_denial_requires_bound_record_and_owner(tmp_path, db):
    with pytest.raises(ValueError, match="bound_source"):
        SourceInput(role="x", run_id="r", acquisition_class=C, denial="missing")
    _, item, owner = frozen(tmp_path, db)
    fake = replace(owner, project_and_validate=lambda raw, cutoff: replace(
        owner.project_and_validate(raw, cutoff), value={"stale": 1}))
    specification = role("rates_credit_liquidity_risk")
    with pytest.raises(ValueError, match="optional_persisted_denial"):
        freeze_run(root=tmp_path, run_id="offline", run_started_at=AT, cutoff=AT,
            roles=(specification,), inputs=(item,), policy=POLICY, owners={specification.owner: fake})


def test_macro_owner_callback_preserves_original_time_and_replays(db, tmp_path):
    db.add(MacroObservation(dedupe_key="fred-fixture", provider="fred", series_code="DGS10", category="rates", value=4.0,
        unit="percent", frequency="daily", observed_at=AT - timedelta(days=1),
        retrieved_at=AT - timedelta(hours=1), source_url="https://fred.stlouisfed.org/series/DGS10"))
    db.commit()
    before = len(db.identity_map)
    result, item, owner = frozen(tmp_path, db)
    value = json.loads(result.content)["components"][0]["value"]
    assert value[0]["observation"]["observed_at"].startswith("2026-08-20")
    assert not db.dirty and not db.new and not db.deleted and len(db.identity_map) == before
    original = owner.project_and_validate((tmp_path / item.artifact).read_bytes(), AT)
    assert original.value == value
    assert isinstance(owner, OwnerAdapter)


def test_fed_callback_does_not_emit_stored_ai_implications(db, tmp_path):
    db.add(MacroEvent(provider="federal_reserve", event_key="release", event_type="statement",
        category="monetary_policy", title="Published statement", event_status="released",
        released_at=AT - timedelta(days=1), retrieved_at=AT - timedelta(hours=1),
        source_url="https://www.federalreserve.gov/example.htm", inferred_implications='["stored AI"]'))
    db.commit()
    result, _, _ = frozen(tmp_path, db, "central_bank_published_events", provider="federal_reserve")
    assert b"stored AI" not in result.content
    assert b"inferred_implications" not in result.content


def test_estimate_absence_does_not_block_optional_c(db, tmp_path):
    result, _, _ = frozen(tmp_path, db, "eligible_valuation_estimates", provider="finnhub")
    assert json.loads(result.content)["components"][0]["availability"] == "UNAVAILABLE"


def test_frozen_inventory_counts_unchanged():
    from collections import Counter
    from pathlib import Path
    data = json.loads(Path("docs/operations/UNIFIED_ACQUISITION_CLASSES.json").read_bytes())
    assert sorted(Counter(r["acquisition_class"] for r in data["roles"]).values()) == [3, 4, 5, 12]


def test_canonical_verdict_never_claims_formal_source_binding_or_adapter_qualification():
    result = cash()
    assert result["consumption_eligible"]
    assert result["formal_source_binding_verified"] is False
    assert result["complete_source_adapter_qualified"] is False


def test_unknown_consumed_type_not_silently_given_financial_owner():
    from scripts.unified_consumption_audit import field_role
    assert field_role({"fact_type": "unreviewed_financial_domain"}, "us") is None
    assert field_role({"fact_type": "earnings"}, "kr") == "opendart_financial_fundamental_domains"


@pytest.mark.parametrize("provider", ["finnhub", "alpha_vantage"])
def test_estimate_inventory_cannot_grant_eps_authority(db, tmp_path, provider):
    from app.models.security import ConsensusEstimate
    db.add(ConsensusEstimate(ticker="*", provider=provider, metric="forward_pe", value=12,
        estimate_period="provider-defined forward consensus", basis="provider-defined",
        estimate_as_of=AT - timedelta(hours=1)))
    db.commit()
    result, _, _ = frozen(tmp_path, db, "eligible_valuation_estimates", provider="finnhub")
    row = json.loads(result.content)["components"][0]
    assert row["availability"] == "UNAVAILABLE" and row["value"] is None
    if provider == "alpha_vantage":
        assert b"alpha_vantage" not in (tmp_path / row["source"]["artifact"]).read_bytes()


def test_canonical_cycle_cannot_be_consumed():
    facts = list(_full_facts())
    target = next(f for f in facts if f.fact_id == "ocf-2026")
    facts[facts.index(target)] = replace(target, input_fact_ids=(target.fact_id,))
    with pytest.raises(ValueError, match="cycle"):
        cash(facts)


@pytest.mark.parametrize("family,provider", [("energy", "fred"), ("rates_credit_liquidity_risk", "eia")])
def test_persisted_owner_cannot_relabel_source_family(db, tmp_path, family, provider):
    with pytest.raises(ValueError, match="role_family_mismatch"):
        frozen(tmp_path, db, family, provider=provider)


def test_persisted_callback_rejects_tampered_value(db, tmp_path):
    _, item, owner = frozen(tmp_path, db)
    document = json.loads((tmp_path / item.artifact).read_bytes())
    document["projection"]["values"] = [{"value": 999}]
    with pytest.raises(ValueError, match="hash_mismatch"):
        owner.project_and_validate(json.dumps(document).encode(), AT)
