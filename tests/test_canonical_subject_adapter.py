"""Single-subject delegation, not source or economic admission fixtures."""
from copy import deepcopy
import pytest
from app.services import canonical_monitoring_source as adapter


def test_existing_whole_source_uses_same_single_subject_boundary(monkeypatch):
    calls = []
    stock = {"ticker": "UNSEEN", "packet": {"generated_at": "frozen"}}
    authority, local = {"owner": "test-double"}, {"local": "test-double"}
    prepared = {"mode": "EVIDENCE_BASED", "untouched": {"value": 1}}
    def owner(s, a):
        calls.append(("owner", deepcopy(s), deepcopy(a)))
    def preflight(s, a, seed, **kw):
        calls.append(("preflight", deepcopy(s), deepcopy(a), deepcopy(seed), kw))
        return {"status": "PASS"}, deepcopy(prepared)
    monkeypatch.setattr(adapter, "source_only_fresh_stock", owner)
    monkeypatch.setattr(adapter, "preflight_subject", preflight)
    direct = adapter.prepare_monitoring_subject(
        stock=stock, authority=authority, local_seed=local, generation="execution")
    single_calls = deepcopy(calls)
    calls.clear()
    whole = {"packets": {"us": {"stocks": {"UNSEEN": stock}}},
             "authority_graph": {"stocks": {"UNSEEN": authority}},
             "authority_graph_sha256": "fixture", "seed": {"parent_run_id": "source"}}
    before = deepcopy(whole)
    result = adapter.prepare_monitoring_source(
        whole=whole, local_seeds={"UNSEEN": local}, valuation_contexts={},
        generation="execution", coverage={}, census={},
        market_projector=lambda *a, **kw: {"unchanged_market": True})
    assert calls == single_calls
    assert result["prepared"]["UNSEEN"] == direct[1] == prepared
    assert result["stocks"]["UNSEEN"] == stock
    assert result["source_generation_id"] == "source"
    assert whole == before
    result["stocks"]["UNSEEN"]["ticker"] = "changed"
    assert stock["ticker"] == "UNSEEN"


@pytest.mark.parametrize(("status", "mode"), [
    ("BLOCKED", "EVIDENCE_BASED"), ("PASS", "UNKNOWN_LIMIT"),
])
def test_single_subject_preserves_strict_economic_preflight(monkeypatch, status, mode):
    monkeypatch.setattr(adapter, "source_only_fresh_stock", lambda *a: None)
    monkeypatch.setattr(adapter, "preflight_subject",
                        lambda *a, **kw: ({"status": status}, {"mode": mode}))
    with pytest.raises(ValueError, match="STRICT_NATIVE_SOURCE_PREFLIGHT_GAP"):
        adapter.prepare_monitoring_subject(stock={"ticker": "UNSEEN", "packet": {"generated_at": "frozen"}},
            authority={}, local_seed={}, generation="execution")


def test_diagnostic_packet_is_not_promoted_to_native_source(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("invalid source reached preflight")
    monkeypatch.setattr(adapter, "preflight_subject", forbidden)
    with pytest.raises(ValueError, match="source_only_fresh_contract_required"):
        adapter.prepare_monitoring_subject(stock={"contract": "lane-source-packet-v1"},
            authority={}, local_seed={}, generation="execution")


def test_owner_denial_propagates_without_fallback(monkeypatch):
    monkeypatch.setattr(adapter, "source_only_fresh_stock", lambda *a: None)
    def denied(*a, **kw):
        raise ValueError("EXACT_SOURCE_USE_DENIED")
    monkeypatch.setattr(adapter, "preflight_subject", denied)
    with pytest.raises(ValueError, match="EXACT_SOURCE_USE_DENIED"):
        adapter.prepare_monitoring_subject(stock={"ticker": "UNSEEN", "packet": {"generated_at": "frozen"}},
            authority={}, local_seed={}, generation="execution")
