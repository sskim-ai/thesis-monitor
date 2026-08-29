# OHLCV Feature Catalog

- Date: `2026-08-29 KST`
- Contract: `cross-market-ai-decision-engine-v1`
- User-visible production change: `0`

The catalog and formulas are fixed in `ohlcv-multi-timeframe-feature-engine-v1`. Daily 1,200 is capped at 1,000 by the provider and reported as `PARTIAL_SAFE`.

| Family | Semantics | Availability |
|---|---|---|
| returns | return_1, return_5, return_10, return_20, return_60, return_120, return_252 | price bars |
| range_and_drawdown | rolling_high_{20,60,120,252}, rolling_low_{20,60,120,252}, distance_from_high, distance_from_low, max_drawdown, trend_sequence_20 | price bars |
| trend | sma_{5,10,20,50,100,200}, ema_{5,10,20,50,100,200}, close_vs_sma | price bars |
| macd | macd_12_26, macd_signal_9, macd_histogram, macd_state | price bars |
| momentum | rsi_14, roc_{10,20}, stochastic_k_14, stochastic_d_3 | price bars |
| volatility | atr_14, atr_pct_14, realized_volatility_20, gap_latest, bollinger_20_2 | price bars |
| directional | adx_14, plus_di_14, minus_di_14, dmi_state | price bars |
| volume | volume_ratio_20, obv, cmf_20, mfi_14 | requires_valid_volume |
| breakout | donchian_high_20, donchian_low_20, donchian_breakout_20 | price bars |
