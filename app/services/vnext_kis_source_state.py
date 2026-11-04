"""Dated KIS capture availability, separate from financial-use authority."""
from copy import deepcopy
from datetime import datetime
from enum import Enum
import json
import re
from zoneinfo import ZoneInfo

from app.services.vnext_research_store import digest
from scripts.kis_eps_wire_calibration import verified
from scripts.kis_estimate_capability_probe import DATA_PATH, TR_ID
from scripts.kis_no_estimate_owner import EMPTY_OUTPUT1, REQUIRED_KEYS

CONTRACT = 'kis-source-observation-reference-v1'
IDENTITY = ('ticker', 'canonical_security_id', 'canonical_company_id', 'country',
            'exchange', 'security_type', 'issuer_type', 'corp_code')


class SourceState(str, Enum):
    PRESENT = 'CURRENT_SOURCE_PRESENT_OWNER_PENDING'
    EMPTY = 'CURRENT_SOURCE_EMPTY_AT_RETRIEVAL'
    HISTORICAL = 'HISTORICAL_REFERENCE_ONLY'
    EPS = 'QUALIFIED_CURRENT_FY1_EPS'
    FPER = 'QUALIFIED_CURRENT_FPER'
    DURABLE = 'PRIVATE_DURABLE'
    REJECTED = 'SOURCE_REJECTED'
    NOT_ATTEMPTED = 'NOT_ATTEMPTED'


def _time(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError('kis_explicit_source_time_required')
    return dt


class ReviewedKISSourceObservations:
    """Bootstrap capability for reviewed immutable originals, never public JSON.

    The caller supplies the backend archive/receipt review, not a model-generated
    approval. This capability proves availability only, even when rows exist.
    """
    def __init__(self, reviewed_capture):
        if not callable(reviewed_capture):
            raise ValueError('backend_kis_source_capability_required')
        self._capture = reviewed_capture
        self._revoked = False
        self._pin = digest(self._load())

    def _load(self):
        batch = deepcopy(self._capture())
        plan = batch['plan']
        verified(plan, plan['contract'])
        if (not plan.get('generation_id') or len(plan['subjects']) != len(set(plan['subjects']))
                or not 1 <= len(plan['subjects']) <= 500
                or not re.fullmatch(r'[0-9a-f]{64}', batch.get('archive_sha256', ''))):
            raise ValueError('kis_source_scope_required')
        seen = set()
        for item in batch['captures']:
            code = item['security']['ticker']
            raw = item['raw'].encode()
            r, q, end = item['receipt'], item['request'], item['physical_end']
            if (code in seen or code not in plan['subjects'] or not re.fullmatch(r'\d{6}', code)
                or any(not item['security'].get(k) for k in IDENTITY)
                or item['security']['country'] != 'KR'
                or item['security']['security_type'].lower() not in ('common stock','common_stock')
                or item['security']['issuer_type'].lower() in ('unknown','ads','adr')
                or len(raw) > 2*1024**2 or r['raw_sha256'] != digest(raw) or r['bytes'] != len(raw)
                or r['request'] != q or q['params'] != {'SHT_CD': code}
                or q['method'] != 'GET' or q['security_code'] != code
                or q['redirects'] is not False or q['retries'] != 0
                or q['path'] != DATA_PATH or q['tr_id'] != TR_ID
                or q['plan_sha256'] != plan['receipt_sha256']
                or r['http_status'] != 200 or r['rt_cd'] != '0'
                or r['response_headers']['tr_cont'] not in ('','D','E')
                or end['http_status'] != 200 or end['path'] != DATA_PATH
                or end['method'] != 'GET' or end['kind'] != 'estimate:' + code
                or not _time(plan['as_of']) <= _time(q['started_at']) <= _time(end['started_at'])
                <= _time(end['ended_at']) <= _time(r['ended_at'])):
                raise ValueError('kis_original_source_request_receipt_binding')
            payload = json.loads(raw)
            if payload.get('rt_cd') != '0':
                raise ValueError('kis_provider_failure')
            seen.add(code)
        if seen != set(plan['subjects']):
            raise ValueError('kis_source_batch_incomplete')
        return batch

    def revoke(self):
        self._revoked = True

    def original_batch(self):
        value = self._load()
        if self._revoked or digest(value) != self._pin:
            raise ValueError('kis_source_capability_revoked_or_changed')
        return value

    def project(self, *, security, as_of):
        batch = self.original_batch()
        at = _time(as_of)
        matches = [c for c in batch['captures'] if c['security']['ticker'] == security['ticker']]
        if not matches:
            return None
        item = matches[0]
        if any(item['security'].get(k) != security.get(k) for k in IDENTITY):
            raise ValueError('kis_source_registered_security_mismatch')
        captured = _time(item['receipt']['ended_at'])
        if captured > at:
            raise ValueError('kis_source_after_consumer_cutoff')
        p = json.loads(item['raw']); header = p.get('output1', {})
        empty = (set(p) == REQUIRED_KEYS and header == EMPTY_OUTPUT1
                 and all(p.get(k) == [] for k in ('output2','output3','output4')))
        present = (isinstance(header,dict) and header.get('sht_cd') == 'A' + security['ticker']
                   and isinstance(p.get('output3'),list) and bool(p['output3']))
        state = SourceState.EMPTY if empty else SourceState.PRESENT if present else SourceState.REJECTED
        retrieval_state = state
        if state != SourceState.REJECTED and captured.astimezone(ZoneInfo('Asia/Seoul')).date() != at.astimezone(ZoneInfo('Asia/Seoul')).date():
            state = SourceState.HISTORICAL
        estimate_date = None
        if present:
            try:
                estimate_date = datetime.strptime(header['estdate'], '%Y%m%d').date().isoformat()
                if estimate_date > captured.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat():
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                state = retrieval_state = SourceState.REJECTED
                estimate_date = None
        plan = batch['plan']; receipt = item['receipt']
        return dict(contract=CONTRACT, canonical_security_id=security['canonical_security_id'],
            ticker=security['ticker'],provider='KIS',metric_family='HOUSE_RESEARCH_ESTIMATE',
            source_generation=plan['generation_id'],captured_at=receipt['ended_at'],analysis_as_of=as_of,
            state=state.value,retrieval_state=retrieval_state.value,estimate_date=estimate_date,
            source_sha256=receipt['raw_sha256'],original_receipt_sha256=digest(receipt),
            request_sha256=digest(item['request']),archive_sha256=batch['archive_sha256'],
            source_key=digest([security['canonical_security_id'],'KIS','HOUSE_RESEARCH_ESTIMATE',
                plan['generation_id'],receipt['ended_at'],digest(item['request']),digest(receipt)]),
            returned_security_code=header.get('sht_cd') if isinstance(header,dict) else None,
            provider_display_name=header.get('item_kor_nm') if isinstance(header,dict) else None,
            identity_scope='EXACT_REQUEST_AND_RETURNED_CODE; name equivalence and financial Owner separately required',
            owner_status='NOT_GRANTED_BY_SOURCE_OBSERVATION',FY1_EPS=None,FPER=None,
            allowed_use='SOURCE_AVAILABILITY_DESCRIPTION_ONLY',numeric_use=False,direction_use=False,
            strict_native=False,private_durable=False,house_recommendation_exposed=False,
            preserves_historical_observations=True,
            limitation='Current capture is not a newly authored forecast. Empty is not permanent noncoverage. No expiry rule inferred.')


def attach(packet, owner):
    if not isinstance(owner, ReviewedKISSourceObservations):
        raise ValueError('backend_kis_source_owner_required')
    out = deepcopy(packet)
    if 'kis_source_status' in out:
        raise ValueError('kis_source_attachment_already_present')
    value = owner.project(security=packet['public_security'],as_of=packet['as_of'])
    if value is not None:
        out['kis_source_status'] = value
    return out


def verify(packet, owner):
    if not isinstance(owner, ReviewedKISSourceObservations):
        raise ValueError('backend_kis_source_owner_required')
    expected = owner.project(security=packet['public_security'],as_of=packet['as_of'])
    if packet.get('kis_source_status') != expected:
        raise ValueError('kis_source_projection_changed')
    return expected
