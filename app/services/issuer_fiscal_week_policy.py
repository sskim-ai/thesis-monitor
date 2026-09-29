"""Source-declared annual fiscal calendars, never a duration tolerance."""
from calendar import day_name, month_name
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
import re

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'issuer-declared-fiscal-week-calendar-v1'
COMPARABLE = 'ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE'
WARNING = 'FISCAL_WEEK_COUNT_DIFFERENCE'


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
    # The reported year labels and end dates are source text, not inferred FYs.
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
    if len({(p['weekday'], p['month'], p['day']) for p in result['policies']}) == 1 and result['years']:
        result['status'] = 'PROVEN'
    result['receipt_sha256'] = digest(result)
    return result


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
