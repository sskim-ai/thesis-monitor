# CPNG Feature Dependency Map

| Family | Kind | Window | Initialization |
| --- | --- | --- | --- |
| close/returns/range/drawdown/SMA/ROC/stochastic/Bollinger/volume ratio/CMF/MFI/Donchian | FINITE | TechnicalFeatureFact.minimum_history | - |
| EMA/MACD | RECURSIVE_FULL_HISTORY | all normalized history | SMA seed followed by recursive EMA |
| RSI/ATR/ADX/DMI | RECURSIVE_FULL_HISTORY | all normalized history | Wilder seed and smoothing |
| OBV | RECURSIVE_FULL_HISTORY | all normalized history | cumulative signed volume |

Implemented catalog: `returns`, `range_and_drawdown`, `trend`, `macd`, `momentum`, `volatility`, `directional`, `volume`, `breakout`. Every fact stores dependency start/end, bar count, and SHA-256.

`TECHNICAL_FEATURE_DEPENDENCY_REGISTRY = PASS`
