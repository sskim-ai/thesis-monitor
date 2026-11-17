"""Source-declared annual fiscal calendars, never a duration tolerance."""
from calendar import day_name, month_name
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'issuer-declared-fiscal-week-calendar-v1'
COMPARABLE = 'ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE'
WARNING = 'FISCAL_WEEK_COUNT_DIFFERENCE'
QUARTER = 'ISSUER_REPORTED_13_14_WEEK_QUARTER'


def _quarter_table(raw):
    from app.services.sec_primary_inline_financial import InlineDocument

    class TableDocument(InlineDocument):
        def __init__(self):
            super().__init__()
            self.tables, self.dei = {}, []

        def handle_starttag(self, tag, attrs):
            super().handle_starttag(tag, attrs)
            if not self.stack or self.stack[-1]['tag']!=tag:
                return
            node = self.stack[-1]
            if tag == 'table':
                self.tables[node['ordinal']] = []
            if tag == 'ix:nonfraction':
                area = next((p['ordinal'] for p in reversed(self.stack) if p['tag']=='table'), None)
                row = next((p['ordinal'] for p in reversed(self.stack) if p['tag']=='tr'), None)
                node.update(table=area, row=row)
            if tag == 'ix:nonnumeric' and node['ns'].get('dei','').startswith('http://xbrl.sec.gov/dei/'):
                node['capturing'] = True
                self.dei.append(node)

        def handle_data(self, value):
            super().handle_data(value)
            for node in self.stack:
                if node['tag']=='table':
                    self.tables[node['ordinal']].append(value)

    parser=TableDocument()
    parser.feed(raw.decode('utf-8'))
    return parser


def extract_reported_quarter(raw, *, issuer, filing):
    """Use a sealed primary 10-Q's statement and issuer-declared Q1 calendar."""
    from app.services.sec_primary_inline_financial import INSTANCE, content, descendants
    from app.services.sec_business_field_quality_service import SEMANTICS

    if filing.get('form')!='10-Q':
        return None
    try:
        doc=_quarter_table(raw)
        issuer=str(issuer).zfill(10)
        def header(name):
            values={' '.join(content(n).split()) for n in doc.dei
                if n['attrs'].get('name')=='dei:'+name}
            if len(values)!=1:
                raise ValueError('reported_quarter_dei')
            return values.pop()
        fiscal_year=int(header('DocumentFiscalYearFocus'))
        if header('DocumentFiscalPeriodFocus')!='Q1' or header('EntityCentralIndexKey').zfill(10)!=issuer:
            return None
        report_end=date.fromisoformat(filing['reportDate'])
        if datetime.strptime(header('DocumentPeriodEndDate'),'%B %d, %Y').date()!=report_end:
            return None
        text=' '.join(' '.join(doc.text).split())
        rule=re.findall(r'fiscal year ends on the (\w+) nearest(?: to)? (\w+) (\d{1,2})'
            r' and typically consists of 52 weeks\. Approximately every [^.]+?53-week fiscal year'
            r' to align [^.]+?policy\.',text,re.I)
        past=re.findall(r'Fiscal year (20\d{2}), which ended on (\w+ \d{1,2}, 20\d{2}) was comprised of '
            r'(52|53) weeks, with the first fiscal quarter consisting of (13|14) weeks\.',text,re.I)
        present=re.findall(r'Fiscal year (20\d{2}) will be comprised of (52|53) weeks and will end on '
            r'(\w+ \d{1,2}, 20\d{2}), with (?:each|the first) fiscal quarter consisting of (13|14) weeks\.',text,re.I)
        rules, prior, current=map(set,(rule,past,present))
        if any(len(options)!=1 for options in (rules,prior,current)):
            return None
        dow, month, day=rules.pop()
        py, p_end, p_year, p_q=prior.pop()
        cy, c_year, c_end, c_q=current.pop()
        weekday=[d.lower() for d in day_name].index(dow.lower())
        mon=[m.lower() for m in month_name].index(month.lower())
        ends={}
        for year, label in ((int(py)-1,None),(int(py),p_end),(int(cy),c_end)):
            anchor=date(year,mon,int(day))
            ends[year]=anchor+timedelta(days=(weekday-anchor.weekday()+3)%7-3)
            if label and datetime.strptime(label,'%B %d, %Y').date()!=ends[year]:
                return None
        if (int(cy)!=fiscal_year or int(py)!=fiscal_year-1 or {int(p_q),int(c_q)}!={13,14}
                or any((ends[year]-ends[year-1]).days!=int(weeks)*7
                       for year,weeks in ((int(py),p_year),(int(cy),c_year)))
                or any(int(q)!=(14 if int(y)==53 else 13) for q,y in ((p_q,p_year),(c_q,c_year)))):
            return None
        def frame(year,weeks):
            start=ends[year-1]+timedelta(days=1)
            return dict(start=start.isoformat(), end=(start+timedelta(days=int(weeks)*7-1)).isoformat(),
                quarter=f'FY{year}-Q1',duration=f'P{weeks}W',months_heading='Three Months Ended')
        periods=[frame(int(cy),c_q),frame(int(py),p_q)]
        if periods[0]['end']!=report_end.isoformat():
            return None
        selected = {}
        unit = {}
        unique_ids=set()
        for node in doc.captures:
            ident=node['attrs'].get('id')
            if not ident or ident in unique_ids:
                return None
            unique_ids.add(ident)
            if node['name']==(INSTANCE,'context'):
                children=list(descendants(node))
                if any(n['name'][1] in {'segment','scenario','explicitmember','typedmember','instant'} for n in children):
                    continue
                parts={k:[n for n in children if n['name']==(INSTANCE,k)] for k in
                    ('identifier','startdate','enddate')}
                if any(len(v)!=1 for v in parts.values()):
                    continue
                identifier=parts['identifier'][0]
                if identifier['attrs'].get('scheme') not in {'http://www.sec.gov/CIK','https://www.sec.gov/CIK'} or content(identifier).zfill(10)!=issuer:
                    continue
                for col,period in enumerate(periods):
                    if (content(parts['startdate'][0]),content(parts['enddate'][0]))==(period['start'],period['end']):
                        selected[ident]=col
            elif node['name']==(INSTANCE,'unit'):
                if len(node['children'])==1 and node['children'][0]['name']==(INSTANCE,'measure'):
                    symbol=content(node['children'][0])
                    prefix,_,currency=symbol.partition(':')
                    if node['ns'].get(prefix)=='http://www.xbrl.org/2003/iso4217' and re.fullmatch(r'[A-Z]{3}',currency):
                        unit[ident]=currency
        display_dates=[date.fromisoformat(p['end']).strftime('%B %d, %Y').replace(' 0',' ') for p in periods]
        qualifier='Three Months Ended '+' '.join(display_dates)
        good={k for k,v in doc.tables.items() if ' '.join(' '.join(v).split()).replace(' 0',' ').startswith(qualifier)
            and re.search(r'\boperating (?:income|loss|profit)\b',' '.join(' '.join(v).split()),re.I)}
        by_row={}
        for node in doc.captures:
            attrs=node['attrs']
            if node.get('table') not in good or not node.get('row') or attrs.get('contextref') not in selected:
                continue
            prefix,_,concept=attrs.get('name','').partition(':')
            if ((prefix,concept) not in SEMANTICS
                    or not node['ns'].get(prefix,'').startswith(('http://fasb.org/us-gaap/','http://xbrl.ifrs.org/'))):
                continue
            value=content(node).replace(',','')
            if not re.fullmatch(r'\d+(?:\.\d+)?',value) or attrs.get('unitref') not in unit:
                continue
            scale=int(attrs.get('scale','0'))
            if not 0<=scale<=9 or attrs.get('sign','') not in ('','-'):
                continue
            amount=Decimal(attrs.get('sign','')+value)*10**scale
            key=node['table'],node['row'],prefix+':'+concept
            by_row.setdefault(key,[]).append(dict(column=selected[attrs['contextref']],amount=int(amount)
                if amount==amount.to_integral_value() else float(amount),currency=unit[attrs['unitref']],
                context=attrs['contextref'],occurrence=attrs['id']))
        pairs={}
        for (table,row,semantic),values in by_row.items():
            if [v['column'] for v in values]==[0,1]:
                pairs.setdefault(semantic,[]).append(dict(table=table,row=row,cells=values))
        pairs={k:v[0] for k,v in pairs.items() if len(v)==1}
        if not pairs:
            return None
        receipt=dict(contract=QUARTER,issuer=issuer,filing=filing,periods=periods,pairs=pairs,
            source_payload_sha256=sha256_bytes(raw),calendar_sha256=digest([rule,past,present]),normalization='NONE')
        return dict(receipt,receipt_sha256=digest(receipt))
    except (KeyError, ValueError, IndexError, TypeError, InvalidOperation, UnicodeError):
        return None


def reported_quarter_comparability(current, prior, *, proof, cutoff):
    """Bind the two Company Facts occurrences to the same reported row."""
    if (not proof or proof.get('contract')!=QUARTER or proof.get('normalization')!='NONE'
            or proof.get('receipt_sha256')!=digest({k:v for k,v in proof.items() if k!='receipt_sha256'})):
        return None
    try:
        filing=proof['filing']
        a,b=rows=(current,prior)
        keys=('issuer_cik','taxonomy','concept','currency','statement_basis','receipt','source_payload_sha256')
        if (any(not a.get(k) or a[k]!=b.get(k) for k in keys)
                or a['statement_basis']!='sec_companyfacts_entity_wide'
                or str(a['issuer_cik']).zfill(10)!=proof['issuer'] or a['receipt']!=filing['accessionNumber']
                or filing['form']!='10-Q' or date.fromisoformat(filing['filingDate'])>cutoff
                or filing['reportDate']!=a['amount_period_end']):
            return None
        pair=proof['pairs'][a['taxonomy']+':'+a['concept']]
        for row,period,cell in zip(rows,proof['periods'],pair['cells'],strict=True):
            if (row['amount']!=cell['amount'] or row['currency']!=cell['currency'] or not row['source_row_identity']
                    or (row['amount_period_start'],row['amount_period_end'])!=(period['start'],period['end'])
                    or date.fromisoformat(period['end'])>date.fromisoformat(filing['filingDate'])
                    or (date.fromisoformat(period['end'])-date.fromisoformat(period['start'])).days+1
                        != 7*int(period['duration'][1:-1])):
                return None
        cq,pq=proof['periods']
        if (not re.fullmatch(r'FY\d{4}-Q1',cq['quarter'])
                or pq['quarter']!=f"FY{int(cq['quarter'][2:6])-1}-Q1"
                or {cq['duration'],pq['duration']}!={'P13W','P14W'}):
            return None
        return dict(contract=QUARTER,current_duration=cq['duration'],prior_duration=pq['duration'],
            current_fiscal_quarter=cq['quarter'],prior_fiscal_quarter=pq['quarter'],
            accession=filing['accessionNumber'],source_payload_sha256=proof['source_payload_sha256'],
            policy_receipt_sha256=proof['receipt_sha256'],comparison_row_sha256=digest(pair),
            quality_reason=WARNING,normalization='NONE')
    except (KeyError, ValueError, IndexError, TypeError):
        return None


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, value):
        self.parts.append(value)


def extract_policy(raw, *, issuer, filing):
    parser = PlainText()
    parser.feed(raw.decode('utf-8', errors='replace'))
    text = re.sub(r'\s+', ' ', ' '.join(parser.parts))
    policies = list(re.finditer(r'fiscal year ends on the (\w+) nearest(?: to)? (\w+) (\d{1,2})'
        r' and typically consists of 52 weeks\. Approximately every [^.]+?53-week fiscal year'
        r' to align [^.]+?policy\.', text, re.I))
    declared = list(re.finditer(
        r'fiscal year is the 52\s*-\s*or 53-week period ending on the '
        r'(\w+) (?:closest|nearest) to (\w+) (\d{1,2})\.', text, re.I))
    policies.extend(declared)
    result = dict(contract=CONTRACT, issuer=str(issuer).zfill(10), filing=filing,
        source_payload_sha256=sha256_bytes(raw), policies=[], years=[], status='UNPROVEN')
    for match in policies:
        try:
            weekday = [x.lower() for x in day_name].index(match[1].lower())
            month = [x.lower() for x in month_name].index(match[2].lower())
            day = int(match[3])
            date(2000, month, day)
        except ValueError:
            continue
        result['policies'].append(dict(weekday=weekday, month=month, day=day, evidence=match[0]))
    # Legacy dates are literal text; declared-calendar dates also need exact source contexts.
    patterns = (
        r'Fiscal year (20\d{2}) was comprised of (52|53) weeks and ended on (\w+ \d{1,2}, 20\d{2})',
        r'Fiscal years (20\d{2}) and (20\d{2}), which ended on (\w+ \d{1,2}, 20\d{2}) and '
        r'(\w+ \d{1,2}, 20\d{2}), respectively, were each comprised of (52|53) weeks',
    )
    for index, pattern in enumerate(patterns):
        for match in re.finditer(pattern, text, re.I):
            values = [(match[1], match[3], match[2])] if index == 0 else [
                (match[1], match[3], match[5]), (match[2], match[4], match[5])]
            for year, end, weeks in values:
                try:
                    record = dict(fiscal_year=int(year), period_end=datetime.strptime(end, '%B %d, %Y').date().isoformat(),
                        weeks=int(weeks), evidence=match[0])
                except ValueError:
                    continue
                if record not in result['years']:
                    result['years'].append(record)
    ambiguous = False
    if declared:
        bound_years = _context_bound_declared_years(raw, text, result)
        ambiguous = bound_years is None
        result['years'].extend(bound_years or [])
        year_values = {}
        for row in result['years']:
            year_values.setdefault(row['fiscal_year'], set()).add((row['period_end'], row['weeks']))
        ambiguous = ambiguous or any(len(values) != 1 for values in year_values.values())
    if not ambiguous and len({(p['weekday'], p['month'], p['day']) for p in result['policies']}) == 1 and result['years']:
        result['status'] = 'PROVEN'
    result['receipt_sha256'] = digest(result)
    return result


def _context_bound_declared_years(raw, text, proof):
    """Declared FY labels need matching issuer-wide source contexts, not inferred FYs."""
    from app.services.sec_primary_inline_financial import (
        InlineDocument, INSTANCE, descendants, content,
    )

    rules = {(p['weekday'], p['month'], p['day']) for p in proof['policies']}
    if len(rules) != 1:
        return []
    declarations = {}
    for match in re.finditer(
            r'Fiscal (20\d{2})(?: and (20\d{2}))? (?:each )?contained (52|53) weeks', text, re.I):
        for year in (match[1], match[2]):
            if year:
                declarations.setdefault(int(year), []).append((int(match[3]), match[0]))
    if any(len({weeks for weeks, _ in values}) != 1 for values in declarations.values()):
        return None
    parser = InlineDocument()
    parser.feed(raw.decode('utf-8', errors='replace'))
    contexts = {}
    for node in parser.captures:
        if node['name'] == (INSTANCE, 'context'):
            contexts.setdefault(node['attrs'].get('id'), []).append(node)
    if any(not key or len(nodes) != 1 for key, nodes in contexts.items()):
        return None
    weekday, month, day = next(iter(rules))
    output = []
    for year, values in sorted(declarations.items()):
        weeks, evidence = values[0]
        try:
            anchor = date(year, month, day)
        except ValueError:
            return None
        end = anchor + timedelta(days=(weekday - anchor.weekday() + 3) % 7 - 3)
        if any(row['fiscal_year'] == year and (row['weeks'] != weeks or row['period_end'] != end.isoformat())
               for row in proof['years']):
            return None
        bindings = []
        for context_id, nodes in contexts.items():
            node = nodes[0]
            children = list(descendants(node))
            if any(n['name'][1] in {'segment', 'scenario', 'explicitmember', 'typedmember'} for n in children):
                continue
            entities = [n for n in node['children'] if n['name'] == (INSTANCE, 'entity')]
            periods = [n for n in node['children'] if n['name'] == (INSTANCE, 'period')]
            if len(node['children']) != 2 or len(entities) != 1 or len(periods) != 1:
                continue
            if len(entities[0]['children']) != 1 or len(periods[0]['children']) != 2:
                continue
            cells = {'identifier': [n for n in entities[0]['children'] if n['name'] == (INSTANCE, 'identifier')]}
            cells.update({key: [n for n in periods[0]['children'] if n['name'] == (INSTANCE, key)]
                          for key in ('startdate', 'enddate')})
            if any(len(value) != 1 for value in cells.values()):
                continue
            if any(value[0]['children'] for value in cells.values()):
                continue
            identifier = cells['identifier'][0]
            if (identifier['attrs'].get('scheme') not in {'http://www.sec.gov/CIK', 'https://www.sec.gov/CIK'}
                    or not re.fullmatch(r'\d{1,10}', content(identifier))
                    or content(identifier).zfill(10) != proof['issuer']):
                continue
            try:
                start = date.fromisoformat(content(cells['startdate'][0]))
                reported_end = date.fromisoformat(content(cells['enddate'][0]))
            except ValueError:
                continue
            if reported_end == end and (end - start).days + 1 == weeks * 7:
                bindings.append(dict(context_id=context_id, context_sha256=digest(node),
                    period_start=start.isoformat(), period_end=end.isoformat()))
        if bindings:
            output.append(dict(fiscal_year=year, period_end=end.isoformat(), weeks=weeks,
                evidence=evidence, period_end_basis='DECLARED_CALENDAR_AND_EXACT_ISSUER_XBRL_CONTEXT',
                source_contexts=bindings))
    return output


def annual_comparability(current, prior, proof):
    """Input tuples are already field-owned; still verify every common basis."""
    if not proof or proof.get('receipt_sha256') != digest({k: v for k, v in proof.items() if k != 'receipt_sha256'}):
        return None
    if proof.get('status') != 'PROVEN' or proof.get('contract') != CONTRACT:
        return None
    keys = ('issuer', 'metric', 'semantic', 'statement_basis', 'currency', 'unit', 'unit_scale', 'formal_state', 'period_role')
    if any(not current.get(k) or current[k] != prior.get(k) for k in keys):
        return None
    if current['period_role'] != 'ANNUAL' or current['formal_state'] != 'FORMAL':
        return None
    try:
        if str(current['issuer']).zfill(10) != proof['issuer']:
            return None
        filing = proof['filing']
        if filing['form'].split('/')[0] not in {'10-K', '20-F', '40-F'}:
            return None
        if current['source_document_id'] != filing['accessionNumber']:
            return None
        rule = proof['policies'][0]
        records = []
        for row in (current, prior):
            start, end = (date.fromisoformat(row[k]) for k in ('period_start', 'period_end'))
            candidates = [y for y in proof['years'] if y['period_end'] == end.isoformat()]
            if len({(y['fiscal_year'], y['weeks']) for y in candidates}) != 1:
                return None
            year = candidates[0]
            anchor = date(year['fiscal_year'], rule['month'], rule['day'])
            expected_end = anchor + timedelta(days=(rule['weekday'] - anchor.weekday() + 3) % 7 - 3)
            if end != expected_end or (end - start).days + 1 != year['weeks'] * 7:
                return None
            records.append((start, end, year))
        a, b = records
        if (a[2]['fiscal_year'] != b[2]['fiscal_year'] + 1 or a[0] != b[1] + timedelta(days=1)
                or {a[2]['weeks'], b[2]['weeks']} - {52, 53}):
            return None
        different = a[2]['weeks'] != b[2]['weeks']
        return dict(contract=COMPARABLE, current_fiscal_year=a[2]['fiscal_year'], prior_fiscal_year=b[2]['fiscal_year'],
            current_weeks=a[2]['weeks'], prior_weeks=b[2]['weeks'],
            quality_reason_codes=[WARNING] if different else [],
            policy_receipt_sha256=proof['receipt_sha256'], value_adjustment=None)
    except (KeyError, ValueError, TypeError, IndexError):
        return None
