"""Original structure engines to dated, reference-only research price facts."""
import json
import math
from datetime import date
from app.services.vnext_research_store import digest
from app.services.ohlcv_structure_service import analyze_chart_structure
from app.services.monitoring_state_service import _nearest_meaningful_zones
from app.services.current_price_context_service import select_current_price_context
from app.services.multi_timeframe_price_structure_service import (
    build_price_structure_evidence_packet, reference_select_price_structure,
    validate_price_structure_selection,
)
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows

CONTRACT = 'vnext-original-price-structure-reference-v1'


def _chart_replay(entry, source_bytes):
    from app.services.vnext_rolling_chart import resolve_chart
    return resolve_chart(entry, source_bytes)


def build_price_attachment(packet, source_bytes):
    """Replay only exact frozen packet source members. No live/Native authority.

    source_bytes is supplied by the trusted local CAS resolver, not the model.
    Incomplete roles cannot enrich the structure or its cross-timeframe score.
    """
    identity = packet.get('public_security', {})
    if not identity.get('canonical_security_id') or not identity.get('ticker'):
        return dict(contract=CONTRACT, status='NOT_QUALIFIED', reasons=['SECURITY_NOT_PRESENT'], facts=[])
    close = next((e for e in packet['evidence'] if e['field']=='completed_close'), None)
    if close is None:
        return dict(contract=CONTRACT,status='NOT_QUALIFIED',reasons=['COMPLETED_SESSION_MISSING'],facts=[])
    session = close['data']['calendar']['session']; currency = close['data']['currency']
    expected_currency = {'KR':'KRW','US':'USD'}.get(identity['country'])
    if currency != expected_currency:
        raise ValueError('price_currency_identity_mismatch')
    periods = {}; sources = {}; rejected = {}; views = {}
    from app.services.vnext_timeframe_views import CONTRACT as VIEW_CONTRACT, replay_view
    view_policy = packet.get('timeframe_view_policy')
    if view_policy is not None and view_policy != VIEW_CONTRACT:
        raise ValueError('unknown_timeframe_view_policy')
    for tf, count in (('daily',1000),('weekly',700),('monthly',300)):
        e = next((e for e in packet['evidence'] if e['field']=='ohlcv.adjusted_'+tf), None)
        if view_policy and e is not None:
            binding = packet.get('timeframe_view_inputs', {}).get(tf)
            if not binding:
                rejected[tf] = 'ORIGINAL_PERIOD_RECEIPT_MISSING'; continue
            view = replay_view(e, source_bytes, identity=identity, timeframe=tf, session=session, binding=binding)
            views[tf] = {k:v for k,v in view.items() if k!='rows'}
            if not view['rows']:
                rejected[tf] = view['status']; continue
            periods[tf] = view['rows']
            sources[tf] = dict(raw_sha256=e['source_sha'], fact_ref=e['ref'],
                parser_sha256=view['parser_sha256'], page_sha256=view['page_sha256'],
                source_captured_at=e['data']['source_captured_at'],
                view_sha256=view['consumer_input_sha256'], source_kind=view['source_kind'],
                start=view['start'], end=view['end'], count=view['count'])
            continue
        if e is None or e['status']!='SOURCE_REFERENCE':
            rejected[tf] = e['data'].get('reason',e['status']) if e else 'ROLE_ABSENT';continue
        from app.services.vnext_rolling_chart import resolve_chart
        try:
            b=resolve_chart(e,source_bytes,security=identity)
        except ValueError as exc:
            # A denied original price role cannot invalidate independent facts.
            # Provenance, identity and resource errors still fail the packet.
            if str(exc) != 'incremental_original_quality_denied':
                raise
            rejected[tf]='ORIGINAL_QUALITY_REPLAY_DENIED'
            continue
        body=b['request_body'];rows=b['selected']
        if (body['stk_cd']!=identity['ticker'].replace('.','-') or body.get('upd_stkpc_tp')!='1'
                or ('stex_tp' in body)!=(identity['country']=='US')
                or (identity['country']=='US' and body.get('stex_tp')!={'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}.get(identity['exchange']))
                or b['calendar']['session']!=session):
            raise ValueError('chart_security_period_or_adjustment_mismatch')
        if b['requested_rows']!=count:
            rejected[tf]='ROLE_REQUEST_WINDOW_INSUFFICIENT';continue
        if tf=='daily' and (not rows or rows[-1]['date']!=session):
            raise ValueError('chart_latest_completed_session_missing')
        if len(rows)<count or not e['data'].get('quality_valid') or not b['quality']['valid']:
            rejected[tf]='ROLE_HISTORY_OR_QUALITY_INSUFFICIENT';continue
        quality=inspect_normalized_ohlcv_rows(rows,timeframe=tf,cutoff=date.fromisoformat(session))
        if not quality.valid:
            rejected[tf]='ORIGINAL_QUALITY_REPLAY_DENIED';continue
        if not b['pages'] or not all(p.get('raw_sha256') and p.get('captured_at') for p in b['pages']):
            raise ValueError('original_page_receipt_missing')
        periods[tf]=rows;sources[tf]=dict(raw_sha256=e['source_sha'],fact_ref=e['ref'],parser_sha256=b['parser_sha256'],page_sha256=[p['raw_sha256'] for p in b['pages']],source_captured_at=e['data']['source_captured_at'])
    if 'daily' not in periods:
        result = dict(contract=CONTRACT,status='NOT_QUALIFIED',reasons=['DAILY_ROLE_NOT_QUALIFIED'],roles_rejected=rejected,facts=[])
        if view_policy:
            available=any(v['permitted_indicators'] for v in views.values())
            result.update(timeframe_view_policy=view_policy, timeframe_views=views,
                independent_features_available=available,
                status='DATED_TIMEFRAME_REFERENCE' if available else 'NOT_QUALIFIED',
                currency=currency,session=session,
                strict_native=False, economic_use=False)
        return result
    structure=analyze_chart_structure(periods,price_basis='adjusted_close')
    price=periods['daily'][-1]['close']
    multi=build_price_structure_evidence_packet(ticker=identity['ticker'],security_id=identity['canonical_security_id'],currency=currency,current_price=price,structure=structure,cutoff=session)
    selection=reference_select_price_structure(multi)
    validity=validate_price_structure_selection(multi,selection)
    if not validity.valid:raise ValueError('original_multitimeframe_selection_denied')
    support,resistance=_nearest_meaningful_zones(structure)
    monitoring=dict(current_price=price,as_of_date=structure['as_of_date'],price_basis=structure['price_basis'],active_support=support,active_resistance=resistance,chart_invalidation=structure['invalidation'],risk_reward=structure['risk_reward'])
    selected=select_current_price_context(dict(monitoring_state={'current':{'price_structure':monitoring}},decision={'currency':currency}))
    fact_source=digest(dict(sources=sources,structure=structure,multi=multi.model_dump(mode='json'),selection=selection.model_dump(mode='json')))
    facts=[]
    def add(kind,value,tf):
        if value is None:return
        facts.append(dict(kind=kind,value=value,unit='ratio' if kind.endswith('_rr') else currency,timeframe=tf,
            as_of=session,basis='ADJUSTED_CHART_REFERENCE_NOT_ORDER_PRICE',source_sha=fact_source,
            source_inputs=sources,fact_id='price.'+kind+':'+fact_source[:16]))
    for name in ('support','resistance'):
        z=selected['active_'+name]
        if z.get('available') and z.get('strength') in ('Strong','Medium'):
            for bound in ('low','high'):add(name+'_'+bound,z['zone_'+bound],z['timeframe'])
    inv=selected['chart_invalidation']
    if inv.get('available') and inv.get('timeframe') in ('daily','weekly'):
        add('chart_invalidation',inv['price'],inv['timeframe'])
    rr=structure['risk_reward']
    if rr.get('available') and rr.get('nearest_target_enforced'):
        for scenario in ('current_price','support_entry'):
            v=rr.get(scenario)
            if v and v['upside']>0 and v['downside']>0:add(scenario+'_rr',v['ratio'],inv['timeframe'])
    result = dict(contract=CONTRACT,status='DATED_CHART_REFERENCE',security_id=identity['canonical_security_id'],
        ticker=identity['ticker'],currency=currency,session=session,source_generation=packet['run_id'],
        current_collection=False,executable_order_price=False,adjusted_unadjusted_equivalence_proven=False,
        source_sha=fact_source,sources=sources,roles_rejected=rejected,structure=structure,
        multi_packet=multi.model_dump(mode='json'),multi_selection=selection.model_dump(mode='json'),
        selected_context=selected,facts=facts,strict_native=False)
    if view_policy:
        result.update(timeframe_view_policy=view_policy,timeframe_views=views)
    return result


def numeric_price_catalog(packet):
    attachment=packet.get('price_attachment')
    if attachment is None:return []
    if attachment.get('contract')!=CONTRACT:raise ValueError('price_attachment_contract')
    result=[]
    for f in attachment['facts']:
        row=dict(fact_id=f['fact_id'],field_path='/price_attachment/'+f['kind'],value=f['value'],unit=f['unit'],
            basis=f['basis'],as_of=f['as_of'],source_sha=f['source_sha'],kind=f['kind'],timeframe=f['timeframe'])
        row['catalog_id']='c'+digest(row)[:16];result.append(row)
    for tf,view in attachment.get('timeframe_views',{}).items():
        for index,f in enumerate(view['features']['facts']):
            try:value=float(f['value'])
            except (ValueError,TypeError):continue
            if not math.isfinite(value):continue
            unit=attachment.get('currency') if f['unit']=='price' else f['unit']
            if not unit:continue
            row=dict(fact_id='analytic:'+view['consumer_input_sha256'],
                field_path='/price_attachment/timeframe_views/'+tf+'/features/facts/'+str(index)+'/value',
                value=value,unit=unit,basis=f['input_basis'],as_of=f['as_of'],source_sha=view['consumer_input_sha256'],
                analytic_timeframe=tf,semantic=f['semantic'])
            row['catalog_id']='c'+digest(row)[:16];result.append(row)
    return result


def price_message(attachment):
    """Deterministic consumer preview; separate from model judgment."""
    rows={r['kind']:r for r in attachment['facts']};bindings=[]
    def take(kind):
        f=rows.get(kind)
        if f is None:return None
        unit='배' if f['unit']=='ratio' else {'USD':'달러','KRW':'원'}[f['unit']]
        rendered=f"{f['value']:,}{unit}";bindings.append(dict(**f,rendered=rendered));return rendered
    def zone(role):
        low,high=take(role+'_low'),take(role+'_high')
        return low+'~'+high if low is not None and high is not None else None
    s,r,iv=zone('support'),zone('resistance'),take('chart_invalidation')
    cr,sr=take('current_price_rr'),take('support_entry_rr')
    if not (s or r):return dict(newbuyer='현재 자료로 신뢰할 진입 가격대를 제시하기 어렵습니다.',holder='보유 판단은 사업 논리와 가격 위험을 분리하며, 검증된 구조 가격이 필요합니다.',bindings=[])
    prefix=f"{attachment['session']} 완료봉의 조정 차트 참고 가격이며 현재 호가가 아닙니다. "
    nb=(('관심 진입 '+s+'의 지지 확인을 관찰. ') if s else '')+(('가까운 저항 '+r+'은 보장된 목표가가 아님. ') if r else '')
    hd=(('유지 관찰 지지 '+s+'. ') if s else '')+(('반등 시 '+r+'의 부담을 별도 검토. ') if r else '')
    if iv:
        condition='완료 일봉의 연속 이탈 또는 완료 주봉의 이탈을 확인할 때 가격 위험 재검토'
        nb+='차트 무효화 '+iv+': '+condition+'. ';hd+='차트 무효화 '+iv+': '+condition+'. 사업 논리 붕괴와는 별개. '
    if cr:nb+='완료봉 종가 기준 R/R '+cr+'. '
    if sr:nb+='지지 중간값 가정 R/R '+sr+'이며 주문가격이 아님. '
    hd+='추가매수는 신규 진입 위험보상 검토와 분리.'
    return dict(newbuyer=prefix+nb,holder=prefix+hd,bindings=bindings)
