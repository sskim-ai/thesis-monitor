# Legacy Technical Prose Suppression

## Rule

When the current v3 section is active, an older or unsupported parallel OHLCV, RSI, MACD,
Bollinger, timeframe-regime, or free-form SR statement is `LEGACY_TECHNICAL_PROSE`. It is
suppressed from the candidate rather than refreshed by AI arithmetic.

A nonredundant indicator statement may remain only when its date equals the current completed
session and that session has canonical indicator evidence. Business, earnings, valuation, and
monitoring-rule prose are outside this suppression class.

## Clause Preservation

Suppression operates at sentence level. If a business sentence and a stale technical sentence
share a paragraph, the business sentence remains byte-equivalent after whitespace normalization.
No replacement indicator values are generated.
