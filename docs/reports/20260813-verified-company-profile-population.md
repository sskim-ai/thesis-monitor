# Verified Company Profile Population Validation

## Scope

- Repository: `sskim-ai/thesis-monitor`
- Branch: `main`
- Base: `c7a24296e3ed1bbdc04b7140ec9464cb5077fa64`
- Database migration: none
- Public Action schema: unchanged (`0.4.5`, 20 operationIds)
- GitHub Actions: pending at report creation

## Active Universe

The active universe was discovered from `WatchlistItem.active`; no expected count was encoded.

| Market | Active |
| --- | ---: |
| US/foreign | 13 |
| KR | 7 |
| Total | 20 |

Before population, all 20 active Company rows had empty `industry`, `sector`, `business_units`, and
`revenue_sources`. The production population run completed with 20 verified profiles, zero partial,
zero ambiguous, and zero unavailable profiles.

## Sources And Storage

- KR: OpenDART official company identity and industry code.
- US/foreign SEC registrants: SEC company-ticker identity plus submissions SIC classification.
- Normalization: generic KSIC/SIC prefix rules; no ticker-specific override.
- Company values: existing `Company.industry` and `Company.sector` columns.
- Provenance: atomic JSON sidecars under `data/company_profile_provenance` with source, source date,
  verification time, official code/description, normalization method, quality, reason, and taxonomy.
- Existing populated values are preserved when an official source is temporarily unavailable.
- No business unit, revenue mix, or dominant-segment share was inferred when the official source did
  not provide one.

## Population And Routing

| Ticker | Company | Official normalized industry | Primary framework | Secondary | Confidence | Quality | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 000660 | SK하이닉스 | Semiconductors | semiconductor | - | high | verified | OpenDART |
| 003690 | 코리안리 | Insurance and Reinsurance | insurance/reinsurance | - | high | verified | OpenDART |
| 005490 | POSCO홀딩스 | Steel Manufacturing | general | - | low | verified | OpenDART |
| 005930 | 삼성전자 | Communications Equipment | general | - | low | verified | OpenDART |
| 010120 | LS일렉트릭 | Electrical Equipment | general | hyperscaler CAPEX | low | verified | OpenDART |
| 012450 | 한화에어로스페이스 | Aerospace Manufacturing | general | - | low | verified | OpenDART |
| 086280 | 현대글로비스 | Transportation and Logistics | shipping/transport | - | high | verified | OpenDART |
| CORZ | Core Scientific | Financial Services | general | hyperscaler CAPEX | low | verified | SEC |
| CRCL | Circle Internet Group | Financial Services | general | - | low | verified | SEC |
| GOOGL | Alphabet Class A | Information Technology Services | general | - | low | verified | SEC |
| HUT | Hut 8 | Financial Services | general | hyperscaler CAPEX | low | verified | SEC |
| IBM | IBM | Computer and Office Equipment | general | - | low | verified | SEC |
| MU | Micron Technology | Semiconductors | semiconductor | - | high | verified | SEC |
| RXRX | Recursion Pharmaceuticals | Biotechnology and Pharmaceuticals | biotech | - | high | verified | SEC |
| SKHY | SK hynix ADR | Semiconductors | semiconductor | - | high | verified | SEC |
| SNDK | SanDisk | Computer Storage Devices | general | hyperscaler CAPEX | low | verified | SEC |
| TSLA | Tesla | Automotive | automotive | consumer | high | verified | SEC |
| TSM | TSMC | Semiconductors | semiconductor | hyperscaler CAPEX | high | verified | SEC |
| WRD | WeRide | Information Technology Services | general | - | low | verified | SEC |
| WULF | TeraWulf | Financial Services | general | hyperscaler CAPEX | low | verified | SEC |

Result: 8 specialized primary routes and 12 verified general routes. General routing reflects a
Knowledge-v3 taxonomy boundary or broad official classification, not an empty profile. Thesis themes
remain secondary and do not replace company identity.

## Read-Path Smoke

The existing `getCompanyProfile` service returned the populated structured identity without a public
schema change for representative KR and US names. Example checks returned Semiconductors/Technology
for both a KR issuer and a US issuer, and Insurance and Reinsurance/Financials for a KR insurer.

## Safety

- No ticker-specific production classification exists.
- The active count is queried dynamically.
- Ambiguous official descriptions remain `ambiguous` and route to general.
- Source failure is recorded, not converted to an inferred industry.
- News and thesis text cannot change the company profile.
