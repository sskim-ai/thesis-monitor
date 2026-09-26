from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from app.services.unified_aggregate_receipt import AggregateReceipt, verify_aggregate
from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import A, B, OwnerAdapter, OwnerProjection, SourceInput, SourceRole, _resolve
from app.services.unified_source_policy import UnifiedSourcePolicy


NOW = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({"kiwoom_rest"}))


def binding(root, path):
    return {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}


def fixture(root, *, cls=A):
    root.mkdir()
    identity = {"run_id": "fixture", "attempt_id": "A" if cls == A else None,
                "acquisition_id": "once" if cls == B else None, "acquisition_class": cls.value}
    durable_json(root / "plan.json", {**identity, "required_read_keys": ["page-set"], "required_pages": 2})
    children = []
    for ordinal in (1, 2):
        name = f"read-{ordinal}"
        body = json.dumps({"values": [ordinal]}).encode()
        durable_bytes(root / (name + ".body"), body)
        request = {"page": ordinal, "continuation": ordinal > 1,
                   "cursor_sha256": hashlib.sha256(("cursor" if ordinal > 1 else "").encode()).hexdigest()}
        receipt = {**identity, "provider": "kiwoom_rest", "ordinal": ordinal,
            "requested_at": NOW.isoformat(), "received_at": NOW.isoformat(),
            "request": request, "request_sha256": digest(request), "read_key": "page-set",
            "outcome": "HTTP_RESPONSE", "http_status": 200, "artifact": name + ".body",
            "artifact_sha256": hashlib.sha256(body).hexdigest()}
        durable_json(root / (name + ".json"), receipt)
        durable_json(root / (name + ".page.json"), {"response_receipt_sha256": digest(receipt),
            "raw_sha256": receipt["artifact_sha256"], "page": ordinal, "continuation": ordinal == 1,
            "next_cursor_sha256": hashlib.sha256(("cursor" if ordinal == 1 else "").encode()).hexdigest()})
        durable_json(root / (name + ".norm.json"), {"response_receipt_sha256": digest(receipt),
            "normalized": ordinal, "normalized_sha256": digest(ordinal)})
        children.append({"child_id": name, "receipt": binding(root, name + ".json"),
                         "accepted_page": binding(root, name + ".page.json"),
                         "normalization": binding(root, name + ".norm.json")})
    durable_json(root / "result.json", [1, 2])
    value = {**identity, "contract": "unified-transitive-source-receipt-v1", "owner": "fixture-owner",
        "role": "fixture-role", "market": "kr", "symbol": "fixture-symbol", "provider": "kiwoom_rest",
        "basis": "fixture-basis", "session": "2026-08-25", "requested_at": NOW.isoformat(),
        "received_at": NOW.isoformat(), "artifact": "result.json",
        "artifact_sha256": binding(root, "result.json")["sha256"], "plan": binding(root, "plan.json"),
        "expected_child_ids": ["read-1", "read-2"], "children": children,
        "normalized_sha256": digest([1, 2]), "validator_contract": "fixture-not-production",
        "coverage": {"pages": 2, "fixture_kind": "SYNTHETIC_INTERFACE_MECHANICS"}}
    return value


def sealed(value):
    return AggregateReceipt.model_validate({**value, "aggregate_sha256": digest(value)})


@pytest.mark.parametrize("cls", [A, B])
def test_transitive_class_a_b_graph_has_deterministic_hash(tmp_path, cls):
    root = tmp_path / "graph"
    value = fixture(root, cls=cls)
    result = verify_aggregate(root, sealed(value), policy=POLICY, cutoff=NOW)
    assert len(result.child_receipts) == 2
    assert [json.loads(b)["values"][0] for b in result.child_bodies] == [1, 2]
    assert sealed(value).aggregate_sha256 == sealed(deepcopy(value)).aggregate_sha256


@pytest.mark.parametrize("case", ["missing", "extra", "duplicate", "order", "run", "attempt",
    "raw", "normalized", "prohibited", "cursor", "incomplete", "plan"])
def test_transitive_negatives(tmp_path, case):
    root = tmp_path / "graph"
    value = fixture(root)
    if case == "missing":
        value["children"].pop()
    elif case == "extra":
        value["children"].append({**value["children"][0], "child_id": "unexpected"})
    elif case == "duplicate":
        value["children"][1] = value["children"][0]
    elif case == "order":
        value["children"].reverse()
    elif case == "raw":
        (root / "read-1.body").write_bytes(b"tampered")
    elif case == "normalized":
        path = root / "read-1.norm.json"
        row = json.loads(path.read_bytes())
        row["normalized"] = 7
        durable_json(path, row)
        value["children"][0]["normalization"] = binding(root, path.name)
    elif case in {"cursor", "incomplete"}:
        path = root / "read-2.page.json"
        row = json.loads(path.read_bytes())
        row["page"] = 9 if case == "cursor" else 2
        row["continuation"] = case == "incomplete"
        durable_json(path, row)
        value["children"][1]["accepted_page"] = binding(root, path.name)
    elif case == "plan":
        durable_json(root / "plan.json", {"run_id": "other"})
        value["plan"] = binding(root, "plan.json")
    else:
        path = root / "read-1.json"
        row = json.loads(path.read_bytes())
        row[{"run": "run_id", "attempt": "attempt_id", "prohibited": "provider"}[case]] = (
            "alpha_vantage" if case == "prohibited" else "another")
        durable_json(path, row)
        value["children"][0]["receipt"] = binding(root, path.name)
    with pytest.raises(ValueError):
        verify_aggregate(root, sealed(value), policy=POLICY, cutoff=NOW)


def test_composition_requires_independent_owner_renormalization(tmp_path):
    root = tmp_path / "graph"
    value = fixture(root)
    receipt = sealed(value)
    durable_json(root / "aggregate.json", receipt.model_dump(mode="json"))
    item = SourceInput(role="fixture-role", run_id="fixture", acquisition_class=A, attempt_id="A",
        requested_at=NOW, received_at=NOW, artifact="result.json", artifact_sha256=value["artifact_sha256"],
        receipt_artifact="aggregate.json", receipt_sha256=binding(root, "aggregate.json")["sha256"])
    role = SourceRole(key="fixture-role", owner="fixture-owner", market="kr", symbol="fixture-symbol",
        acquisition_class=A, mandatory=True, provider="kiwoom_rest", basis="fixture-basis", session="2026-08-25")
    def projection(numbers):
        return OwnerProjection(numbers, role.provider, role.market, role.symbol, role.basis, role.session,
                               True, None, NOW)
    def replay(graph, cutoff):
        assert json.loads(graph.plan)["required_pages"] == len(graph.child_bodies) == 2
        return projection([json.loads(body)["values"][0] for body in graph.child_bodies])
    args = dict(root=root, run_id="fixture", start=NOW - timedelta(seconds=1), cutoff=NOW,
                attempt_id="A", policy=POLICY)
    with pytest.raises(ValueError, match="replay_not_qualified"):
        _resolve(item, role, owners={"fixture-owner": OwnerAdapter("test", "f" * 64,
            lambda *_: pytest.fail("single HTTP owner must not be invoked"))}, **args)
    owners = {"fixture-owner": OwnerAdapter("test", "f" * 64, lambda *_: None, replay)}
    assert _resolve(item, role, owners=owners, **args)["value"] == [1, 2]
    owners["fixture-owner"] = OwnerAdapter("test", "f" * 64, lambda *_: None, lambda *_: projection([3]))
    with pytest.raises(ValueError, match="not_child_derived"):
        _resolve(item, role, owners=owners, **args)
