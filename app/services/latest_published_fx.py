"""Fresh official FX display ownership is independent of equity-session date."""
from datetime import datetime

from app.services.macro_source_time import CONTRACT, source_period
from app.services.unified_snapshot_contract import digest


def validate_context(context, *, observation_date, response_hashes, query_as_of):
    try:
        day, precision = source_period(context['observation_period'], daily_required=True)
        query = datetime.fromisoformat(query_as_of)
        retrieved = datetime.fromisoformat(context['retrieved_at'])
        return bool(context['contract'] == CONTRACT and context['provider'] == 'ecos'
            and context['series_code'] == 'USDKRW'
            and context['observation_date'] == day.isoformat() == observation_date
            and context['observation_precision'] == precision == 'daily'
            and context['query_as_of'] == query_as_of and query.utcoffset() is not None
            and retrieved.utcoffset() is not None and retrieved >= query
            and day <= query.date()
            and context['response_sha256'] in response_hashes
            and context['latest_available_at_query_time'] is True
            and context['display_eligible'] is True and context['direction_eligible'] is False
            and context['freshness_state'] in {'CURRENT_SESSION_OR_DATE', 'LATEST_PUBLISHED_VERIFIED'})
    except (KeyError, TypeError, ValueError):
        return False


def display_receipt(publications, equity_session):
    provider = publications['providers']['ecos']
    rows = [r for r in provider['value']['observations'] if r['series_code'] == 'USDKRW']
    hashes = set(provider['source_hashes'].values())
    row = rows[0] if len(rows) == 1 else None
    context = row['raw_payload']['publication_context'] if row else {}
    eligible = bool(row and validate_context(context,
        observation_date=row['observed_at'][:10], response_hashes=hashes,
        query_as_of=publications['query_as_of']))
    receipt = dict(contract='latest-published-fx-display-v1', run_id=publications['run_id'],
        status='ELIGIBLE' if eligible else 'TYPED_UNAVAILABLE',
        equity_session=equity_session, observation_date=context.get('observation_date') if eligible else None,
        explicit_observation_date_required=eligible and context['observation_date'] != equity_session,
        direction_eligible=False, context_sha256=digest(context),
        reason='OFFICIAL_LATEST_PUBLISHED_DISPLAY_ONLY' if eligible else 'FX_CURRENTNESS_UNPROVEN')
    return dict(**receipt, receipt_sha256=digest(receipt))
