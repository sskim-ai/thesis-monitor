# User Reference Wave Engine Audit

`codex_stock_wave_engine(1).zip` was not present in the supplied Codex attachment or repository.
Per the instruction boundary, no unseen source code was invented or staged. This audit uses only the
source-derived contract quoted in the exact instruction.

- Reference zone lookback: `300/60/60`; v3 override: `1200/600/300`.
- Reference pivots: daily `3/3`, weekly `2/2`, monthly `2/2`.
- Grouping: daily `1.75%`, weekly `2.25%`, monthly `3.00%`.
- Adaptive tolerance: `max(price * grouping_pct, ATR14 * 0.50)`.
- Padding: `min(ATR14 * 0.10, center * 0.01)`.
- Reference SK hynix state: W4 candidate / W5 unconfirmed.
- Families: wave1, wave3, primary-cycle, current rebound, W5 projection.
- Reference zone model: pivot + Bollinger + Fibonacci, with balance boxes separate.

`USER_REFERENCE_ENGINE_AUDIT = PASS` means the available-source boundary and quoted contract were
audited; it does not claim byte-level review of the unavailable reference source.
