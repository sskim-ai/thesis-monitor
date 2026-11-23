import asyncio
from datetime import datetime
import json
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.detailed_stock_message_v2 import _buyer_action, _entry_lines, _entry_quality
from app.services.new_buyer_base_contract import timing
from app.services.new_buyer_input_owner import tactical_catalog
from app.services.unified_snapshot_contract import digest
from tests.test_c42_kr_caller import offline
from tests.test_local_launchd_entry import configuration, code_pin


def test_calendar_and_intent_share_frozen_caps(tmp_path,monkeypatch):
    code_pin(monkeypatch)
    seen=[]
    async def cycle(cfg, directory, session, **kw):
        seen.append((session,json.loads((directory/'intent.json').read_text())['max_models']))
        return dict(status='OFFLINE',normal_messages_sent=False)
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    for market,at,tag,combined,session,cap in [
        ('us','08:10','us-20261124-c38f2a6d',False,'2026-11-23',42),
        ('us','08:10',None,True,'2026-11-23',43),
        ('kr','16:00',None,True,'2026-11-24',27)]:
        path,cfg=configuration(tmp_path/str(cap),market)
        path.write_text(json.dumps(dict(cfg,market_b2_timeout_retry=combined)))
        asyncio.run(job.run_local_scheduled(path,market,one_shot_tag=tag,
            now=datetime.fromisoformat('2026-11-24T'+at+':00+09:00')))
        assert seen[-1]==(session,cap)


def test_c38_cannot_be_upgraded_or_consume_marker(tmp_path):
    path,cfg=configuration(tmp_path)
    path.write_text(json.dumps(dict(cfg,market_b2_timeout_retry=True)))
    with pytest.raises(ValueError,match="conflict"):
        asyncio.run(job.run_local_scheduled(path,'us',one_shot_tag='us-20261124-c38f2a6d',
            now=datetime.fromisoformat('2026-11-24T08:10:00+09:00')))
    assert not (tmp_path/'runs').exists()


def test_us43_actual_budget_reaches_pre_source(tmp_path,monkeypatch):
    from app.services.production_source_configuration import ProductionSourceConfiguration
    class Boundary(Exception): pass
    monkeypatch.setattr(job,'_local_model_runtime',lambda _:tmp_path)
    def stop(*args): raise Boundary
    monkeypatch.setattr(ProductionSourceConfiguration,'model_validate_json',stop)
    cfg=SimpleNamespace(market='us',market_b2_timeout_retry=True,kr_market_timeout_retry=False,
                        source_configuration=SimpleNamespace(read=lambda:b'{}'))
    with pytest.raises(Boundary):
        asyncio.run(job._local_registered_cycle(cfg,tmp_path,'2026-11-23'))
    row=json.loads((tmp_path/'model-runtime-preflight.json').read_text())
    assert (row['max_models'],row['market_timeout_retry_cap'],row['b2_retry_policy'])==(43,1,'B2_PER_TICKER_ONE_RETRY_V1')


def fixture():
    day='2026-11-23'
    price='canonical:price:current'
    zone='canonical:chart:structure:nearest_supports:1'
    def ev(ref,label,**fields):
        return dict(ref_id=ref,as_of=day,label=label,statement=dict(currency='USD',**fields))
    rows=[ev(price,'current_price',current_price=10,price_basis='adjusted_close',price_as_of=day),
          ev('canonical:chart:daily','daily',quality='available',price_basis='adjusted',candle={'close':10}),
          ev(zone,'chart_support_zone',timeframe='daily',zone_low=9,zone_high=11),
          ev('canonical:chart:structure:invalidation','chart_invalidation',timeframe='daily',support_low=9,
             price=8,chart_only=True,status='intact'),
          ev('canonical:chart:structure:risk_reward:current_price','chart_risk_reward_current_price',
             entry=10,ratio=3,rr_basis='current_price',scenario='current_price',classification='attractive',invalidation=8,target=16)]
    ctx=dict(ticker='X',source_evidence_binding=dict(source_generation_id='g'),decision_evidence=rows,
        current_price=dict(value=10,basis='adjusted_close',as_of=day,currency='USD',ref_id=price),
        r2_eligible_range_catalog=dict(tactical_candidates=[dict(candidate_id='watch',evidence_refs=[zone],low=9,high=11,currency='USD')]),
        source_use_projection=dict(source_permissions=[dict(ref_id=r['ref_id'],allowed_uses=['ENTRY']) for r in rows]))
    return ctx


def evaluate(ctx):
    inp=dict(ticker='X',security_id='id',source_generation='g',authority_digests=dict(context=digest(ctx)))
    rows=tactical_catalog(ctx,'X','id')
    t=timing(dict(ticker='X',security_id='id',selected_tactical_candidate='watch',tactical_catalog=rows,current_price=ctx['current_price']))
    return inp,t,_entry_quality(inp,t,ctx,'us','2026-11-23')


def test_supported_only_with_bound_current_price_scenario():
    ctx=fixture()
    assert evaluate(ctx)[2][0]=='SUPPORTED'
    ctx['decision_evidence'][-1]['statement']['rr_basis']='support_entry'
    assert evaluate(ctx)[2][0]=='INSUFFICIENT_EVIDENCE'
    ctx=fixture()
    ctx['source_use_projection']['source_permissions'][-1]['allowed_uses']=['DISPLAY']
    assert evaluate(ctx)[2][0]=='INSUFFICIENT_EVIDENCE'


def test_resistance_overlap_and_invalidation_win_over_positive_rr():
    ctx=fixture(); ref='canonical:chart:structure:nearest_resistance:1'
    ctx['decision_evidence'].append(dict(ref_id=ref,as_of='2026-11-23',label='chart_resistance_zone',
        statement=dict(currency='USD',timeframe='daily',zone_low=10.5,zone_high=12)))
    ctx['source_use_projection']['source_permissions'].append(dict(ref_id=ref,allowed_uses=['ENTRY']))
    assert evaluate(ctx)[2][0]=='CAUTION'
    ctx['decision_evidence'][3]['statement']['status']='hard_invalid'
    assert evaluate(ctx)[2][0]=='BLOCKED'


def test_no_zone_vs_mismatch_and_changed_context():
    ctx=fixture()
    ctx['r2_eligible_range_catalog']['tactical_candidates']=[]
    inp,t,q=evaluate(ctx)
    assert t['reason']=='NO_ELIGIBLE_SELECTED_CANDIDATE' and q[0]=='INSUFFICIENT_EVIDENCE'
    ctx=fixture(); ctx['decision_evidence'][1]['statement']['price_basis']='unadjusted'
    inp,t,q=evaluate(ctx)
    assert t['reason']=='PRICE_ZONE_IDENTITY_BASIS_OR_VALUE_UNRESOLVED' and q[0]=='INSUFFICIENT_EVIDENCE'
    ctx['ticker']='OTHER'
    with pytest.raises(ValueError,match='context_mismatch'):
        _entry_quality(inp,t,ctx,'us','2026-11-23')


def test_action_axes_and_reason_matrix():
    for rel,q,phrase in [('INSIDE','SUPPORTED','검토 가능'),('INSIDE','CAUTION','확인 대기'),
                         ('INSIDE','INSUFFICIENT_EVIDENCE','확인 대기'),('ABOVE','SUPPORTED','조정'),
                         ('BELOW','SUPPORTED','이탈'),('UNRESOLVED','INSUFFICIENT_EVIDENCE','미확인')]:
        assert phrase in _buyer_action('ATTRACTIVE',rel,q)
        assert '회피' in _buyer_action('AVOID',rel,q)
    ctx=fixture();inp,t,_=evaluate(ctx)
    output=dict(new_buyer='WAIT',reason_class='VALUATION_BURDENSOME',valuation_context=dict(state='BURDENSOME'),timing_context=t)
    lines,refs=_entry_lines(output,inp,ctx,'us','2026-11-23')
    assert '부담스러운 가치평가' in lines[0] and '지지 구간 안' in lines[1] and '기업가치 확인 대기' in lines[2]
    assert 'VALUATION_BURDENSOME' not in '\n'.join(lines) and 'INSIDE' not in '\n'.join(lines)
    assert refs and output['timing_context']==t


def test_only_entry_owned_typed_confirmation_or_warning():
    ctx=fixture(); ref='canonical:chart:structure:state'
    state=dict(state='WAIT',user_semantics='price_structure_wait_not_sell_command',reasons=['distribution'])
    ctx['decision_evidence'].append(dict(ref_id=ref,label='chart_state',as_of='2026-11-23',statement=state))
    assert evaluate(ctx)[2][0]=='SUPPORTED'
    ctx['source_use_projection']['source_permissions'].append(dict(ref_id=ref,allowed_uses=['ENTRY']))
    assert evaluate(ctx)[2][0]=='CAUTION'
    state.update(state='CONFIRM_ENTRY',user_semantics='confirmed_breakout_not_buy_command',
                 reasons=['two_close_breakout','volume_ratio_confirmed'])
    assert '거래량 확인' in evaluate(ctx)[2][1]
    ctx['decision_evidence'][-1]['as_of']='2026-11-20'
    assert ref not in evaluate(ctx)[2][2]
