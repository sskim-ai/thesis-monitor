"""Compact observations from already selected official filings. No acquisition or decision rights."""
from collections import defaultdict
from datetime import date
from decimal import InvalidOperation
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
_MAX_SEGMENTS = 8


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
    while families and len(numeric) < _MAX_SEGMENTS:
        for key in list(families):
            numeric.append(families[key].pop(0))
            if not families[key]:
                del families[key]
            if len(numeric) == _MAX_SEGMENTS:
                break
    from app.services.numeric_semantic_registry import build_numeric_registry
    registered = []
    for row in numeric:
        fact = dict(fact_id=row['normalized_hash'], fact_type='reported_segment',
            as_of_date=row['period_end'], fields={row['metric']: row['value'], 'currency': row['currency']})
        entry, = build_numeric_registry([fact])
        if entry['registered'] and entry['unit'] == row['currency']:
            registered.append(dict(ref_id=row['normalized_hash'], as_of=row['period_end'],
                kind='REPORTED_SEGMENT_CONTEXT_ONLY', observation=row, numeric_registry_entry=entry))
    return [dict(ref_id=digest(r), as_of=r['filing_date'], kind='FILING_EXCERPT_CONTEXT_ONLY', observation=r)
            for r in chosen] + registered
