# Track C — Numeric Provenance `:2000` False-Positive Repair

Reproduce run-49:
`numbers_without_provenance:market_context.text:2000`

Find the exact lexer/normalization/span rule that created the phantom value.

Do NOT:
- allowlist 2000
- disable market-context provenance
- weaken unsupported-number rejection

Validator must expose:
raw text, normalized token, parsed numeric, character span, field, matching rule.

Controls:
- real unsupported 2000 must FAIL
- no literal 2000 must not produce 2000
- S&P500 / 10년물 / supported percentages must not create phantom tokens
- validator and renderer must operate on the same final candidate state
