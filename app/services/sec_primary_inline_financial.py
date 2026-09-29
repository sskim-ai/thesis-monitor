"""Exact standard IFRS inline occurrences on the opt-in formal FPI route."""
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'sec-primary-inline-financial-v1'
INSTANCE = 'http://www.xbrl.org/2003/instance'
INLINE = {'http://www.xbrl.org/2013/inlineXBRL', 'http://www.xbrl.org/2008/inlineXBRL'}
REGISTRY = {
    'Revenue': ('revenue', 'statement_revenue'),
    'RevenueFromContractsWithCustomers': ('revenue', 'statement_revenue'),
    'ProfitLossFromOperatingActivities': ('operating_income', 'statement_operating_income'),
    'ProfitLoss': ('net_income', 'statement_net_income'),
}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def qname(name, namespaces):
    prefix, sep, local = str(name).partition(':')
    return (namespaces.get(prefix, ''), local) if sep else (namespaces.get('', ''), prefix)


class InlineDocument(HTMLParser):
    """Keep only context/unit/fact subtrees; large visual tables are not retained."""
    def __init__(self):
        super().__init__()
        self.stack, self.captures, self.text = [], [], []
        self.ordinal = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        ns = dict(self.stack[-1]['ns']) if self.stack else {}
        ns.update({k[6:]: v for k, v in attrs.items() if k.startswith('xmlns:')})
        if 'xmlns' in attrs:
            ns[''] = attrs['xmlns']
        expanded = qname(tag, ns)
        root = expanded in {(INSTANCE, 'context'), (INSTANCE, 'unit')} or (
            expanded[0] in INLINE and expanded[1] == 'nonfraction')
        capturing = root or bool(self.stack and self.stack[-1]['capturing'])
        node = dict(tag=tag, name=expanded, attrs=attrs, ns=ns, text=[], children=[],
                    capturing=capturing, ordinal=self.ordinal)
        self.ordinal += 1
        if self.stack and self.stack[-1]['capturing']:
            self.stack[-1]['children'].append(node)
        if root:
            self.captures.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, value):
        self.text.append(value)
        for node in reversed(self.stack):
            if not node['capturing']:
                break
            node['text'].append(value)


def descendants(node):
    yield node
    for child in node['children']:
        yield from descendants(child)


def content(node):
    return ''.join(node['text']).strip()


def context_value(node):
    children = list(descendants(node))
    def one(local):
        hits = [n for n in children if n['name'] == (INSTANCE, local)]
        if len(hits) != 1:
            raise ValueError('INLINE_CONTEXT_' + local.upper())
        return hits[0]
    identifier = one('identifier')
    if identifier['attrs'].get('scheme') not in {'http://www.sec.gov/CIK', 'https://www.sec.gov/CIK'}:
        raise ValueError('INLINE_ENTITY_SCHEME')
    issuer = content(identifier)
    if not re.fullmatch(r'\d{1,10}', issuer):
        raise ValueError('INLINE_ENTITY_IDENTIFIER')
    if any(n['name'][1] in {'segment', 'scenario', 'explicitmember', 'typedmember'} for n in children):
        raise ValueError('INLINE_DIMENSIONED_CONTEXT')
    start, end = (date.fromisoformat(content(one(k))) for k in ('startdate', 'enddate'))
    if not start < end:
        raise ValueError('INLINE_PERIOD_INVALID')
    months = (end.year - start.year) * 12 + end.month - start.month + 1
    if start.day != 1 or end.day != monthrange(end.year, end.month)[1] or months not in {3, 6, 9, 12}:
        raise ValueError('INLINE_PERIOD_ROLE_UNRESOLVED')
    role = {3: 'single-quarter', 6: 'half-year', 9: 'nine-month', 12: 'annual'}[months]
    return dict(issuer_cik=issuer.zfill(10), period_start=start.isoformat(), period_end=end.isoformat(),
        duration_days=(end-start).days+1, period_scope=role,
        period_type=f'Q{(end.month-1)//3+1}' if months == 3 else role, is_cumulative=months != 3,
        period_resolution_method='EXACT_INLINE_XBRL_CONTEXT')


def extract(raw, *, issuer_cik, filing, source_url):
    parser = InlineDocument()
    parser.feed(raw.decode('utf-8', errors='replace'))
    text = re.sub(r'\s+', ' ', ' '.join(parser.text))
    statement = re.search(r'consolidated statements? of (?:profit or loss|income|operations|comprehensive income)', text, re.I)
    formal = filing['form'].split('/')[0] in {'20-F', '40-F', '6-K'}
    qualified = bool(formal and statement)
    contexts, units = {}, {}
    for node in parser.captures:
        target = contexts if node['name'] == (INSTANCE, 'context') else units if node['name'] == (INSTANCE, 'unit') else None
        if target is not None:
            target.setdefault(node['attrs'].get('id'), []).append(node)
    rows, denials = [], []
    for node in parser.captures:
        if node['name'][0] not in INLINE:
            continue
        attrs = node['attrs']
        namespace, concept = qname(attrs.get('name'), node['ns'])
        if concept not in REGISTRY or not re.fullmatch(r'https?://xbrl\.ifrs\.org/taxonomy/\d{4}-\d{2}-\d{2}/ifrs-full', namespace):
            continue
        field, semantic = REGISTRY[concept]
        try:
            ctx = contexts.get(attrs.get('contextref'), [])
            unit = units.get(attrs.get('unitref'), [])
            if len(ctx) != 1 or len(unit) != 1:
                raise ValueError('INLINE_CONTEXT_OR_UNIT_AMBIGUOUS')
            period = context_value(ctx[0])
            if period['issuer_cik'] != str(issuer_cik).zfill(10):
                raise ValueError('INLINE_ISSUER_MISMATCH')
            measures = [n for n in descendants(unit[0]) if n['name'] == (INSTANCE, 'measure')]
            if len(measures) != 1 or any(n['name'] == (INSTANCE, 'divide') for n in descendants(unit[0])):
                raise ValueError('INLINE_UNIT_UNSUPPORTED')
            unit_ns, currency = qname(content(measures[0]), measures[0]['ns'])
            if unit_ns != 'http://www.xbrl.org/2003/iso4217' or not re.fullmatch('[A-Z]{3}', currency):
                raise ValueError('INLINE_CURRENCY_UNRESOLVED')
            if (not qualified or attrs.get('continuedat') or any(k.endswith(':nil') and v != 'false' for k, v in attrs.items())):
                raise ValueError('INLINE_PURPOSE_OR_VALUE_UNRESOLVED')
            fmt_ns, fmt = qname(attrs.get('format', ''), node['ns'])
            if attrs.get('format') and (fmt != 'num-dot-decimal' or not re.fullmatch(
                    r'https?://www\.xbrl\.org/inlineXBRL/transformation/\d{4}-\d{2}-\d{2}', fmt_ns)):
                raise ValueError('INLINE_TRANSFORM_UNSUPPORTED')
            scale = int(attrs.get('scale', '0'))
            if str(scale) != attrs.get('scale', '0') or not -12 <= scale <= 12 or attrs.get('sign', '') not in {'', '-'}:
                raise ValueError('INLINE_SCALE_OR_SIGN_INVALID')
            literal = content(node)
            if not re.fullmatch(r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', literal):
                raise ValueError('INLINE_NUMERIC_LITERAL_UNSUPPORTED')
            amount = Decimal(literal.replace(',', '')) * (-1 if attrs.get('sign') == '-' else 1)
            value = amount * Decimal(10) ** scale
            if not value.is_finite():
                raise ValueError('INLINE_NONFINITE')
            source_cell = dict(inline_id=attrs.get('id'), ordinal=node['ordinal'], concept=attrs['name'],
                concept_namespace=namespace, context_id=attrs['contextref'], unit_id=attrs['unitref'],
                literal=literal, scale=scale, sign=attrs.get('sign', ''), format=attrs.get('format'),
                context=period, currency=currency)
            payload = sha256_bytes(raw)
            row = dict(contract=CONTRACT, provider='sec_foreign_filing',
                accession=filing['accessionNumber'], document_type=filing['form'], filing_date=filing['filingDate'],
                source_url=source_url, field=field, semantic=semantic, statement_basis='consolidated',
                basis_evidence=statement[0], currency=currency, unit_scale=10 ** scale,
                unit_evidence=currency, reported_value=float(amount), value=float(value),
                source_payload_sha256=payload, source_cell=source_cell,
                source_row_identity=digest(dict(payload=payload, cell=source_cell)), parse_method=CONTRACT,
                standard_concept='ifrs-full:' + concept, **period)
            row['occurrence_id'] = digest(row)
            rows.append(row)
        except (ValueError, TypeError, InvalidOperation) as exc:
            denials.append(dict(field=field, context_id=attrs.get('contextref'), inline_id=attrs.get('id'),
                reason=str(exc) if isinstance(exc, ValueError) and str(exc).startswith('INLINE_') else 'INLINE_PARSE_ERROR'))
    # Collapse presentation duplicates only within the exact source context.
    groups = {}
    for row in rows:
        key = (row['source_cell']['context_id'], *(
            row[k] for k in ('standard_concept', 'period_start', 'period_end', 'currency', 'unit_scale', 'value')))
        groups.setdefault(key, []).append(row)
    deduped = [min(v, key=lambda r: r['source_cell']['ordinal']) for v in groups.values()]
    return dict(contract=CONTRACT, status='RAN', source_payload_sha256=sha256_bytes(raw),
        qualified_document_purpose=qualified, occurrences=deduped, denials=denials,
        duplicate_presentation_count=len(rows)-len(deduped))


def errors(row, cutoff):
    failures = []
    try:
        if row['contract'] != CONTRACT or row['parse_method'] != CONTRACT or row['provider'] != 'sec_foreign_filing':
            failures.append('inline_owner_missing')
        if row['occurrence_id'] != digest({k: v for k, v in row.items() if k != 'occurrence_id'}):
            failures.append('inline_identity_mismatch')
        cell = row['source_cell']
        if row['source_row_identity'] != digest(dict(payload=row['source_payload_sha256'], cell=cell)):
            failures.append('inline_source_identity_mismatch')
        if any(row[k] != v for k, v in cell['context'].items()):
            failures.append('inline_context_mismatch')
        if (REGISTRY[row['standard_concept'].split(':')[1]] != (row['field'], row['semantic'])
                or row['statement_basis'] != 'consolidated' or row['currency'] != cell['currency']
                or row['unit_scale'] != 10 ** cell['scale']
                or row['value'] != float(Decimal(str(row['reported_value'])) * Decimal(10) ** cell['scale'])):
            failures.append('inline_field_unit_mismatch')
        start, end, filed = (date.fromisoformat(row[k]) for k in ('period_start', 'period_end', 'filing_date'))
        url = urlsplit(row['source_url'])
        base = f"/Archives/edgar/data/{int(row['issuer_cik'])}/{row['accession'].replace('-', '')}/"
        if (not start < end <= filed <= cutoff or url.scheme != 'https' or url.netloc != 'www.sec.gov'
                or not url.path.startswith(base) or url.query or url.fragment):
            failures.append('inline_document_period_binding')
    except (KeyError, ValueError, TypeError, IndexError, InvalidOperation):
        failures.append('inline_lineage_incomplete')
    return sorted(set(failures))


def merge_occurrences(inline, table, cutoff):
    """Invalid visual note cells cannot replace exact facts; valid conflicts deny."""
    from app.services.sec_foreign_comparison_service import occurrence_errors
    result, conflicts = list(inline), []
    keys = ('field', 'period_start', 'period_end', 'currency', 'statement_basis')
    for row in table:
        peers = [i for i in inline if all(i.get(k) == row.get(k) for k in keys)]
        if peers:
            if not occurrence_errors(row, cutoff) and any(i['value'] != row['value'] for i in peers):
                conflicts.append(dict(field=row['field'], reason='INLINE_TABLE_CONFLICT',
                    occurrence_ids=[row['occurrence_id'], *[i['occurrence_id'] for i in peers]]))
                result.append(row)
        elif not inline or row.get('period_start'):
            result.append(row)
    return result, conflicts


def comparable_calendar_period(a, b):
    """Exact reported calendar intervals, including leap-day years, not +/- days."""
    try:
        aa, ae, ba, be = (date.fromisoformat(x) for x in
            (a['period_start'], a['period_end'], b['period_start'], b['period_end']))
        return (a['contract'] == b['contract'] == CONTRACT and a['period_scope'] == b['period_scope']
            and aa.year == ba.year + 1 and ae.year == be.year + 1
            and (aa.month, aa.day) == (ba.month, ba.day)
            and ae.month == be.month
            and ae.day == monthrange(ae.year, ae.month)[1] and be.day == monthrange(be.year, be.month)[1])
    except (KeyError, ValueError, TypeError):
        return False
