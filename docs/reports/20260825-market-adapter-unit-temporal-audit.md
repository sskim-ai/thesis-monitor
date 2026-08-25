# Market Adapter Unit and Temporal Audit

## Unit Gates

- KR market-wide flow accepts KRW monetary amounts only.
- Stock quantity and market monetary flow are never combined.
- US foreign/institution/retail flow is rejected as unsupported.
- Concentration and relative relations preserve unit, scope, date, formula, and input refs.
- Unit conflicts observed in immutable replays: `0`.

## Temporal Gates

- Fact `as_of_date` is mandatory; missing dates are suppressed.
- Facts after the assessment date are suppressed.
- Cross-section market, session date, and timezone-aware `as_of <= cutoff` are mandatory.
- Session normalization uses the existing XKRX/XNYS calendar service.
- A 16:05 ET event fails regular-session causality and is eligible only for after-hours context.
- Temporal errors observed in immutable replays: `0`.

Focused negative controls cover future Facts, missing identities/dates, cross-market sections,
post-cutoff sections, wrong arithmetic, wrong KR units, and invented US participant flow.

