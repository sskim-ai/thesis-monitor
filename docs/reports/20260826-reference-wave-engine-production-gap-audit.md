# Reference Wave Engine Production Gap Audit

- Gap A: old reference depth `300/60/60` differs from canonical `1200/600/300`.
- Gap B: monthly Fib now keeps `source_timeframe=monthly`, source degree, and target timeframe.
- Gap C: monthly/weekly/daily maps are built independently before cross-timeframe confluence.
- Gap D: Fib ratios deduplicate by evidence family and method family for scoring.
- Gap E: bullish standard impulse only; no wave is forced when hard rules fail.
- Provider boundary: local `/ohlcv` independently fetches higher timeframes but caps `count` at
  `1000`, so daily 1200 is currently a documented material coverage gap.
- Reference archive: unavailable; instruction-derived contract only.
