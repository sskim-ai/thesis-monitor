# Phase 8.3 Peer / Sector Valuation Capability

## Decision

Phase 8.3 extends the existing active-monitoring peer foundation; it does not create a broad sector
database. The 2026-08-18 immutable operating archive contains 20 final assessments, but no subject
has a `MEDIUM` or `HIGH` peer metric after taxonomy, issuer, date, denominator and security-basis
checks. User-visible peer statistics remain suppressed.

## Capability Matrix

| Market | Provider/source | Universe | PER | PBR | Forward | Point-in-time | Security basis | Historical | Suitability |
|---|---|---|---|---|---|---|---|---|---|
| KR | OpenDART-derived valuation snapshots | 7 monitored issuers | 5 value, 2 unavailable | 5 value, 2 unavailable | 3 modeled fPER/fPBR values | exact stored price session | direct for 5; insufficient for 2 | assessment snapshots only | PARTIAL |
| US | SEC-derived denominators + Finnhub/Alpha Vantage references | 13 monitored issuers | 8 value, 5 not meaningful/missing | 13 values, with ADR basis exclusions | 9 consensus fPER values; denominator/basis often partial | exact stored price session | safe domestic common shares only; TSM/SKHY/WRD unsafe for selected multiples | assessment snapshots only | PARTIAL |
| US | Massive | broad price/reference universe | unsupported | unsupported | unsupported | price/reference only | security reference only | market price cache | NOT A VALUATION PROVIDER |
| KR | KRX Open API | broad market/breadth development | not used | not used | unsupported | publication timing under observation | market identity only | historical breadth PASS | NOT A PEER VALUATION PROVIDER |

No current source provides a broad, economically classified, point-in-time KR or US peer multiple
universe. A new provider is optional future work, not silently substituted in this phase.

## Snapshot Coverage

The audit observed:

- trailing PER: 13 value, 5 not meaningful, 2 unavailable;
- PBR: 18 value, 2 unavailable;
- forward PER: 9 consensus values, 3 modeled values, 3 modeled not meaningful, and remaining bases
  unavailable/not selected;
- forward PBR: 5 modeled values and no consensus cross-section.

Raw availability is not peer eligibility. Same-session date, positive denominator, share basis,
issuer deduplication, comparable taxonomy and minimum sample still apply.

## Active-Universe Result

| Segment | Subjects | User-visible peer states | Result |
|---|---:|---:|---|
| KR | 7 | 0 | no subject reaches three comparable same-market issuers |
| US | 13 | 0 | broad sector fallback is LOW; narrower clean samples remain below three |
| Total | 20 | 0 | fail-closed suppression |

US finance-services candidates form a three-row official-description group, but clean P/E and P/B
samples fall below three after negative EPS/equity and missing denominator exclusions. Technology
candidates can form a six-row sector sample, but sector fallback is deliberately audit-only because
semiconductor, storage, IT services, and office equipment are not one economic peer group.

## Contract Added

- `peer-sector-valuation-v1` and `verified-profile-peers-v2`;
- taxonomy -> sub-industry -> industry -> sector hierarchy;
- same exchange-session alignment using subject `price_as_of`;
- canonical issuer deduplication when identity provenance is reliable;
- separate trailing, consensus-forward, and modeled-forward distributions;
- median, quartiles, IQR, range, relative multiple, premium/discount and peer percentile;
- `HIGH`/`MEDIUM`/`LOW` quality with LOW user-facing suppression;
- industry interpretation contract and no automatic cheap/expensive verdict;
- new exact numeric semantics for peer relative multiple and peer cross-sectional percentile.

## Provider Recommendation

A future broad provider must supply issuer/security identity, verified taxonomy, point-in-time PER and
PBR, denominator period, as-of date, share/ADR basis, source provenance, and historical availability.
Forward consensus requires explicit estimate basis and period. Cost and rate limit should be reviewed
before any subscription; this phase makes no purchase or provider integration.

## Status

Engineering contract: `PASS`

Data capability: `STRONG PARTIAL`

Operating integration: `NO`

Telegram / Pilot / Scheduled Task mutation: `0 / 0 / 0`

