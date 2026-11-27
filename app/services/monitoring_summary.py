"""Deterministic cohort presentation from the existing accepted detailed plans.

No model, price derivation engine, new investment authority, or source I/O.
The logical message plan includes one summary alongside the market and stocks.
"""
from datetime import datetime
from decimal import ROUND_FLOOR
from zoneinfo import ZoneInfo

from app.services.unified_snapshot_contract import digest


def accepted_stock_summary(packet, plan, entry_context):
    from app.services.detailed_stock_message_v2 import (
        _completed_price_session, _entry_assessment, final_entry_action,
    )
    from app.services.kr_forward_valuation_message import KrForwardMessagePlan
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
    return dict(ticker=packet.ticker,status='COMPLETE',price=price(base.valuation.price),
        overall=decision['overall_direction'],holder={'HOLDABLE':'HOLD','REVIEW':'REVIEW','REDUCE':'REDUCE'}[decision['holder']],
        economic=output['new_buyer'],technical=state,entry_quality=assessment.quality,
        rr=rr_text, support=(price(entries['tactical_watch_low'])+'–'+price(entries['tactical_watch_high']) if support else '미산출'),
        rr2=rr2,economic_preferred=economic,action=action,action_class=action_class,
        plan_sha256=plan.acceptance_sha256)


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
                lines.append(row['ticker']+' — '+('B2 타임아웃·분석 미완료' if row['status']=='B2_UNISSUED_TIMEOUT'
                             else '판단 자료 부족(OBSERVE) · '+row.get('price','미확보')))
                continue
            lines.extend((f"{row['ticker']} {row['price']} | {row['overall']} · 보유 {row['holder']} · 기술 {row['technical']} · RR {row['rr']}",
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
            if omitted[ticker]['status']!='B2_UNISSUED_TIMEOUT':
                raise ValueError('summary_unknown_omission')
            rows.append(dict(ticker=ticker,status='B2_UNISSUED_TIMEOUT',omission_sha256=digest(omitted[ticker])))
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


def verify_summary_message(*, messages,market,subjects,omitted):
    matches=[m for m in messages if m['message_id']=='SUMMARY_'+market.upper()]
    if len(matches)!=1:
        raise ValueError('summary_message_missing_or_duplicate')
    actual=matches[0]
    binding=actual['summary_binding']
    expected=summary_message(market=market,generation=actual['generation_id'],subjects=subjects,
        messages=[m for m in messages if m['message_id'] in subjects],omitted=omitted,
        completed=binding['completed'],cutoff=binding['cutoff'])
    if any(actual.get(k)!=v for k,v in expected.items()):
        raise ValueError('summary_message_content_drift')
