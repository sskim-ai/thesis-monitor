# Phase 8.3.1.1 Peer Provider Decision

Date/accessed: `2026-08-18`
Status: `DECISION RESEARCH PASS / NO PROVIDER SELECTED / NO INTEGRATION`

## Decision

No provider currently clears the Phase 8.3.2 hard gate. The technical shortlist remains valid, but
public documents do not grant the exact combination of Telegram derived-display, external LLM
processing, persistent storage, required fields, and entitlement-specific coverage.

Overall entry-gate result: `BLOCKED_ON_PROVIDER_DECISION`.

This is not a calculation blocker. `peer-sector-valuation-v1` remains `PASS`, and measured visible
coverage remains `0/20` because the repository correctly suppresses incomplete samples.

## Mandatory Decision Table

| Provider | Market | Universe | Taxonomy | Current PER/PBR | PIT fundamentals | Consensus history | ADR basis | Issuer dedup | User display rights | AI rights | Storage rights | Cost band | Complexity | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S&P Global MI | global | strong product claim | strong | supported by entitled datasets | `TRUE_POINT_IN_TIME`, product-specific | PIT snapshot available | issuer/security strong; ratio POC required | supported | vendor contract required | LLM-ready products exist; exact use contract required | contract required | institutional/contact | medium-high | `CONDITIONAL` |
| FactSet | global | strong | strong | supported | `TRUE_POINT_IN_TIME`, separate PIT feed | `TRUE_POINT_IN_TIME`, separate PIT consensus | entity/security/listing IDs strong; ratio POC required | supported | client-facing APIs exist; exact publication rights required | FactSet AI exists; external model/output rights require contract | contract required | institutional/contact | medium | `CONDITIONAL` |
| LSEG | global | strong | strong | supported | `TRUE_POINT_IN_TIME`, add-on | I/B/E/S PIT daily snapshots | security coverage strong; per-ADR denominator POC required | likely; entitlement POC | redistribution and derived output require license | AI/client output is redistribution; license required | contract required | institutional/contact | high | `CONDITIONAL` |
| FnGuide FnSpace | KR | strong KR product claim | partial/strong KR | supported | restatement/PIT model unproven | fiscal/daily estimates and forward data documented | KR share-class/basis POC required | company/ticker relation partial | standard terms prohibit app/customer/third-party display | standard rights do not authorize external AI output | standard terms prohibit DB construction | published mid-tier | low | `BLOCKED_BY_LICENSE` |
| DeepSearch | KR | broad KR | stable industry IDs available | historical PER/PBR documented | `UNKNOWN` | target-price history only; EPS consensus PIT unproven | share basis unknown | company IDs available | `UNKNOWN_REQUIRES_VENDOR_CONFIRMATION` | `UNKNOWN_REQUIRES_VENDOR_CONFIRMATION` | unknown | unknown/contact | medium | `CONDITIONAL` |
| Intrinio | US | broad US/ADR product claim | sector/industry available | supported | `POINT_IN_TIME_RECONSTRUCTABLE`, not proven snapshot | 20+ year Zacks history, enterprise-only; exact snapshot contract pending | security-company IDs/share class present; ADR ratio absent | supported by company/security IDs | Startup/Enterprise Order Form required | third-party LLM and external output require redistribution rights | Order Form controls | $150 individual; $333 startup; $1,250+ enterprise | low-medium | `CONDITIONAL` |

Supporting providers remain non-primary: Massive for US price/reference, SEC for filing identity and
timestamps, OpenFIGI for security/share-class identifiers, and Finnhub/Alpha Vantage for audit-only
coverage checks. None proves the complete valuation, PIT, ADR, and license contract.

## Architecture Recommendation

- `BEST TECHNICAL`: one institutional global entitlement. S&P, FactSet, and LSEG remain tied until
  the same questionnaire and 20-stock POC are priced and answered; public evidence is insufficient
  for a forced commercial winner.
- `BEST COST/BENEFIT`: a controlled KR/US split, FnGuide enterprise/custom rights or DeepSearch for
  KR plus Intrinio Startup/Enterprise for US. This remains conditional on written rights and basis.
- `BEST LOW-COST EXPERIMENTAL`: current sources plus audit-only provider trials. This can measure
  fields and coverage but cannot become production canonical data.

The split path is likely more proportionate for a 20-stock monitor, but it creates two licenses and
cross-provider identity/as-of reconciliation. An institutional package is technically cleaner but
may be economically excessive; no unpublished price is inferred.

## Phase 8.3.2 Boundary

Do not begin a provider adapter until one candidate has a selected product/order form, credential or
approved trial, written display and external-AI rights, storage rights, mandatory field dictionary,
and fixture results for Samsung, MU, TSM, SKHY, and GOOG/GOOGL deduplication. Trailing integration may
be split into Phase 8.3.2A and consensus into 8.3.2B.

## Official Evidence

- [S&P fundamental and PIT products](https://www.spglobal.com/market-intelligence/en/solutions/products/fundamental-data)
- [S&P Estimates Snapshot](https://www.spglobal.com/market-intelligence/en/solutions/capital-iq-estimates)
- [S&P licensing terms hub](https://www.spglobal.com/en/licensing-terms-and-conditions)
- [FactSet Fundamentals PIT](https://www.factset.com/marketplace/catalog/product/factset-fundamentals-point-in-time)
- [FactSet Estimates API](https://developer.factset.com/api-catalog/factset-estimates-api)
- [FactSet Symbology API](https://developer.factset.com/api-catalog/symbology-api)
- [FactSet legal page](https://www.factset.com/legal)
- [LSEG quant/PIT product guide](https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/data-for-quant-research-brochure.pdf)
- [LSEG redistribution policy](https://www.lseg.com/en/data-analytics/market-data/data-redistribution)
- [FnSpace service, prices, and license](https://www.fnspace.com/Customer/Info)
- [FnSpace terms](https://www.fnspace.com/Customer/Service)
- [DeepSearch API guide](https://help.deepsearch.com/dp/api/master)
- [Intrinio pricing](https://intrinio.com/pricing)
- [Intrinio terms and AI policy](https://docs.intrinio.com/terms)
- [Intrinio US fundamentals](https://intrinio.com/products/us-fundamentals)
- [Intrinio EPS estimates](https://intrinio.com/products/eps-estimates)

No signup, purchase, vendor contact, adapter, canonical promotion, main merge, or deployment occurred.
