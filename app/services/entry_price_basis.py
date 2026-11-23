"""Price-basis checks shared by the frozen B2 input and its presentation.

The daily frame proves the completed-session quote. A completed weekly/monthly
frame may have a different close and bar label while being evaluated for that
same session. This module grants no source permission or trading conclusion.
"""
from datetime import date

from app.services.new_buyer_base_contract import number


def _day(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def frame_matches_price(frame, *, timeframe, frame_as_of, price, session):
    """Check one accepted chart frame against a B-context quote.

    ``price`` uses ``value/currency/basis/as_of``. Callers must separately bind
    the source identity, ENTRY permission and daily quote before using a
    weekly/monthly frame. Missing evaluation metadata retains only the legacy
    same-session, same-close path; it cannot make an older reference current.
    """
    if not isinstance(frame, dict) or not isinstance(price, dict):
        return False
    session_day, frame_day = _day(session), _day(frame_as_of)
    candle = frame.get('candle')
    close = number(candle.get('close')) if isinstance(candle, dict) else None
    current = number(price.get('value'))
    if (timeframe not in ('daily', 'weekly', 'monthly')
            or session_day is None or frame_day is None or frame_day > session_day
            or price.get('as_of') != session or frame.get('quality') != 'available'
            or not price.get('currency') or frame.get('currency') != price['currency']
            or frame.get('timeframe', timeframe) != timeframe
            or ('as_of_date' in frame and frame['as_of_date'] != frame_as_of)
            or current is None or current <= 0 or close is None or close <= 0
            or (price.get('basis'), frame.get('price_basis')) not in {
                ('adjusted_close', 'adjusted'), ('unadjusted_close', 'unadjusted'),
                ('regular_close', 'unadjusted')}):
        return False
    if any(row.get(key) in ('PARTIAL', 'UNCONFIRMED')
           for row in (frame, candle) for key in ('bar_state', 'completion_state')):
        return False
    metadata_present = 'completed_bar_only' in frame or 'evaluation_as_of' in frame
    if metadata_present and (frame.get('completed_bar_only') is not True
                             or frame.get('evaluation_as_of') != session):
        return False
    if timeframe == 'daily' or not metadata_present:
        return frame_as_of == session and close == current
    return True
