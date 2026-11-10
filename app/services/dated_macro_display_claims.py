"""Original sealed FRED observations -> display-only, never direction authority."""
from datetime import date,datetime
from decimal import Decimal,InvalidOperation
import hashlib,json
from pathlib import Path
import zipfile
from pydantic import BaseModel,ConfigDict
from app.services.unified_snapshot_contract import digest

SERIES=('DGS3','DGS5','DGS10','DGS30','VIXCLS','DCOILWTICO','DTWEXBGS')
YIELDS=SERIES[:4]
CONTRACT='previous-observation-verified-display-only-v1'

def validate_series_unit(series,unit):
    expected='percent' if series in YIELDS else 'usd_per_barrel' if series=='DCOILWTICO' else 'index'
    if series not in SERIES or unit!=expected:raise ValueError('macro_display_series_unit')

class MacroCaptureSelection(BaseModel):
    """A backend-selected file reference, not an Owner or permission token."""
    model_config=ConfigDict(extra='forbid',frozen=True)
    archive_path:str
    archive_sha256:str

def _number(value):
    if isinstance(value,bool):raise ValueError('macro_display_boolean_value')
    try:n=Decimal(str(value))
    except InvalidOperation:raise ValueError('macro_display_invalid_number') from None
    if not n.is_finite():raise ValueError('macro_display_nonfinite')
    return n

def derive_observation(series,raw,receipt,temporal):
    """Internal parser after archive custody; exact receipt/series/time/raw binding."""
    if series not in SERIES or receipt['provider']!='fred' or receipt['request']['params']['series_id']!=series:
        raise ValueError('macro_display_series_binding')
    body_sha=hashlib.sha256(raw).hexdigest()
    if (receipt['artifact_sha256']!=body_sha or temporal['response_sha256']!=body_sha
            or temporal['series_code']!=series or receipt['outcome']!='HTTP_RESPONSE' or receipt['http_status']!=200):
        raise ValueError('macro_display_raw_receipt_binding')
    query=datetime.fromisoformat(temporal['query_as_of']);received=datetime.fromisoformat(receipt['received_at'])
    if query.utcoffset() is None or received.utcoffset() is None or received<query:
        raise ValueError('macro_display_time_binding')
    payload=json.loads(raw)
    if payload.get('series_id',series)!=series:raise ValueError('macro_display_response_series')
    observations=[];seen=set()
    for index,row in enumerate(payload.get('observations',[])):
        observed=date.fromisoformat(row['date'])
        if observed>query.date():raise ValueError('macro_display_future_observation')
        if observed in seen:raise ValueError('macro_display_duplicate_date')
        seen.add(observed)
        if row.get('value') in (None,'.'):continue
        observations.append((observed,_number(row['value']),index))
    observations.sort(reverse=True)
    if not observations:raise ValueError('macro_display_level_missing')
    current,previous=observations[0],observations[1] if len(observations)>1 else None
    if temporal['observation_date']!=current[0].isoformat():raise ValueError('macro_display_latest_binding')
    level=float(current[1]);delta_pp=delta_bp=change_pct=None
    if previous is not None:
        if series in YIELDS:
            delta_pp=float(current[1]-previous[1]);delta_bp=float((current[1]-previous[1])*100)
        elif previous[1]>0:change_pct=float((current[1]/previous[1]-1)*100)
    status='PREVIOUS_OBSERVATION_VERIFIED_DISPLAY_ONLY' if previous is not None else 'DISPLAY_LEVEL_ONLY_PREVIOUS_UNAVAILABLE'
    fields=dict(series_code=series,publication_context=temporal,today_signal_eligible=False,
        observation_date=current[0].isoformat(),previous_observation_date=previous[0].isoformat() if previous else None)
    if series in YIELDS:
        kind='market_nominal_yield';fields.update(level_pct=level,previous_level_pct=float(previous[1]) if previous else None,change_bp=delta_bp)
    else:
        kind='market_oil' if series=='DCOILWTICO' else 'market_volatility' if series=='VIXCLS' else 'market_dollar_index'
        fields.update({'price_usd_per_barrel' if series=='DCOILWTICO' else 'level':level,'return_pct':change_pct})
    fact=dict(fact_id=f'market:{kind.removeprefix("market_")}:{series}',fact_type=kind,as_of_date=current[0].isoformat(),fields=fields)
    from app.services.numeric_semantic_registry import build_numeric_registry
    registry=build_numeric_registry([fact])
    payload=dict(contract=CONTRACT,series_code=series,status=status,level=level,
        previous_value=float(previous[1]) if previous else None,observation_date=current[0].isoformat(),
        previous_observation_date=previous[0].isoformat() if previous else None,
        delta_pp=delta_pp,delta_bp=delta_bp,change_pct=change_pct,
        unit='percent' if series in YIELDS else 'usd_per_barrel' if series=='DCOILWTICO' else 'index',
        raw_sha256=body_sha,receipt_sha256=digest(receipt),source_row_indices=[current[2]]+([previous[2]] if previous else []),
        publication_context=temporal,available_at=receipt['received_at'],query_as_of=temporal['query_as_of'],
        formula='level - previous; bp = percentage_point * 100' if series in YIELDS else '(level / positive_previous - 1) * 100',
        unavailable_reason=None if previous and (series in YIELDS or previous[1]>0) else 'PREVIOUS_MISSING_OR_NONPOSITIVE_DENOMINATOR',
        fact=fact,numeric_registry=registry,direction_eligible=False,same_day_directional_authority=False,
        display_eligible=True,full_market_parent=False)
    return dict(payload,claim_id='dated-macro:'+digest(payload))

def load_claims(selection):
    selection=MacroCaptureSelection.model_validate(selection)
    p=Path(selection.archive_path)
    if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('macro_display_symlink')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=selection.archive_sha256:raise ValueError('macro_display_archive_hash')
    with zipfile.ZipFile(p) as z:
        manifest=json.loads(z.read('MANIFEST.json'))['files']
        def read(name):
            raw=z.read(name);pin=manifest[name]
            if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('macro_display_member_hash')
            return raw
        proof=json.loads(read('MACRO_COLD.json'))
        replay=json.loads(read('evidence/macro/cold-selected-replay.json'))
        provider=replay['providers']['fred']
        if (proof['status']!='ORIGINAL_SELECTED_PUBLICATION_REPLAY_PASS' or proof['value_sha256']!=replay['value_sha256']
                or digest(replay['providers'])!=replay['value_sha256'] or digest(provider['value'])!=provider['value_sha256']):
            raise ValueError('macro_display_original_replay_binding')
        rows={}
        for row in provider['value']['observations']:
            rows.setdefault(row['series_code'],[]).append(row)
        claims=[]
        for series in SERIES:
            source=max(rows[series],key=lambda x:x['observed_at'])
            validate_series_unit(series,source['unit'])
            temporal=source['raw_payload']['publication_context']
            receipts=[r for r in provider['original_receipts'] if r['request']['params'].get('series_id')==series]
            if len(receipts)!=1:raise ValueError('macro_display_receipt_ambiguity')
            receipt=receipts[0];raw=read('evidence/macro/fred/'+receipt['artifact'])
            claim=derive_observation(series,raw,receipt,temporal)
            if claim['level']!=source['value']:raise ValueError('macro_display_normalized_level_changed')
            claims.append(claim)
    return claims

def yield_line(label,level,change_bp,observed,previous):
    suffix=f'{change_bp/100:+.2f}%p / {change_bp:+.0f}bp' if change_bp is not None else '변동 자료 부족'
    baseline=f' · 직전 {previous[5:].replace("-","/")} 대비' if previous else ''
    return f'{label}: {level:.2f}% ({suffix}) · {observed[5:].replace("-","/")}{baseline}'

def render_macro_block(claims):
    by={c['series_code']:c for c in claims}
    if set(by)!=set(SERIES):raise ValueError('macro_display_exact_series_set')
    rate_dates={by[s]['observation_date'] for s in YIELDS};previous_dates={by[s]['previous_observation_date'] for s in YIELDS}
    common=len(rate_dates)==len(previous_dates)==1 and None not in previous_dates
    heading='### 미 국채 금리'
    if common:heading+=f' ({next(iter(rate_dates))[5:].replace("-","/")} 기준 · 직전 {next(iter(previous_dates))[5:].replace("-","/")} 대비)'
    lines=[heading]
    for series in YIELDS:
        c=by[series];line=yield_line(series[3:]+'년 금리',c['level'],c['delta_bp'],c['observation_date'],c['previous_observation_date'])
        if common:line=line.split(' · ')[0]
        lines.append(line)
    lines.append('### 거시지표')
    for series,label in (('DCOILWTICO','WTI'),('DTWEXBGS','광역 달러지수 DTWEXBGS'),('VIXCLS','VIX')):
        c=by[series];unit='달러/배럴' if series=='DCOILWTICO' else ''
        change=f"{c['change_pct']:+.2f}%" if c['change_pct'] is not None else '변동률 자료 부족'
        baseline=f"; 직전 {c['previous_observation_date'][5:].replace('-','/')} 대비" if c['previous_observation_date'] else ''
        lines.append(f"{label} ({c['observation_date'][5:].replace('-','/')}): {c['level']:,.2f}{unit} ({change}{baseline})")
    return '\n\n'.join(lines)+'\n'

def verify_macro_text(text,selection):
    claims=load_claims(selection);expected=render_macro_block(claims)
    if text!=expected:raise ValueError('macro_display_final_text_mismatch')
    return dict(status='PASS',text_sha256=hashlib.sha256(text.encode()).hexdigest(),claim_ids=[c['claim_id'] for c in claims],
        direction_eligible=False,scope='PREVIOUS_OBSERVATION_DISPLAY_ONLY')


def render_us_source_preview(selection):
    """Versioned user format over original C22P sealed source-only results."""
    selection=MacroCaptureSelection.model_validate(selection);claims=load_claims(selection)
    with zipfile.ZipFile(selection.archive_path) as z:
        name='REAL_US_MARKET_NO_SEND.json';raw=z.read(name);pin=json.loads(z.read('MANIFEST.json'))['files'][name]
        if hashlib.sha256(raw).hexdigest()!=pin['sha256'] or len(raw)!=pin['bytes']:raise ValueError('macro_preview_original_message_hash')
        original=json.loads(raw)
    if original['market']!='us' or original['FullMarketParent'] is not False or original['NO_SEND'] is not True:
        raise ValueError('macro_preview_source_only_scope')
    by={f['key']:f for f in original['fields']}
    if len(by)!=len(original['fields']):raise ValueError('macro_preview_duplicate_source_field')
    lines=[f"# 미국시장 · {original['session']} 마감",'SOURCE-ONLY · NO-SEND','### 주요 지수']
    for symbol in ('SPY','QQQ','IWM'):
        f=by[symbol]
        if f['status']!='CURRENT_QUALIFIED' or f['completed_session']!=original['session']:raise ValueError('macro_preview_index_session')
        lines.append(f"{symbol}: {f['value']['close']:,.2f}달러 ({f['value']['return_pct']:+.2f}%)")
    lines.append(render_macro_block(claims))
    for item in original['sector_projection']['selected_items']:
        lines.append(item['text'].replace(' TOP3',' 상대 강세 TOP3').replace(' BOTTOM3',' 상대 약세 BOTTOM3'))
    soxx=by['SECTOR_US_SOXX']
    lines+=['### 반도체 관심 업종',f"SOXX {soxx['value']:+.2f}%",'### 야간선물',
        '일봉·주봉·월봉: 자료 부족. 이번 신규 KRX 조회 0회; 현재 적격 원본·기준 주간장 미확보.',
        '관측일이 다른 자료를 같은 날의 변화로 합성하지 않습니다.']
    text='\n\n'.join(lines)+'\n'
    return dict(contract='dated-US-user-message-format-v2',text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_archive_sha256=selection.archive_sha256,original_message_sha256=hashlib.sha256(raw).hexdigest(),
        session=original['session'],claims=claims,claim_set_sha256=digest(claims),
        market_judgment=None,confidence=None,direction_eligible=False,published_at_missing_reason='DISPLAY_ONLY_NOT_SAME_DAY_DIRECTION',
        full_market_parent=False,NO_SEND=True,default_enabled=False,Strict_READY='0/22')


def verify_us_source_preview(output,selection):
    expected=render_us_source_preview(selection)
    if digest(output)!=digest(expected) or output['text']!=expected['text']:raise ValueError('macro_preview_complete_audit_mismatch')
    return dict(status='PASS',scope='FULL_BODY_INCLUDING_AUXILIARY',text_sha256=expected['text_sha256'],
        claim_set_sha256=expected['claim_set_sha256'],direction_eligible=False)


def render_kr_source_preview(selection):
    """Hide ungenerated stance labels only; preserve the dated original fields."""
    selection=MacroCaptureSelection.model_validate(selection)
    p=Path(selection.archive_path)
    if any(x.is_symlink() for x in (p,*p.parents)) or hashlib.sha256(p.read_bytes()).hexdigest()!=selection.archive_sha256:
        raise ValueError('kr_preview_archive_binding')
    with zipfile.ZipFile(p) as z:
        name='REAL_KR_MARKET_NO_SEND.json';raw=z.read(name)
        pin=json.loads(z.read('MANIFEST.json'))['files'][name]
        if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
            raise ValueError('kr_preview_member_binding')
        original=json.loads(raw)
    if (original['market']!='kr' or original['FullMarketParent'] is not False
            or original['NO_SEND'] is not True or original['market_judgment'] is not None
            or original['confidence'] is not None):
        raise ValueError('kr_preview_source_only_scope')
    text=original['text'].replace(' · 판단 유보 / 확신도 산정 불가','')
    return dict(contract='dated-KR-user-message-format-v2',text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),original=original,
        original_message_sha256=hashlib.sha256(raw).hexdigest(),source_archive_sha256=selection.archive_sha256,
        session=original['session'],market_judgment=None,confidence=None,status='PARTIAL',
        NO_SEND=True,default_enabled=False,full_market_parent=False,direction_eligible=False)


def verify_kr_source_preview(output,selection):
    expected=render_kr_source_preview(selection)
    if output!=expected:raise ValueError('kr_preview_complete_audit_mismatch')
    return dict(status='PASS',scope='FULL_BODY_AND_ORIGINAL_FIELDS',text_sha256=expected['text_sha256'],
        market_judgment=None,confidence=None,direction_eligible=False)
