# Multi-Timeframe Pivot Contract

Each pivot ID binds ticker, timeframe, kind, pivot date, confirmation date, canonical price, and
adjustment basis. Completed adjusted bars are used; `confirmed_at > cutoff` is excluded. A low/high
pair requires same timeframe, `low.date < high.date`, and `low.price < high.price`. An extension
correction is a later low above the selected low.

Invalid selection in one timeframe fails that slot closed and leaves independent slots available.
No weekly pivot can be relabeled monthly or daily.


- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.
