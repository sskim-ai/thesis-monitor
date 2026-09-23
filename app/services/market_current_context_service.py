"""Source-owned current context is not automatically a new daily signal."""
from datetime import date, datetime

from app.macro.publication import PUBLICATION_SERIES, publication_freshness
from app.services.kr_market_digest_quality_service import is_kr_sector_return_row


def current_context_eligible(fact, completed, assessed):
    fields = fact.get('fields') or {}
    if (any(fields.get(k) is True for k in ('source_unavailable', 'renderer_only'))
            or fields.get('structured_state') in {'UNAVAILABLE', 'SOURCE_UNAVAILABLE'}
            or fields.get('quality') not in {'fresh', 'verified'}):
        return False
    observed = fact.get('as_of_date')
    try:
        if date.fromisoformat(observed) > date.fromisoformat(assessed):
            return False
        publication = fields.get('publication_receipt')
        if fields.get('provider') == 'fred' and fields.get('series_code') in PUBLICATION_SERIES:
            return publication_freshness(publication, fields['series_code'], observed,
                completed=completed, assessed=assessed)['factual_display_eligible']
        receipt = fields.get('completed_session_receipt') or {}
        return (fact.get('fact_type') in {'market_index', 'market_sector', 'market_style'}
                and fields.get('provider') == 'ohlcv_analyst'
                and receipt['contract'] == 'completed-market-session-v1'
                and receipt['series_code'] == fields['series_code']
                and receipt['completed_session_date'] == observed == completed
                and receipt['selected_raw_date'] == completed and receipt['dates_relabelled'] is False
                and receipt['return_basis'] == 'adjusted_close_to_previous_completed_session'
                and len(receipt['source_sha256']) == 64
                and datetime.fromisoformat(receipt['assessed_at']).date().isoformat() == assessed)
    except (KeyError, TypeError, ValueError):
        return False


def kr_sector_alias(fact, source, completed, eligible_refs):
    fields = fact.get('fields') or {}
    if (fact.get('fact_type') != 'market_cross_section_sector'
            or fact.get('as_of_date') != completed or fact.get('source') != 'KIWOOM_REST'
            or fields.get('taxonomy') != 'kiwoom-sector-index-v1'
            or fields.get('metric_role') != 'actual_sector_breadth'
            or fields.get('source_ref') not in eligible_refs
            or not is_kr_sector_return_row(market_scope=fields.get('market_scope'), name=fields.get('sector', ''))):
        return False
    matches = [r for r in (source.get('adapter_context') or {}).get('sectors', [])
               if r.get('source_ref') == fields.get('source_ref')]
    return (len(matches) == 1 and matches[0].get('as_of_date') == completed
            and matches[0].get('state') == 'CURRENT_DIRECTIONAL'
            and matches[0].get('return_pct') == fields.get('return_pct')
            and matches[0].get('market_scope') == fields.get('market_scope')
            and matches[0].get('name') == fields.get('sector'))
