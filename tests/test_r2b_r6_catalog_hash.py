from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts import r2b_r2_contract as c
from scripts import m12da_source_use_contract as source


def fixture(monkeypatch, text):
    ref = 'source:business'
    metadata = [dict(ref_id=ref, category='thesis', label='business',
                     as_of='2026-09-01', statement='Frozen evidence.')]
    view = dict(ticker='FICTIONAL', ownership={},
                evidence_packet=dict(ticker='FICTIONAL', evidence=metadata))
    monkeypatch.setattr(c, 'OwnedEvidencePacket', SimpleNamespace(
        model_validate=lambda _: SimpleNamespace(core_refs=[ref], timing_refs=[])))
    atomic = [dict(ticker='FICTIONAL', claim_ref='claim:one',
        claim=dict(text=text, polarity='BULLISH', reason_role='FUNDAMENTAL', logical_condition=None),
        parent_source_refs=[ref])]
    context = dict(evidence_packets=[view['evidence_packet']], evidence_ownership=[
        dict(ticker='FICTIONAL', core_ref_ids=[ref], timing_ref_ids=[])])
    initial = c.build_subject_catalog(context=context, ticker='FICTIONAL', atomic_claims=[])
    authority = source.build_trusted_source_authority_manifest(ticker='FICTIONAL',
        source_generation_id='source-one', catalog=initial, source_metadata=metadata)
    assert authority['status'] == 'PASS'
    catalog, rows, chain = c.bound_chain(view, dict(authority=authority), atomic=atomic,
        generation='execution-one', source_generation='source-one',
        view_receipt=dict(receipt_sha256='a' * 64))
    return catalog, rows, chain


@pytest.mark.parametrize('text', ['ASCII claim.', '\uc601\uc5c5\ud604\uae08 \uac80\uc99d',
    'FCF \uc601\uc5c5\ud604\uae08 USD', '\u73fe\u91d1 \u0394 \u20ac',
    'e\u0301 \u00e9 \u2014 \uac00'])
def test_bound_chain_uses_contract_canonical_hash_without_text_change(monkeypatch, text):
    catalog, _, chain = fixture(monkeypatch, text)
    expected = source.canonical_sha256(catalog)
    assert chain['authority']['catalog_sha256'] == expected
    assert chain['expectation']['catalog_sha256'] == expected
    assert chain['projection']['catalog_sha256'] == expected
    assert chain['validation']['status'] == 'PASS'
    assert catalog['atomic_claims'][0]['claim']['text'] == text


def test_escape_and_key_order_converge_but_meaningful_array_order_does_not(monkeypatch):
    catalog, _, _ = fixture(monkeypatch, '\ud55c\uae00 Latin \u0394')
    escaped = json.loads(json.dumps(catalog, ensure_ascii=True))
    unescaped = json.loads(json.dumps(catalog, ensure_ascii=False))
    reversed_keys = dict(reversed(list(catalog.items())))
    assert escaped == unescaped == catalog
    assert source.canonical_sha256(escaped) == source.canonical_sha256(unescaped)
    assert source.canonical_sha256(catalog) == source.canonical_sha256(reversed_keys)
    second = deepcopy(catalog['atomic_claims'][0])
    second['claim_ref'] = 'claim:two'
    original = dict(catalog, atomic_claims=[catalog['atomic_claims'][0], second])
    changed = dict(catalog, atomic_claims=original['atomic_claims'][::-1])
    assert source.canonical_sha256(original) != source.canonical_sha256(changed)


@pytest.mark.parametrize('kind', ['text', 'value', 'ref'])
def test_tampered_catalog_rejected_by_frozen_expectation(monkeypatch, kind):
    catalog, metadata, chain = fixture(monkeypatch, '\ud55c\uae00 claim')
    tampered = deepcopy(catalog)
    claim = tampered['atomic_claims'][0]
    if kind == 'text':
        claim['claim']['text'] += ' changed'
    elif kind == 'value':
        tampered['entry_catalog']['current_price'] = {'value': 999, 'currency': 'USD'}
    else:
        claim['parent_source_refs'] = ['source:wrong']
    assert source.canonical_sha256(catalog) != source.canonical_sha256(tampered)
    with pytest.raises(ValueError, match='source_input_expectation_authority_catalog_mismatch'):
        source.freeze_source_use_input_expectation(ticker='FICTIONAL',
            source_generation_id='source-one', execution_generation_id='execution-one',
            catalog=tampered, source_metadata=metadata, authority_manifest=chain['authority'])


def test_global_digest_keeps_its_original_unicode_contract():
    value = {'text': '\ud55c\uae00', 'ordered': [1, 2]}
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    assert c.digest(value) == hashlib.sha256(raw).hexdigest()
    assert c.digest(value) != source.canonical_sha256(value)
    assert source.canonical_sha256({'text': 'e\u0301'}) != source.canonical_sha256({'text': '\u00e9'})


def test_existing_metadata_collection_normalization_is_unchanged():
    rows = [dict(ref_id='b', text='\ud55c\uae00'), dict(ref_id='a', text='ASCII')]
    assert source.canonical_source_metadata_sha256(rows) == source.canonical_source_metadata_sha256(rows[::-1])
