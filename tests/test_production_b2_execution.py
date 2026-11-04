import asyncio
from copy import deepcopy
import json

import pytest

from app.services.production_b2_execution import (
    ModelTransportError, SemanticReject, authorize_b2, execute_b2, verify_authorization,
)
from app.services.unified_snapshot_contract import digest
from scripts import newbuyer_b2_v2_shadow as canonical
from scripts import newbuyer_b2_contract as v1
from tests.test_newbuyer_b2_v2 import inputs, outputs


def request_and_auth(**kwargs):
    data = inputs(**kwargs)
    sub = data["v1_request"]["subject"]
    sub["frozen_authority"] = {k: digest(k) for k in ("core", "pass_a", "accepted_b", "context")}
    data["v1_request"]["output_schema"] = v1.output_schema(sub)
    data["v1_request"]["request_sha256"] = digest({k: v for k, v in data["v1_request"].items() if k != "request_sha256"})
    request = canonical.build_request(**data)
    binding = dict(generation_id=sub["source_generation_id"], source_envelope_sha256=digest("source-envelope"),
        owner_sha256=digest("current-owner"), core_sha256=digest("core"), pass_a_sha256=digest("pass_a"),
        pass_b_sha256=digest("accepted_b"))
    auth = authorize_b2(request, **binding)
    return request, auth, binding


class Transport:
    def __init__(self, items):
        self.items = iter(items)
        self.calls = []

    async def request(self, payload, **kwargs):
        self.calls.append((deepcopy(payload), kwargs))
        item = next(self.items)
        if isinstance(item, Exception):
            raise item
        return item


def body(request, index=0):
    return json.dumps({"new_buyer_shadow": outputs(request)[index]}).encode()


def test_current_authorization_detached_and_shadow_flags_unchanged(tmp_path):
    request, auth, binding = request_and_auth(timing="WAIT_FOR_ZONE")
    before = deepcopy(request)
    transport = Transport([body(request)])
    result = asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert result["status"] == "PASS"
    assert request == before
    assert request["shadow_only"] is True and request["dispatch_authorized"] is False
    assert transport.calls[0][0] == canonical.provider_payload(request, expected_request_sha256=auth.request_sha256)
    assert transport.calls[0][1] == dict(model="gpt-5.6-sol", effort="xhigh", timeout=600)
    assert "PRODUCTION_MONITORING" not in json.dumps(transport.calls[0][0])
    assert (tmp_path / "attempt-1/response.raw").read_bytes() == body(request)


@pytest.mark.parametrize("error", [ModelTransportError("offline"), TimeoutError(), b"not json", b"{}"])
def test_transport_form_retry_identical_request(tmp_path, error):
    request, auth, binding = request_and_auth()
    transport = Transport([error, body(request)])
    result = asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert len(result["attempts"]) == 2
    assert transport.calls[0] == transport.calls[1]
    assert result["semantic_retries"] == 0


def test_valid_wire_semantic_failure_not_retried(tmp_path):
    request, auth, binding = request_and_auth()
    item = next(r for r in outputs(request) if r["reason_class"] == "VALUATION_NEUTRAL")
    # Each ref is schema-eligible, but the exact semantic set must match.
    item["reason_evidence_refs"] = ["valuation:PER"]
    item["valuation_context"]["valuation_evidence_refs"] = ["valuation:FORWARD_PE"]
    raw = json.dumps({"new_buyer_shadow": item}).encode()
    transport = Transport([raw, body(request)])
    with pytest.raises(SemanticReject):
        asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert len(transport.calls) == 1
    assert json.loads((tmp_path / "attempt-1/receipt.json").read_bytes())["classification"] == "SEMANTIC_REJECT"


@pytest.mark.parametrize("field", ["generation_id", "source_envelope_sha256", "owner_sha256", "core_sha256", "pass_a_sha256", "pass_b_sha256"])
def test_old_authority_denied_before_transport(field):
    request, auth, binding = request_and_auth()
    binding[field] = digest("different")
    with pytest.raises(ValueError):
        verify_authorization(request, auth, **binding)


def test_total_form_budget_bounded(tmp_path):
    request, auth, binding = request_and_auth()
    transport = Transport([b"{}"] * 4)
    with pytest.raises(ModelTransportError, match="budget"):
        asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert len(transport.calls) == 3


@pytest.mark.parametrize("kwargs", [dict(risk=True), dict(denied=("PER",)), dict(denied=("PER", "FORWARD_PE")), dict(timing="WAIT_FOR_ZONE")])
def test_canonical_economics_preserved(tmp_path, kwargs):
    request, auth, binding = request_and_auth(**kwargs)
    result = asyncio.run(execute_b2(request, auth, current_binding=binding, transport=Transport([body(request)]), directory=tmp_path))
    assert canonical.validate_result(result["output"], request, expected_request_sha256=auth.request_sha256)["status"] == "PASS"
    assert result["output"]["new_buyer_shadow"] == outputs(request)[0]
