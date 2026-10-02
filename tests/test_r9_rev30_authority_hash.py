from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts import m12da_source_use_contract as source
from scripts import r2b_r2_contract as consumer


def inputs(monkeypatch, payload):
    ref = "source:business"
    metadata = [dict(ref_id=ref, category="thesis", label="business",
                     as_of="2026-09-01", statement="Frozen evidence.")]
    view = dict(ticker="FICTIONAL", ownership={},
                evidence_packet=dict(ticker="FICTIONAL", evidence=metadata))
    monkeypatch.setattr(consumer, "OwnedEvidencePacket", SimpleNamespace(
        model_validate=lambda _: SimpleNamespace(core_refs=[ref], timing_refs=[])))
    context = dict(evidence_packets=[view["evidence_packet"]], evidence_ownership=[
        dict(ticker="FICTIONAL", core_ref_ids=[ref], timing_ref_ids=[])])
    catalog = consumer.build_subject_catalog(context=context, ticker="FICTIONAL", atomic_claims=[])
    authority = source.build_trusted_source_authority_manifest(ticker="FICTIONAL",
        source_generation_id="source-one", catalog=catalog, source_metadata=metadata)
    authority["source_note"] = payload
    authority.pop("authority_manifest_sha256")
    authority["authority_manifest_sha256"] = source.canonical_sha256(authority)
    return view, authority


def consume(view, authority):
    return consumer.bound_chain(view, dict(authority=authority), atomic=[],
        generation="execution-one", source_generation="source-one",
        view_receipt=dict(receipt_sha256="a" * 64))[2]


PAYLOADS = [
    {"z": [None, True, False, 0, -1, 1.25], "a": {"text": "ASCII"}},
    {"title": "Issuer\u2019s results"},
    {"title": "\ud55c\uae00 \uc2e4\uc801"},
    {"title": "Symbol \U0001f680"},
    {"nested": [{"mix": "ASCII \u2019 \ud55c\uae00 \U0001f680"}, None, True, 2.5]},
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_producer_original_and_derivative_authority_match_without_mutation(monkeypatch, payload):
    view, authority = inputs(monkeypatch, payload)
    before = deepcopy(authority)
    chain = consume(view, authority)
    assert authority == before
    assert chain["validation"]["status"] == "PASS"
    assert chain["authority"]["source_note"] == payload
    for manifest in (authority, chain["authority"]):
        content = {k: v for k, v in manifest.items() if k != "authority_manifest_sha256"}
        expected = hashlib.sha256(json.dumps(
            content, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        assert manifest["authority_manifest_sha256"] == source.canonical_sha256(content) == expected
        if payload == PAYLOADS[0]:
            assert consumer.digest(content) == expected
        else:
            assert consumer.digest(content) != expected


@pytest.mark.parametrize("payload", PAYLOADS)
def test_semantic_key_order_stable_and_list_order_not_rewritten(monkeypatch, payload):
    view, authority = inputs(monkeypatch, payload)
    reordered = dict(reversed(list(authority.items())))
    assert consume(view, reordered) == consume(view, authority)
    assert source.canonical_sha256({"a": 1, "b": [True, None]}) == source.canonical_sha256(
        {"b": [True, None], "a": 1})
    assert source.canonical_sha256([True, None]) != source.canonical_sha256([None, True])


@pytest.mark.parametrize("mutation", ["content", "stored_hash", "punctuation", "normalization"])
def test_bound_consumer_rejects_changed_content_or_stored_hash(monkeypatch, mutation):
    view, authority = inputs(monkeypatch, {"title": "Issuer\u2019s e\u0301"})
    if mutation == "stored_hash":
        authority["authority_manifest_sha256"] = "0" * 64
    elif mutation == "punctuation":
        authority["source_note"]["title"] = "Issuer's e\u0301"
    elif mutation == "normalization":
        authority["source_note"]["title"] = "Issuer\u2019s \u00e9"
    else:
        authority["source_note"]["extra"] = True
    with pytest.raises(ValueError, match="^authority_hash$"):
        consume(view, authority)


def test_alternate_unicode_encoder_is_not_an_accepted_authority_hash(monkeypatch):
    view, authority = inputs(monkeypatch, PAYLOADS[1])
    content = {k: v for k, v in authority.items() if k != "authority_manifest_sha256"}
    authority["authority_manifest_sha256"] = consumer.digest(content)
    with pytest.raises(ValueError, match="^authority_hash$"):
        consume(view, authority)


def test_unrelated_generic_snapshot_digest_remains_utf8_and_strict():
    payload = {"text": "\ud55c\uae00\u2019\U0001f680", "nested": [True, None, 1.25]}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    assert consumer.digest(payload) == hashlib.sha256(raw).hexdigest()
    assert consumer.digest(payload) != source.canonical_sha256(payload)
    with pytest.raises(ValueError):
        consumer.digest({"nonfinite": float("nan")})
