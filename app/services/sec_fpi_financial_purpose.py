"""Bounded, opt-in FPI document purpose and economic-period ownership.

Metadata orders the finite inspection window; only the existing statement-cell
parser grants financial purpose. Nonfinancial text labels grant no field use.
"""
from datetime import date
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

from app.services.bounded_financial_acquisition import sec_selection, sec_document_identity
from app.services.sec_foreign_comparison_service import parse_document, occurrence_errors
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes

CONTRACT = 'sec-fpi-financial-purpose-v1'
# Two existing four-filing inspection windows, fixed before any follow-up.
# This is a resource ceiling, not a promise that a financial filing is in it.
SEC_FPI_MAX_PURPOSE_CANDIDATES = 8
FINANCIAL = frozenset({'FINANCIAL_STATEMENTS', 'FINANCIAL_RESULTS_OR_EARNINGS'})


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def classify_document(raw, *, url, filing, plan):
    identity = sec_document_identity(url, plan, filing)
    html = raw.decode('utf-8', errors='replace')
    occurrences = parse_document(html, issuer_cik=plan['issuer'],
        accession=filing['accessionNumber'], document_type=filing['form'],
        filing_date=filing['filingDate'], source_url=identity, raw_payload=raw)
    inline = None
    conflicts = []
    if plan.get('financial_owner_policy'):
        from app.services.sec_primary_inline_financial import extract, merge_occurrences
        inline = extract(raw, issuer_cik=plan['issuer'], filing=filing, source_url=identity)
        occurrences, conflicts = merge_occurrences(inline['occurrences'], occurrences, date.fromisoformat(plan['cutoff'][:10]))
    parser = PlainText()
    parser.feed(html)
    text = re.sub(r'\s+', ' ', ' '.join(parser.parts))
    purpose, evidence = 'UNKNOWN_PURPOSE', []
    if occurrences or inline and inline['qualified_document_purpose']:
        purpose = 'FINANCIAL_STATEMENTS'
        if re.search(r'\b(?:financial results|earnings release|quarterly results)\b', text, re.I):
            purpose = 'FINANCIAL_RESULTS_OR_EARNINGS'
        evidence = [o['occurrence_id'] for o in occurrences]
    elif (filing['form'].split('/')[0] != '20-F'
          and not re.search(r'(?i)(?:financial|interim|quarterly)\s+(?:statements?|results|report|information)'
                            r'|(?:consolidated|separate).*?statements? of|earnings release', text)):
        # These labels are diagnostics, never an affirmative financial authority.
        for state, pattern in (
            ('RUMOR_OR_DISCLOSURE_RESPONSE', r'(?i)response to (?:a |the )?(?:disclosure |media )?(?:inquiry|rumou?r)|(?:clarification|disclosure) (?:of|regarding) (?:a |the )?rumou?r'),
            ('DIVIDEND_OR_CAPITAL_RETURN', r'(?i)dividend(?: per share| adjustment| distribution| payment)|cash dividend'),
            ('GOVERNANCE_OR_COMPENSATION', r'(?i)restricted share|share (?:award|incentive) (?:plan|scheme)|compensation|share option|equity incentive|monthly return.*(?:equity issuer|securities)|changes in (?:the )?shareholdings of'),
            ('REVENUE_DISCLOSURE_ONLY', r'(?i)monthly (?:net )?revenue|revenue for (?:the month|august|july|june|may|april|march|february|january|september|october|november|december)'),
            ('CORPORATE_EVENT_NONFINANCIAL', r'(?i)lock-up|lockup|initial public offering|annual general meeting|resignation|board of directors.*(?:resolution|meeting)|waiver from (?:strict )?compliance with (?:rule|the listing rules)'),
        ):
            match = re.search(pattern, text)
            if match:
                purpose, evidence = state, [match[0]]
                break
    cutoff = date.fromisoformat(plan['cutoff'][:10])
    valid = [o for o in occurrences if not occurrence_errors(o, cutoff)]
    periods = sorted({(o['period_start'], o['period_end'], o['period_scope']) for o in valid})
    result = {'contract': CONTRACT, 'accession': filing['accessionNumber'],
        **({'filing_form': filing['form']} if plan.get('financial_owner_policy') else {}),
        'filing_date': filing['filingDate'], 'sec_report_date': filing.get('reportDate'),
        'source_url': url, 'document_identity': identity, 'source_payload_sha256': sha256_bytes(raw),
        'purpose': purpose, 'purpose_evidence': evidence,
        'economic_periods': [{'start': s, 'end': e, 'role': p,
            'source': 'EXACT_STATEMENT_CELL_HEADERS'} for s, e, p in periods],
        'occurrences': occurrences, 'financial_authority': purpose in FINANCIAL and bool(valid),
        'valid_occurrence_ids': [o['occurrence_id'] for o in valid],
        'document_captured': True}
    if inline is not None:
        result.update(inline_owner=inline, source_precedence_conflicts=conflicts, table_owner_ran=True,
            unresolved_financial_content=purpose == 'UNKNOWN_PURPOSE' and bool(re.search(
                r'(?i)(?:financial|interim|quarterly)\s+(?:statements?|results|report|information)'
                r'|(?:consolidated|separate).*?statements? of|earnings release', text)))
        for period in result['economic_periods']:
            period['source'] = 'EXACT_INLINE_OR_STATEMENT_CONTEXT'
    result['receipt_sha256'] = digest(result)
    return result


def candidate_inventory(payload, plan):
    # Reuse existing identity, discovery completeness, form and 550-day gates.
    sec_selection(payload, plan)
    recent = payload['filings']['recent']
    names = ('form', 'accessionNumber', 'primaryDocument', 'filingDate', 'reportDate')
    rows = [dict(zip(names, values, strict=True)) for values in zip(*(recent[n] for n in names), strict=True)]
    rows = [r for r in rows if r['form'] in plan['forms'] and plan['begin'] <= r['filingDate'] <= plan['cutoff'][:10]]
    if plan.get('financial_owner_policy'):
        from app.services.sec_current_financial_candidates import candidate_plan
        frozen = candidate_plan(rows, plan)
        return dict(contract=CONTRACT, candidate_count=len(rows), candidate_cap=3,
            candidates=rows, inspection_window=frozen['candidates'],
            uninspected_count=len(frozen['outside_bound']), exhaustion_reason=None,
            current_financial_plan=frozen, order='FINITE_CURRENT_FINANCIAL_CANDIDATES_METADATA_ONLY')
    rows.sort(key=lambda r: (r['filingDate'], r['reportDate'], r['accessionNumber']), reverse=True)
    selected = rows[:SEC_FPI_MAX_PURPOSE_CANDIDATES]
    return {'contract': CONTRACT, 'candidate_count': len(rows),
        'candidate_cap': SEC_FPI_MAX_PURPOSE_CANDIDATES, 'candidates': rows,
        'inspection_window': selected, 'uninspected_count': max(0, len(rows) - len(selected)),
        'exhaustion_reason': 'FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED' if len(rows) > len(selected) else None,
        'order': 'filingDate_reportDate_accessionNumber_descending_no_filename_or_value_ranking'}


def bind_nonfinancial_embedded_assets(documents, source_documents, plan):
    """An exact IMG resource belongs to its captured nonfinancial filing, not a new report."""
    class Images(HTMLParser):
        def __init__(self):
            super().__init__()
            self.refs = []

        def handle_starttag(self, tag, attrs):
            if tag == 'img' and dict(attrs).get('src'):
                self.refs.append(dict(attrs)['src'])

    for doc, source in zip(documents, source_documents, strict=True):
        if doc['purpose'] != 'UNKNOWN_PURPOSE' or not source['raw'].startswith((b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n')):
            continue
        parents = []
        for owner, raw_owner in zip(documents, source_documents, strict=True):
            if owner['accession'] != doc['accession'] or owner['purpose'] in FINANCIAL | {'UNKNOWN_PURPOSE'}:
                continue
            parser = Images()
            parser.feed(raw_owner['raw'].decode(errors='replace'))
            for ref in parser.refs:
                url = urljoin(owner['source_url'], ref)
                if url == doc['source_url'] and sec_document_identity(url, plan, source['filing']) == url:
                    parents.append({'source_url': owner['source_url'], 'source_payload_sha256': owner['source_payload_sha256'],
                        'purpose': owner['purpose'], 'source_element': {'tag': 'img', 'src': ref}})
        if parents:
            doc.update(purpose='NONFINANCIAL_EMBEDDED_ASSET', original_purpose='UNKNOWN_PURPOSE',
                purpose_evidence=parents, financial_authority=False, asset_content_interpreted=False)
            doc['receipt_sha256'] = digest({k: v for k, v in doc.items() if k != 'receipt_sha256'})


def select_economic_period(documents, *, required_role='single-quarter', uncaptured=()):
    """No annual fallback; unresolved newer documents cannot authorize an old quarter."""
    financial = [d for d in documents if d['purpose'] in FINANCIAL]
    pairs = [(d, p) for d in financial for p in d['economic_periods'] if p['role'] == required_role]
    denials = []
    if not pairs:
        return {'status': 'BLOCKED', 'period_end': None, 'source_accessions': [],
            'denial_reasons': ['NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_BOUND' if not financial else 'NO_COMPARABLE_PERIOD']}
    end = max(p['end'] for _, p in pairs)
    current = [d for d, p in pairs if p['end'] == end]
    latest_filed = max(d['filing_date'] for d in current)
    resolved_filings = {d['accession'] for d in financial if d['economic_periods']}
    unresolved = [d for d in documents if d['accession'] not in resolved_filings
                  and (d['purpose'] == 'UNKNOWN_PURPOSE'
                       or (d['purpose'] in FINANCIAL and not d['economic_periods']))]
    if any(d['filing_date'] >= latest_filed for d in unresolved) or any(f['filingDate'] >= latest_filed for f in uncaptured):
        denials.append('NEWER_FPI_PURPOSE_OR_PERIOD_UNRESOLVED')
    if any(p['end'] > end for d in financial for p in d['economic_periods']):
        denials.append('LATEST_FINANCIAL_PERIOD_NOT_COMPATIBLE_NO_OLDER_SUBSTITUTION')
    return {'status': 'BLOCKED' if denials else 'PASS', 'period_end': end,
        'source_accessions': sorted({d['accession'] for d in current}),
        'required_role': required_role, 'denial_reasons': sorted(set(denials))}
