"""Compact observations from already selected official filings. No acquisition or decision rights."""
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from math import isfinite
import re

from app.services.sec_primary_inline_financial import (
    INLINE, INSTANCE, InlineDocument, content, descendants, monetary_value, qname,
)
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


# Select whole sentences about operating drivers. Rankings are by economic topic,
# shared across issuers. Keep quotations verbatim apart from layout whitespace.
_TOPICS = {
    'mix': r'\b(?:accounted for|represented|contributed)\b.{0,40}% of .{0,40}(?:revenue|sales)',
    'operations': r'\b(?:revenues?|sales|profit(?:ability)?|margin|pricing|utilization|volumes?|shipments?)\b',
    'investment': r'\b(?:capacit(?:y|ies)|capital expenditures?|production|manufacturing|facilit(?:y|ies)|construction)\b',
    'customers': r'\b(?:contracts?|agreements?|customer commitments?|deliver(?:ed|ies)|commercialization)\b',
    'cash': r'\b(?:cash flows?|working capital|capital returns?|repurchases?|dividends?)\b',
}
_TOPIC_WORDS = {k: re.compile(v, re.I) for k, v in _TOPICS.items()}
_EXPLANATION = re.compile(r'\b(?:driven by|due (?:primarily )?to|attributable to|resulted from|reflect(?:ed|ing)|as a result of)\b', re.I)
_CHANGE = re.compile(r'\b(?:increas\w*|decreas\w*|grew|declin\w*|rose|fell|expand\w*|improv\w*|deliver\w*|completed|achieved|executed|entered into|commenced|began|generated|accounted for)\b', re.I)
_PLAN = re.compile(r'\b(?:expect\w*|anticipat\w*|plan(?:s|ned)?|intend\w*|forecast\w*|target(?:s|ed)?|aim(?:s)?|estimat\w*|projected|scheduled|outlook|to be recognized|to be achieved|set to|goals?|committed to|may|might|could|would|will|believ\w*)\b', re.I)
_SKIP = re.compile(r'\b(?:forward.looking statements?|safe harbor|table of contents|see note|refer to note|incorporated by reference|fair value hierarchy|deferred tax assets?|stock price|share price|price target|market price of|trading price|per ADS|per ADR)\b', re.I)
_SENTENCE = re.compile(r'(?<=[.!?])\s+(?=[A-Z(•])')
_FUTURE_ALLOCATION = re.compile(r'\b(?:to be made|authorized .{0,110}repurchases?|authorization to repurchase)\b', re.I)
_ACCOUNTING_BOILERPLATE = re.compile(r'\b(?:which were as follows|classified as at FVTOCI|objective is achieved by)\b', re.I)
_METRICS = {
    'RevenueFromContractWithCustomerExcludingAssessedTax': 'segment_revenue',
    'Revenues': 'segment_revenue', 'Revenue': 'segment_revenue',
    'OperatingIncomeLoss': 'segment_operating_income',
}
_MAX_EXCERPTS = 6
_MAX_FILING_AMOUNTS = 8

# Exact primary-statement concepts. The order retains issuer-specific operating
# lines ahead of the more common profitability and working-capital balances.
_DART_OPERATING_CONCEPTS = {
    'insurance_service_result': ('IS', ('ifrs-full_insuranceserviceresult',)),
    'investment_result': ('IS', ('dart_investmentincomeexpenses',)),
    'other_operating_result': ('IS', ('ifrs-full_otheroperatingincomeexpense',)),
    'investment_income': ('IS', ('ifrs-full_investmentincome',)),
    'research_development_expense': ('IS', ('ifrs-full_researchanddevelopmentexpense',)),
    'current_contract_assets': ('BS', ('ifrs-full_currentcontractassets',)),
    'current_contract_liabilities': ('BS', ('ifrs-full_currentcontractliabilities',)),
    'gross_profit': ('IS', ('ifrs-full_grossprofit',)),
    'current_trade_receivables': ('BS', ('ifrs-full_currenttradereceivables',)),
    'ppe_carrying_amount': ('BS', ('ifrs-full_propertyplantandequipment',
                                  'ifrs-full_propertyplantandequipmentincludingrightofuseassets')),
}


class _FilingDocument(InlineDocument):
    """Reuse the inline context/unit parser and keep visible prose at block boundaries."""
    def __init__(self):
        super().__init__()
        self.paragraph = []
        self.excerpts = {}
        self.pending_layout_line = None

    def flush(self):
        text = ' '.join(''.join(self.paragraph).split()).lstrip('• ').strip()
        self.paragraph.clear()
        if not text:
            return
        block = self.stack[-1] if self.stack else {}
        style = block.get('attrs', {}).get('style', '').lower()
        layout = (self.stack[-2]['ordinal'] if len(self.stack) >= 2 and block['tag'] == 'div'
                  and 'position:' in style and 'top:' in style else None)
        if layout is not None and self.pending_layout_line and self.pending_layout_line[0] == layout:
            text = self.pending_layout_line[1] + ' ' + text
        self.pending_layout_line = None
        sentences = _SENTENCE.split(text)
        if layout is not None and not sentences[-1].endswith(('.', '!', '?')):
            tail = sentences.pop()
            if len(tail) <= 520:
                self.pending_layout_line = (layout, tail)
        for sentence in sentences:
            if (not 48 <= len(sentence) <= 520 or not sentence.endswith(('.', '!'))
                    or '\ufffd' in sentence or not sentence[0].isupper() or _SKIP.search(sentence)
                    or _ACCOUNTING_BOILERPLATE.search(sentence)
                    or re.search(r'\b(?:[A-Z]\.){2,}$|\b(?:Inc|Corp|Ltd)\.$', sentence)):
                continue
            topics = [key for key, regex in _TOPIC_WORDS.items() if regex.search(sentence)]
            if not topics or not (_CHANGE.search(sentence) or _EXPLANATION.search(sentence)):
                continue
            outlook = bool(_PLAN.search(sentence) or _FUTURE_ALLOCATION.search(sentence))
            if outlook:
                kind = 'MANAGEMENT_OUTLOOK_OR_ESTIMATE'
            elif _EXPLANATION.search(sentence):
                kind = 'MANAGEMENT_EXPLANATION'
            elif re.search(r'\b(?:increased|decreased|grew|declined|rose|fell|delivered|completed|accounted for|'
                           r'achieved|entered into|executed|began|commenced|generated|represented)\b', sentence, re.I):
                kind = 'COMPANY_REPORTED_OBSERVATION'
            else:
                kind = 'MANAGEMENT_EXPLANATION'
            score = (3 * bool(_EXPLANATION.search(sentence)) + 2 * bool(_CHANGE.search(sentence))
                     + bool(re.search(r'\d', sentence)) + len(topics)
                     + 2 * bool(re.search(r'\b(?:demand|segment|shipments|billable|pricing|customer engagement)\b', sentence, re.I))
                     + 3 * ('mix' in topics and bool(re.search(r'\b(?:up|down) from\b', sentence, re.I)))
                     - 3 * outlook)
            self.excerpts.setdefault(sentence, (score, topics, kind, self.ordinal))

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'div', 'td', 'th', 'li'):
            self.flush()
        parent_hidden = bool(self.stack and self.stack[-1].get('hide_prose'))
        if tag == 'br' and not parent_hidden:
            self.paragraph.append(' ')
        super().handle_starttag(tag, attrs)
        if self.stack and self.stack[-1]['tag'] == tag:
            node = self.stack[-1]
            style = node['attrs'].get('style') or ''
            node['hide_prose'] = (parent_hidden or tag in ('head', 'script', 'style', 'ix:header', 'ix:hidden')
                                  or 'hidden' in node['attrs'] or bool(re.search(r'display\s*:\s*none', style, re.I)))

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'td', 'th', 'li'):
            self.flush()
        super().handle_endtag(tag)

    def handle_data(self, value):
        if not (self.stack and self.stack[-1].get('hide_prose')):
            self.paragraph.append(value)
        # Unlike the statement parser we do not need a second full-document text copy.
        for node in reversed(self.stack):
            if not node['capturing']:
                break
            node['text'].append(value)


def _segment_period(ctx, issuer, report_end):
    nodes = list(descendants(ctx))
    def one(local):
        hits = [n for n in nodes if n['name'] == (INSTANCE, local)]
        return hits[0] if len(hits) == 1 else None
    entity, start, end = (one(k) for k in ('identifier', 'startdate', 'enddate'))
    if (entity is None or start is None or end is None or content(end) != report_end
            or entity['attrs'].get('scheme') not in ('http://www.sec.gov/CIK', 'https://www.sec.gov/CIK')
            or content(entity).zfill(10) != issuer.zfill(10)
            or any(n['name'][1] in ('typedmember', 'scenario') for n in nodes)):
        return None
    dimensions = []
    for n in nodes:
        if n['name'] != ('http://xbrl.org/2006/xbrldi', 'explicitmember'):
            continue
        axis = n['attrs'].get('dimension', '')
        member = content(n)
        axis_ns, local = qname(axis, n['ns'])
        standard = re.fullmatch(r'https?://fasb\.org/(us-gaap|srt)/\d{4}(?:-\d{2}-\d{2})?', axis_ns)
        member_ns, _ = qname(member, n['ns'])
        if not standard or not member_ns:
            return None
        if (standard[1], local) == ('srt', 'ConsolidationItemsAxis') and member == 'us-gaap:OperatingSegmentsMember':
            continue
        if (standard[1], local) not in {('us-gaap', 'StatementBusinessSegmentsAxis'), ('srt', 'ProductOrServiceAxis')}:
            return None
        dimensions.append((axis, member))
    if not dimensions or len({a for a, _ in dimensions}) != len(dimensions):
        return None
    if not date.fromisoformat(content(start)) < date.fromisoformat(report_end):
        return None
    return content(start), tuple(sorted(dimensions))


def _segment_fields(parser, plan, filing, raw_sha, filename):
    from app.services.bounded_financial_projection import field_record
    contexts, units, groups = defaultdict(list), defaultdict(list), defaultdict(list)
    for n in parser.captures:
        if n['name'] == (INSTANCE, 'context'):
            contexts[n['attrs'].get('id')].append(n)
        elif n['name'] == (INSTANCE, 'unit'):
            units[n['attrs'].get('id')].append(n)
    for n in parser.captures:
        a = n['attrs']
        ns, concept = qname(a.get('name', ''), n['ns'])
        if (n['name'][0] not in INLINE or concept not in _METRICS
                or not re.fullmatch(r'https?://fasb.org/us-gaap/\d{4}(?:-\d{2}-\d{2})?', ns)):
            continue
        ctx, unit = contexts[a.get('contextref')], units[a.get('unitref')]
        if len(ctx) != 1 or len(unit) != 1:
            continue
        try:
            period = _segment_period(ctx[0], plan['issuer'], filing['reportDate'])
            if not period:
                continue
            currency, literal, scale, _, value = monetary_value(n, unit[0])
        except (ValueError, InvalidOperation):
            continue
        start, dims = period
        key = (_METRICS[concept], start, dims, currency)
        groups[key].append((value, n, literal, scale))
    fields = []
    for (metric, start, dims, currency), matches in groups.items():
        if len({m[0] for m in matches}) != 1:
            continue
        value, node, literal, scale = matches[0]
        a = node['attrs']
        lineage = dict(source_document_id=filing['accessionNumber'], source_document_type=filing['form'],
            document=filename, filing_date=filing['filingDate'], occurrence_id=a.get('id') or str(node['ordinal']),
            semantic=a['name'], context_id=a['contextref'], dimensions=dict(dims), period_start=start,
            period_end=filing['reportDate'], period_role='reported_duration', period_kind='duration',
            statement_basis='reported_segment_or_product', currency=currency, unit=currency, unit_scale=10 ** scale,
            source_literal=literal, source_sign=a.get('sign', ''))
        amount = int(value) if value == value.to_integral_value() else float(value)
        row = field_record(plan, metric=metric, value=amount, lineage=lineage,
                           quality=[], raw_sha=raw_sha, role='current')
        if row['context_eligible']:
            fields.append(row)
    # Prefer the most recent discrete duration in this filing. Never aggregate
    # products, segments, comparative periods or currencies.
    fields.sort(key=lambda r: (r['period_start'], -len(r['dimensions'])), reverse=True)
    unique = []
    seen = defaultdict(list)
    for row in fields:
        key = (row['metric'], row['period_start'], row['period_end'], row['currency'], row['value'])
        dims = set(row['dimensions'].items())
        # The same amount is sometimes tagged both at product level and at its
        # product/segment intersection. Keep the broader occurrence only once.
        if not any(previous <= dims for previous in seen[key]):
            unique.append(row)
            seen[key].append(dims)
    return unique


def extract_filing(plan, filing, filename, raw):
    """Project one previously acquired document. This helper grants no source capability."""
    parser = _FilingDocument()
    try:
        parser.feed(raw.decode('utf-8-sig', errors='replace'))
        parser.close()
    except (AssertionError, ValueError):
        # HTMLParser can reject malformed markup in an optional filing attachment.
        return [], []
    parser.flush()
    sha = sha256_bytes(raw)
    texts = []
    for sentence, (score, topics, kind, ordinal) in parser.excerpts.items():
        row = dict(ticker=plan['ticker'], security_id=plan['security']['canonical_security_id'],
            issuer_id=plan['issuer'], source_document_id=filing['accessionNumber'], document=filename,
            document_type=filing['form'], filing_date=filing['filingDate'], report_end=filing['reportDate'],
            raw_artifact_sha256=sha, occurrence=ordinal, classification=kind, excerpt=sentence)
        texts.append((score, topics, row))
    return texts, _segment_fields(parser, plan, filing, sha, filename)


def dart_operating_observations(plan, filing, rows, raw_sha):
    from app.services.bounded_financial_projection import field_record
    from app.services.kr_financial_lineage_service import opendart_field_lineage
    from app.services.opendart_financial_recovery_service import FieldSpec, select_basis_occurrence

    # The lineage owner assigns calendar-quarter bounds. A filing ending in a
    # different fiscal month cannot substantiate those dates.
    period = re.search(r'\((\d{4})[./-](\d{1,2})\)', filing.get('report_name', '').replace(' ', ''))
    end_month = {'11013': 3, '11012': 6, '11014': 9, '11011': 12}.get(filing['report_code'])
    if not period or (int(period[1]), int(period[2])) != (filing['business_year'], end_month):
        return []
    totals = [r for r in rows if r.get('account_detail') in (None, '', '-')]
    current, comparative = [], []
    for metric, (statement, concepts) in _DART_OPERATING_CONCEPTS.items():
        statements = ('IS', 'CIS') if statement == 'IS' else ('BS',)
        columns = ['thstrm_amount']
        if statement == 'IS':
            columns.append('frmtrm_amount' if filing['report_code'] == '11011' else 'frmtrm_q_amount')
        current_identity = None
        for column in columns:
            spec = FieldSpec(metric, concepts, (), statements, source_column=column)
            selected = select_basis_occurrence(totals, spec, basis='CFS')
            if selected.status != 'selected':
                break
            row = selected.row
            identity = (row['sj_div'], row['account_id'], row.get('account_nm'), row.get('ord'))
            if current_identity is not None and identity != current_identity:
                break
            lineage = opendart_field_lineage(row, logical_field=metric, report_code=filing['report_code'],
                source_column=column, selected=True, requested_fs_div='CFS')
            literal = str(row[column]).strip()
            if (not lineage['lineage_verified'] or not isfinite(lineage['amount'])
                    or not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)', literal)):
                break
            role = 'current' if column == 'thstrm_amount' else 'prior'
            witness = dict(source_document_id=filing['receipt_no'], source_document_type=filing['report_code'],
                filing_date=filing['receipt_date'], document=filing['report_name'], semantic=row['account_id'],
                account_name=row.get('account_nm'), source_column=column, source_literal=literal,
                occurrence_id=lineage['source_row_identity'], period_start=lineage['amount_period_start'],
                period_end=lineage['amount_period_end'], period_role=lineage['amount_period_type'],
                statement_basis=lineage['statement_basis'], currency=lineage['currency'], unit='KRW', unit_scale=1)
            field = field_record(plan, metric=metric, value=int(literal.replace(',', '')), lineage=witness,
                                 quality=[], raw_sha=raw_sha, role=role, allow_instant=True)
            if not field['context_eligible']:
                break
            (current if role == 'current' else comparative).append(field)
            current_identity = identity
    # Leave space for up to two same-statement comparative income amounts.
    keep = _MAX_FILING_AMOUNTS - min(2, len(comparative))
    numeric = current[:keep]
    kept_metrics = {r['metric'] for r in numeric}
    remaining = (r for r in comparative if r['metric'] in kept_metrics)
    numeric += list(remaining)[:_MAX_FILING_AMOUNTS - len(numeric)]
    return _registered_observations(numeric, 'reported_operating', 'REPORTED_OPERATING_CONTEXT_ONLY')


def dart_document_observations(plan, filing, parsed, provenance):
    """Bind selected original document spans to the existing economic-context path."""
    from app.services.bounded_financial_projection import field_record
    from app.services.numeric_semantic_registry import build_numeric_registry, resolve_numeric_semantic

    if not parsed or not parsed.get('period_end'):
        return []
    if (plan['provider'] != 'opendart' or plan['market'] != 'kr'
            or filing.get('role') != 'current' or filing['corp_code'] != plan['issuer']
            or filing['ticker'] != plan['ticker']
            or any(provenance[key] != filing[key] for key in ('corp_code','ticker','receipt_no','report_code'))
            or provenance['filing_date'] != filing['receipt_date']
            or not parsed['period_end'] <= filing['receipt_date'] <= plan['cutoff'][:10]):
        return []
    report_month = re.search(r'\((\d{4})[./-](\d{1,2})\)', filing['report_name'].replace(' ', ''))
    if (not report_month or (int(report_month[1]), int(report_month[2])) !=
            (int(parsed['period_end'][:4]), int(parsed['period_end'][5:7]))):
        return []
    common = dict(source_document_id=filing['receipt_no'], source_document_type=filing['report_code'],
                  document=filing['report_name'], filing_date=filing['receipt_date'],
                  report_start=parsed['period_start'], report_end=parsed['period_end'],
                  xml_name=provenance['xml_name'], xml_sha256=provenance['xml_sha256'],
                  retrieved_at=provenance['retrieved_at'])
    raw_sha = provenance['zip_sha256']
    result = []
    for text in parsed['texts']:
        observation = dict(**common, source_provider='opendart', ticker=plan['ticker'],
            issuer_id=plan['issuer'], security_id=plan['security']['canonical_security_id'],
            raw_artifact_sha256=raw_sha, section=text['section'], line=text['line'],
            statement_basis=text['scope'], classification=text['classification'], excerpt=text['excerpt'])
        result.append(dict(ref_id=digest(observation), as_of=filing['receipt_date'],
                           kind='DART_BUSINESS_EXCERPT_CONTEXT_ONLY', observation=observation))
    for cell in parsed['numbers']:
        metric, unit = cell['metric'], cell['unit']
        spec, _ = resolve_numeric_semantic('dart_business_metric', 'fields.'+metric, {'unit':unit})
        if spec is None:
            continue
        amount = Decimal(str(cell['value'])) * cell['unit_scale']
        value = int(amount) if amount == amount.to_integral_value() else float(amount)
        anchor = dict(section=cell['section'], line=cell['line'], subject=cell['subject'],
                      row_header=cell['row_header'], column_header=cell['column_header'])
        monetary = unit in ('KRW', 'USD')
        lineage = dict(**common, **anchor, occurrence_id=digest([provenance['xml_sha256'],anchor,metric]),
            classification=cell['classification'], semantic=metric, statement_basis=cell['scope'],
            period_start=cell['period_start'], period_end=cell['period_end'], period_role=cell['period_role'],
            source_literal=cell['source_text'], source_unit=cell['unit_label'], unit_scale=cell['unit_scale'],
            currency=unit if monetary else None, unit=unit, notes=cell.get('notes', []))
        role = 'current' if cell['period_end'] == parsed['period_end'] else 'historical'
        record = field_record(plan, metric=metric, value=value, lineage=lineage, quality=[],
                              raw_sha=raw_sha, role=role, allow_instant=True, monetary=monetary)
        if not record['context_eligible'] or cell['period_end'] > parsed['period_end']:
            continue
        ref = record['normalized_hash']
        entry, = build_numeric_registry([dict(fact_type='dart_business_metric', fact_id=ref,
            as_of_date=cell['period_end'], fields={metric:value,'unit':unit})])
        if entry['registered'] and entry['prose_allowed'] and entry['value'] == value and entry['unit'] == unit:
            result.append(dict(ref_id=ref, as_of=record['period_end'], kind='DART_BUSINESS_METRIC_CONTEXT_ONLY',
                               observation=record, numeric_registry_entry=entry))
    return result


def select_observations(texts, fields):
    """Bound model input and retain distinct documents, operating topics and segment metrics."""
    ranked = sorted(texts, key=lambda t: (t[2]['report_end'], t[0]), reverse=True)
    chosen = []
    used = set()
    def take(candidates):
        for _, _, row in candidates:
            if row['excerpt'] not in used and len(chosen) < _MAX_EXCERPTS:
                chosen.append(row)
                used.add(row['excerpt'])
                return
    for topic in ('operations', 'mix', 'customers', 'investment', 'cash'):
        take(r for r in ranked if topic in r[1])
    for item in sorted(ranked, key=lambda t: t[0], reverse=True):
        take([item])
        if len(chosen) == _MAX_EXCERPTS:
            break
    # Round-robin across metric and dimension families, so large segment catalogs
    # cannot crowd out product revenue or operating income.
    families = defaultdict(list)
    for row in fields:
        families[(row['metric'], tuple(sorted(row['dimensions'])))].append(row)
    numeric = []
    while families and len(numeric) < _MAX_FILING_AMOUNTS:
        for key in list(families):
            numeric.append(families[key].pop(0))
            if not families[key]:
                del families[key]
            if len(numeric) == _MAX_FILING_AMOUNTS:
                break
    return [dict(ref_id=digest(r), as_of=r['filing_date'], kind='FILING_EXCERPT_CONTEXT_ONLY', observation=r)
            for r in chosen] + _registered_observations(numeric, 'reported_segment', 'REPORTED_SEGMENT_CONTEXT_ONLY')


def _registered_observations(numeric, fact_type, kind):
    from app.services.numeric_semantic_registry import build_numeric_registry
    registered = []
    for row in numeric:
        fact = dict(fact_id=row['normalized_hash'], fact_type=fact_type,
            as_of_date=row['period_end'], fields={row['metric']: row['value'], 'currency': row['currency']})
        entry, = build_numeric_registry([fact])
        if entry['registered'] and entry['unit'] == row['currency']:
            registered.append(dict(ref_id=row['normalized_hash'], as_of=row['period_end'],
                kind=kind, observation=row, numeric_registry_entry=entry))
    return registered
