"""Opt-in calendar-quarter derivation from one immutable statement document.

This resolves period lineage only. Acquisition, filing/issuer identity and all
financial quality/use owners remain separate mandatory gates.
"""
from calendar import monthrange
from datetime import date, datetime
from hashlib import sha256
import re

from app.services.sec_foreign_statement_boundary_service import Document, text

POLICY = 'SOURCE_BOUND_CALENDAR_QUARTER_DERIVATION_V1'
METHOD = 'source_bound_calendar_quarter_derivation_v1'
ORDINAL = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4}
ENDED = re.compile(r'\b(first|second|third|fourth) quarter ended '
                   r'([A-Za-z]+) (\d{1,2}),? (20\d{2})\b', re.I)
CAPTION = re.compile(r'\b(20\d{2}) (first|second|third|fourth) quarter consolidated results\s*:', re.I)
LABEL = re.compile(r'^([1-4])Q(\d{2}|20\d{2})(?: Amount)?(?: [a-z])?$', re.I)


def source_record(raw, *, issuer_cik, accession, document_type, filing_date, source_url):
    """The caller must obtain raw/identity from the original verified receipt."""
    try:
        html = raw.decode('utf-8')
    except UnicodeDecodeError:
        return {}
    return {sha256(raw).hexdigest(): dict(raw_utf8=html, issuer_cik=str(issuer_cik).zfill(10),
        accession=accession, document_type=document_type, filing_date=filing_date, source_url=source_url)}


class QuarterDocument:
    def __init__(self, html):
        self.document = Document()
        self.document.feed(html)
        self.nodes = {}
        def visit(node):
            self.nodes[node['path']] = node
            for child in node['children']:
                visit(child)
        visit(self.document.root)
        self.premises = []
        for node in self.nodes.values():
            if node['tag'] not in {'p', 'div', 'section', 'article'}:
                continue
            value = text(node)
            matches = list(ENDED.finditer(value))
            if not matches or any(ENDED.search(text(c)) for c in node['children'] if c['tag'] in {'p','div','section','article'}):
                continue
            ancestors, parent = [], node
            while parent:
                ancestors.append(parent['tag'])
                parent = parent['parent']
            if set(ancestors) & {'table','head','script','style','aside','footer'}:
                continue
            # A forecast or a footnote cannot provide the reporting premise.
            if (not re.search(r'\b(?:announced|reported)\b.*\b(?:revenue|results|income)\b', value, re.I)
                    or re.search(r'\b(?:guidance|forecast|expected|projected|footnote)\b', value, re.I)):
                continue
            for match in matches:
                quarter, month, day, year = match.groups()
                try:
                    end = datetime.strptime(f'{month} {day} {year}', '%B %d %Y').date()
                except ValueError:
                    continue
                q = ORDINAL[quarter.lower()]
                if end.month != q*3 or end.day != monthrange(end.year, end.month)[1]:
                    continue
                self.premises.append(dict(path=node['path'], text=value, quarter=q, end=end))
        visible = text(self.document.root)
        self.contrary_calendar = bool(re.search(r'\b(?:52|53)[ -]week|\b(?:4-4-5|4-5-4|5-4-4)\b', visible, re.I))
        for match in re.finditer(r'\bfiscal year (?:ends?|ended|ending) (?:on )?([A-Za-z]+) (\d{1,2})', visible, re.I):
            if (match[1].lower(), match[2]) != ('december', '31'):
                self.contrary_calendar = True

    def resolve(self, ownership, headers, table_headers):
        if (self.contrary_calendar or ownership['status'] != 'PASS'
                or ownership['statement_basis'] != 'consolidated'):
            return None
        label = LABEL.fullmatch(' '.join(dict.fromkeys(headers)).strip())
        if not label:
            return None
        metadata = [self.nodes[p] for p in ownership['metadata_dom_paths']]
        caption = ' '.join(text(n) for n in metadata)
        captions = list(CAPTION.finditer(caption))
        if len(captions) != 1 or re.search(r'\b(?:guidance|forecast|nine months|year.to.date|ytd)\b', caption, re.I):
            return None
        year, word = captions[0].groups()
        year, quarter = int(year), ORDINAL[word.lower()]
        premises = [p for p in self.premises if p['quarter'] == quarter and p['end'].year == year]
        if len(premises) != 1 or len({(p['quarter'], p['end']) for p in self.premises}) != 1:
            return None
        # Require current and YoY columns in this very statement, not another row.
        labels = []
        for value in table_headers:
            match = LABEL.fullmatch(value)
            if match:
                y = int(match[2]); labels.append((int(match[1]), y+2000 if y < 100 else y))
        if (quarter, year) not in labels or (quarter, year-1) not in labels:
            return None
        q, y = int(label[1]), int(label[2])
        y = y+2000 if y < 100 else y
        if not ((y == year and 1 <= q <= quarter) or (y == year-1 and q == quarter)):
            return None
        start = date(y, q*3-2, 1)
        end = date(y, q*3, monthrange(y, q*3)[1])
        premise = premises[0]
        return dict(period_start=start.isoformat(), period_end=end.isoformat(),
            duration_days=(end-start).days+1, period_scope='single-quarter', period_type=f'Q{q}',
            is_cumulative=False, period_resolution_method=METHOD,
            period_source_proof=dict(policy=POLICY, method=METHOD,
                derivation='CALENDAR_RESULT_NOT_EXPLICIT_REPORTED_START',
                reported_end=premise['end'].isoformat(), premise_dom_path=premise['path'],
                premise_text=premise['text'], caption_dom_paths=ownership['metadata_dom_paths'],
                caption_text=caption, table_dom_path=ownership['table_dom_path'],
                column_header=' '.join(headers), comparable_columns=[list(v) for v in sorted(set(labels))],
                calendar_scope='Same-document stated quarter/end alignment; no contrary fiscal convention',
                unit_evidence=ownership['unit_evidence'], accounting_basis=ownership['statement_basis']))
