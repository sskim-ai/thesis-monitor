"""Offline presentation and receipt consistency only; never a Market/Source Owner."""
from copy import deepcopy
from datetime import date, datetime
from math import isfinite
import json
from pathlib import Path
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


def _aware(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('market_timezone_required')
    return result


def _component_fields(reference, *, market, session, cutoff, qualified_at):
    """Project only explicit fields from the original Cold's normalized value.

    Called only with read_dated_component's result, never an external ledger.
    Sector ranking, flows and macro use different semantics/Owners and are not
    inferred from an index or from an unverified observation.
    """
    if (reference['market'] != market or reference['full_market_parent'] is not False
            or reference['original_cold_status'] != 'ORIGINAL_COMPONENT_OWNER_COLD_PASS_NOT_FULL_PARENT'):
        raise ValueError('market_original_component_owner_required')
    captured = _aware(qualified_at)
    boundary = _aware(cutoff)
    if captured < _aware(reference['query_as_of']) or captured > boundary:
        raise ValueError('market_capture_after_cutoff')
    if reference['completed_session'] != session:
        raise ValueError('market_field_session_mismatch')
    if date.fromisoformat(session) > boundary.date():
        raise ValueError('market_future_period')
    result = {}
    def add(key, value, unit, ref, period, available, session_price=True):
        if _aware(available) > boundary or date.fromisoformat(period) > boundary.date():
            raise ValueError('market_field_after_cutoff_or_future_period')
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError('market_field_nonfinite_or_missing')
        result[key] = dict(status='PASS', qualification='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY', value=value,
            unit=unit, period=period, available_at=available, captured_at=qualified_at,
            ref=ref, source_sha256=reference['original_bundle_sha256'],
            original_owner_receipt_sha256=reference['original_component_sha256'],
            normalized_value_sha256=reference['value_sha256'], session=session, is_session_price=session_price)
    if market == 'us':
        for symbol in ('SPY', 'QQQ'):
            rows = [x for x in reference['value']['observations'] if x['series_code'] == symbol]
            if len(rows) != 1:
                continue
            row = rows[0]
            if (row['unit'] != 'usd' or row['market_session'] != 'us_regular'
                    or row.get('is_preliminary') is not False or row['observed_at'][:10] != session
                    or row.get('raw_payload', {}).get('return_basis') != 'same_response_adjacent_adjusted_regular_closes'):
                raise ValueError('market_original_return_semantics_or_unit')
            add(symbol+'_RETURN', row['change_pct'], '%', symbol+':change_pct', session, qualified_at)
    else:
        for row in reference['value']['indices']:
            if row['symbol'] in ('KOSPI', 'KOSDAQ'):
                if row['symbol'] in result:
                    raise ValueError('market_duplicate_index')
                add(row['symbol'], row['return_pct'], '%', row['source_ref'], session, qualified_at)
        breadth = reference['value'].get('breadth')
        if breadth:
            counts = {k:breadth[k] for k in ('advance_count','decline_count','unchanged_count','eligible_count')}
            if (any(type(v) is not int or v < 0 for v in counts.values())
                    or sum(v for k,v in counts.items() if k != 'eligible_count') != counts['eligible_count']):
                raise ValueError('market_breadth_counts_inconsistent')
            add('BREADTH', counts['advance_count'], 'stocks', 'breadth:advance_count', session, qualified_at)
            result['BREADTH']['value'] = counts
    return result


def _publication_fields(capture, *, market, cutoff):
    """Replay saved official responses; retain their own publication vintage."""
    from app.services.fresh_publication_replay import replay_fresh_publications, replay_selected_market_publications
    from app.services.unified_source_policy import UnifiedSourcePolicy
    root = Path(capture['root'])
    if any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('market_publication_symlink')
    def read_raw(name):
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('market_publication_unsafe_path')
        path=root/relative
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('market_publication_symlink')
        return path.read_bytes()
    def pinned(name):
        raw = read_raw(name)
        if digest(raw) != capture['files'][name]:
            raise ValueError('market_publication_pinned_bytes_mismatch')
        return json.loads(raw)
    freeze = pinned('freeze.json'); ended = pinned('capture.json')
    inputs = {}
    selected=capture.get('profile')=='dated-selected-market-publication-replay-v1'
    if capture.get('profile') not in (None,'dated-selected-market-publication-replay-v1'):
        raise ValueError('market_publication_profile_unknown')
    for provider in (('fred','ecos') if selected else ('fred','eia','ecos')):
        summary = pinned(provider+'/capture-summary.json')
        receipts = summary['receipts']; bodies = {}
        for receipt in receipts:
            name = provider+'/'+receipt['artifact']
            body = read_raw(name)
            if digest(body) != receipt['artifact_sha256']:
                raise ValueError('market_publication_original_body_mismatch')
            bodies[receipt['artifact']] = body
        inputs[provider] = dict(receipts=receipts,bodies=bodies,body_hashes={k:digest(v) for k,v in bodies.items()})
    run_ids = {r['run_id'] for data in inputs.values() for r in data['receipts']}
    if len(run_ids) != 1: raise ValueError('market_publication_mixed_runs')
    replay_fn=replay_selected_market_publications if selected else replay_fresh_publications
    replay = replay_fn(run_id=run_ids.pop(),run_started_at=_aware(freeze['started_at']),
        acquisition_cutoff=_aware(ended['ended_at']),as_of=_aware(freeze['as_of']),providers=inputs,
        policy=UnifiedSourcePolicy(frozenset(('fred','eia','ecos'))))
    mapping = {'DGS3':('US3Y','percent','%'),'DGS5':('US5Y','percent','%'),
        'DGS10':('US10Y','percent','%'),'DGS30':('US30Y','percent','%'),
        'DCOILWTICO':('WTI','usd_per_barrel','USD/barrel'),'DTWEXBGS':('DOLLAR','index','index'),
        'VIXCLS':('VIX','index','index')} if market == 'us' else {'USDKRW':('USDKRW','원','KRW/USD')}
    result = {}; boundary = _aware(cutoff)
    for provider,data in replay['providers'].items():
        for row in data['value']['observations']:
            if row['series_code'] not in mapping: continue
            key,original_unit,unit = mapping[row['series_code']]
            temporal = row['raw_payload']['publication_context']
            if temporal.get('display_eligible') is not True: continue
            if row['unit'] != original_unit: raise ValueError('market_publication_unit_mismatch')
            matches = [r for r in data['original_receipts'] if r['artifact_sha256'] == temporal['response_sha256']]
            if len(matches) != 1: raise ValueError('market_publication_receipt_not_unique')
            receipt = matches[0]; available = receipt['received_at']; period = row['observed_at'][:10]
            if (_aware(available) > boundary or date.fromisoformat(period) > boundary.date()
                    or temporal.get('direction_eligible') is not False):
                raise ValueError('market_publication_availability_or_scope')
            if key in result: raise ValueError('market_publication_duplicate_latest')
            value = row['value']
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value):
                raise ValueError('market_publication_nonfinite')
            result[key] = dict(status='PASS',qualification='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY',value=value,
                unit=unit,original_unit=original_unit,period=period,available_at=available,captured_at=available,
                ref=provider+':'+row['series_code'],source_sha256=temporal['response_sha256'],
                original_owner_receipt_sha256=digest(encoded(receipt)),normalized_value_sha256=data['value_sha256'],
                is_session_price=False,publication_time=temporal.get('publication_time'),
                vintage=temporal,definition='Trade Weighted U.S. Dollar Index: Broad, Goods and Services (DTWEXBGS), not DXY' if key=='DOLLAR' else row['series_code'],
                latest_currentness_rechecked=False)
    return result


def market_preview(market, *, ledger, source_bundles=(), publication_captures=()):
    """External PASS claims must equal an original Cold replay projection.

    Pinned bundle paths/hashes come from the caller's preserved custody record,
    not from a PASS row. The original Cold checks transitive raw/receipt lineage.
    This renderer cannot issue a Full Market Parent or an investment judgment.
    """
    if market not in MARKET_FIELDS or ledger['market']!=market:raise ValueError('market_lane_mismatch')
    from app.services.dated_market_component_reference import read_dated_component
    verified = {}
    for bundle in source_bundles:
        reference = read_dated_component(bundle['path'], expected_sha256=bundle['sha256'], enabled=True)
        # Bind the post-capture qualification time too, not only the earlier
        # plan freeze. A delayed capture cannot become PIT-available at freeze.
        raw = Path(bundle['path']).read_bytes()
        if digest(raw) != bundle['sha256']:
            raise ValueError('market_bundle_changed_after_cold')
        original = json.loads(raw)
        projected = _component_fields(reference, market=market, session=ledger['candidate_session'],
            cutoff=ledger['candidate_cutoff'], qualified_at=original['owner_proof']['qualification_cutoff'])
        if set(verified) & set(projected):
            raise ValueError('market_duplicate_original_field')
        verified.update(projected)
    for capture in publication_captures:
        projected = _publication_fields(capture,market=market,cutoff=ledger['candidate_cutoff'])
        if set(verified) & set(projected): raise ValueError('market_duplicate_original_field')
        verified.update(projected)
    fields=[]
    for key,label,unit in MARKET_FIELDS[market]:
        row=deepcopy(ledger.get('fields',{}).get(key,dict(status='MISSING',value=None)))
        if row['status']=='PASS':
            if key not in verified or encoded(row)!=encoded(verified[key]):
                raise ValueError('market_field_original_owner_projection_required')
        elif key in verified:
            row = deepcopy(verified[key])
        else:
            row['value']=None
            row.setdefault('reason', 'No independently replayed original Owner field')
        fields.append(dict(key=key,label=label,expected_unit=unit,**row))
    # This preview route intentionally cannot mint FULL MARKET PASS from saved JSON.
    any_pass=any(f['status']=='PASS' for f in fields)
    state='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY' if any_pass else 'MARKET_FORMAT_PREVIEW_ONLY'
    lines=['# '+market.upper()+' 시장 — NO-SEND 날짜 명시 자료',
        ('PARTIAL_VERIFIED_FIELDS' if any_pass else 'NO_VERIFIED_FIELDS')+' / FULL_PARENT_NOT_PROVEN',
        '검사 대상 완료 세션: '+str(ledger.get('candidate_session'))+' (현재 신호 아님).',
        '판단 가용시점 상한: '+str(ledger.get('candidate_cutoff'))]
    lines += ['- '+f['label']+': '+(str(f['value'])+' '+f['unit']+' / '+f['period']+' / 수집 '+f['captured_at']+' / 원본 '+f['ref'] if f['status']=='PASS' else '자료 부족: '+f['reason']) for f in fields]
    lines += [f['key']+' 정의: '+f['definition']+'; 최신성 재조회 없음.' for f in fields if f.get('definition')]
    lines += ['NO_QUALIFIED_MARKET_JUDGMENT']
    lines += ['시장 판단: 유보 / 확신도: 산정 불가.','Full Market Parent·동일 lane 종목 시세 결속 미입증. 현재 시장 판단 또는 실제 발송 적격성을 의미하지 않습니다.']
    text='\n\n'.join(lines)+'\n'
    return dict(market=market,contract='C22L_V3_OFFLINE_MARKET_FORMAT',state=state,NO_SEND=True,full_market_parent=False,
        candidate_session=ledger.get('candidate_session'),latest_completed_session=ledger.get('latest_completed_session','UNKNOWN'),fields=fields,
        judgment=None,confidence=None,text=text,content_sha256=digest(text.encode()))


def combined_preview(title, items):
    if any(x.get('NO_SEND') is not True for x in items):raise ValueError('preview_NO_SEND_required')
    labels=[dict(market=x.get('market'),session=x.get('price_session') or x.get('candidate_session'),research_as_of=x.get('research_as_of')) for x in items]
    return '\n\n'.join(['# '+title,'OFFLINE_FORMAT_PREVIEW_ONLY / MARKET_INPUT_NOT_QUALIFIED',
        'DATED_RESEARCH_MIXED_VINTAGE_NOT_SAME_DAY_PUBLICATION',
        '각 부분의 기준: '+str(labels),*[x['text'] for x in items]])+'\n'
