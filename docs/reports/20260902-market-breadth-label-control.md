# Market Breadth Label Control

The first frozen candidate authored `KOSPI/KOSDAQ 상승 종목 비율` immediately before two numeric
placeholders. The numeric binder also owns the approved `상승 종목 비율` label, so both references
were correctly rejected as duplicate authored labels.

The ownership normalizer now removes only the matching approved label and particle before a
`market_advance_ratio` placeholder. `KOSPI`/`KOSDAQ`, the placeholder, fact declaration, value, and
interpretation remain. The binder then renders the canonical label and number once.

`MARKET_BREADTH_AUTHORED_LABEL_CONFLICT = 0`

