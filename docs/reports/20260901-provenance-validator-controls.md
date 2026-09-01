# Provenance Validator Controls

Positive structural-label controls:

- `Russell 2000은`
- `S&P500은`
- `KOSPI 200은`
- `KOSDAQ 150은`
- run-49 final normalized `Russell 2000이었습니다`

All remain structural labels and do not create free numeric claims.

Negative controls:

- unsupported `2000`
- unsupported `$2000`
- unsupported `2,000`
- unsupported `2000%`

All remain visible to numeric provenance. Exact diagnostics identify the `2000` span and
`visible_numeric_literal_v2` rule.

`REAL_UNSUPPORTED_2000_REJECTED = PASS`

`MARKET_CONTEXT_PROVENANCE_DISABLED = 0`
