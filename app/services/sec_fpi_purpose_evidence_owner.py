"""Source-bound operating-statement purpose, never financial-use authority.

The parent must obtain source_anchor and expected_capture_sha256 independently
from its sealed original probe replay. They are trust inputs, not fields copied
from an untrusted proposed disposition. This module performs no acquisition.
"""
from copy import deepcopy
from datetime import date, datetime
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit

from app.services.bounded_financial_acquisition import sec_base, sec_document_identity
from app.services.bounded_fpi_followup import request_manifest
from app.services.sec_fpi_financial_purpose import classify_document
from app.services.sec_fpi_purpose_probe import CONTRACT as PROBE_CONTRACT, PURPOSE
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'sec-fpi-purpose-evidence-owner-v1'
SCOPE = 'NOT_NEWER_REPORTED_ISSUER_OPERATING_STATEMENTS_ONLY'
MEDIA_CLEAR = 'NO_REPORTED_OPERATING_FINANCIAL_CONTENT'
MEDIA_FINANCIAL = 'REPORTED_OPERATING_FINANCIAL_CONTENT'
_DATE = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
_METRICS = r'\b(?:revenue|net sales|turnover|operating (?:income|profit|loss)|net (?:income|profit|loss)|gross profit|EBITDA|earnings per share)\b'
_STATEMENTS = (r'\b(?:balance sheets?|income statements?|statements? of (?:income|operations|comprehensive|cash|financial|changes)|'
               r'(?:audited|unaudited|consolidated|condensed|interim|quarterly)\s+(?:financial\s+)?statements?|'
               r'independent auditors?[^.]{0,20}(?:report|review)|financial statements?|financial results|'
               r'quarterly results|earnings (?:release|results)|financial information|financial highlights|results of operations)\b')


def _matches(pattern, text):
    return list(re.finditer(pattern, text, re.I))


class _Content(HTMLParser):
    """Inspect all text, including hidden elements, without executing scripts."""
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.text = ''
        self.segments, self.tables, self.stack, self.references = [], [], [], []
        self.active = []
        self.inline_media = False
        self.feed(html)
        self.close()
        for table in self.stack:
            table['end'] = len(self.text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'p', 'div', 'table', 'tr', 'td', 'th', 'li', 'br', 'hr', 'body', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self._boundary()
        if tag == 'table':
            table = {'section_id': f'table-{len(self.tables)}', 'start': len(self.text), 'end': None}
            self.tables.append(table)
            self.stack.append(table)
        if tag in {'script', 'style'}:
            self.active.append(tag)
        if tag in {'svg', 'canvas', 'math'} or 'srcdoc' in attrs:
            self.inline_media = True
        key = {'img': 'src', 'a': 'href', 'iframe': 'src', 'object': 'data',
               'embed': 'src', 'source': 'src', 'video': 'src', 'audio': 'src'}.get(tag)
        if key and attrs.get(key):
            self.references.append({'tag': tag, 'reference': attrs[key]})
        for key in ('poster', 'srcset'):
            if attrs.get(key):
                for value in attrs[key].split(','):
                    self.references.append({'tag': tag, 'reference': value.strip().split()[0]})
        for value in attrs.values():
            for match in re.finditer(r'url\([\s\"\x27]*([^\)\"\x27]+)', value or '', re.I):
                self.references.append({'tag': tag, 'reference': match[1].strip()})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == 'table' and self.stack:
            self.stack.pop()['end'] = len(self.text)
        if tag in self.active:
            self.active.remove(tag)
        if tag in {'p', 'div', 'table', 'tr', 'td', 'th', 'li', 'body', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self._boundary()

    def _boundary(self):
        if self.text and not self.text.endswith(' '):
            self.text += ' '

    def handle_data(self, data):
        text = re.sub(r'\s+', ' ', data)
        if not text.strip():
            self._boundary()
            return
        start = len(self.text)
        self.text += text
        self.segments.append({'start': start, 'end': len(self.text),
            'section_ids': [t['section_id'] for t in self.stack],
            'source_position': list(self.getpos()), 'active_content': bool(self.active)})

    def span(self, start, end):
        return {'start': start, 'end': end, 'text': self.text[start:end],
            'coordinate_system': 'WHOLE_DOCUMENT_NORMALIZED_TEXT_V1',
            'section_ids': sorted({s for row in self.segments if row['start'] < end and row['end'] > start
                                   for s in row['section_ids']})}


def _binding(primary, index, plan, receipts, anchor, expected, filing):
    if (plan.get('contract') != PROBE_CONTRACT or plan.get('purpose') != PURPOSE
            or plan.get('financial_authority') is not False or plan.get('source_use_eligible') is not False
            or digest({'plan': plan, 'receipts': receipts}) != expected):
        raise ValueError('purpose_evidence_original_probe_binding_failed')
    if (set(anchor) != {'discovery_sha256', 'discovery_receipt_file_sha256'}
            or any(not re.fullmatch(r'[a-f0-9]{64}', str(v)) for v in anchor.values())
            or any(plan['source_binding'].get(k) != v for k, v in anchor.items())):
        raise ValueError('purpose_evidence_original_discovery_anchor_failed')
    members = [f for f in plan['filings'] if f['accessionNumber'] == filing['accessionNumber']]
    if len(members) != 1 or members[0] != filing:
        raise ValueError('purpose_evidence_exact_filing_required')
    requests = {r['logical_id']: r for r in request_manifest(plan)}
    selected = {}
    for stage, raw in (('document', primary), ('index', index)):
        candidates = [r for r in receipts if r['filing'] == filing and r['stage'] == stage and not r['failure_class']]
        if len(candidates) != 1:
            raise ValueError('purpose_evidence_successful_primary_and_index_required')
        receipt = candidates[0]
        request = requests.get(receipt['logical_id'])
        url = sec_base(plan, filing) + (filing['primaryDocument'] if stage == 'document' else 'index.json')
        if (request is None or request['url'] != url or request['method'] != 'GET' or request['params']
                or receipt['request_sha256'] != digest(request) or receipt['plan_sha256'] != digest(plan)
                or receipt['HTTP_status'] != 200 or receipt.get('error_type') or receipt.get('purpose') != PURPOSE
                or receipt['raw_sha256'] != sha256_bytes(raw)):
            raise ValueError('purpose_evidence_raw_request_receipt_mismatch')
        selected[stage] = {'url': url, 'raw_sha256': sha256_bytes(raw), 'receipt_sha256': digest(receipt),
            'request_sha256': receipt['request_sha256'], 'started_at': receipt['started_at'], 'finished_at': receipt['finished_at']}
    return {'issuer': plan['issuer'], 'filing': deepcopy(filing), 'probe_generation': plan['run_id'],
        'probe_cutoff': plan['cutoff'], 'probe_capture_sha256': expected, 'probe_plan_sha256': digest(plan),
        'original_source_binding': deepcopy(plan['source_binding']), 'sources': selected}


class MediaReviewRegistry:
    """Ephemeral backend authority; JSON labels cannot recreate a pixel review.

    review_event_validator is trusted parent code, not a request parameter. It
    must authenticate an actual whole-asset inspection event against raw pixels,
    source binding and original acquisition. It returns status PASS, scope
    WHOLE_ASSET_PIXELS, disposition and a reason, or refuses the event.
    """
    def __init__(self, review_event_validator):
        if not callable(review_event_validator):
            raise ValueError('media_review_event_validator_required')
        self._validator, self._issued = review_event_validator, {}

    def record(self, asset_raw, *, asset_url, filing, primary_sha256, index_sha256,
               probe_capture_sha256, request, request_receipt, review_event):
        if not isinstance(asset_raw, bytes) or not (asset_raw.startswith((b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n', b'GIF87a', b'GIF89a'))
                or asset_raw[:4] == b'RIFF' and asset_raw[8:12] == b'WEBP'):
            raise ValueError('media_raster_bytes_required_not_attachment_text')
        binding = dict(asset_url=asset_url, asset_sha256=sha256_bytes(asset_raw), asset_bytes=len(asset_raw),
            filing=deepcopy(filing), primary_sha256=primary_sha256, index_sha256=index_sha256,
            probe_capture_sha256=probe_capture_sha256)
        if (request['url'] != asset_url or request['method'] != 'GET' or request['params']
                or request_receipt['request_sha256'] != digest(request)
                or request_receipt['raw_sha256'] != binding['asset_sha256']
                or request_receipt['HTTP_status'] != 200 or request_receipt['failure_class']
                or request_receipt.get('error_type')):
            raise ValueError('media_original_transport_binding_failed')
        observation = self._validator(review_event, asset_raw=asset_raw, binding=deepcopy(binding),
            request=deepcopy(request), request_receipt=deepcopy(request_receipt))
        if (not isinstance(observation, dict) or observation.get('status') != 'PASS'
                or observation.get('scope') != 'WHOLE_ASSET_PIXELS'
                or observation.get('disposition') not in {MEDIA_CLEAR, MEDIA_FINANCIAL, 'UNKNOWN'}
                or not observation.get('reason')):
            raise ValueError('media_actual_inspection_event_required')
        token = object()
        self._issued[token] = {**binding, 'observation': deepcopy(observation),
            'review_event': deepcopy(review_event), 'review_event_sha256': digest(review_event),
            'request_receipt_sha256': digest(request_receipt)}
        return token

    def validate(self, token, *, asset_url, filing, primary_sha256, index_sha256, probe_capture_sha256):
        try:
            row = self._issued[token]
        except (KeyError, TypeError):
            raise ValueError('media_unissued_or_serialized_capability') from None
        expected = dict(asset_url=asset_url, filing=filing, primary_sha256=primary_sha256,
            index_sha256=index_sha256, probe_capture_sha256=probe_capture_sha256)
        if any(row[k] != v for k, v in expected.items()):
            raise ValueError('media_filing_or_capture_binding_mismatch')
        return deepcopy(row)


def _coverage(index, content, plan, filing, binding, observations, validator):
    base = sec_base(plan, filing)
    directory = json.loads(index)['directory']
    if directory.get('name') != urlsplit(base).path.rstrip('/') or not isinstance(directory.get('item'), list):
        raise ValueError('purpose_evidence_index_identity_failed')
    names = [r.get('name') for r in directory['item'] if isinstance(r, dict)]
    if (len(names) != len(directory['item']) or len(names) != len(set(names))
            or any(not isinstance(n, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', n) or n in {'.', '..'} for n in names)
            or filing['primaryDocument'] not in names):
        raise ValueError('purpose_evidence_index_membership_failed')
    accession = filing['accessionNumber']
    containers = {filing['primaryDocument'], accession + '.txt', accession + '-index.html',
                  accession + '-index.htm', accession + '-index-headers.html'}
    inventory = {base + n for n in names if n not in containers}
    primary_url = base + filing['primaryDocument']
    inventory.update(urljoin(primary_url, r['reference']).split('#', 1)[0] for r in content.references
                     if urljoin(primary_url, r['reference']).split('#', 1)[0] != primary_url)
    results, used = [], set()
    for url in sorted(inventory):
        row = {'asset_url': url, 'status': 'MEDIA_CONTENT_UNRESOLVED', 'observation': None}
        try:
            sec_document_identity(url, plan, filing)
        except ValueError:
            row['status'] = 'UNRESOLVED_EXTERNAL_OR_INVALID_REFERENCE'
            results.append(row)
            continue
        # An index extension is inventory only, never evidence about its pixels.
        if validator is not None:
            for number, observation in enumerate(observations):
                try:
                    evidence = validator(observation, asset_url=url, filing=filing,
                        primary_sha256=binding['sources']['document']['raw_sha256'],
                        index_sha256=binding['sources']['index']['raw_sha256'],
                        probe_capture_sha256=binding['probe_capture_sha256'])
                except ValueError:
                    continue
                if number in used or row['observation'] is not None:
                    raise ValueError('media_duplicate_or_reused_capability')
                used.add(number)
                row.update(status=evidence['observation']['disposition'], observation=evidence)
        results.append(row)
    if len(used) != len(observations):
        raise ValueError('media_unbound_observation')
    if content.inline_media:
        results.append({'asset_url': primary_url + '#inline-media', 'status': 'MEDIA_CONTENT_UNRESOLVED', 'observation': None})
    return results


def _semantics(content, cutoff, original):
    text = content.text
    evidence, allowed, labels = [], [], []
    rationale = None

    def require(pattern):
        hits = _matches(pattern, text)
        evidence.extend(content.span(m.start(), m.end()) for m in hits)
        return bool(hits)

    schedule = all([require(r'plans? to hold[^.]{0,140}conference call'), require(r'\bAgenda\b'),
        require(r'\bDate and Time\b'), require(r'materials[^.]{0,220}will be available[^.]{0,180}' + _DATE)])
    if schedule:
        future = _matches(r'materials[^.]{0,220}will be available[^.]{0,180}(' + _DATE + ')', text)
        dates = [datetime.strptime(m[1].replace(',', ''), '%B %d %Y').date() for m in future]
        meetings = _matches(r'Date and Time\s+(' + _DATE + ')', text)
        meeting_dates = [datetime.strptime(m[1].replace(',', ''), '%B %d %Y').date() for m in meetings]
        if dates and meeting_dates and all(d > cutoff for d in dates + meeting_dates):
            rationale = 'FUTURE_EARNINGS_CALL_SCHEDULE_NOT_DELIVERED_RESULTS'
            allowed = [(m.start(), m.end()) for m in _matches(
                r'\b\d{4}\s+[1-4]Q\s+Earnings Results\b|'
                r'Financial Information[\s\u00ae>/\-]{1,20}Earnings Release', text)]
            labels.extend({'label': m[0], 'role': 'SCHEDULE_ONLY_NOT_REPORTED_PERIOD'}
                          for m in _matches(r'\b\d{4}\s+[1-4]Q\b', text))
            labels.extend({'label': d.isoformat(), 'role': 'FUTURE_MATERIALS_RELEASE'} for d in dates)
    disposal = all([require(r'Report on Disposal of Treasury Shares'), require(r'disposed of[^.]{0,100}treasury shares'),
        require(r'Period of Disposal'), require(r'Type and Number of Disposed Shares'),
        require(r'Disposal\s+Price\s+per\s+Share'), require(r'Aggregate\s+Disposal\s+Price'),
        require(r'Treasury Shares Held after the Disposal'), require(_DATE), require(r'\b\d[\d,]+\b')])
    if disposal:
        rationale = 'TREASURY_SHARE_DISPOSAL_CAPITAL_TRANSACTION'
    acquisition = all([require(r'Decision on Acquisition of Treasury Shares'), require(r'approved[^.]{0,150}acquisition of treasury shares'),
        require(r'Number of Treasury Shares to be Acquired'), require(r'Estimated Aggregate Acquisition Value'),
        require(r'Planned Acquisition Period'), require(r'Limit on Treasury Share Acquisition Amount')])
    cap_tables = [t for t in content.tables if t['end'] is not None
        and re.search(r'Limit on distributable profit under the Commercial Act', text[t['start']:t['end']], re.I)
        and re.search(r'Total Limit on Treasury Share Acquisition Amount', text[t['start']:t['end']], re.I)]
    cap_notes = _matches(r'The[^.!?]{0,20}Limit on distributable profit[^.!?]{0,220}prepared based on[^.!?]{0,100}'
                        r'financial statements as of the end of fiscal year (\d{4})', text)
    historical_cap = acquisition and len(cap_tables) == 1 and len(cap_notes) == 1 and int(cap_notes[0][1]) < cutoff.year
    if historical_cap:
        rationale = 'TREASURY_ACQUISITION_WITH_HISTORICAL_LEGAL_CAP'
        allowed.append((cap_notes[0].start(), cap_notes[0].end()))
        evidence.extend(content.span(t['start'], t['end']) for t in cap_tables)
        evidence.append(content.span(cap_notes[0].start(), cap_notes[0].end()))
        labels.append({'label': cap_notes[0][1], 'role': 'HISTORICAL_LEGAL_CAP_NOT_OPERATING_PERIOD'})
    rumor = (original['purpose'] == 'RUMOR_OR_DISCLOSURE_RESPONSE'
        and require(r'(?:Response to Disclosure Inquiry|Clarification Regarding Rumors)')
        and require(r'no matters have been determined') and require(r'further disclosure'))
    cancellation = all([require(r'Decision on Cancellation of Treasury Shares'), require(r'approved[^.]{0,100}cancellation'),
        require(r'Number of Shares to be Cancelled'), require(r'Aggregate Cancellation Value'), require(r'no change to[^.]{0,50}capital')])
    returns = all([require(r'Shareholder Return Policy'), require(r'policy period'),
        require(r'plans to return[^.]{0,120}Free Cash Flow'), require(r'acquir\w*[^.]{0,80}cancel[^.]{0,40}treasury shares'),
        require(r'cash dividends'), require(r'forward-looking statements')])
    if rumor:
        rationale = 'UNDETERMINED_CORPORATE_EVENT_RUMOR_RESPONSE'
    elif cancellation:
        rationale = 'TREASURY_SHARE_CANCELLATION_CAPITAL_TRANSACTION'
    elif returns:
        rationale = 'PROSPECTIVE_CAPITAL_RETURN_POLICY_NOT_REPORTED_CASH_FLOW'
    if disposal or acquisition or cancellation:
        labels.extend({'label': m[0], 'role': 'CAPITAL_TRANSACTION_CONTEXT_NOT_OPERATING_PERIOD'}
                      for m in _matches(_DATE, text))
    conflicts = _matches(_METRICS, text)
    conflicts += [m for m in _matches(_STATEMENTS, text)
                  if not any(start <= m.start() and m.end() <= end for start, end in allowed)]
    for m in _matches(r'\b(?:net assets|retained earnings)\b', text):
        if not historical_cap or not any(t['start'] <= m.start() < t['end'] for t in cap_tables):
            conflicts.append(m)
    conflicts += _matches(r'\b(?:three|six|3|6)[ -]months?\s+(?:ended|ending)|\b(?:Q[1-4]|[1-4]Q)\s+(?:revenue|profit)', text)
    conflicts += _matches(r'\bfree\s+cash\s+flow\s*(?:\([^)]{0,60}\)\s*)?'
        r'(?:(?:was|is|of|amounted to|:|=)\s*)?(?:[A-Z]{3}|[$\u20ac\u20a9])?\s*[-+(]?\s*\d', text)
    conflicts += _matches(r'\b(?:free cash flow|cash flow from operating activities)\s+'
        r'(?:for[^.]{0,60})?(?:was|is|totaled|totalled|of|:)\s*(?:(?:KRW|USD|Won)\s*)?[-(]?\d|'
        r'\b(?:profit|loss|sales|cash flows?)\s+(?:for|during)\s+(?:the\s+)?(?:quarter|period|year|three|six)\b', text)
    if original.get('source_precedence_conflicts'):
        rationale = None
    return rationale, evidence, labels, [content.span(m.start(), m.end()) for m in conflicts]


def qualify_purpose(primary, index, *, probe_plan, probe_receipts, source_anchor,
                    expected_capture_sha256, filing, media_observations=(), media_validator=None):
    """Recompute one exact filing. A result is audit-only across generations."""
    if not isinstance(primary, bytes) or not isinstance(index, bytes) or max(len(primary), len(index)) > 20 * 1024**2:
        raise ValueError('purpose_evidence_bounded_raw_bytes_required')
    if media_validator is not None and (not isinstance(getattr(media_validator, '__self__', None), MediaReviewRegistry)
            or getattr(media_validator, '__func__', None) is not MediaReviewRegistry.validate):
        raise ValueError('media_backend_registry_validator_required')
    binding = _binding(primary, index, probe_plan, probe_receipts, source_anchor, expected_capture_sha256, filing)
    content = _Content(primary.decode('utf-8'))
    original = classify_document(primary, url=binding['sources']['document']['url'], filing=filing,
        plan={**probe_plan, 'financial_owner_policy': 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'})
    coverage = _coverage(index, content, probe_plan, filing, binding, media_observations, media_validator)
    rationale, spans, labels, conflicts = _semantics(content, date.fromisoformat(probe_plan['cutoff'][:10]), original)
    gaps = [r['asset_url'] for r in coverage if r['status'] != MEDIA_CLEAR]
    reasons = []
    if conflicts:reasons.append('UNDEFINED_OR_CONFLICTING_FINANCIAL_CONTENT')
    if any(r['status'] == MEDIA_FINANCIAL for r in coverage):reasons.append('FINANCIAL_MEDIA_REQUIRES_ORIGINAL_FIELD_PARSER')
    if gaps:reasons.append('MEDIA_CONTENT_UNRESOLVED')
    if re.search(r'attached (?:hereto|as)|furnished (?:herewith|as exhibit)|incorporated (?:herein )?by reference', content.text, re.I):
        reasons.append('ATTACHMENT_OR_INCORPORATED_CONTENT_UNRESOLVED')
    if filing['form'].endswith('/A'):reasons.append('AMENDED_FILING_REQUIRES_RELATED_SOURCE_REVIEW')
    if any(row['active_content'] for row in content.segments):reasons.append('ACTIVE_INLINE_CONTENT_UNRESOLVED')
    if any(ord(c) > 127 and c.isalpha() for c in content.text):reasons.append('UNINSPECTED_LANGUAGE_CONTENT')
    if original['occurrences']:
        classification = 'FINANCIAL_WITH_FIELD_PERIOD' if original['valid_occurrence_ids'] and original['economic_periods'] else 'UNKNOWN_UNRESOLVED'
        reasons.append('ORIGINAL_STATEMENT_OCCURRENCES_PRESENT')
    elif rationale and not reasons:
        classification = 'CONFIRMED_NON_FINANCIAL'
    else:
        classification = 'UNKNOWN_UNRESOLVED'
        if not rationale:reasons.append('PURPOSE_GRAMMAR_UNRESOLVED')
    result = {'contract': CONTRACT, 'classification': classification, 'classification_scope': SCOPE,
        'rationale': rationale, 'binding': binding, 'original_classifier': original,
        'source_spans': spans, 'period_labels': labels, 'conflicting_spans': conflicts,
        'field_absence_audit': {'normalized_text_sha256': sha256_bytes(content.text.encode()),
            'inspected_text_characters': len(content.text), 'inspected_segments': len(content.segments),
            'inspected_tables': len(content.tables), 'original_occurrence_count': len(original['occurrences']),
            'complete_for_purpose': classification == 'CONFIRMED_NON_FINANCIAL', 'numeric_fact_authority': False},
        'media_coverage': coverage, 'unresolved_assets': gaps, 'denial_reasons': sorted(set(reasons)),
        'related_filing_caveats': [content.span(m.start(), m.end()) for m in _matches(
            r'(?:Related Disclosure|please refer to|See the current report)[^.]{0,300}', content.text)],
        'economic_periods': original['economic_periods'], 'financial_authority': False, 'source_use_eligible': False,
        'current_owner_eligible': False, 'cross_generation_use': 'AUDIT_ONLY_REQUIRES_ORIGINAL_RECONCILIATION_OWNER',
        'admitted_fact_count': 0, 'native_ready': False}
    result['receipt_sha256'] = digest(result)
    return result


def validate_purpose(receipt, primary, index, **kwargs):
    expected = qualify_purpose(primary, index, **kwargs)
    if receipt != expected:
        raise ValueError('purpose_evidence_replay_mismatch')
    return expected
