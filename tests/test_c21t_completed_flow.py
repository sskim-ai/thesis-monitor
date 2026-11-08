"""C21T changed boundaries, real types with synthetic source only."""
import ast,asyncio,json,os
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import PriceContext,PriceDecisionContext,PricePeriodSummary
from app.services import ohlcv_client as module
from app.services.thesis_evaluation_service import _build_price_decision
from app.services.packet_owned_technical_context_service import load_packet_owned_technical_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision
from test_provider_native_technical import raw_payload,fixture_completion


def captured(monkeypatch,market='kr',summary_only=False,partial=True):
    ticker='123456' if market=='kr' else 'SYNTH'
    monkeypatch.setattr(module,'get_settings',lambda:Settings(_env_file=None,monitor_retry_attempts=1,
        kr_price_structure_v3_enabled=True,us_price_structure_v3_enabled=True))
    queries=[]
    def handle(request):
        p=dict(request.url.params);queries.append(p);tf=p['periods']
        payload=raw_payload(ticker,market,tf,{'daily':85,'weekly':150,'monthly':28}[tf],p['adjusted']=='true')
        rows=payload['periods'][tf]
        native=deepcopy(rows[-1]['indicators'])
        if tf=='daily':
            rows[:]=[r for r in rows if r['date']<='2026-11-05']
            rows[-1].update(open=95,high=96,low=94,close=95)
            if not summary_only:
                rows[-1]['investor_flow']={'foreign_net_buy_qty':7,'foreign_net_buy_qty_20':140}
            if partial:
                rows.append(dict(date='2026-11-06',open=135,high=136,low=134,close=135,volume=1200,
                    bar_state='PARTIAL',investor_flow={'foreign_net_buy_qty':999,'foreign_net_buy_qty_20':9999}))
            payload['supply_demand']={'as_of_date':'2026-11-06','score':9999,'primary_signal':'UNVERIFIED_TAIL',
                'foreign_net_buy_qty_20':9999}
        for r in rows:r.pop('indicators',None)
        limit=int(p['indicator_limit'])
        if limit:
            for r in rows[-limit:]:r['indicators']=deepcopy(native)
        return httpx.Response(200,json=payload)
    c=module.OhlcvClient(transport=httpx.MockTransport(handle),completion_verifier=fixture_completion)
    context=asyncio.run(c.fetch_price_context(ticker,as_of=datetime(2026,11,8,12,tzinfo=timezone.utc)))
    return context,queries,ticker


def numeric_values(value):
    if isinstance(value,dict):return [n for x in value.values() for n in numeric_values(x)]
    if isinstance(value,(tuple,list)):return [n for x in value for n in numeric_values(x)]
    return [value] if type(value) in (float,int) else []


def test_completed_flow_to_prompt_and_original_sr(monkeypatch):
    context,queries,ticker=captured(monkeypatch)
    assert context.supply.as_of_date=='2026-11-05'
    assert context.supply.foreign_net_buy_qty==7
    assert context.supply.foreign_net_buy_qty_20==140
    assert context.supply.score is None
    assert context.decision.current_price is None
    technical=load_packet_owned_technical_context(context.technical_context_payload(),ticker=ticker)
    evidence=build_decision_evidence_packet(packet={'packet_id':'C21T_SYNTHETIC','market':'kr','assessment_date':'2026-11-06'},
        stock={'ticker':ticker,'company_name':'SYNTHETIC','fact_catalog':[],
               'investor_supply':context.supply.model_dump(mode='json')},technical_context=technical)
    prompt=compact_ai_context(evidence)
    runtime=context.chart.structure['price_structure_v3']
    rendered=build_kr_price_structure_rollout_decision(runtime,ticker=ticker,monitored_subject=True,enabled=True)
    assert rendered.section and rendered.numeric_bindings and not rendered.render_validation_errors
    assert '조정봉·' in rendered.section and '현재가' not in rendered.section
    for packet in [context.supply.model_dump(mode='json'),runtime,prompt]:
        assert not {999,9999}.intersection(numeric_values(packet))
    assert len(queries)==4 and [q['include_investor_flows'] for q in queries]==['true','false','false','false']
    target=Path(os.environ['C21T_OUTPUT']);target.mkdir(exist_ok=True)
    (target/'KR-NO_SEND.md').write_text('SYNTHETIC NO-SEND ONLY\n'+rendered.section)
    (target/'COMPLETED_FLOW.json').write_text(json.dumps({'supply':context.supply.model_dump(mode='json'),
        'prompt':prompt,'renderer':rendered.to_dict(),'queries':queries},ensure_ascii=False,indent=2))


def test_us_does_not_consume_injected_kr_flow(monkeypatch):
    context,queries,_=captured(monkeypatch,'us')
    assert not context.supply.available and context.supply.foreign_net_buy_qty is None
    assert all(q['include_investor_flows']=='false' for q in queries)


@pytest.mark.parametrize('partial',[True,False])
def test_unbound_top_level_summary_never_relabels_completed_supply(monkeypatch,partial):
    context,_,_=captured(monkeypatch,summary_only=True,partial=partial)
    assert not context.supply.available
    assert context.supply.foreign_net_buy_qty_20 is None and context.supply.score is None


@pytest.mark.parametrize('rules',['{}','{"support_zone_low":90,"support_zone_high":100}'],ids=['empty','rules'])
def test_owned_price_text_matches_independent_owner(rules):
    context=PriceContext(price_source_scope='dated_technical_only',decision=PriceDecisionContext(
        current_price=96,currency='USD',price_as_of='2026-11-05',exchange_trade_date='2026-11-05',price_basis='close'),
        periods={'daily':PricePeriodSummary(requested_count=85,actual_count=84,latest_close=95,latest_date='2026-11-05')})
    cold=PriceContext.model_validate_json(context.model_dump_json())
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules=rules),cold)
    assert (d.current_price,d.currency,d.price_as_of,d.price_basis)==(96,'USD','2026-11-05','close')
    assert '미확인' not in d.current_position
    if rules=='{}':assert '미산출' in d.current_position


def test_missing_owner_and_legacy_fallback_are_distinct():
    period=PricePeriodSummary(requested_count=85,actual_count=84,latest_close=95,latest_date='2026-11-05')
    native=PriceContext(price_source_scope='dated_technical_only',periods={'daily':period})
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules='{}'),native)
    assert d.current_price is None and '미확인' in d.current_position
    old=PriceContext(periods={'daily':period})
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules='{}'),old)
    assert d.current_price==95 and d.price_as_of=='2026-11-05'


def test_ast_checks_actual_completed_dataflow_not_comment_text():
    source=Path(module.__file__).read_text();tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='OhlcvClient')
    fetch=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='fetch_price_context')
    calls=[n for n in ast.walk(fetch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_investor_supply_context']
    assert len(calls)==1 and ast.unparse(calls[0].args[0])=='completed_supply_rows'
    completed=next(n for n in ast.walk(fetch) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='completed_periods')
    assert calls[0].lineno>completed.lineno
