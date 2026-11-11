"""Single unsent market message from backend-selected sealed dated evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

from app.services.confirmed_sector_taxonomy import VERSION, verify_retained_sector_output
from app.services.dated_market_legacy_adapter import render_retained_component_sectors
from app.services.unified_snapshot_contract import digest


def _sealed_member(path, archive_sha256, name):
    p = Path(path)
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('dated_slots_symlink')
    if hashlib.sha256(p.read_bytes()).hexdigest() != archive_sha256:
        raise ValueError('dated_slots_archive_hash')
    with zipfile.ZipFile(p) as z:
        manifest = json.loads(z.read('MANIFEST.json'))['files']
        raw = z.read(name)
        if len(raw) != manifest[name]['bytes'] or hashlib.sha256(raw).hexdigest() != manifest[name]['sha256']:
            raise ValueError('dated_slots_member_hash')
    return json.loads(raw)


def render_retained_market_message(*, archive_path, archive_sha256, reference_path, market,
                                   flow_archive_path=None, flow_archive_sha256=None, enabled=False):
    if enabled is not True:
        raise ValueError('dated_slots_default_off')
    custody = dict(archive_path=archive_path, archive_sha256=archive_sha256,
                   reference_path=reference_path, market=market, enabled=enabled)
    sector = render_retained_component_sectors(**custody, taxonomy_version=VERSION)
    audit = verify_retained_sector_output(sector, **custody)
    original = _sealed_member(archive_path, archive_sha256, market.upper()+'_MARKET.json')
    session = sector['session']
    slots = []
    # Rebuild from original structured fields, never append the old rendered
    # unavailable slots to an updated message.
    for field in original['fields']:
        if field.get('status') != 'PASS':
            continue
        slots.append(dict(slot_id=field['key'], origin=field,
            text=f"{field['label']}: {field['value']} {field['unit']} · {field['period']} 관측 · 원본 {field['ref']}"))
    slots.append(dict(slot_id='SECTORS', text=sector['text'], origin_audit=audit))
    if market == 'kr':
        if flow_archive_path is not None and flow_archive_sha256 is not None:
            receipt = _sealed_member(flow_archive_path, flow_archive_sha256, 'KR_AGGREGATE_ONLY_ACTUAL_REPLAY.json')
            flow = receipt['value']
            if (flow['scope'] != 'AGGREGATE_ONLY_SOURCE_REFERENCE' or flow['session'] != session
                    or flow['concentration_eligible'] is not False or flow['full_market_parent'] is not False):
                raise ValueError('dated_slots_aggregate_scope')
            for row in flow['market_flows']:
                if row['currency'] != 'KRW' or row['exchange_basis'] != 'KRX_NXT_INTEGRATED':
                    raise ValueError('dated_slots_flow_units')
                actor = {'foreign': '외국인', 'institution': '기관', 'retail': '개인'}[row['actor']]
                slots.append(dict(slot_id='FLOW_'+row['market']+'_'+row['actor'], origin=row,
                    text=f"{row['market']} {actor} 집계 수급: {row['net_buy_amount']:,.0f} KRW · {session} · {row['exchange_basis']} · {row['source_ref']}"))
        else:
            slots.append(dict(slot_id='FLOW', text='집계 수급: 자료 부족 (원래 집계 Replay 영수증 미제공)'))
        slots.append(dict(slot_id='CONCENTRATION', text='집중수급: 미검증, 사용하지 않음'))
    else:
        slots.append(dict(slot_id='NIGHT', text='한국 야간선물 · 일: 자료 부족 / 주: 자료 부족 / 월: 자료 부족'))
        slots.append(dict(slot_id='DOLLAR_DEFINITION', text='광역 달러 DTWEXBGS는 DXY가 아닙니다. 당일 변화로 추정하지 않습니다.'))
    slots.append(dict(slot_id='JUDGMENT', text='시장 판단: 유보 · 확신도 산정 불가 · 최신 공시 NOT_CHECKED'))
    ids = [s['slot_id'] for s in slots]
    if len(ids) != len(set(ids)):
        raise ValueError('dated_slots_duplicate_slot')
    title = ('미국' if market == 'us' else '한국')+' 시장 · '+session+' · 과거 연구 / NO-SEND'
    text = title+'\n\n'+'\n\n'.join(s['text'] for s in slots)+'\n\n최신 시장 판단·Full Market Parent·발송 적격성이 아닙니다.\n'
    return dict(contract='dated-market-single-slot-v1', market=market, session=session,
        state='HISTORICAL_SOURCE_VERIFIED_PREVIEW_NOT_LATEST_PARTIAL', slots=slots, text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), sector_complete_audit=audit,
        full_market_parent=False, latest_current=False, NO_SEND=True, default_enabled=False)


def verify_retained_market_message(output, **custody):
    expected = render_retained_market_message(**custody)
    if type(output) is not dict or digest(output) != digest(expected) or output.get('text') != expected['text']:
        raise ValueError('dated_slots_complete_message_mismatch')
    return dict(status='PASS', text_sha256=expected['text_sha256'], slots=len(expected['slots']),
                scope='DATED_SOURCE_ONLY_COMPLETE_MESSAGE', NO_SEND=True, full_market_parent=False)
