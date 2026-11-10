from dataclasses import replace
from datetime import date
from app.services.krx_night_history_service import _session_dates,build_same_contract_timeframes,store_normalized_bar
from app.services.night_futures import NightFuturesItem,night_futures_context_row


def test_end_date_calendar_opt_in_preserves_legacy_shape_and_no_V4_fill(tmp_path):
    from tests.test_krx_night_history_service import _bar
    start,end=date(2026,11,2),date(2026,11,8)
    assert date(2026,11,7) not in _session_dates(start,end)
    assert date(2026,11,7) in _session_dates(start,end,night_end_dates=True)
    store_normalized_bar(tmp_path,_bar(date(2026,11,4),maturity='2026-12'))
    legacy=build_same_contract_timeframes(tmp_path,instrument_root='KOSPI200',reference_date=date(2026,11,4))
    assert 'calendar_contract' not in legacy.model_dump(mode='json')
    from tests.test_c22s_source_only import capture
    p,v=capture(tmp_path/'capture')
    raw=v['provider_value']['observations'][0]
    from app.services.night_futures import summarize_night_futures
    item=summarize_night_futures({'observations':[{**raw,**raw['raw_payload']}]}).items[0]
    legacy_item=replace(item,night_trade_date=None,regular_reference_date=None,observation_time_kst=None)
    ctx=night_futures_context_row(legacy_item)
    assert all(k not in ctx for k in ('night_trade_date','regular_reference_date','observation_time_kst'))


def test_offline_fixture_cannot_be_reported_as_live_source(tmp_path):
    import asyncio,httpx,pytest
    from tests.test_c22s_source_only import DATES,CUTOFF,capture
    from app.services.krx_source_only import issue_source_only_parent,collect_source_only
    parent=issue_source_only_parent(root=tmp_path/'live',run_id='live',exact_dates=DATES,cutoff=CUTOFF,live_enabled=True)
    with pytest.raises(ValueError,match='mode_mismatch'):
        asyncio.run(collect_source_only(parent,enabled=True,transport=httpx.MockTransport(lambda r:httpx.Response(200)),api_key='dummy'))
    assert not list(parent.root.glob('read-*.response.json'))
    p,v=capture(tmp_path/'mock')
    assert v['source_mode']=='OFFLINE_MOCK' and v['financial_HTTP']==0 and v['physical_HTTP']==2
