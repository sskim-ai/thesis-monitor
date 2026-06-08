from datetime import date, timedelta


def lookback_cutoff(lookback_days: int) -> date:
    return date.today() - timedelta(days=lookback_days)

