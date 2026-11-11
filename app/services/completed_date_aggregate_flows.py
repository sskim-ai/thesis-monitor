"""Dated ka10051 amounts from original receipts and a pinned Provider contract."""
from datetime import date,datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal
import ast,hashlib,json,re

from pydantic import BaseModel, ConfigDict
from app.services.unified_aggregate_receipt import AggregateReceipt,verify_aggregate
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.market_cross_section_service import MarketFlowFact
from app.services.unified_aggregate_owners import validate_aggregate_flow_rows
from app.services.kiwoom_kr_market_context_service import (
    _aggregate_row,_signed_int,MARKETS,FLOW_FIELDS,KA10051_AMOUNT_UNIT_KRW,KiwoomKrMarketContextService,
)


class CompletedDateAggregateFlows(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    contract: Literal['completed-date-aggregate-flows-v1']='completed-date-aggregate-flows-v1'
    scope: Literal['COMPLETED_DATE_AGGREGATE_FLOWS']='COMPLETED_DATE_AGGREGATE_FLOWS'
    session: str
    market_flows: tuple[MarketFlowFact,...]
    bindings: tuple[dict,...]
    provider_document: dict
    original_aggregate_sha256: str
    first_system_available_at: datetime
    response_date_echo: Literal['NOT_PROVIDED']='NOT_PROVIDED'
    full_market_parent: Literal[False]=False
    economic_use: Literal[False]=False
    concentration_eligible: Literal[False]=False


def project_completed_date_flows(*,root,session,cutoff,original_observed_at,official_source,official_sha256,official_commit):
    raw=Path(official_source).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=official_sha256 or not re.fullmatch('[0-9a-f]{40}',official_commit):
        raise ValueError('completed_flow_official_document_pin')
    tree=ast.parse(raw);constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_domestic_sector_investor_net_buy']
    doc=ast.get_docstring(functions[0]) if len(functions)==1 else ''
    if (constants.get('API_ID')!='ka10051' or constants.get('API_URL')!='/api/dostk/sect'
            or 'inds_netprps' not in constants.get('TABLE_KEYS',{}) or not doc
            or not all(x in doc for x in ('base_dt: 기준일자','YYYYMMDD','금액:0','3:통합'))):
        raise ValueError('completed_flow_official_contract_semantics')
    root=Path(root);receipt=AggregateReceipt.model_validate_json((root/'aggregate.json').read_bytes())
    if receipt.provider!='kiwoom_rest' or receipt.market!='kr' or receipt.session!=session:
        raise ValueError('completed_flow_original_market_session')
    graph=verify_aggregate(root,receipt,policy=UnifiedSourcePolicy(frozenset(('kiwoom_rest',))),cutoff=cutoff,
        completion_observed_at=original_observed_at)
    plan=json.loads(graph.plan)
    if plan['session']!=session:raise ValueError('completed_flow_plan_date')
    result=[];bindings=[]
    for market,spec in MARKETS.items():
        def child(api):
            matches=[(r,b) for r,b in zip(graph.child_receipts,graph.child_bodies) if r.get('read_key')==market+':'+api]
            if len(matches)!=1:raise ValueError('completed_flow_unique_native_child')
            r,b=matches[0]
            if r['session']!=session or r['provider']!='kiwoom_rest' or r['http_status']!=200 or b is None:
                raise ValueError('completed_flow_successful_native_child')
            data=json.loads(b)
            if data['return_code']!=0:raise ValueError('completed_flow_native_return_code')
            return r,data
        r,payload=child('ka10051');h,history=child('ka20009')
        body=dict(mrkt_tp=spec['ka10051_market'],amt_qty_tp='0',base_dt=session.replace('-',''),stex_tp='3')
        if r['request']['body']!=body or r['request']['route']!='/api/dostk/sect' or r['request']['api_id']!='ka10051':
            raise ValueError('completed_flow_exact_request_date_or_units')
        if h['request']['body']!={'mrkt_tp':spec['ka20001_market'],'inds_cd':spec['code']}:
            raise ValueError('completed_flow_history_market_identity')
        observed=datetime.fromisoformat(r['received_at'])
        if observed>cutoff:raise ValueError('completed_flow_after_cutoff')
        historical=KiwoomKrMarketContextService._completed_history_row(history=history,session_date=date.fromisoformat(session),observed_at=observed)
        row=_aggregate_row(payload,market=market,code=spec['code'])
        if str(row['inds_cd']).removesuffix('_AL')!=spec['code'] or row['inds_nm']!=f'종합({market})':
            raise ValueError('completed_flow_composite_identity')
        if (abs(Decimal(row['cur_prc']))/100!=abs(Decimal(historical['cur_prc_n']))
                or Decimal(row['flu_rt'])/100!=Decimal(historical['flu_rt_n'])):
            raise ValueError('completed_flow_exact_completed_index')
        dates=[payload[k] for k in ('base_dt','dt','trde_dt') if k in payload]
        dates += [row[k] for k in ('base_dt','dt','trde_dt') if k in row]
        if any(str(v).replace('-','')!=session.replace('-','') for v in dates):
            raise ValueError('completed_flow_contradicting_response_date')
        if graph.accepted_pages[graph.child_receipts.index(r)]['continuation']:
            raise ValueError('completed_flow_aggregate_page_incomplete')
        for actor,(field,_) in FLOW_FIELDS.items():
            result.append(MarketFlowFact(actor=actor,market=market,net_buy_amount=_signed_int(row[field])*KA10051_AMOUNT_UNIT_KRW,
                currency='KRW',exchange_basis='KRX_NXT_INTEGRATED',source_unit='100M_KRW',source_unit_scale_krw=KA10051_AMOUNT_UNIT_KRW,
                source_ref=f'kiwoom:ka10051:{market}:{actor}:{session}'))
        bindings.append(dict(market=market,base_dt=body['base_dt'],aggregate_code=row['inds_cd'],row_count=len(payload['inds_netprps']),
            completed_index=str(abs(Decimal(row['cur_prc']))/100),requested_at=r['requested_at'],received_at=r['received_at'],
            request_sha256=r['request_sha256'],raw_sha256=r['artifact_sha256'],history_raw_sha256=h['artifact_sha256'],
            response_date_echo_present=bool(dates)))
    validate_aggregate_flow_rows(result,session=session)
    return CompletedDateAggregateFlows(session=session,market_flows=tuple(result),bindings=tuple(bindings),
        provider_document=dict(repository='Kiwoom-Securities/Kiwoom-REST-API',commit=official_commit,sha256=official_sha256,
            temporal_basis='Official base_dt reference-date contract + original exact request + independent date-specific index equality',
            unit_basis='Original Kiwoom MarketFlowFact amt_qty_tp=0 normalization at 100M_KRW; unchanged'),
        original_aggregate_sha256=receipt.aggregate_sha256,first_system_available_at=receipt.received_at)
