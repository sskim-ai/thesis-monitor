# Track A — KR Daily OHLCV Zero Root Cause + Repair

## Objective

Explain and repair why all seven KR Price Structure controls requested daily 1200 bars but received 0.

Trace:

```text
request
→ canonical OHLCV service
→ provider/cache
→ raw rows
→ completed-bar filter
→ coverage
```

Compare with the previously passing canonical 1200-bar KR path.

Do not synthesize daily data from weekly/monthly.

## Hard gates

```text
DAILY_ZERO_ROOT_CAUSE = PASS
UNEXPLAINED_DAILY_ZERO = 0
SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_WEEKLY_MONTHLY = 0
UNVERIFIED_DAILY_PROVIDER_FALLBACK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
LOOKAHEAD_LEAK = 0
```

Use 000660, 003690, 005490, 005930, 010120, 012450, 086280 as regression controls.
