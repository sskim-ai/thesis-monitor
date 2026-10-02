import asyncio
from copy import deepcopy
from datetime import date, datetime
from enum import Enum
import json
from pathlib import Path

import httpx
import pytest

from app.services.bounded_financial_acquisition import BoundedReader, collect
from app.services.bounded_financial_projection import project
from app.services.fpi_filing_document_graph import document_slot_plan
from app.services.sec_logical_cell_reference import (
    ReferenceTarget, logical_reference_inventory, require_json_native,
)
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest, encoded
from test_r9_rev15_financial_owners import plan, filing, submission, inline_html


class RuntimeString(str, Enum):
    VALUE = 'value'


@pytest.mark.parametrize('bad', [(), set(), b'bytes', Path('path'), date(2026, 1, 1),
    datetime(2026, 1, 1), object(), {1: 'nonstring'}, float('nan'), float('inf'),
    float('-inf'), RuntimeString.VALUE, ReferenceTarget(canonical_href='a', document_identity='a')])
def test_public_json_assertion_rejects_runtime_types(bad):
    with pytest.raises(ValueError, match='non_json_native'):
        require_json_native({'nested': [bad]})


def test_json_native_validator_never_coerces():
    value = {'a': [None, True, False, 1, -1, 0.25, 'x', {}]}
    assert require_json_native(value) is None
    assert json.loads(encoded(value)) == value


@pytest.mark.parametrize('target', [('a', 'a'), ['a', 'a'], {},
    {'canonical_href': 'a'}, {'document_identity': 'a'},
    {'canonical_href': 'a', 'document_identity': 'a', 'extra': 1},
    {'canonical_href': b'a', 'document_identity': 'a'},
    {'canonical_href': '', 'document_identity': 'a'}])
def test_resolver_target_requires_exact_named_object(target):
    with pytest.raises(ValueError):
        logical_reference_inventory('<a href="a">label</a>', accession='acc',
            filing_form='20-F', source_document='primary', resolve=lambda _: target)


@pytest.mark.parametrize('as_model', [False, True])
def test_resolver_explicit_typed_dump_and_roundtrip(as_model):
    target = {'canonical_href': 'a#section', 'document_identity': 'a'}
    resolve = ReferenceTarget(**target) if as_model else target
    value = logical_reference_inventory('<a href="a">label</a>', accession='acc',
        filing_form='20-F', source_document='primary', resolve=lambda _: resolve)
    assert value['anchors'][0]['target'] == target
    require_json_native(value)
    assert value == json.loads(encoded(value))


def test_slot_plan_asserts_entire_public_surface_before_hash():
    p, f = plan(), filing('20-F')
    f['runtime_metadata'] = ('not', 'json')
    with pytest.raises(ValueError, match='non_json_native'):
        document_slot_plan({'directory': {'item': []}}, '', p, f)


@pytest.mark.parametrize('ticker,parts', [('TSM', ['Articles of ', 'Incorporation']),
    ('WRD', ['Land Lease ', 'with Local ', 'Government'])])
def test_collect_durable_reload_production_projection(tmp_path, ticker, parts):
    p = plan()
    p.update(ticker=ticker, cutoff='2026-04-01T00:00:00+00:00')
    f = {**filing('20-F'), 'reportDate': '2025-12-31', 'filingDate': '2026-03-15'}
    html = inline_html() + '<table><tr><td>' + ''.join(
        f'<a href="legal.htm">{part}</a>' for part in parts) + '</td></tr></table>'
    index = {'directory': {'item': [{'name': f['primaryDocument'], 'type': 'text.gif'},
                                   {'name': 'legal.htm', 'type': 'text.gif'}]}}

    def respond(request):
        if '/submissions/' in str(request.url):
            return httpx.Response(200, json=submission([f]))
        if '/companyfacts/' in str(request.url):
            return httpx.Response(200, json={'cik': 123})
        if str(request.url).endswith('index.json'):
            return httpx.Response(200, json=index)
        assert str(request.url).endswith(f['primaryDocument'])
        return httpx.Response(200, text=html)

    reader = BoundedReader(p, tmp_path, transport=httpx.MockTransport(respond))
    acquired = asyncio.run(collect(reader))
    path = tmp_path/'persisted-acquisition.json'
    durable_json(path, acquired, exclusive=True)
    loaded = json.loads(path.read_bytes())
    assert loaded == acquired
    assert digest(loaded) == digest(acquired)
    for slot in loaded['document_slot_plans']:
        require_json_native(slot)
        assert slot == document_slot_plan(index, html, p, slot['filing'])
    first = project(p, loaded, tmp_path, reader.receipts, field_semantics=True)
    assert first == project(p, json.loads(path.read_bytes()), tmp_path, reader.receipts, field_semantics=True)
    assert first['fpi_purpose']['selection']['status'] == 'PASS'
    for mutation in ('target', 'source_hash', 'order', 'span', 'missing', 'tuple', 'cross_document'):
        damaged = deepcopy(loaded)
        inventory = damaged['document_slot_plans'][0]['logical_cell_reference_inventory']
        a = next(row for row in inventory['anchors'] if row['target'])
        if mutation == 'target':
            a['target']['canonical_href'] += '#changed'
        elif mutation == 'cross_document':
            a['target']['document_identity'] += '.other'
        elif mutation == 'source_hash':
            inventory['source_sha256'] = '0'*64
        elif mutation == 'order':
            a['dom_order'] += 1
        elif mutation == 'span':
            a['byte_start'] += 1
        elif mutation == 'missing':
            a['target'].pop('document_identity')
        else:
            a['target'] = tuple(a['target'].values())
        with pytest.raises(ValueError, match='fpi_document_slot_plan_replay_mismatch'):
            project(p, damaged, tmp_path, reader.receipts, field_semantics=True)
