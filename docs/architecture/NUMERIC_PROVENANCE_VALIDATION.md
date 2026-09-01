# Numeric Provenance Validation

Contract: `numeric-provenance-validation-v2`

## Validated Text

Numeric provenance validates the exact post-normalization, post-ownership text that the renderer
would expose. Correction diagnostics use that same bound output and include path, literal token,
numeric value, character span, matched rule, and binding attempts.

## Structural Numerics

Known index names such as `Russell 2000` are structural labels, not standalone quantitative claims.
Their boundaries use ASCII-aware lookarounds so a Korean particle immediately after the label does
not defeat classification. This is a grammar fix, not a ticker/value allowlist.

Unsupported standalone `2000` remains rejectable. Market-context provenance remains enabled, and
all genuine quantitative claims still require canonical binding.

## Run-49 Finding

The raw AI candidate did not contain `2000`. Ownership normalization inserted the canonical market
sentence containing `Russell 2000이었습니다`. The former trailing `\b` saw the Hangul particle as a
word character and misclassified the label's number. The repaired lexer recognizes the full index
label and reports zero phantom numeric claims.
