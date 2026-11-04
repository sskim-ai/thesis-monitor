"""SYNTHETIC_NOT_REAL_CURRENT: original owners, temporary DB, mock HTTP only.

These fixtures issue real in-process capabilities from synthetic Class-C rows.
They do not establish current registration, financial authority, or readiness for
any real issuer. No validator, registry, or ownership decision is monkeypatched.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import asyncio
import json
import sqlite3

import httpx
import pytest

from app.services import bounded_financial_acquisition as acquisition_owner
from app.services import current_financial_purpose_intake as current
from app.services import minimal_class_c_export as export_owner
from app.services import prospective_class_c_owner as prospective
from app.services import selected_financial_owner as selected
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_minimal_class_c_export import database


PROVENANCE = "SYNTHETIC_NOT_REAL_CURRENT"
AT = datetime(2026, 9, 26, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({
    "canonical_local", "local", "local+openfigi", "sec_official_identity",
    "sec_edgar", "dart", "opendart", "kiwoom",
}))


@dataclass
class SyntheticClock:
    value: datetime

    def now(self):
        return self.value


def synthetic_clock(monkeypatch, at=AT):
    """Patch clocks only; callers may advance ``clock.value`` between stages."""
    clock = SyntheticClock(at)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock.value.astimezone(tz) if tz else clock.value.replace(tzinfo=None)

    monkeypatch.setattr(export_owner, "datetime", FrozenDatetime)
    monkeypatch.setattr(acquisition_owner, "datetime", FrozenDatetime)
    monkeypatch.setattr(prospective, "_now", clock.now)
    monkeypatch.setattr(current, "_now", clock.now)
    return clock


def registered(tmp_path, ticker, market, security_override=None, *,
               run_id="synthetic-ng42", first_eligible_session=None, policy=POLICY):
    """Return ``(live_original_owner, document, security)`` from synthetic rows.

    Use ``document['cutoff']`` and the same ``run_id`` for the financial plan.
    Call ``synthetic_clock`` first when a deterministic capture time is needed.
    This helper does not project financial facts or issue a financial parent.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    permission = database(tmp_path, [(ticker, market)])
    overrides = dict(security_override or {})
    if "ticker" in overrides and overrides.pop("ticker") != ticker:
        raise ValueError("synthetic_fixture_ticker_mismatch")
    allowed = set(export_owner.COLUMNS["securitymaster"]) - {"id", "ticker"}
    if not set(overrides) <= allowed:
        raise ValueError("synthetic_fixture_unknown_security_column")
    with sqlite3.connect(permission.database) as db:
        for column, value in overrides.items():
            db.execute(f"UPDATE securitymaster SET {column}=? WHERE ticker=?", (value, ticker))
        db.execute("UPDATE watchlistitem SET first_eligible_session=? WHERE ticker=?",
                   (first_eligible_session, ticker))
        if "exchange" in overrides:
            db.execute("UPDATE watchlistitem SET exchange=? WHERE ticker=?", (overrides["exchange"], ticker))
    now = prospective._now()
    approval = prospective.record_backend_approval(prospective.ApprovalDecision(
        event_id=PROVENANCE, approved=True, user_message_sha256=digest(PROVENANCE),
        effective_at=now - timedelta(minutes=1), expires_at=now + timedelta(minutes=45),
        subjects=(ticker,)))
    capture = export_owner.capture_authorized_class_c(permission)
    owner, document = prospective.issue_prospective_owner(
        approval=approval, capture=capture, market=market,
        source_generation_id="synthetic-ng42-class-c-export", generation_id=run_id, policy=policy)
    security = next(row["record"] for component in document["roles"].values()
                    for row in component["records"] if row["table"] == "securitymaster"
                    and row["record"]["ticker"] == ticker)
    return owner, document, deepcopy(security)


@pytest.fixture
def clock(monkeypatch):
    return synthetic_clock(monkeypatch)


@pytest.fixture(autouse=True)
def synthetic_provenance(record_property):
    record_property("provenance", PROVENANCE)


def _plan(document, security, *, run_id="synthetic-ng42"):
    return acquisition_owner.make_plan(
        security, market=document["market"], cutoff=datetime.fromisoformat(document["cutoff"]),
        run_id=run_id, all_subjects_fresh=True)


FAMILIES = [
    pytest.param("UNSEENUS", "us", {"cik": "9141001"}, "SEC_DOMESTIC", id="domestic-us"),
    pytest.param("OTHERUS", "us", {"cik": "9141002", "exchange": "NYSE"},
                 "SEC_DOMESTIC", id="heldout-domestic-us"),
    pytest.param("UNSEENADS", "us", {
        "cik": "9142002", "issuer_type": "adr", "security_type": "ads",
        "ordinary_share_identifier": "923456", "country": "KR", "adr_ratio": 2.0,
    }, "SEC_FPI", id="heldout-ads"),
    pytest.param("OTHERFPI", "us", {
        "cik": "9143003", "issuer_type": "foreign_private_issuer", "security_type": "adr",
        "ordinary_share_identifier": "FICTITIOUS-ORDINARY", "country": "SG", "adr_ratio": 1.0,
    }, "SEC_FPI", id="heldout-fpi"),
    pytest.param("923456", "kr", {"corp_code": "00914567"}, "OPENDART", id="heldout-dart"),
    pytest.param("934567", "kr", {"corp_code": "00914568", "exchange": "KOSDAQ"},
                 "OPENDART", id="second-dart"),
]


@pytest.mark.parametrize("ticker,market,overrides,family", FAMILIES)
def test_original_registration_parent_family_and_idempotent_lookup(
        tmp_path, clock, ticker, market, overrides, family):
    owner, doc, security = registered(tmp_path, ticker, market, overrides)
    plan = _plan(doc, security)
    assert current.source_family(plan) == family
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    first = current.resolve_parent(parent, plan=plan)
    assert current.resolve_parent(parent, plan=deepcopy(plan)) == first
    assert first["source_family"] == family
    assert first["issuer_canonical_id"] == security["canonical_company_id"]
    assert first["security_canonical_id"] == security["canonical_security_id"]
    assert first["provider_issuer"] == plan["issuer"]
    assert first["source_plan_sha256"] == digest(plan)
    assert first["scope"] == "FINANCIAL_SOURCE_INTAKE_ONLY_NOT_NATIVE_OR_DIRECTION"
    first["run_id"] = "caller-modified-copy"
    assert current.resolve_parent(parent)["run_id"] == plan["run_id"]


def test_original_prospective_requalification_is_usable_by_current_parent(tmp_path, clock):
    owner, doc, security = registered(
        tmp_path, "REQUALIFIED", "us", first_eligible_session="2026-09-26")
    assert doc["denials"] == []
    assert all(component["eligible"] for component in doc["roles"].values())
    assert doc["prospective_owner_receipt"]["bindings"]["REQUALIFIED"][
        "original_first_eligible_session"] == "2026-09-26"
    plan = _plan(doc, security)
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    assert current.resolve_parent(parent, plan=plan)["run_id"] == plan["run_id"]


@pytest.mark.parametrize("mutation", [
    "wrong_issuer", "wrong_security", "wrong_company", "missing_relation",
    "wrong_ads_ratio", "missing_ads_ratio", "wrong_generation", "wrong_cutoff",
    "wrong_market", "wrong_provider", "wrong_forms",
])
def test_rehashed_plan_cannot_replace_registered_identity_or_family(tmp_path, clock, mutation):
    owner, doc, security = registered(tmp_path, "UNSEENADS", "us", {
        "issuer_type": "adr", "security_type": "ads", "cik": "9142002",
        "ordinary_share_identifier": "923456", "country": "KR", "adr_ratio": 2.0,
    })
    plan = _plan(doc, security)
    if mutation == "wrong_issuer":
        plan["security"]["cik"] = "9142999"
        plan["issuer"] = "0009142999"
    elif mutation == "wrong_security":
        plan["security"]["canonical_security_id"] = "security:another"
    elif mutation == "wrong_company":
        plan["security"]["canonical_company_id"] = "issuer:another"
    elif mutation == "missing_relation":
        plan["security"]["ordinary_share_identifier"] = None
    elif mutation == "wrong_ads_ratio":
        plan["security"]["adr_ratio"] = 20.0
    elif mutation == "missing_ads_ratio":
        plan["security"]["adr_ratio"] = None
    elif mutation == "wrong_generation":
        plan["run_id"] = "another-run"
    elif mutation == "wrong_cutoff":
        plan["cutoff"] = (clock.value - timedelta(seconds=1)).isoformat()
    elif mutation == "wrong_market":
        plan["market"] = "kr"
    elif mutation == "wrong_provider":
        plan["provider"] = "opendart"
    else:
        plan["forms"] = ["10-Q", "10-K"]
    plan["identity_sha256"] = digest(plan["security"])
    with pytest.raises(ValueError):
        current.issue_parent(registration_owner=owner, plan=plan)


def test_registered_unknown_ads_ratio_and_relation_remain_unknown(tmp_path, clock):
    owner, doc, security = registered(tmp_path, "UNKNOWNRELATION", "us", {
        "issuer_type": "adr", "security_type": "ads", "cik": "9142444",
        "ordinary_share_identifier": None, "adr_ratio": None,
    })
    plan = _plan(doc, security)
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    receipt = current.resolve_parent(parent, plan=plan)
    assert security["ordinary_share_identifier"] is None and security["adr_ratio"] is None
    assert receipt["source_family"] == "SEC_FPI"
    assert receipt["scope"] == "FINANCIAL_SOURCE_INTAKE_ONLY_NOT_NATIVE_OR_DIRECTION"
    changed = deepcopy(plan)
    changed["security"]["adr_ratio"] = 1.0
    changed["identity_sha256"] = digest(changed["security"])
    with pytest.raises(ValueError, match="current_financial_registered_identity_mismatch"):
        current.issue_parent(registration_owner=owner, plan=changed)


@pytest.mark.parametrize("action", ["parent", "registration", "expiry", "changed_plan", "json", "unissued"])
def test_live_parent_lifetime_and_non_rehydratable_authority(tmp_path, clock, action):
    owner, doc, security = registered(tmp_path, "UNSEENUS", "us")
    plan = _plan(doc, security)
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    receipt = current.resolve_parent(parent)
    if action == "parent":
        current.revoke_parent(parent)
    elif action == "registration":
        prospective.revoke_prospective_owner(owner)
    elif action == "expiry":
        clock.value = datetime.fromisoformat(receipt["expires_at"])
    elif action == "changed_plan":
        plan["maximum_HTTP_attempts"] += 1
    elif action == "json":
        parent = json.loads(json.dumps(receipt))
    else:
        parent = current.CurrentFinancialParent()
    with pytest.raises(ValueError):
        current.resolve_parent(parent, plan=plan)


def capture_for_plan(directory, plan):
    """Original bounded acquisition with synthetic provider bytes, never a GET."""
    from tests.test_bounded_financial_acquisition import filing, submission
    from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload

    family = current.source_family(plan)
    assert family in {"SEC_DOMESTIC", "OPENDART"}
    document = filing("10-Q")
    if family == "SEC_DOMESTIC":
        document["accessionNumber"] = f'{int(plan["issuer"]):010d}-26-000001'
    row = {**_companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30",
                               filed="2026-08-01"), "accn": document["accessionNumber"]}
    observations = [row, dict(row, start="2025-04-01", end="2025-06-30", val=20)]
    companyfacts = _companyfacts_payload("us-gaap", {
        "Revenues": [dict(r, val=100 if r["start"].startswith("2026") else 80) for r in observations],
        "OperatingIncomeLoss": observations,
    })
    companyfacts["cik"] = int(plan["issuer"])
    dart_rows = []
    for ordinal, (concept, label, value, prior) in enumerate([
        ("ifrs-full_Revenue", "Revenue", 100, 80),
        ("dart_OperatingIncomeLoss", "Operating income", 20, 15),
        ("ifrs-full_ProfitLoss", "Profit", 10, 8),
    ], 1):
        dart_rows.append(dict(
            corp_code=plan["issuer"], rcept_no="20260814000001", bsns_year="2026", reprt_code="11012",
            fs_div="CFS", sj_div="CIS", account_id=concept, account_nm=label, account_detail="-",
            ord=str(ordinal), currency="KRW", thstrm_amount=str(value), frmtrm_q_amount=str(prior),
            thstrm_nm="\uc81c 1 \uae30 \ubc18\uae30", frmtrm_q_nm="\uc81c 0 \uae30 \ubc18\uae30"))
    calls = []

    def respond(request):
        calls.append(request.url.path)
        if family == "OPENDART":
            if request.url.path.endswith("/list.json"):
                return httpx.Response(200, json={"status": "000", "total_page": 1, "list": [dict(
                    corp_code=plan["issuer"], stock_code=plan["ticker"], corp_name="Synthetic",
                    report_nm="\ubc18\uae30\ubcf4\uace0\uc11c (2026.06)",
                    rcept_no="20260814000001", rcept_dt="20260814")]})
            if request.url.path.endswith("/fnlttSinglAcntAll.json"):
                return httpx.Response(200, json={"status": "000", "list":
                    dart_rows if request.url.params["fs_div"] == "CFS" else []})
        elif request.url.path == f'/submissions/CIK{plan["issuer"]}.json':
            return httpx.Response(200, json={**submission([document]), "cik": int(plan["issuer"])})
        elif request.url.path == f'/api/xbrl/companyfacts/CIK{plan["issuer"]}.json':
            return httpx.Response(200, json=companyfacts)
        elif request.url.path.endswith("/primary.htm"):
            return httpx.Response(200, text="<html>Synthetic filing</html>")
        raise AssertionError("unexpected synthetic transport request: " + request.url.path)

    reader = acquisition_owner.BoundedReader(
        plan, directory, api_key="synthetic-no-credential", transport=httpx.MockTransport(respond))
    acquired = asyncio.run(acquisition_owner.collect(reader))
    assert acquired["denials"] == []
    assert len(calls) == reader.attempts == len(reader.receipts)
    return dict(plan=plan, acquisition=acquired, directory=directory,
                receipts=reader.receipts, field_semantics=True)


def _current_projection_case(tmp_path, ticker="UNSEENUS", market="us"):
    owner, doc, security = registered(tmp_path / "registration", ticker, market)
    plan = _plan(doc, security)
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    inputs = capture_for_plan(tmp_path / "capture", plan)
    projection = current.project_current(parent, **inputs)
    from app.services.bounded_financial_stock_owner import reported_comparisons
    facts, denied = reported_comparisons(plan, projection)
    assert facts and not denied
    envelope = selected.select(plan=plan, acquisition=inputs["acquisition"], projection=projection,
                               facts=facts, current_financial_parent=parent)
    return owner, parent, inputs, projection, facts, envelope


@pytest.mark.parametrize("ticker,market", [("UNSEENUS", "us"), ("923456", "kr")])
def test_original_projector_comparisons_selected_v2_validate(tmp_path, clock, ticker, market):
    _, parent, inputs, projection, facts, envelope = _current_projection_case(tmp_path, ticker, market)
    assert envelope["contract"] == "selected-financial-owner-v2"
    assert envelope["owner_type"] == ("direct_sec" if market == "us" else "direct_opendart")
    assert envelope["selected_fact_ids"] == sorted(fact["fact_id"] for fact in facts)
    for _ in range(2):
        assert selected.validate(envelope, projection=projection, facts=facts, bridge=None,
                                 current_financial_parent=parent) == envelope
    assert current.resolve_parent(parent, plan=inputs["plan"])["source_family"] == (
        "SEC_DOMESTIC" if market == "us" else "OPENDART")


@pytest.mark.parametrize("mutation", [
    "unregistered_projection", "projection", "comparison", "wrong_parent", "public_receipt",
    "reconstructed_parent", "revoked_parent", "raw_bytes", "v1_relabel",
])
def test_current_selected_requires_original_projection_and_live_parent(tmp_path, clock, mutation):
    owner, parent, inputs, projection, facts, envelope = _current_projection_case(tmp_path)
    if mutation == "unregistered_projection":
        parent = current.issue_parent(registration_owner=owner, plan=inputs["plan"])
        from app.services.bounded_financial_projection import project
        projection = project(**inputs)
        assert projection["contract"]
    elif mutation == "projection":
        projection = deepcopy(projection)
        projection["caller_claimed_financial_quality"] = "PASS"
    elif mutation == "comparison":
        facts = deepcopy(facts)
        facts[0]["value"] = "caller-rewritten-comparison"
    elif mutation == "wrong_parent":
        other, doc, security = registered(tmp_path / "other-registration", "OTHERUS", "us")
        parent = current.issue_parent(registration_owner=other, plan=_plan(doc, security))
    elif mutation == "public_receipt":
        parent = current.resolve_parent(parent)
    elif mutation == "reconstructed_parent":
        parent = current.CurrentFinancialParent()
    elif mutation == "revoked_parent":
        current.revoke_parent(parent)
    elif mutation == "raw_bytes":
        raw = inputs["directory"] / inputs["receipts"][0]["artifact"]
        raw.write_bytes(raw.read_bytes() + b"\n")
    else:
        with pytest.raises(ValueError, match="selected_financial_current_route_cannot_downgrade"):
            selected.select(plan=inputs["plan"], acquisition=inputs["acquisition"],
                            projection=projection, facts=facts)
        envelope = deepcopy(envelope)
        envelope["contract"] = "selected-financial-owner-v1"
        envelope.pop("current_parent")
        envelope.pop("current_purpose_receipt_sha256")
        parent = None
    if mutation in {"projection", "comparison", "v1_relabel"}:
        envelope["selected_projection_sha256"] = digest(projection)
        envelope["selected_fact_ids"] = sorted(f["fact_id"] for f in facts)
        envelope["envelope_sha256"] = digest({k: v for k, v in envelope.items() if k != "envelope_sha256"})
    with pytest.raises(ValueError):
        selected.validate(envelope, projection=projection, facts=facts, bridge=None,
                          current_financial_parent=parent)


@pytest.mark.parametrize("field,value", [
    ("monitored_security", "ANOTHER"),
    ("issuer_identity", "0009999999"),
    ("owner_type", "direct_opendart"),
    ("selected_acquisition_sha256", "f" * 64),
    ("field_completeness", {"owner": "caller", "partial_field_consumption_allowed": True}),
    ("source_completeness", {"owner": "caller", "state": "COMPLETE"}),
])
def test_rehashed_public_envelope_does_not_replace_backend_issuance(tmp_path, clock, field, value):
    _, parent, _, projection, facts, envelope = _current_projection_case(tmp_path)
    forged = deepcopy(envelope)
    forged[field] = value
    forged["envelope_sha256"] = digest({k: v for k, v in forged.items() if k != "envelope_sha256"})
    with pytest.raises(ValueError, match="selected_financial_unissued_or_changed_current_envelope"):
        selected.validate(forged, projection=projection, facts=facts, bridge=None,
                          current_financial_parent=parent)
    assert selected.validate(envelope, projection=projection, facts=facts, bridge=None,
                             current_financial_parent=parent) == envelope


@pytest.mark.parametrize("bridge_key", ["bridge", "origin"])
def test_current_bridge_requires_separate_legitimate_source_parent(tmp_path, clock, bridge_key):
    _, parent, inputs, projection, facts, _ = _current_projection_case(tmp_path)
    with pytest.raises(ValueError, match="current_selected_bridge_requires_separate_source_parent"):
        selected.select(plan=inputs["plan"], acquisition=inputs["acquisition"], projection=projection,
                        facts=facts, current_financial_parent=parent, **{bridge_key: {}})


def test_original_v1_still_valid_but_not_a_current_parent(tmp_path, clock):
    from app.services.bounded_financial_projection import project
    from app.services.bounded_financial_stock_owner import reported_comparisons

    owner, doc, security = registered(tmp_path / "registration", "LEGACYUS", "us",
                                      run_id="synthetic-ng42-legacy")
    plan = _plan(doc, security, run_id="synthetic-ng42-legacy")
    inputs = capture_for_plan(tmp_path / "capture", plan)
    projection = project(**inputs)
    facts, denied = reported_comparisons(plan, projection)
    assert facts and not denied
    envelope = selected.select(plan=plan, acquisition=inputs["acquisition"], projection=projection, facts=facts)
    assert envelope["contract"] == "selected-financial-owner-v1"
    assert selected.validate(envelope, projection=projection, facts=facts, bridge=None) == envelope
    parent = current.issue_parent(registration_owner=owner, plan=plan)
    with pytest.raises(ValueError, match="selected_financial_current_route_cannot_downgrade"):
        selected.validate(envelope, projection=projection, facts=facts, bridge=None)
    with pytest.raises(ValueError, match="current_financial_original_projection_required"):
        selected.select(plan=plan, acquisition=inputs["acquisition"], projection=projection,
                        facts=facts, current_financial_parent=parent)


def _legacy_case(tmp_path, *, ticker="LEGACYREPLAY", run_id="synthetic-original-legacy"):
    from app.services.bounded_financial_projection import project
    from app.services.bounded_financial_stock_owner import reported_comparisons

    owner, doc, security = registered(tmp_path / "registration", ticker, "us", run_id=run_id)
    plan = _plan(doc, security, run_id=run_id)
    inputs = capture_for_plan(tmp_path / "capture", plan)
    projection = project(**inputs)
    facts, denied = reported_comparisons(plan, projection)
    assert facts and not denied
    envelope = selected.select(plan=plan, acquisition=inputs["acquisition"], projection=projection, facts=facts)
    return owner, inputs, projection, facts, envelope


@pytest.mark.parametrize("mutation", ["plan_sha", "unused_fact_metadata", "both"])
def test_rehashed_legacy_provenance_cannot_escape_original_producer(tmp_path, clock, mutation):
    _, inputs, projection, facts, envelope = _legacy_case(tmp_path)
    forged_projection, forged_facts, forged_envelope = deepcopy((projection, facts, envelope))
    if mutation in {"plan_sha", "both"}:
        forged_projection["plan_sha256"] = digest("unissued-original-plan")
    if mutation in {"unused_fact_metadata", "both"}:
        for fact in forged_facts:
            fact["unused_metadata"] = "changed-without-changing-financial-amounts"
    forged_envelope["selected_projection_sha256"] = digest(forged_projection)
    forged_envelope["envelope_sha256"] = digest({
        k: v for k, v in forged_envelope.items() if k != "envelope_sha256"})
    with pytest.raises(ValueError):
        selected.select(plan=inputs["plan"], acquisition=inputs["acquisition"],
                        projection=forged_projection, facts=forged_facts)
    with pytest.raises(ValueError, match="selected_financial_unissued_or_changed_legacy_envelope"):
        selected.validate(forged_envelope, projection=forged_projection, facts=forged_facts, bridge=None)
    assert selected.validate(envelope, projection=projection, facts=facts, bridge=None) == envelope


def test_current_content_cannot_become_legacy_by_public_rehash(tmp_path, clock):
    _, parent, inputs, projection, facts, envelope = _current_projection_case(tmp_path)
    forged_plan, forged_acquisition, forged_projection, forged_facts = deepcopy(
        (inputs["plan"], inputs["acquisition"], projection, facts))
    forged_plan["run_id"] = "caller-claimed-historical-plan"
    forged_acquisition["plan_sha256"] = digest(forged_plan)
    forged_projection["plan_sha256"] = digest(forged_plan)
    forged_projection.pop("current_purpose_intake", None)
    for fact in forged_facts:
        fact["unused_metadata"] = "evade-old-global-fact-hash-tombstone"
    forged = deepcopy(envelope)
    forged.update(contract="selected-financial-owner-v1", selected_projection_sha256=digest(forged_projection),
                  selected_acquisition_sha256=digest(forged_acquisition))
    forged.pop("current_parent")
    forged.pop("current_purpose_receipt_sha256")
    forged["envelope_sha256"] = digest({k: v for k, v in forged.items() if k != "envelope_sha256"})
    current.revoke_parent(parent)
    with pytest.raises(ValueError, match="selected_financial_original_project_required"):
        selected.select(plan=forged_plan, acquisition=forged_acquisition,
                        projection=forged_projection, facts=forged_facts)
    with pytest.raises(ValueError, match="selected_financial_unissued_or_changed_legacy_envelope"):
        selected.validate(forged, projection=forged_projection, facts=forged_facts, bridge=None)


@pytest.mark.parametrize("field,value", [
    ("monitored_security", "FORGED"), ("issuer_identity", "0009999999"),
    ("owner_type", "direct_opendart"), ("selected_acquisition_sha256", "e" * 64),
    ("field_completeness", {"caller": "complete"}), ("source_completeness", {"caller": "complete"}),
])
def test_legacy_public_envelope_rehash_does_not_issue_authority(tmp_path, clock, field, value):
    _, _, projection, facts, envelope = _legacy_case(tmp_path)
    forged = deepcopy(envelope)
    forged[field] = value
    forged["envelope_sha256"] = digest({k: v for k, v in forged.items() if k != "envelope_sha256"})
    with pytest.raises(ValueError, match="selected_financial_unissued_or_changed_legacy_envelope"):
        selected.validate(forged, projection=projection, facts=facts, bridge=None)


def test_legacy_validation_replays_original_raw_after_issuance(tmp_path, clock):
    _, inputs, projection, facts, envelope = _legacy_case(tmp_path)
    raw = inputs["directory"] / inputs["receipts"][0]["artifact"]
    raw.write_bytes(raw.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        selected.validate(envelope, projection=projection, facts=facts, bridge=None)


def test_same_issuer_same_raw_date_historical_plan_is_not_current_fact_tombstone(tmp_path, clock):
    owner, historical, historical_projection, historical_facts, historical_envelope = _legacy_case(
        tmp_path / "historical", ticker="SAMEISSUER", run_id="synthetic-same-issuer-history")
    current_owner, doc, security = registered(tmp_path / "current-registration", "SAMEISSUER", "us")
    plan = _plan(doc, security)
    assert plan["run_id"] != historical["plan"]["run_id"]
    assert plan["security"] == historical["plan"]["security"]
    assert plan["cutoff"] == historical["plan"]["cutoff"]
    parent = current.issue_parent(registration_owner=current_owner, plan=plan)
    inputs = capture_for_plan(tmp_path / "current-capture", plan)
    projection = current.project_current(parent, **inputs)
    from app.services.bounded_financial_stock_owner import reported_comparisons
    facts, denied = reported_comparisons(plan, projection)
    assert facts == historical_facts and not denied
    assert [r["raw_sha256"] for r in inputs["receipts"]] == [r["raw_sha256"] for r in historical["receipts"]]
    for revoke in (False, True):
        if revoke:
            current.revoke_parent(parent)
        assert selected.validate(historical_envelope, projection=historical_projection,
                                 facts=historical_facts, bridge=None) == historical_envelope
        assert selected.select(plan=historical["plan"], acquisition=historical["acquisition"],
                               projection=historical_projection, facts=historical_facts) == historical_envelope
        with pytest.raises(ValueError, match="selected_financial_current_route_cannot_downgrade"):
            selected.select(plan=plan, acquisition=inputs["acquisition"], projection=projection, facts=facts)
    prospective.require_generation(owner, "synthetic-same-issuer-history")


def test_original_legacy_bridge_replays_source_owner_and_not_public_json(tmp_path, clock):
    from app.services.bounded_financial_stock_owner import assemble
    from app.services.fresh_financial_stock_owner import fresh_stock_baseline
    from tests.rev9_source_fixtures import bridge_inputs

    inputs, _ = bridge_inputs(tmp_path)
    financial = inputs["financial_inputs"]
    result = assemble(baseline=fresh_stock_baseline(inputs["technical_inputs"]),
                      local_seed=inputs["technical_inputs"]["local_seed"], **financial)
    assert result["status"] == "PASS", result["mandatory_missing"]
    envelope = result["selected_financial_owner"]
    bridge = result["issuer_business_bridge"]
    source_inputs = financial["issuer_business"]["source_inputs"]
    origin = assemble(**source_inputs)
    facts = [f for f in result["packet"]["stocks"][0]["fact_catalog"]
             if f["fact_id"] in envelope["selected_fact_ids"]]
    assert facts and envelope["contract"] == "selected-financial-owner-v1"
    assert envelope["owner_type"] == "issuer_business_bridge"
    assert envelope["field_completeness"]["partial_field_consumption_allowed"]
    assert envelope["unselected_owner_states"][0]["state"] == "UNSELECTED"
    assert selected.validate(envelope, projection=origin["projection"],
                             facts=facts, bridge=bridge) == envelope
    with pytest.raises(ValueError, match="selected_financial_original_issuer_inputs_required"):
        selected.select(plan=financial["plan"], acquisition=financial["acquisition"],
                        projection=result["projection"], facts=facts, bridge=bridge, origin=origin)
    raw = source_inputs["directory"] / source_inputs["receipts"][0]["artifact"]
    raw.write_bytes(raw.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        selected.validate(envelope, projection=origin["projection"], facts=facts, bridge=bridge)


@pytest.mark.parametrize("ticker,market", [("MU", "us"), ("005930", "kr")])
@pytest.mark.parametrize("business", [False, True], ids=["original-fresh", "business-opt-in"])
def test_original_fresh_consumer_reaches_live_current_selected_owner(tmp_path, clock, ticker, market, business):
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from tests.rev8_source_fixtures import fresh_inputs

    # These identities only select the existing technical fixtures; financial
    # parent generality is exercised independently with held-out identities.
    owner, document, security = registered(tmp_path / "registration", ticker, market, {
        "canonical_company_id": "synthetic-issuer-" + ticker,
        "canonical_security_id": "security-" + ticker,
        "exchange": "NASDAQ" if market == "us" else "KRX",
        "issuer_type": "domestic_us" if market == "us" else "domestic_kr",
        "identity_provider": "sec_edgar" if market == "us" else "opendart",
    }, run_id="run")
    clock.value += timedelta(seconds=10)
    inputs = fresh_inputs(tmp_path / "fresh", ticker, security_overrides=security)
    fin = inputs["financial_inputs"]
    assert fin["plan"]["cutoff"] == document["cutoff"]
    parent = current.issue_parent(registration_owner=owner, plan=fin["plan"])
    fin["current_financial_parent"] = parent
    if business:
        inputs.update(reported_comparison_business=True, source_window=dict(
            run_id="run", collection_started_at=AT.isoformat(), source_query_cutoff=AT.isoformat(),
            business_availability_cutoff=clock.value.isoformat()))
    result = assemble_fresh_stock(**inputs)
    assert result["status"] == "PASS", result["mandatory_missing"]
    assert result["mandatory_missing"] == []
    envelope = result["selected_financial_owner"]
    assert envelope["contract"] == "selected-financial-owner-v2"
    assert envelope["current_parent"] == current.resolve_parent(parent, plan=fin["plan"])
    assert envelope["selected_fact_ids"]
    assert result["fresh_run_id"] == "run"
    assert result["complete_source_adapter_qualified"] is False
    if business:
        from app.services.reported_business_projection import projection_for_fact, validate_packet_binding

        packet = result["packet"]
        stock = packet["stocks"][0]
        validate_packet_binding(stock, packet)
        projected = [projection_for_fact(stock, fact, ticker=ticker, packet_id=packet["packet_id"],
                                        assessment_date=packet["assessment_date"], market=market)
                     for fact in stock["fact_catalog"] if fact["fact_id"] in envelope["selected_fact_ids"]]
        assert projected and all(p.kind == "COMPARISON" for p in projected)
        assert all(p.selected_owner_sha256 == envelope["envelope_sha256"] for p in projected)
        assert all(p.recurrence_verified is False and p.security_valuation_transfer is False for p in projected)
    current.revoke_parent(parent)
    with pytest.raises(ValueError, match="current_financial_live_parent_required"):
        assemble_fresh_stock(**inputs)
