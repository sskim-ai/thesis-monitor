# MACD D/W/M Contract

- Date: `2026-08-29 KST`
- Contract: `cross-market-ai-decision-engine-v1`
- User-visible production change: `0`

MACD uses completed closes, EMA 12 minus EMA 26, EMA 9 signal, and histogram. State combines MACD-vs-signal and zero-line position. The AI receives registered values/states and cannot calculate a cross itself. D/W/M availability follows each timeframe's minimum history.
