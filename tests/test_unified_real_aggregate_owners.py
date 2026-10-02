"""Real normalizers; synthetic transport mechanics, never current source proof."""

import asyncio
from dataclasses import replace
from datetime import datetime
import hashlib
import json

from pydantic import TypeAdapter
import pytest

from app.macro.providers.base import MacroProviderResult
from app.macro.providers.market import OhlcvMarketProvider
from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
from app.services.unified_aggregate_receipt import AggregateReceipt, verify_aggregate
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import A, SourceInput, SourceRole, _resolve
from app.services.unified_source_policy import UnifiedSourcePolicy
from test_unified_owner_interfaces import market_observer, market_transport, kr_service, US_CUTOFF
from test_kiwoom_rest_market_context import OBSERVED_AT, SESSION_DATE


def clock(monkeypatch, at):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    monkeypatch.setattr("app.services.unified_source_observer.datetime", Clock)
    monkeypatch.setattr("app.services.unified_kiwoom_observer.datetime", Clock)


def binding(root, path):
    return {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}


def aggregate(root, role, normalized, at):
    plan = json.loads((root / "plan.json").read_bytes())
    children = []
    for path in sorted(root.glob("*.response.json")):
        stem = path.name.removesuffix(".response.json")
        norm, page = stem + ".normalization.json", stem + ".page.json"
        children.append({"child_id": stem, "receipt": binding(root, path.name),
            "normalization": binding(root, norm) if (root / norm).exists() else None,
            "accepted_page": binding(root, page) if (root / page).exists() else None})
    durable_json(root / "aggregate-value.json", normalized)
    value = {"owner": role.owner, "role": role.key, "market": role.market, "provider": role.provider,
        "symbol": role.symbol, "basis": role.basis, "session": role.session,
        "run_id": plan["run_id"], "attempt_id": plan["attempt_id"], "acquisition_id": None,
        "acquisition_class": A.value, "requested_at": at.isoformat(), "received_at": at.isoformat(),
        "artifact": "aggregate-value.json", "artifact_sha256": binding(root, "aggregate-value.json")["sha256"],
        "plan": binding(root, "plan.json"), "children": children,
        "expected_child_ids": [c["child_id"] for c in children], "normalized_sha256": digest(normalized),
        "validator_contract": "real-owner-synthetic-transport", "coverage": {"fixture_only": True},
        "contract": "unified-transitive-source-receipt-v1"}
    return AggregateReceipt.model_validate({**value, "aggregate_sha256": digest(value)})


def us_fixture(tmp_path, monkeypatch):
    clock(monkeypatch, US_CUTOFF)
    root = tmp_path / "us"
    observer = market_observer(root)
    provider = OhlcvMarketProvider(market_transport([]), source_observer=observer)
    result = asyncio.run(provider.collect(US_CUTOFF))
    role = SourceRole(key="us_market_prices", owner="us_market", market="us", symbol="*",
        provider="ohlcv_analyst", basis="adjusted_close", session="2026-08-25",
        acquisition_class=A, mandatory=True)
    receipt = aggregate(root, role, TypeAdapter(MacroProviderResult).dump_python(result, mode="json"), US_CUTOFF)
    policy = UnifiedSourcePolicy(frozenset({role.provider}))
    owner = us_market_aggregate_owner(role=role, source_url=provider.settings.ohlcv_base_url.rstrip('/') + '/ohlcv',
                                     policy=policy)
    graph = verify_aggregate(root, receipt, policy=policy, cutoff=US_CUTOFF)
    return root, role, receipt, policy, owner, graph


def test_us_real_child_normalizer_installed_in_composition(tmp_path, monkeypatch):
    root, role, receipt, policy, owner, graph = us_fixture(tmp_path, monkeypatch)
    replay = owner.project_aggregate_and_validate(graph, US_CUTOFF)
    assert digest(replay.value) == receipt.normalized_sha256
    assert replay == owner.project_aggregate_and_validate(graph, US_CUTOFF)
    durable_json(root / "aggregate.json", receipt.model_dump(mode="json"))
    item = SourceInput(role=role.key, run_id=receipt.run_id, attempt_id=receipt.attempt_id,
        acquisition_class=A, requested_at=US_CUTOFF, received_at=US_CUTOFF,
        artifact=receipt.artifact, artifact_sha256=receipt.artifact_sha256,
        receipt_artifact="aggregate.json", receipt_sha256=binding(root, "aggregate.json")["sha256"])
    resolved = _resolve(item, role, root=root, run_id=receipt.run_id, start=US_CUTOFF, cutoff=US_CUTOFF,
        attempt_id=receipt.attempt_id, policy=policy, owners={role.owner: owner})
    assert resolved["value_sha256"] == receipt.normalized_sha256


@pytest.mark.parametrize("case", ["plan", "missing", "extra", "order", "identity", "stale", "currency_basis"])
def test_us_callback_rejects_child_and_plan_errors(tmp_path, monkeypatch, case):
    _, _, _, _, owner, graph = us_fixture(tmp_path, monkeypatch)
    if case == "plan":
        plan = json.loads(graph.plan)
        plan["reads"].pop()
        graph = replace(graph, plan=json.dumps(plan).encode())
    elif case == "missing":
        graph = replace(graph, child_bodies=graph.child_bodies[:-1])
    elif case == "extra":
        graph = replace(graph, child_bodies=(*graph.child_bodies, graph.child_bodies[0]))
    elif case == "order":
        graph = replace(graph, child_receipts=tuple(reversed(graph.child_receipts)))
    else:
        body = json.loads(graph.child_bodies[0])
        if case == "identity":
            body["resolved_symbol"]["code"] = "OTHER"
        elif case == "stale":
            body["periods"]["daily"][0]["date"] = "2026-08-24"
        else:
            body["meta"]["adjusted"] = False
        graph = replace(graph, child_bodies=(json.dumps(body).encode(), *graph.child_bodies[1:]))
    with pytest.raises(ValueError):
        owner.project_aggregate_and_validate(graph, US_CUTOFF)


def test_us_callback_does_not_read_normalized_candidate(tmp_path, monkeypatch):
    _, _, receipt, _, owner, graph = us_fixture(tmp_path, monkeypatch)
    graph = replace(graph, normalized=b'{"caller_value": 999}')
    assert digest(owner.project_aggregate_and_validate(graph, US_CUTOFF).value) == receipt.normalized_sha256


@pytest.mark.parametrize("family", ["kr_local_indices_sectors_breadth", "kr_market_investor_flows"])
def test_kiwoom_whole_page_real_owner_replay(tmp_path, monkeypatch, family):
    clock(monkeypatch, OBSERVED_AT)
    root = tmp_path / "A"
    service, _ = kr_service(root)
    asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
    normalization = json.loads((root / "normalization.json").read_bytes())
    role = SourceRole(key=family, owner="kiwoom_pages", market="kr", symbol="*",
        provider="kiwoom_rest", basis="query_time", session=str(SESSION_DATE),
        acquisition_class=A, mandatory=family == "kr_local_indices_sectors_breadth")
    receipt = aggregate(root, role, normalization["roles"][family]["value"], OBSERVED_AT)
    policy = UnifiedSourcePolicy(frozenset({role.provider}))
    graph = verify_aggregate(root, receipt, policy=policy, cutoff=OBSERVED_AT)
    owner = kiwoom_aggregate_owner(role=role, observed_at=OBSERVED_AT, max_pages=5,
                                   max_requests_per_page=1, policy=policy)
    value = owner.project_aggregate_and_validate(graph, OBSERVED_AT)
    assert digest(value.value) == receipt.normalized_sha256
    assert value == owner.project_aggregate_and_validate(graph, OBSERVED_AT)
    with pytest.raises(ValueError, match="page_artifacts"):
        owner.project_aggregate_and_validate(replace(graph, accepted_pages=()), OBSERVED_AT)
