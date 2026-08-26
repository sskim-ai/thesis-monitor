# Multi-Timeframe Evidence Packet

Contract: `multi-timeframe-price-structure-shadow-v2`.

The packet holds security/currency/current-price identity, adjusted-price basis, cutoff, canonical
hash, and independent monthly/weekly/daily slots. Slots contain confirmed pivot IDs and SR candidate
IDs, not raw OHLCV. Compact evidence retains all major pivots and meaningful zones.

Evidence source: `20260826-ai-fibonacci-multi-timeframe-shadow-evidence.json` (`SHA-256 b5a4b03bcbbe71b2baadc9058789f8e68f9db460fe6770daec7fa2ef16cedced`).


- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.
