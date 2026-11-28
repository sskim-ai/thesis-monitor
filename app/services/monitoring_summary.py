"""Deterministic cohort presentation from the existing accepted detailed plans.

No model, price derivation engine, new investment authority, or source I/O.
The logical message plan includes one summary alongside the market and stocks.
"""
from datetime import datetime
from decimal import ROUND_FLOOR
from zoneinfo import ZoneInfo

from app.services.unified_snapshot_contract import digest


def preopen_source_context(source):
    """Keep only actual checked scopes and existing event IDs; unknown stays visible."""
    owned = source.get('preopen_source', {})
    watermarks = dict(owned.get('event_watermarks', {}))
    events = source.get('event_view', {})
    receipt, binding = events.get('receipt', {}), events.get('binding', {})
    provider = binding.get('provider')
    if provider:
        checked = (receipt.get('request_started_at') is not None and receipt.get('received_at') is not None
                   and binding.get('denial') in (None, 'no_qualified_business_event'))
        watermarks[provider] = dict(status='CHECKED' if checked else 'UNAVAILABLE',
            acquisition_class=receipt.get('acquisition_class'),
            coverage='BOUNDED_NEWS_SEARCH', requested_at=receipt.get('request_started_at'),
            received_at=receipt.get('received_at'), source_query_cutoff=receipt.get('source_query_cutoff'),
            ids=sorted({row['event_fingerprint'] for row in binding.get('selected', ())
                        if row.get('status') == 'PASS' and row.get('event_fingerprint')}),
            source_receipt_sha256=receipt.get('source_receipt_sha256'))
    return dict(security=owned.get('security'), event_watermarks=watermarks)


def _preopen_stock(packet, plan, base, context, output, assessment, session, selected,
                   support_row, scenario_row, scenario_value):
    from app.services.new_buyer_base_contract import number

    source = base.source_stock
    valuation = base.valuation
    currency, security_id = valuation.currency, plan.authorization.security_id
    projection = source.get('completed_session_current_price') or {}
    close_ref = next((key for row in plan.rows if row.section == 'price'
                      for key in row.numeric_registry_keys if key.endswith(':fields.current_price')), None)
    close = (valuation.price if close_ref and session is not None
        and projection.get('availability') == 'AVAILABLE'
        and projection.get('price_as_of') == session == valuation.price_session.isoformat()
        and projection.get('current_price') == valuation.price
        and projection.get('currency') == currency
        and projection.get('adjustment_basis') == valuation.price_basis else None)
    sc = assessment.scenario or {}
    support = None
    if support_row is not None:
        ref = support_row.source_fact_ids[0]
        evidence = next(row for row in packet.evidence if row.ref_id == ref)
        from app.services.entry_candidate_basis import statement

        entries = base.accepted_calibration.entries
        support = dict(candidate_id=output['timing_context']['selected'], ref=ref,
            low=entries['tactical_watch_low'], high=entries['tactical_watch_high'],
            timeframe=statement({'statement': evidence.statement}).get('timeframe'),
            status=sc.get('status'))
    stop_row = next((row for row in plan.rows if row.row_id == 'price:selected-support-invalidation'), None)
    stop = float(assessment.invalidation_price) if stop_row is not None else None
    target, rr = scenario_value('current_target'), scenario_value('current_rr')
    target_basis = sc.get('current_target_basis') if target is not None else None
    applicable_from = (close if close is not None and stop is not None and target is not None
        and stop < close < target and rr is not None and target_basis
        and sc.get('possible_current_barrier') is None and not sc.get('current_rr_reason')
        and not sc.get('current_overlap') and not sc.get('active_obstacle') else None)
    current_scenario = None
    if stop_row is not None or scenario_row is not None:
        current_scenario = dict(target=target, target_basis=target_basis, stop=stop,
            stop_ref=assessment.invalidation_ref if stop is not None else None,
            stop_timeframe=assessment.invalidation_timeframe if stop is not None else None,
            status=sc.get('status'), rr=rr, possible_barrier=scenario_value('possible_current_barrier'),
            reason=sc.get('current_rr_reason'), applicable_from=applicable_from)
    band_target = scenario_value('band_target')
    support_scenario = None
    if scenario_row is not None:
        support_scenario = dict(target=band_target,
            target_basis=sc.get('band_target_basis') if band_target is not None else None,
            assumption=sc.get('band_target_assumption') if band_target is not None else None,
            rr=scenario_value('band_rr'), intersection=sc.get('rr2_intersection'),
            rr2_low=scenario_value('rr2_low'), rr2_high=scenario_value('rr2_high'),
            reason=sc.get('band_reason'), overlap=sc.get('band_overlap'))
    history = context.get('historical_price_context') or {}
    review = output.get('economic_price_review') or {}
    side = review.get('preferred_boundary', 'NONE')
    boundary = number(selected.get(side.lower())) if selected and side in ('LOW', 'HIGH') else None
    candidate_row = next((row for row in plan.rows if row.row_id == 'valuation:historical-price-context'), None)
    if (boundary is None or boundary <= 0 or not candidate_row
            or selected.get('candidate_sha256') not in candidate_row.source_hashes):
        boundary = None
    quote = history.get('current_price') or {}
    comparable = (boundary is not None and selected.get('currency') == quote.get('currency') == currency
                  and close is not None and quote.get('as_of') == session and quote.get('basis') == valuation.price_basis
                  and number(quote.get('value')) == number(close)
                  and (selected.get('origin') != 'PROVIDER_QUARTERLY_REFERENCE'
                       or selected.get('quote_basis_comparable') is True))
    economics = dict(candidate_id=review.get('candidate_id'), origin=selected.get('origin', 'HISTORICAL_REFERENCE') if selected else None,
        side=side, price=float(boundary) if boundary is not None else None,
        price_basis=valuation.price_basis if comparable else None,
        status='CONDITIONAL' if boundary is not None else 'UNSELECTED' if selected else
            'UNRESOLVED' if history.get('candidates') else 'UNAVAILABLE')
    provenance = preopen_source_context(source)
    technical = output.get('technical_assessment', {})
    return dict(version=1, security_id=security_id, market=packet.market,
        exchange=(provenance['security'] or {}).get('exchange') or projection.get('exchange'), currency=currency,
        price_basis=valuation.price_basis if close is not None else None, price_precision=1 if currency == 'KRW' else .01,
        close=close, close_ref=close_ref if close is not None else None, close_session=session,
        close_reason=None if close is not None else 'COMPLETED_CLOSE_UNAVAILABLE',
        support=support, current_scenario=current_scenario, support_scenario=support_scenario, economics=economics,
        active_material_risk=bool(context['active_risk_refs']), confidence_veto=bool(context['confidence_veto_refs']),
        technical_state=technical.get('state'), technical_change=technical.get('change'),
        entry_quality=assessment.quality, entry_reason=assessment.reason_code, **provenance)


def _rr_basis(quality, rr, target, barrier):
    if quality == 'BLOCKED' or rr is None or target is None:
        return None
    return 'ENTRY 적격 저항 기준' + (' · 중간 장벽 역할 미확정' if barrier is not None else '')


def accepted_stock_summary(packet, plan, entry_context):
    from app.services.detailed_stock_message_v2 import (
        _completed_price_session, _entry_assessment, final_entry_action,
    )
    from app.services.kr_forward_valuation_message import KrForwardMessagePlan
    from app.services.detailed_stock_message_service import reference_price_display
    from app.services.new_buyer_base_contract import number
    from app.services.price_structure_v3_renderer_service import _price_display

    base = plan.base.base if isinstance(plan.base, KrForwardMessagePlan) else plan.base
    context = plan.b2_request['provider_request']['input']
    output = plan.b2_result['output']['new_buyer_shadow']
    decision = base.accepted_calibration.decision
    session = _completed_price_session(packet,base,plan.authorization.security_id)
    assessment = _entry_assessment(context,output['timing_context'],entry_context,packet.market,session)
    action = final_entry_action(output,context,assessment)
    currency = base.valuation.currency
    def price(value):
        return _price_display(value,currency) if value is not None else '미산출'
    technical = output.get('technical_assessment',{})
    state = {'SUPPORTIVE':'지지','MIXED':'혼재','ADVERSE':'약화','INSUFFICIENT':'자료 부족'}.get(technical.get('state'),'미산출')
    change = {'IMPROVING':'개선','DETERIORATING':'악화','STABLE':'변화 제한'}.get(technical.get('change'))
    if change:
        state += '·'+change
    support = next((r for r in plan.rows if r.row_id=='price:accepted-tactical-support'),None)
    scenario = next((r for r in plan.rows if r.row_id=='price:selected-support-rr'),None)
    entries = base.accepted_calibration.entries
    sc = assessment.scenario or {}
    keys = set(scenario.numeric_registry_keys if scenario else ())
    def value(field):
        key = sc.get('evidence_ref','').removeprefix('canonical:')+':fields.entry_scenario.'+field
        return sc.get(field) if key in keys else None
    rr = number(value('current_rr'))
    rr_text = ('2배 미만' if rr is not None and rr < 2 and f'{rr:.2f}'=='2.00'
               else f'{rr:.2f}배' if rr is not None else '미산출')
    low, high = value('rr2_low'),value('rr2_high')
    rr2 = (price(low)+'–'+price(high) if low is not None and high is not None else
           '교집합 없음' if scenario and sc.get('rr2_intersection')=='EMPTY' else
           '표시 정밀도 미만' if scenario and sc.get('rr2_intersection')=='BELOW_DISPLAY_PRECISION' else '미산출')
    if assessment.quality=='BLOCKED':
        rr_text=rr2='구조 재검토'
    rr_basis = _rr_basis(assessment.quality, rr, value('current_target'), value('possible_current_barrier'))
    historical = context.get('historical_price_context') or {}
    review = output.get('economic_price_review') or {}
    selected = next((r for r in historical.get('candidates',()) if r['candidate_id']==review.get('candidate_id')),None)
    eligible = (context['business_gate']['v2_business_gate_pass'] and not context['active_risk_refs']
                and not context['confidence_veto_refs']
                and context['valuation_evaluability']['evaluability_state']=='EVALUABLE')
    economic = ('경제적 시나리오 미확정' if historical.get('candidates') and eligible
                else '선택 제한' if historical.get('candidates') else '미산출')
    if selected:
        economic = '선호가 미선택'
        if review.get('preferred_boundary') in ('LOW','HIGH'):
            ceiling = number(selected[review['preferred_boundary'].lower()])
            precision = number(1 if currency=='KRW' else '0.01')
            ceiling = ceiling.quantize(precision,rounding=ROUND_FLOOR)
            if ceiling > 0:
                economic = price(float(ceiling))+' 이하 선호'
                if selected.get('origin')=='PROVIDER_QUARTERLY_REFERENCE' and not selected.get('quote_basis_comparable'):
                    economic += '(조건부·가격기준 미확정)'
    action_class = ('REVIEW_NOW' if action=='신규 매수 검토 가능'
                    else 'CONDITIONAL' if action.startswith('조건부 신규 매수 검토 가능')
                    else 'AVOID' if output['new_buyer']=='AVOID' else 'WAIT')
    quote = reference_price_display(base.valuation.price,currency) if base.valuation.price is not None else '미산출'
    return dict(ticker=packet.ticker,status='COMPLETE',price=quote,
        overall=decision['overall_direction'],holder={'HOLDABLE':'HOLD','REVIEW':'REVIEW','REDUCE':'REDUCE'}[decision['holder']],
        economic=output['new_buyer'],technical=state,entry_quality=assessment.quality,
        rr=rr_text, **({'rr_basis': rr_basis} if rr_basis else {}), support=(price(entries['tactical_watch_low'])+'–'+price(entries['tactical_watch_high']) if support else '미산출'),
        rr2=rr2,economic_preferred=economic,action=action,action_class=action_class,
        plan_sha256=plan.acceptance_sha256,
        preopen=_preopen_stock(packet, plan, base, context, output, assessment, session, selected,
                               support, scenario, value))


def _render(market, completed, cutoff, rows):
    stamp = datetime.fromisoformat(cutoff).astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()
    done = [r for r in rows if r['status']=='COMPLETE']
    counts = {k:sum(r['economic']==k for r in done) for k in ('ATTRACTIVE','WAIT','AVOID')}
    immediate = sum(r['action_class']=='REVIEW_NOW' for r in done)
    conditional = sum(r['action_class']=='CONDITIONAL' for r in done)
    lines = [('한국' if market=='kr' else '미국')+' 종목 Summary',
        f'기준 완료장 {completed} · 분석 기준일 {stamp} KST',
        f'분석 완료 {len(done)}/{len(rows)} · 신규매수 검토 가능 {immediate+conditional} (일반 {immediate}, 조건부 {conditional})',
        f"기업·가격 매력 {counts['ATTRACTIVE']} · 대기 {counts['WAIT']} · 회피 {counts['AVOID']} · 미완료/제한 {len(rows)-len(done)}",
        '가격은 기준 종가·관찰 구간이며 매수 주문가가 아님. RR2는 기존 구조 유지 전제.']
    for group,title in (('ATTRACTIVE','기업·가격 매력 있음'),('WAIT','경제적 조건 대기'),('AVOID','신규매수 회피'),('LIMIT','분석 미완료·제한')):
        selected = [r for r in rows if (r.get('economic')==group if group!='LIMIT' else r['status']!='COMPLETE')]
        if not selected:
            continue
        lines.extend(('',title))
        for row in selected:
            if row['status']!='COMPLETE':
                status = row['status']
                if status in {'CORE_UNISSUED_TIMEOUT','A_UNISSUED_TIMEOUT','B_UNISSUED_TIMEOUT','B2_UNISSUED_TIMEOUT'}:
                    label = status.split('_',1)[0]+' 타임아웃·분석 미완료'
                else:
                    label = '판단 자료 부족(OBSERVE) · '+row.get('price','미확보')
                lines.append(row['ticker']+' — '+label)
                continue
            rr_note = ' (' + row['rr_basis'] + ')' if row.get('rr_basis') else ''
            lines.extend((f"{row['ticker']} {row['price']} | {row['overall']} · 보유 {row['holder']} · 기술 {row['technical']} · RR {row['rr']}{rr_note}",
                f"지지 {row['support']} | RR2 {row['rr2']} | 경제 {row['economic_preferred']}",
                row['action']))
    return '\n'.join(lines)


def summary_message(*, market,generation,subjects,messages,omitted,completed,cutoff):
    expected = set(subjects)
    if len(expected)!=len(subjects) or set(omitted)-expected:
        raise ValueError('summary_subject_scope')
    by_id = {m['message_id']:m for m in messages}
    if len(by_id)!=len(messages) or set(by_id)!=expected-set(omitted):
        raise ValueError('summary_detail_coverage')
    rows=[]
    for ticker in subjects:
        if ticker in omitted:
            status = omitted[ticker]['status']
            if status not in {'CORE_UNISSUED_TIMEOUT','A_UNISSUED_TIMEOUT','B_UNISSUED_TIMEOUT','B2_UNISSUED_TIMEOUT'}:
                raise ValueError('summary_unknown_omission')
            rows.append(dict(ticker=ticker,status=status,omission_sha256=digest(omitted[ticker])))
        else:
            m=by_id[ticker]
            row=m['summary_row']
            if row['ticker']!=ticker or row['plan_sha256']!=m['plan_sha256'] or m['generation_id']!=generation:
                raise ValueError('summary_detail_plan_drift')
            rows.append(row)
    binding=dict(market=market,generation=generation,subjects=list(subjects),completed=completed,cutoff=cutoff,rows=rows)
    text=_render(market,completed,cutoff,rows)
    return dict(message_id='SUMMARY_'+market.upper(),generation_id=generation,text=text,
        plan_sha256=digest(binding),content_sha256=digest(text),summary_binding=binding)


def verify_summary_message(*, messages,market,subjects,omitted,expected_cutoff=None,
                           expected_generation=None,expected_completed=None):
    matches=[m for m in messages if m['message_id']=='SUMMARY_'+market.upper()]
    if len(matches)!=1:
        raise ValueError('summary_message_missing_or_duplicate')
    actual=matches[0]
    binding=actual['summary_binding']
    ids=['MARKET_'+market.upper(),'SUMMARY_'+market.upper(),*[t for t in subjects if t not in omitted]]
    if ([m['message_id'] for m in messages] != ids
            or (expected_cutoff is not None and binding['cutoff'] != expected_cutoff)
            or (expected_generation is not None and actual['generation_id'] != expected_generation)
            or (expected_completed is not None and binding['completed'] != expected_completed)):
        raise ValueError('summary_frozen_cohort_binding_drift')
    expected=summary_message(market=market,generation=actual['generation_id'],subjects=subjects,
        messages=[m for m in messages if m['message_id'] in subjects],omitted=omitted,
        completed=binding['completed'],cutoff=binding['cutoff'])
    if any(actual.get(k)!=v for k,v in expected.items()):
        raise ValueError('summary_message_content_drift')
