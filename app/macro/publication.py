"""Publication-owned freshness, independent of observation frequency/daily delta."""
from datetime import date, datetime, time
from hashlib import sha256
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

PUBLICATION_SERIES = frozenset({"DGS3", "DGS5", "DGS10", "DGS30", "DCOILWTICO"})
CONTRACT = "fred-published-observation-v1"


class _Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.period = self.updated = self.next_release = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get('class') or '').split())
        if tag == 'meta' and attrs.get('name') == 'dcterms:PeriodOfTime':
            self.period = attrs.get('content')
        if tag == 'span' and 'updated-text' in classes and attrs.get('title'):
            if 'default-text' in classes:
                self.updated = attrs['title']
            elif 'text-link' in classes:
                self.next_release = attrs['title']


def publication_receipt(body: bytes, series: str, as_of: datetime) -> dict:
    if series not in PUBLICATION_SERIES or as_of.tzinfo is None:
        raise ValueError("publication_series_or_cutoff_invalid")
    metadata = _Metadata()
    metadata.feed(body.decode('utf-8'))
    if not all((metadata.period, metadata.updated, metadata.next_release)):
        raise ValueError('publication_metadata_incomplete')
    attributes = dict(piece.strip().split(":", 1) for piece in metadata.period.split(';') if piece.strip())
    expected = date.fromisoformat(attributes['end'])
    updated_text, abbreviation = metadata.updated.rsplit(' ', 1)
    published = datetime.strptime(updated_text, '%b %d, %Y %I:%M %p').replace(tzinfo=ZoneInfo('America/Chicago'))
    if published.tzname() != abbreviation:
        raise ValueError('publication_timezone_mismatch')
    next_day = datetime.strptime(metadata.next_release, '%b %d, %Y').date()
    # H.15 publishes at 16:15 ET. WTI has no verified release clock: deny from
    # the start of its declared next release date until a new publication arrives.
    next_due = datetime.combine(next_day, time(0) if series == 'DCOILWTICO' else time(16, 15),
                                tzinfo=ZoneInfo('America/New_York'))
    if expected > published.date() or next_due <= published:
        raise ValueError('publication_date_order_invalid')
    return dict(contract=CONTRACT, series_code=series, provider='fred',
                source_url=f'https://fred.stlouisfed.org/series/{series}',
                source_sha256=sha256(body).hexdigest(), expected_observation_date=expected.isoformat(),
                published_at=published.isoformat(), next_publication_due=next_due.isoformat(),
                assessed_at=as_of.isoformat(), observation_frequency='daily',
                publication_calendar='official_series_next_release',
                current=published <= as_of < next_due)


def publication_current(receipt, series, observed, as_of):
    try:
        return (receipt['contract'] == CONTRACT and series in PUBLICATION_SERIES
                and receipt['series_code'] == series and receipt['provider'] == 'fred'
                and receipt['source_url'] == f'https://fred.stlouisfed.org/series/{series}'
                and len(receipt['source_sha256']) == 64
                and receipt['current'] is True and observed == receipt['expected_observation_date']
                and datetime.fromisoformat(receipt['published_at']) <= as_of
                < datetime.fromisoformat(receipt['next_publication_due']))
    except (KeyError, TypeError, ValueError):
        return False
