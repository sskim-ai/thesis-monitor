# Legacy Technical Prose Suppression

## Rule

When the current v3 section is active, an older or unsupported parallel OHLCV, RSI, MACD,
Bollinger, timeframe-regime, or free-form SR statement is `LEGACY_TECHNICAL_PROSE`. It is
suppressed from the candidate rather than refreshed by AI arithmetic.

A nonredundant indicator statement may remain only when its date equals the current completed
session and that session has canonical indicator evidence. Business, earnings, valuation, and
monitoring-rule prose are outside this suppression class.

Detection follows `legacy-technical-token-detection-v1`: semantic field first, complete token
second, freshness/redundancy third, sentence suppression last. Company identity, status lines, and
section headings are protected before lexical matching. Indicator acronyms attached to Korean
postpositions remain valid tokens; the same letters inside an ordinary word do not match.

## Clause Preservation

Suppression operates at sentence level. If a business sentence and a stale technical sentence
share a paragraph, the business sentence remains byte-equivalent after whitespace normalization.
No replacement indicator values are generated.

The policy records matched terms, spans, token-boundary classes, semantic fields, and suppression
reasons. This makes every removed sentence auditable without applying a free-form keyword scan to
the complete message.
