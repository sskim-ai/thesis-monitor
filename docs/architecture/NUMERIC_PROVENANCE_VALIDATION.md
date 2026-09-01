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

Canonical product, model, index, and security identifiers may also contain digits. The validator
classifies the complete token as an identifier only when that exact visible span is owned by
canonical evidence or a structured registry entry. It then masks only the identifier's character
span before numeric extraction. This keeps `KF-21` and `FA-50` from producing phantom `21` and `50`
claims while still validating an adjacent quantity such as `KF-21 10대`.

Shape alone never grants an exemption. An invented `ZZ-999`, a plain `21-50` range, `-21%`, and
`$-50` remain ordinary numeric claims unless their numbers bind through the existing provenance
contract. Identifier diagnostics retain the full span, identifier type, canonical source,
fact/reference ID when available, and character span.

## Run-49 Finding

The raw AI candidate did not contain `2000`. Ownership normalization inserted the canonical market
sentence containing `Russell 2000이었습니다`. The former trailing `\b` saw the Hangul particle as a
word character and misclassified the label's number. The repaired lexer recognizes the full index
label and reports zero phantom numeric claims.

## Run-50 Finding

The KR run-50 legacy candidate used canonical Hanwha Aerospace model identifiers `KF-21` and
`FA-50`. The previous lexer removed neither identifier span and emitted their suffixes as unsupported
numeric claims. The canonical-identifier boundary now recognizes the evidence-owned full tokens;
the frozen replay reports zero identifier-derived numeric errors without weakening the independent
000660 valuation-quality or 005930 risk/reward controls.
