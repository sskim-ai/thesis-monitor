# Legacy Technical Token Detection

## Contract

`legacy-technical-token-detection-v1` recognizes technical terms only as complete lexical tokens.
The renderer first identifies a semantic field, then recognizes a token, then applies the existing
freshness and redundancy rule. A substring inside an ordinary word is never sufficient.

ASCII acronyms (`RSI`, `MACD`, `OHLCV`, `ATR`, `EMA`, and `SMA`) require a non-ASCII-word start and
may be followed by whitespace, punctuation, a number, end of text, or a Korean suffix. `Bollinger`
uses an English word boundary with the same Korean-suffix allowance. Existing Korean technical
terms retain exact phrase matching.

Thus `RSI가`, `MACD가`, and `OHLCV를` are valid, while `Recursion`, `conversion`, `precision`, and
`macdonald` are not. Every accepted match retains the matched text, span, boundary class, and
semantic field for audit.

## Isolation

The contract changes only the archive/test renderer classifier. It does not calculate an
indicator, SR, Fib, price, or business fact and is not imported by production delivery.
