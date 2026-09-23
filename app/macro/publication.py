"""Publication-owned freshness, independent of observation frequency/daily delta."""
from datetime import date, datetime, time
from hashlib import sha256
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

PUBLICATION_SERIES = frozenset({"DGS2", "DGS3", "DGS5", "DGS10", "DGS30", "DCOILWTICO",
                                "DFII10", "T10YIE", "BAMLH0A0HYM2", "VIXCLS"})
H15_CLOCK_SERIES = frozenset({'DGS2', 'DGS3', 'DGS5', 'DGS10', 'DGS30'})
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
    # Preserve the existing H.15 clock. Other series have no verified clock here:
    # deny from the start of the declared release day, never assume H.15 timing.
    next_due = datetime.combine(next_day, time(16, 15) if series in H15_CLOCK_SERIES else time(0),
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


def publication_freshness(receipt, series, observed, *, completed, assessed):
    """Calendar-owned publication validity is distinct from current-session evidence."""
    state = 'STALE_UNEXPECTED'
    try:
        at = datetime.fromisoformat(receipt['assessed_at'])
        valid = (at.date().isoformat() == assessed
                 and date.fromisoformat(observed) <= date.fromisoformat(completed)
                 <= date.fromisoformat(assessed)
                 and publication_current(receipt, series, observed, at))
        if valid:
            state = ('CURRENT_BY_PROVIDER_CALENDAR' if observed == completed
                     else 'LATEST_PUBLISHED_WITH_LAG')
    except (KeyError, TypeError, ValueError):
        pass
    return dict(contract='macro-publication-freshness-display-v1', state=state,
                observation_date=observed, completed_session=completed,
                calendar_owner='official_series_next_release',
                reason=('provider_publication_verified_for_cutoff' if state != 'STALE_UNEXPECTED'
                        else 'publication_receipt_missing_expired_or_unverified_for_cutoff'),
                current_direction_eligible=state == 'CURRENT_BY_PROVIDER_CALENDAR',
                factual_display_eligible=state != 'STALE_UNEXPECTED')
