"""Prove one physical page can satisfy two selected consumers without another send."""
import asyncio
from contextlib import asynccontextmanager
import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.production_source_seal import row_count_proofs
from app.services.sealed_fresh_dispatch import consume_bound_result
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from tests.test_c22ab_selected_source import compile_market


def test_selected_market_reuses_exact_page_and_retains_original_receipt(tmp_path):
    async def scenario():
        # A market-listed synthetic request uses the existing compiler; no
        # actual registration, secrets, or financial transport are present.
        compiled, _, _ = compile_market('us', 'GOOGL')
        plan = compiled['plan']
        run = object.__new__(SelectedSourceDispatcher)
        intents = []
        run.plan, run._require_current = plan, lambda: None
        run.run_ledger = SimpleNamespace(identity={}, before_http=lambda **kw: intents.append(kw['logical_id']),
                                         result=lambda key, ok: None)
        run.admission = {'synthetic': True}
        run._initialize(root=tmp_path/'dispatch', secrets=('PLAN_CREDENTIAL',))
        calls = []

        async def response(request):
            api = request.headers['api-id']
            calls.append(api)
            if api == 'usa10099':
                venue = json.loads(request.content)['stex_tp']
                rows = [{'stk_cd':'GOOGL'}] if venue == 'ND' else []
                return httpx.Response(200,json={'list':rows})
            return httpx.Response(200,json={'result_list':[{'date':'2026-11-10'},{'date':'2026-11-09'}]})

        inner = httpx.MockTransport(response)
        sealed = SealedSourceTransport(run, inner, providers={'kiwoom'})

        async def request(logical_id):
            wire, _, _ = run.resolve(logical_id)
            d = json.loads(wire)
            req = httpx.Request(d['method'], d['url'], headers=d['headers'], content=d['body'])
            return await sealed.handle_async_request(req)

        stock = 'us:GOOGL:adjusted_daily:page1'
        market = 'us_market:GOOGL'
        source = await request(stock)
        for venue in ('ND','NY','NA'):
            await request('us_market:discovery:'+venue)
        used = await request(market)
        assert used.content == source.content
        assert calls.count('usa06012') == 1
        assert market not in intents and intents.count(stock) == 1
        final = run.results[market]
        assert final['attempts'] == [] and final['reused_wire']['logical_id'] == stock
        assert final['reused_wire']['receipt_sha256'] == run.results[stock]['receipt_sha256']
        assert final['retrieval_time'] == run.results[stock]['retrieval_time']
        assert consume_bound_result(root=run.root,plan=plan,logical_id=market,
                                    receipt_sha256=final['receipt_sha256'])['status']=='PASS'
        provider = tmp_path/'app/providers/kiwoom.py'
        provider.parent.mkdir(parents=True)
        provider.write_text('# fixture')
        from app.services.unified_run_artifacts import sha256_bytes
        proofs = row_count_proofs(tmp_path,dict(native_owner_root=str(tmp_path),
            native_owner={'owner_files':{'app/providers/kiwoom.py':sha256_bytes(provider.read_bytes())}},
            us_market_reads=[{'role':market,'params':{'count':2}}]),
            dict(logical_results=run.results))
        assert proofs[market]['rows'] == 2
        with pytest.raises(SourceSafetyStop,match='not_unique'):
            await request(market)
        assert calls.count('usa06012') == 1

        # Rehashing an altered receipt does not detach it from its physical origin.
        changed = dict(final,retrieval_time='2026-11-10T23:00:00+00:00')
        changed.pop('receipt_sha256')
        changed['receipt_sha256'] = digest(changed)
        (run.root/'receipts'/market/'final.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='reuse_origin_mismatch'):
            consume_bound_result(root=run.root,plan=plan,logical_id=market,receipt_sha256=changed['receipt_sha256'])

    asyncio.run(scenario())


@pytest.mark.parametrize('status',[200,429])
def test_direct_completed_close_counts_only_under_original_lane(monkeypatch,status):
    from app.services import kiwoom_global_lane
    from app.services.selected_source_dispatch import _completed_close_on_lane

    events = []

    class Lane:
        @asynccontextmanager
        async def slot(self):
            events.append('lane_entered')
            try:
                yield
            except Exception:
                events.append('lane_failure')
                raise
            finally:
                events.append('lane_exited')

    monkeypatch.setattr(kiwoom_global_lane,'configured_lane',Lane)
    request = httpx.Request('POST','https://api.kiwoom.com/api/us/mrkcond')

    async def send(req):
        events.append('physical')
        return httpx.Response(status,json={'return_code':0})

    async def run():
        transport = SimpleNamespace(handle_async_request=send)
        if status==429:
            with pytest.raises(httpx.HTTPStatusError):
                await _completed_close_on_lane(transport,request)
        else:
            assert (await _completed_close_on_lane(transport,request)).status_code==200
        monkeypatch.setattr(kiwoom_global_lane,'configured_lane',lambda:None)
        with pytest.raises(SourceSafetyStop,match='original_lane_required'):
            await _completed_close_on_lane(transport,request)

    asyncio.run(run())
    assert events==['lane_entered','physical',*(['lane_failure'] if status==429 else []),'lane_exited']
