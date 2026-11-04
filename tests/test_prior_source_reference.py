"""Synthetic immutable archive replay, with original receipts unchanged."""

from datetime import datetime, timezone
from hashlib import sha256
import zipfile

import pytest

from app.services import prior_source_reference as p
from app.services.unified_snapshot_contract import encoded
from test_unified_stock_acquisition import fixture_receipt, plan as source_plan


@pytest.fixture
def plan():
    return source_plan.__wrapped__()


def archive(tmp_path, plan, mutate=None):
    receipt = fixture_receipt(plan, tmp_path)
    receipt["pages"][0]["response_continuation"] = {"cont_yn": "N", "next_key": ""}
    if mutate:
        mutate(receipt)
    logical = {
        "plan.json": encoded(
            {"generation_id": plan.run_id, "stock_plan": plan.model_dump(mode="json")}
        ),
        "receipt.json": encoded(receipt),
        "page.body": (tmp_path / "page.body").read_bytes(),
        "bars.json": (tmp_path / "bars.json").read_bytes(),
    }
    entries, mapping = {}, {}
    for name, raw in logical.items():
        pin = sha256(raw).hexdigest()
        entries["blobs/" + pin] = raw
        mapping[name] = dict(blob="blobs/" + pin, bytes=len(raw), sha256=pin)
    entries["map.json"] = encoded(
        dict(contract="exact-byte-content-addressed-evidence-v1", files=mapping)
    )
    manifest = encoded(
        dict(
            files={n: dict(bytes=len(r), sha256=sha256(r).hexdigest()) for n, r in entries.items()}
        )
    )
    path = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(path, "w") as z:
        for n, r in entries.items():
            z.writestr(n, r)
        z.writestr("manifest.json", manifest)
    store = p.open_prior_store(
        archive=path,
        archive_sha256=sha256(path.read_bytes()).hexdigest(),
        manifest_sha256=sha256(manifest).hexdigest(),
        content_map_member="map.json",
    )
    return store, receipt


def replay(store, plan):
    return p.replay_stock_reference(
        store=store,
        plan_member="plan.json",
        receipt_member="receipt.json",
        entry_id=plan.reads[0].entry_id,
    )


def request(plan):
    r = plan.reads[0]
    return dict(
        consumer_generation="NEW",
        cutoff=datetime(2026, 9, 27, tzinfo=timezone.utc),
        security_id=r.canonical_security_id,
        market=r.market,
        session=r.latest_completed_session,
        role=r.role,
        consumer="CORE",
        use_axis="CORE_DIRECTION",
    )


def test_replay_is_not_current_acquisition(plan, tmp_path):
    store, receipt = archive(tmp_path, plan)
    ref, identity = replay(store, plan)
    assert identity["origin_generation"] == plan.run_id
    assert identity["original_receipt_sha256"] == sha256(encoded(receipt)).hexdigest()
    decision = p.classify_stock_use(ref, **request(plan))
    assert decision["decision"] == "FRESH_WINDOW_REQUIRED"
    assert decision["D02"] == "NOT_GRANTED"
    assert decision["current_required_acquisition"] == "NOT_SATISFIED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", "OTHER"),
        ("acquisition_id", "OTHER"),
        ("plan_sha256", "0" * 64),
        ("normalized_sha256", "0" * 64),
        ("status", "FAILED"),
    ],
)
def test_new_archive_hash_does_not_replace_original_owner(plan, tmp_path, field, value):
    store, _ = archive(tmp_path, plan, lambda r: r.update({field: value}))
    with pytest.raises(ValueError):
        replay(store, plan)


@pytest.mark.parametrize(
    "field,value",
    [
        ("consumer_generation", "run"),
        ("security_id", "WRONG"),
        ("market", "kr"),
        ("session", "2026-09-28"),
        ("role", "unadjusted_weekly_valuation"),
        ("purpose", "SCHEDULED"),
        ("cutoff", datetime(2026, 9, 25, tzinfo=timezone.utc)),
    ],
)
def test_cross_generation_use_denials(plan, tmp_path, field, value):
    store, _ = archive(tmp_path, plan)
    ref, _ = replay(store, plan)
    req = request(plan)
    req[field] = value
    with pytest.raises(ValueError):
        p.classify_stock_use(ref, **req)


def test_json_or_revoked_reference_has_no_live_authority(plan, tmp_path):
    store, _ = archive(tmp_path, plan)
    ref, identity = replay(store, plan)
    for forged in (identity, p.StockReference()):
        with pytest.raises(ValueError):
            p.classify_stock_use(forged, **request(plan))
    p.revoke_prior_store(store)
    with pytest.raises(ValueError):
        p.classify_stock_use(ref, **request(plan))


def test_malformed_original_raw_not_current_rights(plan, tmp_path):
    def mutate(r):
        r["pages"][0]["request"]["payload"]["stk_cd"] = "OTHER"

    store, _ = archive(tmp_path, plan, mutate)
    with pytest.raises(ValueError):
        replay(store, plan)


def test_historical_chart_requires_separate_use_policy(plan, tmp_path):
    store, _ = archive(tmp_path, plan)
    ref, _ = replay(store, plan)
    req = request(plan)
    req.update(consumer="TECHNICAL_CONTEXT", use_axis="HISTORICAL_CHART_CONTEXT")
    result = p.classify_stock_use(ref, **req)
    assert result["decision"] == "DENIED"
    assert result["reason"] == "HISTORICAL_CHART_REUSE_POLICY_AND_CORRECTION_AUTHORITY_REQUIRED"
    assert result["current_required_acquisition"] == "NOT_SATISFIED"
