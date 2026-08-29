# OHLCV Multi-Timeframe Feature Engine

Contract: `ohlcv-multi-timeframe-feature-engine-v1`.

Only completed daily, weekly, and monthly bars at or before the explicit cutoff are eligible. Explicit provisional bars are excluded. Every feature carries a deterministic Fact ID, timeframe, formula, minimum history, as-of date, adjustment basis, and source SHA.

The requested windows are daily 1,200, weekly 600, and monthly 300. The current provider request cap is 1,000, so daily coverage is explicitly `PARTIAL`; missing history is never synthesized.

Implemented families: returns, rolling range/drawdown, SMA/EMA, MACD 12/26/9, RSI, ATR/volatility/gap, standard Bollinger 20/2, ADX/DMI, ROC/stochastic, volume ratio/OBV/CMF/MFI, and Donchian breakouts. Existing Price Structure and dynamic Bollinger layers remain separate canonical owners.
