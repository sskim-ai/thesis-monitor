"""Optional documentary verification for the existing OpenDART owner.

The trusted capture composition root supplies an independently admitted seal
pin, never a model/caller JSON digest. This module issues no economic authority
or registry; original financial replay and its existing live registry own use.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
import json
import re
import zipfile

from app.services.dart_public_financial_adapter import (
    _DartTables, _query, _VIEWER_KEYS, index_section_membership,
)
from app.services.sec_foreign_comparison_service import grid
from app.services.unified_snapshot_contract import digest

CONTRACT = 'opendart-documentary-duration-v1'
_MINT = object()
_NUMBER = r'(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?'


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('documentary_duplicate_json_member')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


class DocumentaryDurationInput:
    """Non-JSON sealed capture handle, re-read on every original-owner replay."""
    __slots__ = ('_path', '_pin', '_members', '_security', '_generation', '_cutoff')

    def __init__(self, token, path, pin, members, security, generation, cutoff):
        if token is not _MINT:
            raise ValueError('documentary_trusted_capture_handle_required')
        for key, value in dict(_path=str(path), _pin=pin,
                _members=tuple(sorted(members.items())),
                _security=json.dumps(security, sort_keys=True),
                _generation=generation, _cutoff=cutoff).items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name, value):
        raise AttributeError('immutable_documentary_capture')

    def __deepcopy__(self, memo):
        return self

    def read(self):
        path = Path(self._path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
            raise ValueError('documentary_plain_bounded_seal_required')
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != self._pin:
            raise ValueError('documentary_admitted_seal_changed')
        with zipfile.ZipFile(BytesIO(raw)) as z:
            names = z.namelist()
            if (len(names) != len(set(names)) or len(names) > 256 or
                    sum(i.file_size for i in z.infolist()) > 32*1024**2 or z.testzip()):
                raise ValueError('documentary_seal_invalid')
            manifest = _json(z.read('manifest.json'))['members']
            if set(names) != set(manifest)|{'manifest.json'}:
                raise ValueError('documentary_seal_membership')
            out = {}
            for role, name in self._members:
                body = z.read(name)
                if manifest.get(name) != dict(bytes=len(body), sha256=sha256(body).hexdigest()):
                    raise ValueError('documentary_member_hash_mismatch')
                out[role] = body
        return out


def load_admitted_documentary_capture(*, archive, admitted_archive_sha256, members,
                                    security, execution_generation, review_cutoff):
    """Trusted local capture adapter only, not a public authority issuance API.

    The seal pin must come from the independently reviewed capture receipt. A
    self-hashed archive supplied by a model is not an admitted source.
    """
    if (set(members) != {'index_raw', 'index_receipt', 'section_raw', 'section_receipt'}
            or len(set(members.values())) != 4 or not execution_generation):
        raise ValueError('documentary_capture_members_required')
    _instant(review_cutoff)
    handle = DocumentaryDurationInput(_MINT, archive, admitted_archive_sha256, members,
        security, execution_generation, review_cutoff)
    handle.read()
    return handle


def _instant(value):
    v = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if v.tzinfo is None:
        raise ValueError('documentary_aware_time_required')
    return v


def _received(raw, receipt, path):
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= 2*1024**2
            or receipt.get('method') != 'GET' or receipt.get('HTTP_status') != 200
            or receipt.get('error') is not None or receipt.get('follow_redirects') is not False
            or receipt.get('credentials_used') is not False or receipt.get('retries') != 0
            or receipt.get('source_owner_issued') is not False
            or receipt.get('revoked') or receipt.get('superseded')
            or receipt.get('body_bytes') != len(raw)
            or receipt.get('body_sha256') != sha256(raw).hexdigest()
            or receipt.get('response_headers', {}).get('content-length') not in (None, str(len(raw)))
            or not receipt.get('response_headers', {}).get('content-type', '').lower().startswith('text/html;')
            or not re.fullmatch('[a-f0-9]{64}', receipt.get('authorization_sha256', ''))):
        raise ValueError('documentary_capture_receipt_mismatch')
    params = receipt.get('params', {})
    query = _query(receipt['url'] + ('?'+urlencode(params) if params else ''), path)
    start, end = _instant(receipt['started_at']), _instant(receipt['finished_at'])
    if start > end or not receipt.get('source_generation'):
        raise ValueError('documentary_capture_time_or_generation')
    return query, raw.decode('utf-8', errors='strict')


def _decimal(text):
    if not isinstance(text, str) or not re.fullmatch(rf'(?:-?{_NUMBER}|\({_NUMBER}\))', text):
        raise ValueError('documentary_exact_amount_required')
    value = Decimal(text.replace(',', '').replace('(', '-').replace(')', ''))
    if not value.is_finite():
        raise ValueError('documentary_exact_amount_required')
    return value


def reconcile_documentary_duration(selection, spec, filing, documentary, *, security,
                                   original_raw, source_generation, source_cutoff):
    """Return bounded H1 CFS CFO lineage; no XBRL impersonation or direction."""
    from app.services.kr_financial_lineage_service import opendart_field_lineage
    if type(documentary) is not DocumentaryDurationInput:
        raise ValueError('documentary_trusted_capture_handle_required')
    if (json.loads(documentary._security) != security or filing.ticker != security.get('ticker')
            or security.get('corp_code') != filing.corp_code or security.get('country') != 'KR'
            or not security.get('canonical_security_id') or not security.get('canonical_company_id')):
        raise ValueError('documentary_security_binding')
    if (spec.logical_field != 'operating_cash_flow' or spec.source_column != 'thstrm_amount'
            or selection.status != 'needs_xbrl' or selection.basis != 'CFS'
            or len(selection.candidates) != 1 or filing.report_code != '11012'
            or filing.correction or not filing.receipt_no.startswith(filing.receipt_date.strftime('%Y%m%d'))
            or not filing.receipt_date <= date.fromisoformat(source_cutoff[:10])):
        raise ValueError('documentary_original_selection_or_asof')
    row = selection.candidates[0]
    expected = dict(corp_code=filing.corp_code, rcept_no=filing.receipt_no,
        reprt_code=filing.report_code, bsns_year=str(filing.business_year), fs_div='CFS', sj_div='CF',
        currency='KRW', account_id='ifrs-full_CashFlowsFromUsedInOperatingActivities')
    if (any(str(row.get(k)) != v for k,v in expected.items())
            or row.get('account_nm') != '\uc601\uc5c5\ud65c\ub3d9\uc73c\ub85c \uc778\ud55c \ud604\uae08\ud750\ub984'
            or row.get('account_detail') not in (None, '-')):
        raise ValueError('documentary_original_row_identity')
    payload = _json(original_raw)
    # The original selector fills an omitted fs_div from its verified CFS
    # request. Preserve the exact raw occurrence alongside that normalization.
    occurrences = [(i, r) for i, r in enumerate(payload.get('list', []))
        if {**r, 'fs_div': str(r.get('fs_div') or selection.basis).upper()} == row]
    if payload.get('status') != '000' or len(occurrences) != 1:
        raise ValueError('documentary_original_row_membership')
    source = documentary.read()
    ir, sr = [_json(source[k]) for k in ('index_receipt', 'section_receipt')]
    iq, index_text = _received(source['index_raw'], ir, '/dsaf001/main.do')
    sq, text = _received(source['section_raw'], sr, '/report/viewer.do')
    if (iq != {'rcpNo': filing.receipt_no} or set(sq) != _VIEWER_KEYS
            or sq['rcpNo'] != filing.receipt_no or sq['dtd'] != 'dart4.xsd'
            or any(not sq[k].isdigit() for k in _VIEWER_KEYS-{'rcpNo','dtd'})
            or ir['source_generation'] != sr['source_generation']
            or ir['authorization_sha256'] != sr['authorization_sha256']
            or len({source_generation, sr['source_generation'], documentary._generation}) != 3
            or not _instant(ir['finished_at']) <= _instant(sr['started_at'])
            or not _instant(source_cutoff) <= _instant(documentary._cutoff)
            or not _instant(sr['finished_at']) <= _instant(documentary._cutoff)):
        raise ValueError('documentary_capture_relationship_or_generation')
    node = index_section_membership(index_text, sq, filing.corp_code)
    parent = sr.get('parent', {})
    if (parent.get('sha256') != ir['body_sha256'] or parent.get('bytes') != ir['body_bytes']
            or parent.get('relationship') != 'ORIGINAL_DART_LITERAL_INDEX_NODE'
            or parent.get('title') != node.get('text')
            or not re.fullmatch(r'[0-9]+-[0-9]+\.\s*\uc5f0\uacb0 \ud604\uae08\ud750\ub984\ud45c', node.get('text',''))):
        raise ValueError('documentary_index_parent_or_cf_section')
    parser = _DartTables()
    parser.feed(text); parser.close()
    if (len(parser.tables) != 2 or parser.structure or parser.stack or parser.cell or parser.row
            or any(t['nested'] for t in parser.tables)):
        raise ValueError('documentary_cf_table_shape')
    header, table = [grid(t) for t in parser.tables]
    if (len(header) != 4 or any(len(r) != 1 or not r[0] for r in header)
            or header[0][0]['text'] != '\uc5f0\uacb0 \ud604\uae08\ud750\ub984\ud45c'
            or re.sub(r'\s','',header[3][0]['text']) != '(\ub2e8\uc704:\uc6d0)'):
        raise ValueError('documentary_scope_or_unit')
    periods, labels = [], []
    for index, h in enumerate(header[1:3]):
        m = re.fullmatch(r'(\uc81c\s*[0-9]+\s*\uae30\s*\ubc18\uae30)\s+(20[0-9]{2}\.[0-9]{2}\.[0-9]{2})\s+\ubd80\ud130\s+(20[0-9]{2}\.[0-9]{2}\.[0-9]{2})\s+\uae4c\uc9c0', h[0]['text'])
        if not m:
            raise ValueError('documentary_explicit_period')
        start, end = m[2].replace('.','-'), m[3].replace('.','-')
        year = filing.business_year-index
        if (start,end) != (f'{year}-01-01',f'{year}-06-30') or date.fromisoformat(end) > filing.receipt_date:
            raise ValueError('documentary_half_year_period')
        periods.append(dict(start=start,end=end,header=h[0]['text']))
        labels.append(re.sub(r'\s','',m[1]))
    if (len(table) < 2 or any(len(r) != 3 or any(c is None for c in r) for r in table)
            or [re.sub(r'\s','',c['text']) for c in table[0][1:]] != labels):
        raise ValueError('documentary_comparison_columns')
    matches = [(i,r) for i,r in enumerate(table) if r[0]['text'] == row['account_nm']]
    if len(matches) != 1:
        raise ValueError('documentary_unique_metric_row')
    ri, values = matches[0]
    if any(c['rowspan'] != 1 or c['colspan'] != 1 for c in values):
        raise ValueError('documentary_merged_metric_row')
    amounts = [_decimal(c['text']) for c in values[1:]]
    if any(v != v.to_integral_value() for v in amounts):
        raise ValueError('documentary_integral_won_required')
    if amounts != [_decimal(str(row[k])) for k in ('thstrm_amount','frmtrm_q_amount')]:
        raise ValueError('documentary_exact_value_mismatch')
    # Preserve every other row as correlated context, never independent support.
    counter = [dict(row=i,label=r[0]['text'],current=r[1]['text'],prior=r[2]['text'])
        for i,r in enumerate(table[1:],1) if i != ri]
    proof = dict(contract=CONTRACT, admitted_capture_seal_sha256=documentary._pin,
        security=deepcopy(security), source_generation=source_generation,
        documentary_generation=sr['source_generation'], execution_generation=documentary._generation,
        original_raw_sha256=sha256(original_raw).hexdigest(), source_cutoff=source_cutoff,
        review_cutoff=documentary._cutoff, retrospective=True, current_qualified=False,
        availability='NEWLY_DOCUMENTED_RETROSPECTIVE_QUALIFICATION_NOT_OLD_CAPTURE',
        correction_status='ORIGINAL_DISCOVERY_ASOF_ONLY_CURRENT_NOT_CHECKED',
        filing_available_date=filing.receipt_date.isoformat(), original_row=deepcopy(occurrences[0][1]),
        original_row_locator=f'list[{occurrences[0][0]}]', normalized_selected_row=deepcopy(row),
        index_raw_sha256=ir['body_sha256'], document_raw_sha256=sr['body_sha256'],
        index_receipt_sha256=digest(ir), document_receipt_sha256=digest(sr),
        document_captured_at=sr['finished_at'], locator=sq, title=node['text'],
        periods=periods, unit_header=header[3][0]['text'], currency='KRW', scale=1,
        cells=[dict(table=1,row=ri,column=c+1,value=str(v),literal=values[c+1]['text']) for c,v in enumerate(amounts)],
        counterevidence_rows=counter, independent_corroboration=False,
        allowed_use='DATED_H1_CFS_CFO_FACT_AND_SAME_FILING_COMPARISON',
        denied_uses=['Q2_STANDALONE','CASH_CONVERSION','FCF','RECURRENCE','VALUATION','DIRECTION','STRICT_NATIVE'])
    proof['receipt_sha256'] = digest(proof)
    result = opendart_field_lineage(row, logical_field=spec.logical_field,
        report_code=filing.report_code, source_column=spec.source_column, selected=True, requested_fs_div='CFS')
    result.update(amount=int(amounts[0]), amount_period_start=periods[0]['start'],
        amount_period_end=periods[0]['end'], amount_period_type='year_to_date_cumulative',
        duration_days=(date.fromisoformat(periods[0]['end'])-date.fromisoformat(periods[0]['start'])).days+1,
        fiscal_year=filing.business_year, fiscal_quarter=2,
        period_source=CONTRACT, lineage_verified=True, quality_state='verified_usable',
        denial_reason=None, documentary_reconciliation=proof)
    return result
