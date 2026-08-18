# Phase 8.3.1 US Provider Matrix

Date/accessed: `2026-08-18`
Evidence policy: official product, API, pricing, and license pages only

## Institutional Matrix

| Provider | Coverage/taxonomy | Valuation/forward | PIT/history | Identity/ADR | Price/license | Verdict |
|---|---|---|---|---|---|---|
| S&P Global MI | Compustat 80k+ active/inactive; CIQ Financials 180k; classifications | CIQ Estimates 60k, ratios/multiples | Compustat PIT since 1987; estimate change snapshots | broad identifiers and entity/security data; ADR ratio still entitlement-test item | contact sales; negotiated display/AI rights | `BEST_INSTITUTIONAL_PIT_FIT` |
| FactSet | 59k companies, 19k active estimate coverage, classifications | detailed consensus, actuals, guidance, fixed/rolling forward periods | estimate history since 1999 and PIT products | permanent/regional/listing/entity IDs; ADR ratio POC required | contact sales; negotiated rights | `BEST_TECHNICAL_API_FIT` |
| LSEG | Worldscope 55.6k active + 45.3k inactive across 125 markets | I/B/E/S consensus across 22k active companies | PIT packages with daily/weekly/monthly point dates | broad global identifiers; per-ADR proof required | contact sales; negotiated rights | strong institutional shortlist |
| Bloomberg Data License | 70m instruments, 40k fields, 8k datasets | fundamentals, estimates, pricing | historical/PIT products and bulk delivery | strong instrument/reference hierarchy; entitlement POC required | institutional/contact; redistribution contract required | technically strong, highest complexity |
| Morningstar Direct Web Services | APIs over 300k investments; equity data/research | investment details and equity data; exact consensus/PIT scope not proven publicly | exact peer PIT contract unclear | Morningstar security IDs; ADR ratio unclear | contact sales; client-facing APIs available by contract | secondary institutional research |

## Cost-Aware Matrix

| Provider | Strength | Hard gap | License/cost signal | Verdict |
|---|---|---|---|---|
| Intrinio | 15+ years US fundamentals, filing/calculation timestamps, ADR coverage; Zacks estimate add-ons | exact issuer hierarchy and ADR ratio need POC; estimates are enterprise add-ons | Individual $150/mo prohibits display; Startup $333+/mo; AI/customer use needs rights | `BEST_US_COST_BENEFIT_CONDITIONAL` |
| Tiingo | 5,500+ US/ADR, 20+ years, daily PE/PB, filing release date, permaTicker, delisted status | no official consensus; ADR ratio/issuer relation absent | $0/$30 individual; business/redistribution contact | good trailing/PIT-reconstructable component |
| Nasdaq Data Link Sharadar + Zacks | filing fundamentals and separate estimates products | dataset-specific PIT, join, ADR basis, pricing and display rights must be verified | premium/order-form license | split-feed research candidate |
| FMP | broad profiles, CIK/ISIN/CUSIP, SIC/industry, ratios and analyst estimates | true PIT/restatement snapshots, estimate revisions, issuer hierarchy and ADR ratio unproven | low published tiers; display/redistribution requires special license | low-cost POC only |
| Massive | strong US reference, CIK/FIGI/SIC, prices, statements; latest TTM ratios | ratios are most-recent-day only; no broad consensus; filing endpoint may reflect later filing/restatement | low individual add-on; business rights separate | keep as price/reference supplemental |
| Finnhub | broad current metrics and estimates products | payload probe lacked exact as-of/forward basis; TSM mapped to `2330.TW`; ADR ratio absent | all-in-one commercial tier expensive; rights require review | not primary without basis/PIT proof |
| SimFin | 5,000 US stocks, 20+ years, statements/daily ratios | no consensus; PIT/restatement and security hierarchy partial | free/paid; commercial license available | fundamentals research component |
| Alpha Vantage | overview identity/taxonomy/current valuation; estimate endpoint | no true PIT; live MU estimates empty; issuer/ADR basis weak | free 25/day and paid; commercial use requires contact | narrow supplement only |
| OpenFIGI + SEC | share-class FIGI and authoritative CIK/filings | no valuation, consensus, issuer hierarchy, or ADR ratio | free/public APIs subject to terms | identity/filing auxiliaries only |

## Mandatory Fixture Findings

- MU: Finnhub live fields include trailing and forward metrics but no payload-level as-of; not safe
  point-in-time evidence. Alpha current Overview lacks an explicit as-of, and its MU estimate list was
  empty in this entitlement.
- TSM: Finnhub returned underlying symbol `2330.TW` for the US ticker request and no ADR ratio. OpenFIGI
  supplied security/share-class IDs but no issuer ID or depositary ratio. `SECURITY_BASIS_PARTIAL`
  remains correct.
- TSLA and GOOGL: broad coverage is plausible but unmeasured; GOOG/GOOGL issuer dedup requires an
  issuer hierarchy rather than ticker similarity.
- RXRX: even a valid multiple does not enable biotech PER attractiveness.
- CORZ/HUT/WULF: negative denominator and infrastructure-framework guardrails remain active.

## Official Evidence

- S&P fundamentals/PIT/estimates: <https://www.spglobal.com/market-intelligence/en/solutions/products/fundamental-data>
- S&P API developer guide: <https://www.support.marketplace.spglobal.com/content/dam/spglobal/mi/en/documents/marketplace/api/guides/spglobalapidevelopersguide.pdf>
- FactSet Estimates API: <https://developer.factset.com/api-catalog/factset-estimates-api>
- FactSet classifications: <https://developer.factset.com/api-catalog/classifications-api>
- FactSet PIT paper: <https://insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf?hsLang=en-us>
- LSEG company fundamentals: <https://developers.lseg.com/en/api-catalog/daas/DaaS/Products/CompanyFundamentalsViaDaaS>
- LSEG fundamentals/estimates: <https://developers.lseg.com/en/article-catalog/article/fundamentals-estimates-dcf>
- LSEG quant/PIT brochure: <https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/data-for-quant-research-brochure.pdf>
- Bloomberg Data License: <https://professional.bloomberg.com/products/data/data-management/data-license/>
- Morningstar Direct Web Services: <https://developer.morningstar.com/direct-web-services>
- Morningstar licensed research/data: <https://www.morningstar.com/business/products/licensed-research>
- Intrinio pricing and rights: <https://intrinio.com/pricing>
- Intrinio US fundamentals: <https://intrinio.com/products/us-fundamentals>
- Intrinio fundamental timestamps: <https://data.intrinio.com/documentation/web_api/filter_fundamental_v2>
- Intrinio terms: <https://docs.intrinio.com/terms>
- Tiingo fundamentals: <https://www.tiingo.com/documentation/fundamentals>
- Tiingo pricing and terms: <https://www.tiingo.com/pricing>, <https://api.tiingo.com/tos/>
- FMP docs/pricing: <https://site.financialmodelingprep.com/developer/docs/stable>, <https://site.financialmodelingprep.com/developer/docs/pricing/>
- Massive stock/reference overview: <https://massive.com/docs/rest/stocks>
- Massive ratios: <https://massive.com/docs/rest/stocks/fundamentals/ratios>
- Nasdaq Data Link data organization: <https://docs.data.nasdaq.com/v1.0/docs/data-organization>
- SimFin fundamentals: <https://www.simfin.com/en/fundamental-data-download/>
- Alpha Vantage docs/terms: <https://www.alphavantage.co/documentation/>, <https://www.alphavantage.co/terms_of_service/>
- Finnhub pricing/API: <https://api.finnhub.io/pricing>, <https://finnhub.io/docs/api>
- OpenFIGI API: <https://www.openfigi.com/api/documentation>
- SEC EDGAR APIs: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>

## US Recommendation

1. `BEST TECHNICAL FIT`: FactSet, conditional on entitlement-specific ADR and display rights.
2. `BEST INSTITUTIONAL PIT`: S&P Global MI, especially where backtest integrity is mandatory.
3. `BEST COST/BENEFIT, CONDITIONAL`: Intrinio commercial/startup plus estimate entitlements.

LSEG is a credible institutional alternative. Bloomberg is technically strong but has the greatest
cost and integration complexity. No US provider is approved for integration in this phase.
