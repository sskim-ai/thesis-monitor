"""Offline presentation and receipt consistency only; never a Market/Source Owner."""
from copy import deepcopy
from datetime import datetime
import re
from app.services.dated_research_model import digest,encoded
from app.services.dated_split_research_consumer import validate_message

MARKET_FIELDS={
    'us':(('SPY_RETURN','SPY 등락률','%'),('QQQ_RETURN','QQQ 등락률','%'),
          ('US3Y','미 국채 3년','%'),('US5Y','미 국채 5년','%'),('US10Y','미 국채 10년','%'),('US30Y','미 국채 30년','%'),
          ('WTI','WTI 원유','USD/barrel'),('DOLLAR','달러 지수·정확한 정의','원본 정의 필요'),('VIX','VIX','index'),
          ('SECTOR_TOP3','미국 섹터 TOP3','원본 범위 필요'),('SECTOR_BOTTOM3','미국 섹터 BOTTOM3','원본 범위 필요'),
          ('NIGHT_D','KOSPI200 야간선물 일봉','원본 단위 필요'),('NIGHT_W','KOSPI200 야간선물 주봉','원본 단위 필요'),('NIGHT_M','KOSPI200 야간선물 월봉','원본 단위 필요')),
    'kr':(('KOSPI','KOSPI 등락률','%'),('KOSDAQ','KOSDAQ 등락률','%'),('BREADTH','상승·하락 종목수','원본 범위 필요'),
          ('FOREIGN_FLOWS','외국인 수급','원본 단위·범위 필요'),('INSTITUTION_FLOWS','기관 수급','원본 단위·범위 필요'),
          ('KOSPI_TOP3','KOSPI 섹터 TOP3','원본 범위 필요'),('KOSPI_BOTTOM3','KOSPI 섹터 BOTTOM3','원본 범위 필요'),
          ('KOSDAQ_TOP3','KOSDAQ 섹터 TOP3','원본 범위 필요'),('KOSDAQ_BOTTOM3','KOSDAQ 섹터 BOTTOM3','원본 범위 필요'),
          ('USDKRW','USD/KRW 고시·종가 기준','KRW/USD'))}


def _sentences(text):
    return re.split(r'(?<=[.!?])\s+',text or '')


def stock_short(message, *, view, source_evidence):
    proof=validate_message(message,view=view,source_evidence=source_evidence)
    if not proof['publication_pass']:raise ValueError('source_bound_publication_required')
    m=message;a=m['split_panel']['axes'];f=a['newbuyer_fundamental_attractiveness'];t=a['newbuyer_entry_timing'];p=m['prior_panel']
    periods=m['technical_periods']
    lines=[f"# {m['company_name']} ({m['ticker']}) — 과거 연구 / NO-SEND",
        '현재 시세·매매 권고 아님. 재무 원문 품질 PARTIAL.',
        '연구 기준: '+m['as_of'],
        '완료봉: '+ ' / '.join(k+' '+v['completed_period_end'] for k,v in periods.items()),
        f"과거 C22G ADJ: Overall {p['overall']['state']} / 가상 Holder {p['holder_virtual']['state']} (실제 보유자 아님)",
        f"C22J V3 BLIND: 사업 매력 {f['state']} ({f['confidence']}) / 진입시점 {t['state']} ({t['confidence']})",
        '신규매수 해석: '+_sentences(f['statement']['text'])[0]+' '+_sentences(t['statement']['text'])[0]]
    values={v['metric']:v for v in m['valuations']}
    labels=(('PER',('PER',)),('PBR',('PBR',)),('fPER',('FPER','FORWARD_PE')),('FY1 EPS',('FY1_EPS',)))
    lines+=['## 밸류에이션 — 후행 조회 회고 자료, 당시 가용 정보로 소급 불가']
    for label,aliases in labels:
        v=next((values[x] for x in aliases if x in values),None)
        if v is None:lines+=['- '+label+': 자료 부족'];continue
        z=v['temporal'];fact=v['fact']
        lines += [f"- {label}: {fact['value']} {fact['unit']} ({v['provider']}; 조회 {z['retrieved_at']})"]
        if v['canonical_horizon'] or v['forecast_fiscal_period'] or z['issuer_estimate_vintage'] or z['reference_price_as_of']:
            lines += [f"  대상 {v['forecast_fiscal_period'] or v['canonical_horizon'] or '자료 부족'} / 추정 빈티지 {z['issuer_estimate_vintage'] or '자료 부족'} / 가격 기준일 {z['reference_price_as_of'] or '자료 부족'}"]
    lines+=['## 실적·사업 위험']
    lines += ['- '+x['text'] for x in f['pro'][:1]+f['con'][:2] if x['text']]
    for r in m['financial']:
        if r['fiscal_comparability']:
            q=r['fiscal_comparability'];line=f"- 원본 회계연도 비교: {q['current_weeks']}주 / {q['prior_weeks']}주. 주수 보정·연율화 없음."
            if line not in lines:lines.append(line)
        for caution in r['anomaly_cautions']:
            line='- 원본 재무 이상치 경고: '+caution
            if line not in lines:lines.append(line)
    if any('PBR_VS_NEGATIVE' in w for w in m['warnings']):lines+=['- 음의 보고 자기자본과 PBR의 범위·기간 정합성 미확인. 낮은 PBR을 저평가 증거로 사용하지 않습니다.']
    lines += ['- 구조적 위험 UNKNOWN은 미판단이며 위험이 없다는 뜻이 아닙니다.']
    changes=[]
    for axis in (f,t):
        changes += [s for s in _sentences(axis['statement']['text']) if any(w in s for w in
            ('확인되면','확인되고','확인되거나','완화되면','판단을 변경','판단을 철회'))][:1]
    lines += ['## 판단 변경 조건']+['- '+s for s in changes]
    withheld=sum(x.get('text') is None for axis in a.values() for cells in ([axis['statement']],axis['pro'],axis['con'],axis['unknown'],axis['temporal_limitations']) for x in cells)
    if withheld:lines += ['서술 중 숫자 검증 보류. 검증된 구조화 인용은 감사 JSON에 별도 보존하며 원문을 수정하지 않았습니다.']
    lines += ['재무 기간·조회시각·기술 완료일이 다른 회고 연구입니다. 개인 등록 Thesis 미비교. 새 Overall·Holder·현재가격 권한 없음.']
    text='\n\n'.join(lines)+'\n'
    return dict(contract='C22L_V3_SOURCE_BOUND_STOCK_SHORT',ticker=m['ticker'],market=view['market'],
        research_as_of=m['as_of'],price_session=periods['daily']['completed_period_end'],NO_SEND=True,
        publication=proof,content_sha256=digest(text.encode()),text=text,
        authoritative_consumer_sha256=digest(encoded(m)),original_hashes=deepcopy(m['sealed_hashes']),
        original_citations=deepcopy(m['split_panel']['citations']),financial_periods=[dict(ref=r['ref'],observations=r['observations']) for r in m['financial']],
        state='C22L_V3_SOURCE_BOUND_STOCK_SHORT_PASS',current_signal=False,withheld_prose_items=withheld)


def check_lane_receipts(*, market,session,cutoff,parent,children):
    """Consistency audit after the original Owner; does not construct or authorize that Owner."""
    if parent['market']!=market or parent['session']!=session or parent['cutoff']!=cutoff:
        raise ValueError('market_parent_lane_session_or_cutoff_mismatch')
    if parent['child_hashes']!=[c['raw_sha256'] for c in children]:raise ValueError('market_parent_child_hash_mismatch')
    for c in children:
        if c['market']!=market or c['session']!=session or c['parent_fingerprint']!=parent['fingerprint']:
            raise ValueError('market_child_parent_or_session_mismatch')
        if datetime.fromisoformat(c['available_at'])>datetime.fromisoformat(cutoff):raise ValueError('market_child_after_cutoff')
    return dict(state='RECEIPT_CONSISTENCY_ONLY_NOT_OWNER_GRANT',full_parent_issued=False)


def market_preview(market, *, ledger):
    """Ledger contains only original qualified field projections or explicit missing states."""
    if market not in MARKET_FIELDS or ledger['market']!=market:raise ValueError('market_lane_mismatch')
    fields=[]
    for key,label,unit in MARKET_FIELDS[market]:
        row=deepcopy(ledger.get('fields',{}).get(key,dict(status='MISSING',value=None)))
        if row['status']=='PASS':
            if row.get('value') is None or not all(row.get(k) for k in ('ref','source_sha256','unit','period','available_at','original_owner_receipt_sha256')):
                raise ValueError('market_field_original_provenance_required')
            if row.get('is_session_price') and row.get('session')!=ledger['candidate_session']:
                raise ValueError('market_field_session_mismatch')
            if datetime.fromisoformat(row['available_at'])>datetime.fromisoformat(ledger['candidate_cutoff']):
                raise ValueError('market_field_after_cutoff')
        else:
            row['value']=None
        fields.append(dict(key=key,label=label,expected_unit=unit,**row))
    # This preview route intentionally cannot mint FULL MARKET PASS from saved JSON.
    state='MARKET_FORMAT_PREVIEW_ONLY' if not any(f['status']=='PASS' for f in fields) else 'PARTIAL_ORIGINAL_FIELD_PROJECTIONS_NOT_FULL_PARENT'
    lines=['# '+market.upper()+' 시장 — NO-SEND 형식 미리보기',
        'FORMAT_PREVIEW_ONLY / MARKET_INPUT_NOT_QUALIFIED',
        '최신 완료 세션: 자료 부족. 기존 후보 세션 '+str(ledger.get('candidate_session'))+' (현재 신호 아님).']
    lines += ['- '+f['label']+': '+(str(f['value'])+' '+f['unit']+' / '+f['period'] if f['status']=='PASS' else '자료 부족') for f in fields]
    lines += ['시장 판단: 유보 / 확신도: 산정 불가.','Full Market Parent·동일 lane 종목 시세 결속 미입증. 현재 시장 판단 또는 실제 발송 적격성을 의미하지 않습니다.']
    text='\n\n'.join(lines)+'\n'
    return dict(market=market,contract='C22L_V3_OFFLINE_MARKET_FORMAT',state=state,NO_SEND=True,full_market_parent=False,
        candidate_session=ledger.get('candidate_session'),latest_completed_session='UNKNOWN',fields=fields,
        judgment=None,confidence=None,text=text,content_sha256=digest(text.encode()))


def combined_preview(title, items):
    if any(x.get('NO_SEND') is not True for x in items):raise ValueError('preview_NO_SEND_required')
    labels=[dict(market=x.get('market'),session=x.get('price_session') or x.get('candidate_session'),research_as_of=x.get('research_as_of')) for x in items]
    return '\n\n'.join(['# '+title,'OFFLINE_FORMAT_PREVIEW_ONLY / MARKET_INPUT_NOT_QUALIFIED',
        'DATED_RESEARCH_MIXED_VINTAGE_NOT_SAME_DAY_PUBLICATION',
        '각 부분의 기준: '+str(labels),*[x['text'] for x in items]])+'\n'
