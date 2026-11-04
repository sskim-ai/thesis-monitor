"""Pinned historical projection, never an Owner capability or current price grant.

The local operator supplies previously reviewed archive/member pins. Matching
hashes establish custody, not economic authority. No startup, Settings, collector
or price algorithm is imported; existing outputs are only mapped to dated text.
"""
from datetime import date
import io
import json
import math
from pathlib import Path
import re
import zipfile

from app.services.vnext_research_store import digest, plain
from app.services.vnext_composite_research import ALLOWED, instant

CONTRACT = 'vnext-pinned-historical-price-reference-v1'
ORIGINAL = 'vnext-original-price-structure-reference-v1'
BASIS = 'ADJUSTED_CHART_REFERENCE_NOT_ORDER_PRICE'
KINDS = {'support_low', 'support_high', 'resistance_low', 'resistance_high',
         'chart_invalidation', 'current_price_rr', 'support_entry_rr'}


def load_pinned_archive(path, archive_sha256, member, member_sha256):
    """Local manual read-only input. Pins must come from reviewed custody records."""
    if not all(re.fullmatch('[0-9a-f]{64}', x or '') for x in (archive_sha256, member_sha256)):
        raise ValueError('historical_pin_required')
    p = plain(path)
    if not p.is_file() or p.stat().st_size > 64*1024**2:
        raise ValueError('historical_archive_size')
    raw = p.read_bytes()
    if digest(raw) != archive_sha256:
        raise ValueError('historical_archive_pin')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist()) != len(set(z.namelist())) or len(z.namelist()) > 1000:
            raise ValueError('historical_archive_members')
        name = Path(member)
        if name.is_absolute() or '..' in name.parts or member not in z.namelist():
            raise ValueError('historical_member')
        if z.getinfo(member).file_size > 4*1024**2:
            raise ValueError('historical_member_size')
        body = z.read(member)  # zipfile validates this member's CRC.
    if digest(body) != member_sha256:
        raise ValueError('historical_member_pin')
    return dict(packet_bytes=body, custody=dict(archive_sha256=archive_sha256,
        member=member, member_sha256=member_sha256, authority='REVIEWED_HISTORICAL_REFERENCE_NOT_OWNER'))


def project(packet, reference):
    if digest(reference['packet_bytes']) != reference['custody']['member_sha256']:
        raise ValueError('historical_loaded_bytes_changed')
    old = json.loads(reference['packet_bytes'])
    a = old.get('price_attachment', {})
    identity = packet['public_security']
    if (a.get('contract') != ORIGINAL or a.get('status') != 'DATED_CHART_REFERENCE' or
        a.get('security_id') != identity['canonical_security_id'] or a.get('ticker') != packet['ticker'] or
        any(old.get('public_security', {}).get(k) != identity.get(k)
            for k in ('canonical_security_id', 'country', 'exchange', 'security_type', 'issuer_type')) or
        ('canonical_company_id' in old.get('public_security', {}) and
         old['public_security']['canonical_company_id'] != identity.get('canonical_company_id'))):
        raise ValueError('historical_identity_or_contract')
    for key in ('current_collection', 'executable_order_price', 'adjusted_unadjusted_equivalence_proven', 'strict_native'):
        if a.get(key) is not False:
            raise ValueError('historical_authority_escalation')
    if old.get('holdings_included') is not False or old.get('user_thesis_included') is not False:
        raise ValueError('private_historical_packet')
    if a.get('currency') != {'KR':'KRW', 'US':'USD'}.get(identity['country']):
        raise ValueError('historical_currency')
    if date.fromisoformat(a['session']) > instant(packet['as_of']).date() or instant(old['as_of']) > instant(packet['as_of']):
        raise ValueError('historical_after_cutoff')
    if a['source_generation'] not in {r['run_id'] for r in packet['source_runs']}:
        raise ValueError('historical_generation')
    if a['source_sha'] != digest(dict(sources=a['sources'], structure=a['structure'],
                                     multi=a['multi_packet'], selection=a['multi_selection'])):
        raise ValueError('historical_structure_binding')
    bindings=[]
    for tf, source in a['sources'].items():
        if tf not in ('daily','weekly','monthly') or tf in a['roles_rejected']:
            raise ValueError('historical_rejected_role')
        current=[e for e in packet['evidence'] if e['field']=='ohlcv.adjusted_'+tf and
                 e['source_sha']==source['raw_sha256'] and e['status'] in ALLOWED]
        previous=[e for e in old['evidence'] if e['field']=='ohlcv.adjusted_'+tf and e['source_sha']==source['raw_sha256'] and e['status'] in ALLOWED]
        if len(current)!=1 or len(previous)!=1:
            raise ValueError('historical_source_not_selected')
        e=current[0]
        if (e['data'].get('quality_valid') is not True or e['data'].get('adjusted') is not True or
            e['data'].get('calendar',{}).get('session') != a['session'] or
            e['provenance']['captured_at'] != source['source_captured_at']):
            raise ValueError('historical_quality_session_time')
        dependencies={v['raw_sha256'] for v in e['provenance']['dependencies']}
        if not source['page_sha256'] or not set(source['page_sha256']) <= dependencies:
            raise ValueError('historical_page_receipts')
        bindings.append(dict(timeframe=tf, ref=e['ref'], source_sha=e['source_sha'],
                             receipt_sha256=e['provenance']['receipt_sha256']))
    if not bindings:
        raise ValueError('historical_no_sources')
    facts=[];seen=set()
    for f in a['facts']:
        kind=f['kind'];value=f['value']
        if (kind not in KINDS or kind in seen or type(value) not in (int,float) or
            not math.isfinite(value) or value<=0 or f['timeframe'] not in a['sources'] or
            f['source_inputs']!=a['sources'] or f['source_sha']!=a['source_sha'] or
            f['basis']!=BASIS or f['as_of']!=a['session'] or
            f['unit']!=('ratio' if kind.endswith('_rr') else a['currency'])):
            raise ValueError('historical_fact_contract')
        seen.add(kind);facts.append(dict(f))
    for side in ('support','resistance'):
        pair={f['kind']:f['value'] for f in facts if f['kind'].startswith(side+'_')}
        if pair and (set(pair)!={side+'_low',side+'_high'} or pair[side+'_low']>pair[side+'_high']):
            raise ValueError('historical_zone_pair')
    return dict(contract=CONTRACT, original_contract=ORIGINAL, custody=reference['custody'],
                original_attachment_sha256=digest(a), source_generation=a['source_generation'],
                ticker=packet['ticker'], security_id=a['security_id'], currency=a['currency'],
                session=a['session'], facts=facts, source_bindings=bindings,
                roles_rejected=a['roles_rejected'], owner_reissued=False,
                current_collection=False, executable_order_price=False, strict_ready=False,
                model='OFF', send=False, current_invocation_input_sha256=digest(packet))


def attach(packet, reference):
    if packet.get('historical_price_reference'):
        raise ValueError('historical_attachment_already_present')
    return dict(packet, historical_price_reference=project(packet, reference))
