# Fibonacci Per-Timeframe Numeric Provenance

Backend formulas use Decimal arithmetic and six-decimal half-up rounding. Every level has timeframe,
ratio, mode, anchor refs, formula, calculation version, currency, adjusted-price basis, as-of, and a
deterministic level ID.

`AI_CALCULATED_FIB_PRICE = 0`; `UNREGISTERED_FIBONACCI_NUMERIC = 0`; anchor price/date/ticker
mismatches are all `0`.


- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.


Exact benchmark calculations are in
`20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md` and the canonical JSON evidence.
