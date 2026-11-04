"""Deterministic display of live-owned dated facts; no new investment signal."""
from app.services.vnext_dated_technical_owner import DatedTechnicalOwner, TARGETS
from app.services.vnext_research_store import digest

CONTRACT = 'dated-technical-appendix-v1'
DISPLAY = ('close', 'sma_20', 'sma_50', 'sma_100', 'sma_200',
           'ema_20', 'ema_50', 'ema_100', 'ema_200', 'rsi_14', 'atr_14',
           'macd_12_26', 'macd_signal_9', 'macd_histogram',
           'rolling_high_120', 'rolling_low_120', 'rolling_high_252', 'rolling_low_252')
MINIMUM = {**{f'{kind}_{n}': n for kind in ('sma', 'ema') for n in (20,50,100,200)},
           'close': 1, 'rsi_14': 15, 'atr_14': 14, 'macd_12_26': 26,
           'macd_signal_9': 34, 'macd_histogram': 34,
           **{f'rolling_{kind}_{n}': n for kind in ('high','low') for n in (120,252)}}


def build_appendix(owner, *, security, cutoff):
    if type(owner) is not DatedTechnicalOwner:
        raise ValueError('appendix_live_original_owner_required')
    roles = {}
    for tf in TARGETS:
        kw = dict(security=security, timeframe=tf, cutoff=cutoff)
        if tf not in owner.sources:
            roles[tf] = dict(status='SOURCE_NOT_QUALIFIED', reason='ROLE_ABSENT')
            continue
        try:
            receipt = owner.issue(**kw)
            value = owner.consume(receipt, **kw)
        except ValueError as exc:
            # Revocation, identity and ownership failures are not displayable.
            if str(exc) != 'history_no_contiguous_qualified_rows':
                raise
            roles[tf] = dict(status='SOURCE_NOT_QUALIFIED', reason=str(exc))
            continue
        facts = {f['semantic']: f for f in value['features']['facts']}
        count = len(value['rows'])
        indicators = {}
        for name in DISPLAY:
            if name in facts:
                f = facts[name]
                if f['minimum_history'] > count:
                    raise ValueError('appendix_feature_minimum_history')
                indicators[name] = dict(status='DATED_NOT_CURRENT', fact=f)
            else:
                indicators[name] = dict(status='INSUFFICIENT_HISTORY' if count < MINIMUM[name]
                    else 'SOURCE_NOT_QUALIFIED', minimum_history=MINIMUM[name])
        roles[tf] = dict(status='TECHNICAL_DATED_REFERENCE_ONLY', count=count,
            requested_up_to=TARGETS[tf], as_of=value['effective_analysis_as_of'],
            basis=value['basis'], currency=security.get('currency', 'NOT_QUALIFIED'),
            receipt_sha256=digest(value), sources=value['sources'],
            source_views=value['source_views'], conflicts=value['conflicts'],
            indicators=indicators, all_engine_facts=value['features']['facts'],
            adjustment_authority='PROVIDER_BASIS_ONLY_NOT_INDEPENDENT_ACTION_PROOF',
            exhaustion_meaning='PAGE_EXHAUSTION_NOT_LISTING_AGE_PROOF')
    return dict(contract=CONTRACT, security=security, cutoff=cutoff, roles=roles,
        permitted_slots=['summary','uncertainty'], new_judgment=False, current_price=False,
        timing=False, newbuyer=False, holder=False, overall=False, strict_ready=False, send=False)


def render_appendix(value):
    if value['contract'] != CONTRACT:
        raise ValueError('appendix_contract')
    lines = [f"# {value['security']['ticker']} | DATED_TECHNICAL_APPENDIX", '',
        '과거 기준 기술 참고 / NO-SEND. 기존 AI 판단과 별개이며 현재 가격·매수·보유·Timing 권한이 없습니다.', '']
    for tf, role in value['roles'].items():
        lines += [f'## {tf}', '']
        if role['status'] == 'SOURCE_NOT_QUALIFIED':
            lines += [f"SOURCE_NOT_QUALIFIED: {role['reason']}", '']; continue
        lines += [f"{role['count']}봉 / 최대 목표 {role['requested_up_to']}봉 | 완료 기간 종료일 {role['as_of']} | {role['basis']} | 통화 {role['currency']}",
            f"Owner receipt: `{role['receipt_sha256']}`", '',
            '| 지표 | 값 / 원본 단위 | 공급자 봉 표시일 | 최소 봉 | 원래 공식 |', '|---|---|---|---:|---|']
        for name, item in role['indicators'].items():
            if 'fact' not in item:
                lines.append(f"| {name} | {item['status']} | - | {item['minimum_history']} | - |")
                continue
            f = item['fact']
            lines.append(f"| {name} | {f['value']} {f['unit']} | {f['as_of']} | {f['minimum_history']} | {f['formula'].replace('|','/')} |")
        lines += ['', 'SMA/EMA60은 기존 FeatureEngine에 없어 생성하지 않았습니다. 50기간 지표와 구분합니다.',
            '주·월봉은 독립 native 원본입니다. 페이지 소진은 상장 연한 확정이 아닙니다.',
            '주·월봉의 공급자 표시일과 완료 기간 종료일은 다를 수 있습니다. price 단위에 별도 검증되지 않은 통화를 덧붙이지 않습니다.',
            '지표별 전체 입력·의존 구간 SHA와 공식은 같은 이름의 JSON에 있습니다.', '']
        for s in role['sources']:
            lines.append(f"- 검토한 원본 `{s['source_generation']}` / `{s['source_sha256']}` / 마지막 원본 {s['last_raw_date']}")
        for v in role['source_views']:
            bad=v.get('first_invalid')
            lines.append(f"- 원본 {v['full_source_rows']}봉 → 완료 후보 {v['completed_rows']}봉 → 연속 {v['count']}봉; "
                f"최초 차단 {bad if bad else '없음'}; 미완료 제외 {v['excluded_incomplete']}; 최종 미확정 제외 {v.get('excluded_latest_unsettled',[])}")
        for conflict in role['conflicts']:
            lines.append(f"- 연결 거절: {conflict['reason']} / {', '.join(conflict['changed_dates']) or '중복 기간 없음'}")
        lines.append('')
    return '\n'.join(lines)
