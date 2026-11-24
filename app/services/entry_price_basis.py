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


def frame_price_failures(frame, *, timeframe, frame_as_of, price, session):
    """Explain the existing completed-frame check without relaxing its basis.

    ``price`` uses ``value/currency/basis/as_of``. Callers must separately bind
    the source identity, ENTRY permission and daily quote before using a
    weekly/monthly frame. Missing evaluation metadata retains only the legacy
    same-session, same-close path; it cannot make an older reference current.
    """
    if not isinstance(frame, dict) or not isinstance(price, dict):
        return ('FRAME_OR_PRICE_MISSING',)
    session_day, frame_day = _day(session), _day(frame_as_of)
    candle = frame.get('candle')
    close = number(candle.get('close')) if isinstance(candle, dict) else None
    current = number(price.get('value'))
    failures = []
    checks = (
        ('TIMEFRAME_MISSING_OR_MISMATCH', timeframe in ('daily', 'weekly', 'monthly')
            and frame.get('timeframe', timeframe) == timeframe),
        ('FRAME_SESSION_MISMATCH', session_day is not None and frame_day is not None
            and frame_day <= session_day and price.get('as_of') == session
            and ('as_of_date' not in frame or frame['as_of_date'] == frame_as_of)),
        ('FRAME_UNAVAILABLE', frame.get('quality') == 'available'),
        ('FRAME_CURRENCY_MISMATCH', bool(price.get('currency'))
            and frame.get('currency') == price['currency']),
        ('FRAME_PRICE_INVALID', current is not None and current > 0 and close is not None and close > 0),
        ('FRAME_PRICE_BASIS_MISMATCH', (price.get('basis'), frame.get('price_basis')) in {
                ('adjusted_close', 'adjusted'), ('unadjusted_close', 'unadjusted'),
                ('regular_close', 'unadjusted')}),
    )
    failures.extend(code for code, passed in checks if not passed)
    if any(row.get(key) in ('PARTIAL', 'UNCONFIRMED')
           for row in (frame, candle if isinstance(candle, dict) else {})
           for key in ('bar_state', 'completion_state')):
        failures.append('FRAME_INCOMPLETE')
    metadata_present = 'completed_bar_only' in frame or 'evaluation_as_of' in frame
    if metadata_present:
        if frame.get('completed_bar_only') is not True:
            failures.append('FRAME_INCOMPLETE')
        if frame.get('evaluation_as_of') != session:
            failures.append('FRAME_EVALUATION_MISMATCH')
    if timeframe == 'daily' or not metadata_present:
        if frame_as_of != session:
            failures.append('FRAME_SESSION_MISMATCH')
        if close != current:
            failures.append('FRAME_CLOSE_MISMATCH')
    return tuple(dict.fromkeys(failures))


def frame_matches_price(frame, *, timeframe, frame_as_of, price, session):
    return not frame_price_failures(frame, timeframe=timeframe, frame_as_of=frame_as_of,
                                    price=price, session=session)
