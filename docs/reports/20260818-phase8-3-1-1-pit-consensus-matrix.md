# Phase 8.3.1.1 Point-In-Time And Consensus Matrix

Date/accessed: `2026-08-18`

| Provider/product | Fundamentals class | Restatement behavior | Consensus class | Required metadata | Result |
|---|---|---|---|---|---|
| S&P Compustat/CIQ PIT | `TRUE_POINT_IN_TIME` for entitled snapshot products | preserved as-known snapshots documented | CIQ Estimates Snapshot is `TRUE_POINT_IN_TIME` since Aug 2016 | effective/to dates, period, currency, estimate details | technical pass, entitlement conditional |
| FactSet Fundamentals PIT | `TRUE_POINT_IN_TIME`, separate feed since 1999 | product states data as it appeared and incorporates known restatement timing | FactSet PIT consensus is `TRUE_POINT_IN_TIME`; standard Estimates is not equivalent | local-market snapshot date, FY/FQ, currency, estimate count | technical pass, product-specific entitlement |
| LSEG Worldscope/Standardised PIT | `TRUE_POINT_IN_TIME`, add-on | point date reflects source/feed availability | I/B/E/S PIT daily snapshots; historical series alone is distinct | timestamp array, period, estimate count, currency | technical pass, entitlement conditional |
| FnSpace | `HISTORICAL_SERIES`; true as-known/restatement behavior `UNKNOWN` | not established publicly | daily/fiscal estimated results and forward fields documented, but immutable estimate snapshots unproven | estimate effective date, fiscal period, analyst count, currency | partial |
| DeepSearch | `HISTORICAL_LATEST_RESTATED` or `UNKNOWN`; public docs do not distinguish | unknown | target-price observations have dates; EPS consensus snapshot history unproven | revision/effective timestamp and denominator metadata absent publicly | partial/unknown |
| Intrinio fundamentals | `POINT_IN_TIME_RECONSTRUCTABLE` | filing, update, first-calculable, earnings-disclosure timestamps and signatures exposed; no vendor snapshot guarantee | Zacks EPS history/revisions are enterprise-only; exact as-known snapshot contract pending | estimate date, fiscal period, count, currency, history entitlement | conditional |

## Contract Notes

- `historical` never means `TRUE_POINT_IN_TIME` by itself.
- S&P, FactSet, and LSEG PIT results apply only to the named PIT products, not every desktop/API field.
- Intrinio exposes enough filing/change timestamps to reconstruct an as-known fundamental set after
  an exact POC, but later standardized revisions must be replayed rather than assumed away.
- FnSpace and DeepSearch remain unsuitable for historical backtests until restatement and estimate
  revision behavior is answered in writing.
- FY1, NTM, calendar year, modeled forward, and consensus forward remain separate distributions.

## Evidence

- [S&P fundamental/PIT stack](https://www.spglobal.com/market-intelligence/en/solutions/products/fundamental-data)
- [S&P Capital IQ Estimates Snapshot](https://www.spglobal.com/market-intelligence/en/solutions/capital-iq-estimates)
- [FactSet Fundamentals PIT product](https://www.factset.com/marketplace/catalog/product/factset-fundamentals-point-in-time)
- [FactSet PIT consensus methodology](https://insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf?hsLang=en-us)
- [FactSet Estimates API and inputDateTime history](https://developer.factset.com/api-catalog/factset-estimates-api)
- [LSEG quant/PIT product guide](https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/data-for-quant-research-brochure.pdf)
- [LSEG FY1 estimate field example](https://developers.lseg.com/en/article-catalog/article/fundamentals-estimates-dcf)
- [FnSpace service/data schedule](https://www.fnspace.com/Customer/Info)
- [DeepSearch dated target-price history](https://help.deepsearch.com/dp/api/func/company/consensus/searchtargetprices)
- [DeepSearch historical market multiples](https://help.deepsearch.com/dp/api/data/market)
- [Intrinio fundamental timestamps](https://data.intrinio.com/documentation/web_api/filter_fundamental_v2)
- [Intrinio EPS estimate history](https://intrinio.com/products/eps-estimates)
