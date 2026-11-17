"""Rank retained observations without lending them investment authority."""
from collections import Counter
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo

from app.services.confirmed_sector_taxonomy import KR_NAMES, US_BROAD, PROVIDERS, classify_row
from app.services.market_numeric_claim_service import number
from app.services.unified_snapshot_contract import digest


def _name_key(name):
    return re.sub(r'[\s/·ㆍ]+', '', name).casefold() if isinstance(name, str) else ''


def sector_observations(facts, registry, *, market, completed, bad_registry=()):
    kind = 'market_cross_section_sector' if market == 'kr' else 'market_sector'
    sectors = [f for f in facts if f['fact_type'] == kind]

    def identity(fact):
        fields = fact['fields']
        return ((fields.get('market_scope'), fields.get('sector_code')) if market == 'kr'
                else ('US', fields.get('series_code')))

    occurrences = Counter(identity(f) for f in sectors)
    refs = Counter(f['fact_id'] for f in sectors)
    accepted, audit = [], []
    for fact in sectors:
        venue, code = identity(fact)
        fields, ref = fact['fields'], fact['fact_id']
        value = fields.get('return_pct')
        key = (ref, 'fields.return_pct')
        row = registry.get(key, {})
        provider = fact.get('source') or fields.get('provider')
        category = None
        reason = None
        observed = fields.get('observed_at')
        if observed is not None:
            try:
                time = datetime.fromisoformat(observed)
                zone = ZoneInfo('Asia/Seoul' if market == 'kr' else 'America/New_York')
                # The US OHLCV daily producer encodes the bar date at UTC midnight.
                bar_label = (market == 'us' and provider == PROVIDERS['us']
                    and fields.get('market_session') == 'us_regular'
                    and time.utcoffset() == timedelta(0) and time.hour == time.minute == time.second == time.microsecond == 0)
                session_date = time.date() if bar_label or not time.tzinfo else time.astimezone(zone).date()
                same_day = session_date.isoformat() == completed
            except (ValueError, TypeError):
                same_day = False
        else:
            same_day = True  # The canonical sector source pins the session in source_ref.
        if fact['as_of_date'] != completed or not same_day:
            reason = 'OBSERVATION_SESSION_MISMATCH'
        elif provider != PROVIDERS[market] or fields.get('provider', provider) != provider or fields.get('source_unavailable'):
            reason = 'OBSERVATION_SOURCE_MISMATCH'
        elif occurrences[(venue,code)] != 1 or refs[ref] != 1 or key in bad_registry:
            reason = 'DUPLICATE_OR_CONFLICT'
        elif not number(value) or not number(row.get('value')) or row.get('value') != value or row.get('unit') not in {'pct','percent'}:
            reason = 'RETURN_VALUE_OR_UNIT_MISMATCH'
        elif market == 'kr':
            canonical = KR_NAMES.get(venue, {}).get(code)
            if (not canonical or _name_key(fields.get('sector')) != _name_key(canonical)
                    or fields.get('taxonomy') != 'kiwoom-sector-index-v1'
                    or fields.get('source_ref') != f'kiwoom:ka20003:{venue}:{code}:{completed}'
                    or fields.get('metric_role') not in {'sector_price_proxy','actual_sector_breadth'}):
                reason = 'SECTOR_IDENTITY_OR_SOURCE_REF_MISMATCH'
            else:
                category, reason = classify_row(dict(fields,sector=canonical), market)
        elif code not in (*US_BROAD,'SOXX'):
            reason = 'NOT_CONFIGURED_SECTOR'
        else:
            category, reason = classify_row(fields, market)
        audit.append(dict(fact_id=ref,venue=venue,code=code,session=fact['as_of_date'],
            category=category,reason=reason,source_fact_sha256=digest(fact),
            observation_only=True,directional_authority_added=False))
        if category in {'KR_DETAILED_INDUSTRY','KR_SIZE_STYLE_INDEX','US_BROAD_SECTOR','US_SEMICONDUCTOR_WATCH'}:
            accepted.append((venue,code,category,fact,row))
    return accepted, audit


def detailed_count(venue):
    if venue == 'US':
        return len(US_BROAD)
    return sum(classify_row(dict(market_scope=venue,sector_code=code,sector=name,
        taxonomy='kiwoom-sector-index-v1'),'kr')[0] == 'KR_DETAILED_INDUSTRY'
        for code,name in KR_NAMES[venue].items())
