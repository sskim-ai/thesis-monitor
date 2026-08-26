# Existing Fibonacci Path Audit v2

`EXISTING_FIBONACCI_PATH = COMPUTED_NOT_RENDERED`.

The current engine chooses one weekly-primary/daily-fallback major anchor family and calculates
retracement/extension sets. Those facts are retained in packet/chart context, but recent generated
message prose does not own or display Fibonacci labels. Monthly swings can confirm structure but do
not receive an independent Fibonacci set.

The v2 shadow contract does not replace this production path. It computes independent monthly,
weekly, and daily sets after same-timeframe ID validation. Selected prose levels pass the value gate;
calculation availability alone does not force rendering.


- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.
