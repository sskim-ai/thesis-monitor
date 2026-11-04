"""Deterministic presentation of an already validated, public research judgment.

This module issues no financial or model authority. The live review owner calls
it only after the original output and exact parent have passed validation.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import re

from app.services.vnext_research_store import digest
from app.services import vnext_research_v3 as v3
import copy

CONTRACT = 'vnext-readable-source-display-v1'
RESEARCH_VIEW_CONTRACT = 'ai-research-readable-and-audit-v1'
SIGNALS = {
    'LIMITED_POSITIVE': '제한적으로 긍정적', 'MIXED': '개선과 부담이 혼재',
    'LIMITED_NEGATIVE': '제한적으로 부정적', 'INSUFFICIENT_EVIDENCE': '근거 부족',
    'UNKNOWN': '미확인', 'NEUTRAL': '중립적 연구 관찰',
}
LABELS = {
    'support_low': '지지 하단', 'support_high': '지지 상단',
    'resistance_low': '저항 하단', 'resistance_high': '저항 상단',
    'chart_invalidation': '차트 무효화',
    'current_price_rr': '당시 조정 완료봉 종가 가정 손익비',
    'support_entry_rr': '지지 중간값 진입 가정 손익비',
}
TIMEFRAMES = {'daily': '일봉', 'weekly': '주봉', 'monthly': '월봉'}


def _formatted_number(value, places=2):
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValueError('readable_nonfinite_number')
    return f'{value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,.{places}f}'


def day(value):
    return str(value).split('T')[0] if value else '미확인'


def unit_value(value, unit):
    if unit == 'percent':
        return ('+' if Decimal(str(value)) > 0 else '') + _formatted_number(value) + '%'
    if unit in ('ratio', 'multiple'):
        return '약 ' + _formatted_number(value) + '배'
    if unit in ('KRW', 'KRW_PER_SHARE'):
        return ('약 ' + _formatted_number(value, 0) if unit == 'KRW' else _formatted_number(value, 1)) + '원'
    if unit in ('USD', 'USD_PER_SHARE'):
        return _formatted_number(value) + '달러'
    return _formatted_number(value) + ' ' + {'EUR': '유로', 'JPY': '엔'}.get(unit, str(unit or '단위 미확인'))


def claim_label(n):
    field = n.get('field', n.get('fact_id', '')).split(':')[0]
    metric = field.removeprefix('valuation.')
    if n.get('kind') in LABELS:
        return LABELS[n['kind']] + ' ' + unit_value(n['value'], n['unit'])
    label = {'financial.revenue': '매출', 'financial.operating_income': '영업이익',
             'financial.net_income': '순이익'}.get(field)
    if label:
        basis = {'consolidated single_quarter': '연결 단일분기',
                 'standalone single_quarter': '별도 단일분기'}.get(n.get('basis'), n.get('basis', '기준 미확인'))
        return f"{label} {unit_value(n['value'], n['unit'])} ({basis} {day(n.get('as_of'))})"
    label = {'FY1_EPS': 'KIS FY1 예상 EPS', 'FPER': '날짜 명시 FPER',
             'PER': '제공사 PER', 'PBR': '제공사 PBR'}.get(metric, metric)
    return label + ' ' + unit_value(n['value'], n['unit'])


def _text(value, claims):
    text = str(value or '')
    for n in sorted(claims, key=lambda x: len(x['rendered']), reverse=True):
        text = text.replace(n['rendered'], claim_label(n))
    # Only formatting of timestamps; original timestamps remain in the audit.
    text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', lambda m: day(m[0]), text)
    if re.search(r'\b[0-9a-f]{64}\b|Strict decision:|assessment:|chart_invalidation:|KRW_PER_SHARE', text):
        raise ValueError('readable_internal_token_requires_review')
    return text


def project(original, record, *, post_model_packet=None, persisted_record_ids=()):
    p = original['projection']; v = p['verdict']; parent = record['packet']['composite']
    if (p['binding'] != record['binding'] or digest(record['packet']) != p['binding']['packet_sha256']
            or p['public_security'] != parent['public_security'] or p['evidence_cutoff'] != parent['as_of']
            or p['decision'] is not None or v['decision'] is not None
            or p['holder_scope'] != 'HYPOTHETICAL'
            or any(p[k] is not False for k in ('send','strict_ready','holdings_included','user_thesis_included'))):
        raise ValueError('readable_exact_research_parent_required')
    if (v['newbuyer_stance'] != 'WAIT_FOR_TRIGGER' or v['holder_stance'] != 'RISK_REVIEW'
            or v['valuation_judgment'] != 'UNPROVEN'):
        raise ValueError('readable_stance_not_reviewed')
    claims = p['numeric_claims']; text = lambda s: _text(s, claims)
    prices = {}
    for n in claims:
        if n.get('kind') in LABELS:
            key = (n['kind'], n.get('as_of'), n.get('timeframe'), n['unit'])
            if key in prices and prices[key]['value'] != n['value']:
                raise ValueError('readable_conflicting_price')
            prices[key] = n
    signal = SIGNALS.get(v['economic_evidence_signal'], '기존 감사 자료의 사업 판단 참고')
    lines = [f"# {p['display_name']} ({p['public_security']['ticker']})",
             f"검증된 AI 연구 · 연구용·미발송 · 모델 근거 기준 {day(p['evidence_cutoff'])}", '',
             f'**사업: {signal}.** ' + text(v['provisional_business_signal']),
             '**가치평가: 적정가·안전마진 미입증.** 신규매수는 조건 확인 전 관망이며, 가상 보유자는 투자 논리와 가격 위험을 점검합니다.',
             '**가격/타이밍:** ' + text(v['entry_timing_view']), '', '## 투자 논리와 반론']
    for role, heading in (('economic_drivers_positive', '지지 근거'), ('economic_drivers_negative', '부담 근거')):
        for d in v[role]:
            lines.append(f"- {heading}: {text(d['claim'])} {text(d['limitations'])}")
    lines += [text(v['counterevidence']), '판단을 바꿀 반증: ' + text(v['thesis_invalidation']), '', '## 가치평가']
    lines.append(text(v['valuation_expectations']))
    for s in p['dated_scopes']:
        if s['metric'] == 'FY1_EPS':
            lines.append(f"- 전망 기간 {s['period']} · 추정 작성 {day(s['estimate_date'])} · 회계목록 {day(s['fiscal_inventory_as_of'])} (현재 최신성 미확인)")
        if s.get('price_session'):
            price_unit = s['unit'].removesuffix('_PER_SHARE') if s['unit'] not in ('multiple','ratio') else next((q['unit'].removesuffix('_PER_SHARE') for q in p['dated_scopes'] if q['metric']=='FY1_EPS'), '단위 미확인')
            lines.append(f"- FPER 분자: {day(s['price_session'])} 비수정 완료 종가 {unit_value(s['price_value'], price_unit)}. 아래 조정 차트와 별도 기준입니다.")
    extras = _post_model(parent, post_model_packet)
    if extras:
        lines += ['', '### AI 판단 이후 추가 확인된 참고 지표 (모델 미반영)']
        for n in extras:
            lines.append(f"- {claim_label(n)} · 수집 {day(n['as_of'])}. 지표 자체 기준일·분모 기간 미확인.")
        lines.append('이 값은 기존 AI 판단을 바꾸거나 과거 모델 입력의 빈 항목을 소급 보완하지 않습니다.')
    lines += ['', '## 가격과 기술적 조건']
    if prices:
        for n in prices.values():
            lines.append(f"- {day(n['as_of'])} 조정 {TIMEFRAMES.get(n.get('timeframe'), '차트')} · {claim_label(n)}")
        kinds={n['kind'] for n in prices.values()}
        absent=[]
        for label, required in (('지지', {'support_low','support_high'}),('무효화', {'chart_invalidation'}),('손익비', {'current_price_rr','support_entry_rr'})):
            if not (kinds & required): absent.append(label)
        if absent: lines.append('이 모델에 적격 ' + '·'.join(absent) + ' 수치는 제공되지 않았습니다.')
    else:
        lines.append('이 모델 입력에 적격 지지·저항·무효화·손익비 수치가 없어 가격 경계를 제시하지 않습니다.')
    for d in v['timing_support'] + v['timing_risks']:
        lines.append(text(d['claim']) + ' ' + text(d['limitations']))
    lines += ['', '## 신규매수자: 조건 확인 전 관망',
              '관망 이유: ' + text(v['newbuyer']['assessment']),
              '확인할 진입 여건: ' + text(v['newbuyer']['entry']),
              '회복 확인: ' + text(v['newbuyer']['breakout']),
              '악화 시 재점검: ' + text(v['newbuyer']['chart_invalidation']),
              '', '## 가상 보유자 관점', text(v['holder']['assessment']),
              '위험 점검: ' + text(v['holder']['risk_review']),
              '추가 보유 판단의 선행조건: ' + text(v['holder']['add_position']),
              '', '## 다음 확인', '1. ' + text(v['missing_next_fact']),
              '', '## 근거의 한계', text(v['uncertainty']),
              '', '기준 안내: 과거 동결 원본을 재사용한 미발송 연구입니다. KIS 전망은 자체 추정으로 컨센서스가 아니며, EPS와 파생 FPER는 독립 근거가 아닙니다. 제공사 배수의 지표 기준일·분모 기간은 미확인입니다. 조정 차트는 당시의 참고 시나리오로 현재 주문가격이 아닙니다. 표시 반올림은 조건 충족 판정이 아닙니다. 실제 보유내역·매수단가를 반영하지 않았으며 정식 투자판단·Native 사용권은 부여하지 않습니다.']
    if p['comparison']['blind_signal'] != p['comparison']['adjudication_signal']:
        lines.insert(-2, '재검토: ' + text(p['comparison']['change']))
    preview='\n'.join(lines)
    if re.search(r'\d+\.\d{7,}|\b[0-9a-f]{64}\b|Strict decision:|assessment:|chart_invalidation:|KRW_PER_SHARE', preview):
        raise ValueError('readable_raw_precision_or_internal_token')
    def durable(packet, n):
        return any(e.get('ref')==n.get('ref') and e.get('record_id') in persisted_record_ids
                   for e in packet.get('evidence', []))
    field_states = [dict(field=n['field'], source_as_of=n['as_of'], source_available=True,
        private_durable=durable(parent,n), model_input_consumed=True,
        used_in_model_output=any(q.get('catalog_id')==n['catalog_id'] for q in claims),
        user_displayed=any(q.get('catalog_id')==n['catalog_id'] for q in claims),
        role='ORIGINAL_MODEL_INPUT', source_ref=n.get('ref'))
        for n in record['packet']['numeric_reference_catalog']]
    field_states += [dict(field=n['field'],source_as_of=n['as_of'],source_available=True,
        private_durable=durable(post_model_packet,n),model_input_consumed=False,used_in_model_output=False,user_displayed=True,
        role='POST_MODEL_SOURCE_REFERENCE',source_ref=n.get('ref')) for n in extras]
    audit = dict(contract=RESEARCH_VIEW_CONTRACT,kind='AI_RESEARCH_EVIDENCE_AUDIT',parent_binding=deepcopy(p['binding']),
        original_product=deepcopy(original),record={k:deepcopy(val) for k,val in record.items() if k!='price_source_bytes'},
        price_bytes_sha256={k:digest(val) for k,val in record.get('price_source_bytes',{}).items()},
        post_model_packet=deepcopy(post_model_packet),post_model_numbers=deepcopy(extras),
        original_product_sha256=digest(original),readable_sha256=digest(preview),
        display_rounding_only=True,source_bytes_location='Pinned original archive, unchanged',
        field_states=field_states,all_original_warnings_preserved=True)
    return dict(readable=dict(contract=RESEARCH_VIEW_CONTRACT,kind='AI_RESEARCH_MESSAGE_READABLE',preview=preview,
        parent_binding=deepcopy(p['binding']),original_product_sha256=digest(original),audit_sha256=digest(audit),
        field_states=deepcopy(field_states),decision=None,send=False,strict_ready=False,holder_is_hypothetical=True,new_model_calls=0),audit=audit)


def _post_model(parent, later):
    if later is None: return []
    def instant(value):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None: raise ValueError('post_model_timezone_required')
        return dt
    cutoff=instant(parent['as_of'])
    if (later['public_security'] != parent['public_security'] or instant(later['as_of']) < cutoff
            or any(later[k] is not False for k in ('send','strict_ready','holdings_included','user_thesis_included'))):
        raise ValueError('post_model_public_security_scope')
    original={digest(n) for n in parent['numeric_catalog']}
    return [deepcopy(n) for n in later['numeric_catalog'] if n['field'] in ('valuation.PER','valuation.PBR')
            and digest(n) not in original and cutoff < instant(n['as_of']) <= instant(later['as_of'])]


# Preserve the original v1 composition/component/Market display API unchanged.
def number(row):
    value = Decimal(str(row['value'])); unit = row['unit']
    places = 0 if unit == 'KRW' else 2
    label = {'KRW': '원', 'USD': '달러', 'percent': '%', 'multiple': '배', 'ratio': '배', 'index': '포인트'}.get(unit, unit)
    if unit == 'KRW' and row['field_path'].startswith('/data/fields/'):
        if abs(value) >= 10**12: value /= Decimal(10**12); label = '조 원'; places = 2
        elif abs(value) >= 10**8: value /= Decimal(10**8); label = '억 원'; places = 2
    shown = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    rounded = shown != value
    return ('약 ' if rounded else '') + format(shown, ',f') + label


def readable_number(row, packet):
    text = number(row)
    if row.get('analytic_timeframe'):
        old = v3.friendly_number(row, packet)
        unit = {'USD':'달러','KRW':'원','percent':'%','ratio':'배','price':'','score':''}.get(row['unit'],row['unit'])
        return old.replace(f"{row['value']:,}"+unit, text, 1)
    if row.get('derived_role'):
        return ('당기' if row['derived_role'] == 'current' else '전기 비교')+' 영업이익률 '+text+' ('+row['as_of']+' 원문 연동 계산, 투자 사용권 아님)'
    if row.get('kind') or row.get('market_label'):
        old = v3.friendly_number(row, packet)
        unit = {'KRW':'원','USD':'달러','ratio':'배','index':'포인트','percent':'%'}[row['unit']]
        return old.replace(f"{row['value']:,}"+unit, text, 1)
    evidence = next(e for e in packet['evidence'] if e['ref'] == row['fact_id'])
    names = {'macro.DGS10':'미국 국채 십년물 금리','macro.T10YIE':'미국 십년 기대인플레이션',
        'macro.BAMLH0A0HYM2':'미국 하이일드 신용 스프레드','macro.VIXCLS':'VIX','macro.DCOILWTICO':'WTI',
        'valuation.PER':'PER','valuation.PBR':'PBR','valuation.FPER':'예상 PER'}
    label = names.get(evidence['field'], '')
    basis = row['basis'] if evidence['field'].startswith('financial.') else ''
    return (label+' ' if label else '')+text+' ('+row['as_of']+(' '+basis if basis else '')+')'


def render(checked, packet):
    """Exact path+substring replacement, retaining untouched source numeric IDs."""
    result = copy.deepcopy(checked)
    for row in result['numeric_claims']:
        path = row['text_ref']; obj = result['rendered']; keys = path.split('.')
        target = obj
        for key in keys[:-1]: target = target[int(key)] if isinstance(target, list) else target[key]
        old = row['rendered']; text = target[keys[-1]]
        if text.count(old) != 1: raise ValueError('display_occurrence_ambiguous')
        new = readable_number(row, packet)
        # Remove only a duplicated exact label immediately before this occurrence.
        for label in ('KOSPI', 'KOSDAQ', '미국 국채 십년물 금리', '미 국채 금리'):
            if new.startswith(label) or label == '미 국채 금리' and new.startswith('미국 국채 십년물 금리'):
                text = text.replace(label+' '+old, old)
        target[keys[-1]] = text.replace(old, new, 1)
        row['exact_rendered'] = old; row['rendered'] = new; row['display_only_rounding'] = True
    result['display_contract'] = CONTRACT
    result['pre_display_sha256'] = digest(checked)
    result['tradable_tick_conversion'] = False
    return result
