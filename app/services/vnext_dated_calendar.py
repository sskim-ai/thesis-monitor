"""Opt-in KRX regular-session correction; legacy calendar replay stays unchanged."""
from functools import lru_cache

import pandas as pd
from exchange_calendars.exchange_calendar_xkrx import XKRXExchangeCalendar

from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range

POLICY = 'krx-2026-official-dated-calendar-v1'
SOURCE_URL = 'https://open.krx.co.kr/contents/MKD/01/0110/01100305/MKD01100305.jsp'
VISIBLE_TABLE_SHA256 = 'aca8f7f5bda7140ebb3519173805d856c2602f7ccd1879b66414826758730d2c'
EXTRA_HOLIDAYS = ('2026-06-03', '2026-07-17')


class _OfficialKRX2026(XKRXExchangeCalendar):
    @property
    def adhoc_holidays(self):
        return pd.DatetimeIndex(super().adhoc_holidays).union(pd.DatetimeIndex(EXTRA_HOLIDAYS)).tolist()


@lru_cache(maxsize=32)
def _corrected(start, end):
    from datetime import timedelta
    return _OfficialKRX2026(start=start-timedelta(days=370), end=end+timedelta(days=370))


def calendar_for_range(market, *, start, end, policy=None):
    if policy not in (None, POLICY):
        raise ValueError('dated_calendar_policy_unknown')
    if policy == POLICY and market == 'KR':
        return 'XKRX', _corrected(start, end)
    return _calendar_for_range(market, start=start, end=end)
