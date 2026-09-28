import asyncio
from datetime import date, datetime, timezone
import hashlib
import json

import httpx
import pytest
from pydantic import TypeAdapter

from app.jobs.probe_krx_night_futures import fetch_live_probe
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.krx_night_history_service import persist_krx_response
from app.services.unified_aggregate_receipt import AggregateReceipt, verify_aggregate
from app.services.unified_krx_history_replay import replay_krx_history_aggregate
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts.unified_two_blocker_prequalification import freeze_krx, run
from test_krx_night_futures_probe import _row


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


@pytest.fixture
def original_archive(tmp_path):
    """Portable synthetic mechanics only, never an actual source qualification."""
    archive = tmp_path / "archive"
    history = archive / "private/isolated-data/market/krx-night-history"
    observed = datetime(2026, 9, 2, 23, 10, tzinfo=timezone.utc)
    bodies = {}
    for day in ("2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03"):
        rows = []
        if day != "2026-09-03":
            for product, code, name in (("KOSPI 200 선물", "A016C000", "코스피200 F 202612"),
                                        ("KOSDAQ 150 선물", "A066C000", "코스닥150 F 202612")):
                for session, close in (("정규", "100"), ("야간", "101")):
                    row = _row(product, session, code, name + (" 야간" if session == "야간" else ""),
                        close, day.replace("-", ""), "1" if session == "야간" else None)
                    row.update(TDD_OPNPRC="100", TDD_HGPRC="102", TDD_LWPRC="99")
                    rows.append(row)
        bodies[day] = encoded({"OutBlock_1": rows})
    persist_krx_response(root=history, query_date=date(2026, 8, 31),
        fetched_at=datetime(2026, 9, 1, tzinfo=timezone.utc), http_status=200, raw_body=bodies["2026-08-31"])

    def response(request):
        day = datetime.strptime(request.url.params["basDd"], "%Y%m%d").date().isoformat()
        return httpx.Response(200, content=bodies[day])

    probe = asyncio.run(fetch_live_probe(run_date=date(2026, 9, 3), observation_time=observed,
        api_key="fixture", transport=httpx.MockTransport(response)))
    probe.live_source = True
    write(archive / "source/night-probe.json", {**probe.model_dump(mode="json"), "live_source": True})
    candidate = TypeAdapter(MacroProviderResult).dump_python(
        materialize_night_probe(probe, history_directory=history), mode="json")
    write(archive / "source/night-provider.json", candidate)
    write(archive / "report/source-snapshot-manifest.json", {"generation_id": "synthetic-only"})
    return archive


@pytest.fixture
def frozen(original_archive, tmp_path):
    root = tmp_path / "replay"
    receipt = freeze_krx(original_archive, root, "offline-proof")
    return root, receipt


def replay(frozen):
    root, receipt = frozen
    return asyncio.run(replay_krx_history_aggregate(root=root, receipt=receipt,
        expected_plan_sha256=receipt.plan.sha256))


def rehash_receipt(receipt, **updates):
    fields = {**receipt.model_dump(mode="json", exclude={"aggregate_sha256"}), **updates}
    return AggregateReceipt(**fields, aggregate_sha256=digest(fields))


def change_plan(frozen, change):
    root, receipt = frozen
    plan = json.loads((root / receipt.plan.path).read_bytes())
    change(plan)
    write(root / receipt.plan.path, plan)
    binding = {"path": receipt.plan.path, "sha256": hashlib.sha256((root / receipt.plan.path).read_bytes()).hexdigest()}
    return root, rehash_receipt(receipt, plan=binding)


def test_real_owner_mechanics_deterministic_without_production_storage(frozen, monkeypatch):
    import app.services.krx_night_history_service as owner
    import app.macro.providers.krx as provider
    monkeypatch.setattr(owner, "default_krx_night_history_directory", lambda: pytest.fail("implicit storage"))
    monkeypatch.setattr(provider, "default_krx_night_history_directory", lambda: pytest.fail("implicit storage"))
    result = replay(frozen)
    assert result == replay(frozen)
    assert result["status"] == "PASS" and result["private_storage_removed"]
    assert result["source_child_count"] == 4
    assert result["external_provider_calls"] == 0
    assert not result["complete_source_adapter_qualified"]
    assert [p["product"] for p in result["products"]] == ["KOSPI200"]


def test_historical_graph_cannot_be_used_as_live_aggregate(frozen):
    root, receipt = frozen
    with pytest.raises(ValueError):
        verify_aggregate(root, receipt, cutoff=receipt.received_at,
            policy=UnifiedSourcePolicy(frozenset({"krx_night_futures"})))


@pytest.mark.parametrize("updates", [
    {"basis": "previous_night_close"}, {"provider": "kiwoom_rest"},
    {"session": "2026-09-01"}, {"coverage": {"live_qualified": True}},
    {"acquisition_id": "new-live-cohort"},
])
def test_rehashed_aggregate_identity_cannot_change_authority(frozen, updates):
    root, receipt = frozen
    with pytest.raises(ValueError):
        replay((root, rehash_receipt(receipt, **updates)))


@pytest.mark.parametrize("change", [
    lambda p: p.update(products=["KOSDAQ150"]),
    lambda p: p.update(products=["KOSPI200", "KOSDAQ150", "OTHER"]),
    lambda p: p["children"].append(p["children"][0]),
    lambda p: p["children"].pop(0),
    lambda p: p["children"].reverse(),
    lambda p: p.update(run_id="another-run"),
    lambda p: p.update(source_archive_id="another-archive"),
    lambda p: p.update(session_date="2026-09-01"),
    lambda p: p.update(owner_fingerprint="changed"),
    lambda p: p["children"][0].update(query_date="2026-09-02"),
    lambda p: p.update(observed_at="2026-09-02T20:00:00Z"),
])
def test_frozen_plan_semantic_guards(frozen, change):
    with pytest.raises(ValueError):
        replay(change_plan(frozen, change))


def test_pinned_plan_cannot_be_replaced(frozen):
    root, original = frozen
    _, receipt = change_plan(frozen, lambda p: p.update(run_id="other"))
    with pytest.raises(ValueError, match="frozen_plan_changed"):
        asyncio.run(replay_krx_history_aggregate(root=root, receipt=receipt,
            expected_plan_sha256=original.plan.sha256))


@pytest.mark.parametrize("target", ["body", "receipt", "source_probe", "source_candidate", "source_manifest"])
def test_original_hash_tamper_rejected(frozen, target):
    root, receipt = frozen
    plan = json.loads((root / receipt.plan.path).read_bytes())
    binding = plan["children"][0][target] if target in {"body", "receipt"} else plan[target]
    (root / binding["path"]).write_bytes(b"{}")
    with pytest.raises(ValueError, match="hash_mismatch"):
        replay(frozen)


def test_candidate_rehashed_numeric_tamper_still_fails(frozen):
    root, receipt = frozen
    candidate = json.loads((root / receipt.artifact).read_bytes())
    candidate["observations"][0]["value"] += 1
    write(root / receipt.artifact, candidate)
    mutated = rehash_receipt(receipt, artifact_sha256=hashlib.sha256((root / receipt.artifact).read_bytes()).hexdigest(),
        normalized_sha256=digest(candidate))
    with pytest.raises(ValueError, match="expected_projection_mismatch"):
        replay((root, mutated))


def test_missing_body_fails(frozen):
    root, receipt = frozen
    plan = json.loads((root / receipt.plan.path).read_bytes())
    (root / plan["children"][0]["body"]["path"]).unlink()
    with pytest.raises(ValueError, match="artifact_missing"):
        replay(frozen)


def test_stock_original_absence_never_promotes_synthetic_night_success(original_archive, tmp_path):
    output = tmp_path / "proof"
    result = run(original_archive, output)
    assert result["blockers"] == ["STOCK_MATERIALIZATION"]
    assert not result["NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED"]
    assert result["R2B"] == "NOT_GENERATED_NOT_EXECUTED"
    inventory = json.loads((output / "stock-source-inventory.json").read_bytes())
    assert len(inventory["subjects"]) == 22 and inventory["missing_role_bindings"] == 88
    assert all(not s["stock_packet_generated"] for s in inventory["subjects"])


def test_no_price_response_reconstruction_from_old_packets(original_archive, tmp_path):
    write(original_archive / "private/current-packets/us.json", {"stocks": [{"ticker": "IBM",
        "assessment": {"price": 42}, "technical_context": {"raw_bar_fingerprint": "old"}}]})
    output = tmp_path / "proof"
    run(original_archive, output)
    assert json.loads((output / "stock-source-inventory.json").read_bytes())["standalone_original_ohlcv_candidates"] == []
