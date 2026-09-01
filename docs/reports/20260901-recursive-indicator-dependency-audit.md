# Recursive Indicator Dependency Audit

EMA/MACD use SMA-seeded recursion; RSI/ATR/ADX/DMI use Wilder seeds and smoothing; OBV is cumulative. Their exact current output depends on all supplied normalized history. No finite warmup equivalence was introduced.

`RECURSIVE_INDICATOR_HISTORY_APPROXIMATED_AS_SAFE = 0`
