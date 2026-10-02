"""Bounded exact-security schedule policy, not an all-time absence theorem.

Offline only. Raw date fields retain their own meanings; none is renamed to an
effective date. Production imports and the old all-security owner are unchanged.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta
import re

from scripts import kis_current_fy1_owner as p
from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.kis_fy1_semantic_owner import SemanticGap

ACTION = 'CorporateActionCompatibilityReceiptV2'
FAMILY = 'KISExactSecurityScheduleFamilyV2'
POLICY = 'BOUNDED_EXACT_SECURITY_SHARE_UNIT_GUARD_V1'
ENVELOPE = 'SHARE_UNIT_GUARD_ENVELOPE_V1'
CLEAR = 'NO_RELEVANT_SHARE_UNIT_ACTION_FOUND_V1'
EVENT = 'POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT'
UNRESOLVED = 'CORPORATE_ACTION_DATE_UNRESOLVED'
INCOMPLETE = 'CORPORATE_ACTION_SOURCE_INCOMPLETE'
CONFLICT = 'CORPORATE_ACTION_IDENTITY_CONFLICT'
VARIANTS = {
    'merger_split': p.ROUTES['merger_split'],
    'rev_split': p.ROUTES['rev_split'],
    'bonus_issue': p.ROUTES['bonus_issue'],
    'paidin_capin_gb1': ('paidin-capin', 'HHKDB669100C0', {'GB1': '1'}),
    'paidin_capin_gb2': ('paidin-capin', 'HHKDB669100C0', {'GB1': '2'}),
    'cap_dcrs': p.ROUTES['cap_dcrs'],
}
DATE_FIELDS = {
    'merger_split': ('record_date', 'list_dt', 'td_stop_dt'),
    'rev_split': ('record_date', 'list_dt', 'td_stop_dt'),
    'bonus_issue': ('record_date', 'right_dt', 'list_date'),
    'paidin_capin_gb1': ('record_date', 'right_dt', 'list_date', 'sub_term_ft', 'sub_term'),
    'paidin_capin_gb2': ('record_date', 'right_dt', 'list_date', 'sub_term_ft', 'sub_term'),
    'cap_dcrs': ('record_date', 'list_dt', 'td_stop_dt'),
}
# cust_cd/opp_cust_cd are merger counterparties, not the row's security owner.
IDENTITY_FIELDS = ('sht_cd', 'stck_shrn_iscd', 'short_code')
TERMINAL_HEADERS = {'D', 'E'}
MORE_HEADERS = {'M', 'F'}


def envelope(estimate, session):
    start, end = date.fromisoformat(estimate), date.fromisoformat(session)
    if start > end:
        raise SemanticGap('ESTIMATE_AFTER_PRICE')
    return {'policy': ENVELOPE, 'start': str(start - timedelta(days=365)),
            'end': str(end + timedelta(days=365)), 'critical_start_exclusive': estimate,
            'critical_end_inclusive': session}


def action_params(variant, code, window, cursor=''):
    if not re.fullmatch(r'[0-9]{6}', code):
        raise SemanticGap('EXACT_NUMERIC_SECURITY_REQUIRED')
    return {'CTS': cursor, 'SHT_CD': code,
        'F_DT': date.fromisoformat(window['start']).strftime('%Y%m%d'),
        'T_DT': date.fromisoformat(window['end']).strftime('%Y%m%d'), **VARIANTS[variant][2]}


def route_contract(variant, documentation):
    item = documentation['actions'][variant]
    path, tr, extras = VARIANTS[variant]
    if (item.get('method') != 'GET' or item.get('path') != '/uapi/domestic-stock/v1/ksdinfo/' + path
            or item.get('tr_id') != tr or item.get('extra_params') != extras
            or item.get('security_filter') != 'EXACT_SHT_CD'
            or not re.fullmatch(r'[a-f0-9]{64}', item.get('source_sha256', ''))):
        raise SemanticGap('EXACT_ROUTE_DOCUMENTATION_GAP')
    return item


def next_cursor(payload, headers, current, seen, contract):
    status = headers.get('tr_cont')
    if status in TERMINAL_HEADERS:
        return None
    if status not in MORE_HEADERS:
        raise SemanticGap('CONTINUATION_STATUS_UNKNOWN')
    binding = contract.get('cursor_binding')
    if (not isinstance(binding, dict) or binding.get('request_param') != 'CTS'
            or binding.get('response_location') != 'body'
            or not re.fullmatch(r'[a-f0-9]{64}', binding.get('source_sha256', ''))):
        raise SemanticGap('CONTINUATION_CURSOR_AUTHORITY_GAP')
    value = payload.get(binding.get('field'))
    if not isinstance(value, str) or not value.strip():
        raise SemanticGap('CONTINUATION_CURSOR_MISSING')
    if value == current or value in seen:
        raise SemanticGap('CONTINUATION_CURSOR_UNCHANGED_OR_LOOP')
    return value


def row_identity(row, code):
    """Classify one row only; never perform a global numeric-code rejection."""
    fields = {k: row[k] for k in IDENTITY_FIELDS if row.get(k) not in (None, '')}
    if not fields:
        return 'MISSING_IDENTITY'
    return 'EXACT' if all(v == code for v in fields.values()) else 'CONFLICT'


def _dates(value):
    if not isinstance(value, str) or not value.strip():
        raise SemanticGap('EVENT_DATE_MISSING')
    value = value.strip()
    forms = (r'[0-9]{8}', r'[0-9]{4}-[0-9]{2}-[0-9]{2}',
             r'[0-9]{4}\.[0-9]{2}\.[0-9]{2}', r'[0-9]{4}/[0-9]{2}/[0-9]{2}')
    formats = ('%Y%m%d', '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d')
    for pattern, fmt in zip(forms, formats):
        if re.fullmatch(pattern, value):
            try:
                return [datetime.strptime(value, fmt).date()]
            except ValueError:
                break
        match = re.fullmatch('(' + pattern + r')\s*~\s*(' + pattern + ')', value)
        if match:
            try:
                days = [datetime.strptime(part, fmt).date() for part in match.groups()]
                if days[0] <= days[1]:
                    return days
            except ValueError:
                break
    raise SemanticGap('EVENT_DATE_FORMAT_OR_INTERVAL_UNRESOLVED')


def event_decision(variant, row, estimate, session, documented_columns):
    start, end = date.fromisoformat(estimate), date.fromisoformat(session)
    fields = {k: deepcopy(v) for k, v in row.items()
              if k in DATE_FIELDS[variant] or k in documented_columns and
              (k.endswith(('_dt', '_date')) or 'term' in k)}
    parsed, errors = {}, []
    # Undocumented date-shaped columns are not silently used as an absence proof.
    for key in row:
        if (key.endswith(('_dt', '_date')) or 'term' in key) and key not in fields:
            fields[key] = deepcopy(row[key])
            errors.append('UNDOCUMENTED_DATE_FIELD:' + key)
    relevant = DATE_FIELDS[variant]
    for field in relevant:
        try:
            parsed[field] = [str(d) for d in _dates(row.get(field))]
        except SemanticGap as exc:
            errors.append(str(exc) + ':' + field)
    days = [date.fromisoformat(d) for values in parsed.values() for d in values]
    if any(start < d <= end for d in days):
        classification = 'CRITICAL_WINDOW_DATE'
    elif days and min(days) <= start and max(days) > end:
        classification = 'STRADDLING_ACTION_PROCESS'
    elif errors or not days:
        classification = 'AMBIGUOUS_EXACT_SECURITY_ACTION'
    elif max(days) <= start:
        classification = 'WHOLLY_ON_OR_BEFORE_ESTIMATE'
    elif min(days) > end:
        classification = 'WHOLLY_AFTER_PRICE'
    else:
        classification = 'AMBIGUOUS_EXACT_SECURITY_ACTION'
    return {'raw': deepcopy(row), 'source_dates': fields, 'parsed_relevant_dates': parsed,
        'errors': errors, 'classification': classification,
        'blocks': classification not in {'WHOLLY_ON_OR_BEFORE_ESTIMATE', 'WHOLLY_AFTER_PRICE'},
        'effective_date_inferred': False}


def family_receipt(variant, code, estimate, session, pages, documentation):
    window = envelope(estimate, session)
    contract = route_contract(variant, documentation)
    hashes, receipt_hashes, audits, page_audits, errors = [], [], [], [], []
    cursor, seen, page_fingerprints, complete = '', set(), set(), False
    if not pages:
        errors.append('MISSING_FAMILY_SOURCE')
    for index, (evidence, receipt) in enumerate(pages):
        hashes.append(evidence.sha256)
        receipt_hashes.append(digest(receipt))
        page = {'page': index + 1, 'raw_sha256': evidence.sha256,
                'request_sha256': digest(receipt.get('request', {})),
                'request': deepcopy(receipt.get('request', {})),
                'response_headers': deepcopy(receipt.get('response_headers', {})),
                'retrieved_at': receipt.get('ended_at')}
        page_audits.append(page)
        try:
            if complete:
                raise SemanticGap('PAGE_AFTER_TERMINAL')
            payload = p._source(evidence, receipt, contract['path'], contract['tr_id'],
                                action_params(variant, code, window, cursor))
            if receipt['request'].get('tr_cont') != ('' if index == 0 else 'N'):
                raise SemanticGap('CONTINUATION_REQUEST_GAP')
            rows = payload.get('output1')
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise SemanticGap('ACTION_ROWS_GAP')
            # A changed envelope/cursor cannot disguise an unchanged data page.
            row_hash = digest(rows)
            if evidence.sha256 in hashes[:-1] or row_hash in page_fingerprints:
                raise SemanticGap('DUPLICATE_PAGE_LOOP')
            page_fingerprints.add(row_hash)
            page['row_count'] = len(rows)
            for row in rows:
                identity = row_identity(row, code)
                if identity != 'EXACT':
                    audits.append({'raw': deepcopy(row), 'identity': identity, 'blocks': True})
                    errors.append('ACTION_IDENTITY_' + identity)
                else:
                    audits.append({'identity': identity, **event_decision(variant, row, estimate, session, contract['columns'])})
            next_value = next_cursor(payload, receipt['response_headers'], cursor, seen, contract)
            page['next_cursor'] = next_value
            complete = next_value is None
            if not complete:
                seen.add(cursor)
                cursor = next_value
        except (SemanticGap, KeyError, ValueError, TypeError) as exc:
            errors.append(str(exc) if isinstance(exc, SemanticGap) else 'MALFORMED_ACTION_SOURCE')
            complete = False
            break
    if not complete:
        errors.append('CONTINUATION_OR_SOURCE_INCOMPLETE')
    identity_conflict = any(e == 'ACTION_IDENTITY_CONFLICT' for e in errors)
    state = CONFLICT if identity_conflict else INCOMPLETE if errors else 'COMPLETE_QUERY'
    return sealed({'contract': FAMILY, 'variant': variant, 'security_code': code,
        'estimate_date': estimate, 'price_date': session, 'guard_envelope': window,
        'state': state, 'query_status': state, 'continuation_status': 'TERMINAL' if complete else 'UNRESOLVED',
        'source_hashes': hashes, 'source_receipt_hashes': receipt_hashes, 'pages': page_audits,
        'row_audits': audits, 'returned_exact_security_rows': [a['raw'] for a in audits if a['identity'] == 'EXACT'],
        'errors': sorted(set(errors)), 'policy': POLICY, 'effective_date_theorem': False,
        'official_documentation_sha256': digest(documentation)})


def compatibility_receipt(eps, price, families):
    p.eps_receipt(eps)
    verified(price, p.PRICE)
    code, estimate, session = eps['security_code'], eps['estdate'], price['session_date']
    if price['security_code'] != code:
        raise SemanticGap('ACTION_SECURITY_MISMATCH')
    window = envelope(estimate, session)
    errors, events, identity_conflict = [], [], False
    if set(families) != set(VARIANTS):
        errors.append('REQUIRED_ACTION_VARIANT_MISSING_OR_EXTRA')
    for variant, receipt in sorted(families.items()):
        verified(receipt, FAMILY)
        if (receipt['variant'] != variant or receipt['security_code'] != code
                or receipt['estimate_date'] != estimate or receipt['price_date'] != session
                or receipt['guard_envelope'] != window or receipt['policy'] != POLICY):
            raise SemanticGap('ACTION_FAMILY_BINDING_GAP')
        if receipt['state'] != 'COMPLETE_QUERY' or receipt['errors'] or receipt['continuation_status'] != 'TERMINAL':
            errors.append('INCOMPLETE_VARIANT:' + variant)
        identity_conflict |= receipt['state'] == CONFLICT
        events.extend({'variant': variant, **deepcopy(a)} for a in receipt['row_audits'])
    # A blocked row is not necessarily evidence of an in-window action.
    proven = any(a.get('classification') in {'CRITICAL_WINDOW_DATE', 'STRADDLING_ACTION_PROCESS'}
                 for a in events)
    unresolved = any(a['blocks'] for a in events)
    state = (CONFLICT if identity_conflict else INCOMPLETE if errors else EVENT if proven
             else UNRESOLVED if unresolved else CLEAR)
    return sealed({'contract': ACTION, 'state': state, 'security_code': code,
        'canonical_security_id': price['canonical_security_id'], 'estimate_date': estimate,
        'price_date': session, 'guard_envelope': window, 'policy': POLICY,
        'query_status': 'COMPLETE' if not errors else 'INCOMPLETE',
        'queried_variants': sorted(families), 'variants': deepcopy(families), 'events': events,
        'denial_reasons': sorted(set(errors)), 'adjustments_performed': 0,
        'policy_claim': 'BOUNDED_SCHEDULE_GUARD_ONLY_NOT_ALL_TIME_ACTION_ABSENCE',
        'share_unit_action_found_or_ambiguous': any(a['blocks'] for a in events)})


def validate_compatibility(candidate, eps, price):
    verified(candidate, ACTION)
    if candidate != compatibility_receipt(eps, price, candidate['variants']):
        raise SemanticGap('ACTION_GUARD_REPRODUCTION_GAP')
