import asyncio
from copy import deepcopy
from datetime import timedelta
import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.bounded_financial_acquisition import collect
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.selected_source_plan import COUNTS, build_stock_plan, compile_selected_plan
from app.services.unified_snapshot_contract import digest
from tests.test_c22ab_selected_source import compile_market
from tests.test_reported_business_native_projection import source


def case(tmp_path, source, monkeypatch, *, variant='same'):
    old = source['financial_inputs']
    start = source['technical_inputs']['plan'].frozen_at
    _, compiler, _ = compile_market('us','CORZ')
    compiler['identities'] = {'CORZ': old['plan']['security']}
    compiler['stock'] = build_stock_plan(market='us',identities=compiler['identities'],at=start,
        generation=old['plan']['run_id'],code_sha='a'*40,counts=COUNTS)
    from app.services.unified_stock_event_input import make_read
    compiler['news_reads'] = [make_read(security=old['plan']['security'],market='us',run_id=old['plan']['run_id'],
        lookback_days=3,security_records=[old['plan']['security']])]
    compiled = compile_selected_plan(compiler_args=compiler)
    current = compiled['candidate']['financial_plans']['CORZ']
    discovery, facts, document = old['receipts']
    raw = (old['directory']/document['artifact']).read_bytes()
    request = json.loads((old['directory']/'request-003.plan.json').read_bytes())
    original_plan = dict(current,run_id='ORIGINAL_SEC_FIXTURE',cutoff=(start-timedelta(hours=1)).isoformat())
    request['plan_sha256'] = digest(original_plan)
    original = dict(document,plan_sha256=digest(original_plan),request_sha256=digest(request),
        started_at=(start-timedelta(minutes=10)).isoformat(),finished_at=(start-timedelta(minutes=9)).isoformat())
    pin = dict(identity=dict(ticker=current['ticker'],issuer=current['issuer'],
        canonical_security_id=current['security']['canonical_security_id']),origin_generation=original_plan['run_id'],
        original_cutoff=original_plan['cutoff'],original_plan_sha256=digest(original_plan),
        original_receipt_sha256=digest(original),raw_sha256=document['raw_sha256'])
    body = tmp_path/'retained-filing.body'
    body.write_bytes(raw)
    proof = dict(pin=pin,original_receipt=original,original_request=request)
    if variant == 'bad-bytes':
        body.write_bytes(raw+b'changed')
    elif variant == 'bad-receipt':
        pin['original_receipt_sha256'] = '0'*64
    elif variant == 'not-200':
        original['HTTP_status'] = 404
        pin['original_receipt_sha256'] = digest(original)
    elif variant == 'wrong-security':
        pin['identity']['canonical_security_id'] = 'OTHER_SECURITY'
    elif variant == 'future':
        original['finished_at'] = (start+timedelta(seconds=1)).isoformat()
        pin['original_receipt_sha256'] = digest(original)
    elif variant == 'symlink':
        body = tmp_path/'not-regular.body'
        body.symlink_to(old['directory']/document['artifact'])
    elif variant == 'wrong-url':
        request['url'] += '.changed'
        original['request_sha256'] = digest(request)
        pin['original_receipt_sha256'] = digest(original)
    responses = json.loads((old['directory']/discovery['artifact']).read_bytes())
    if variant == 'new':
        responses['filings']['recent']['accessionNumber'][0] = '0000001234-26-000009'
    clock = (start+timedelta(seconds=9)).isoformat()
    monkeypatch.setattr('app.services.sealed_fresh_dispatch.stamp',lambda:clock)
    dispatcher = object.__new__(SelectedSourceDispatcher)
    physical, intents = [], []
    dispatcher.plan = compiled['plan']
    dispatcher._require_current = lambda: None
    dispatcher.run_ledger = SimpleNamespace(identity={},before_http=lambda **kw:intents.append(kw['logical_id']),
        result=lambda key,ok:None,stop=lambda code:None)
    dispatcher.admission = {'synthetic':True}
    root = tmp_path/'sealed'
    dispatcher._initialize(root=root/'dispatch',secrets=('PLAN_CREDENTIAL','Synthetic contact fixture'))

    async def response(wire):
        physical.append(str(wire.url))
        if '/submissions/' in str(wire.url):
            return httpx.Response(200,json=responses)
        if '/companyfacts/' in str(wire.url):
            return httpx.Response(200,content=(old['directory']/facts['artifact']).read_bytes())
        return httpx.Response(200,content=raw)

    transport = httpx.MockTransport(response)
    reader = SealedFinancialReader(current,root/'financial'/current['ticker'],dispatcher=dispatcher,
        transport=transport, user_agent='Synthetic contact fixture',
        retained_sec={} if variant == 'absent' else {request['url'] if variant != 'wrong-url'
            else request['url'].removesuffix('.changed'):dict(proof=proof,body=body)})
    return reader,dispatcher,physical,intents,original


def test_selected_retained_document_reaches_original_financial_core(tmp_path, source, monkeypatch):
    reader, dispatcher, physical, intents, original = case(tmp_path,source,monkeypatch)
    acquisition = asyncio.run(collect(reader))
    assert reader.logical == 3 and reader.attempts == len(physical) == len(intents) == 2
    reused, = [r for r in reader.receipts if 'retained_sec_origin' in r]
    assert reused['attempt'] == 0 and reused['HTTP_status'] is None
    assert reused['finished_at'] == original['finished_at'] < reader.plan['cutoff'] < reused['selected_at']
    assert dispatcher.results[reused['sealed_logical_id']]['attempts'] == []
    inputs = dict(source,financial_inputs=dict(plan=reader.plan,acquisition=acquisition,
        directory=reader.output,receipts=reader.receipts,field_semantics=True))
    first = assemble_fresh_stock(**inputs)
    assert first['status'] == 'PASS' and first['comparative_fact_refs']
    assert assemble_fresh_stock(**inputs) == first
    rejected = deepcopy(reader.receipts)
    rejected[-1]['selected_at'] = rejected[-1]['finished_at']
    with pytest.raises(ValueError,match='retained_sec_financial_use_mismatch'):
        assemble_fresh_stock(**dict(inputs,financial_inputs=dict(inputs['financial_inputs'],receipts=rejected)))


@pytest.mark.parametrize('variant',['new','absent'])
def test_only_missing_or_new_document_uses_original_physical_slot(tmp_path, source, monkeypatch, variant):
    reader, _, physical, intents, _ = case(tmp_path,source,monkeypatch,variant=variant)
    asyncio.run(collect(reader))
    assert reader.logical == reader.attempts == len(physical) == len(intents) == 3
    assert reader.receipts[-1]['HTTP_status'] == 200 and reader.receipts[-1]['attempt'] == 1
    assert ('000000123426000009' in physical[-1]) == (variant == 'new')


@pytest.mark.parametrize('variant',['bad-bytes','bad-receipt','not-200','wrong-security','future','symlink','wrong-url'])
def test_selected_invalid_retained_provenance_is_not_sent_or_accepted(tmp_path, source, monkeypatch, variant):
    reader, _, physical, intents, _ = case(tmp_path,source,monkeypatch,variant=variant)
    with pytest.raises(ValueError,match='retained_sec'):
        asyncio.run(collect(reader))
    assert len(physical) == len(intents) == 2
    assert len(reader.receipts) == 2
