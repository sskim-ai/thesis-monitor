# Phase 8.3.1 Broad Peer Provider Capability

Date: `2026-08-18`
Scope: official-source research plus existing-entitlement read-only probes
Status: `RESEARCH COMPLETE / PROVIDER SELECTION OPEN / NO INTEGRATION`

## Existing Bottleneck

The immutable Phase 8.3 universe has 20 active assessments, 7 KR and 13 US. It contains 13 trailing
PER values, 18 PBR values, 9 consensus-forward PER values, and several modeled values, but zero
user-visible peer states. The failure reason is not statistics or validation. The active-monitoring
source does not provide at least three same-session, taxonomy-compatible, independently identified,
denominator-safe peers for any subject.

Phase 8.3 remains:

- contract: `PASS`;
- capability: `STRONG PARTIAL`;
- current user-visible coverage: `0/20`;
- broad point-in-time provider: `OPEN`;
- operating integration: `NO`.

## Mandatory Provider Contract

A production candidate must prove broad listed-security coverage, issuer/security hierarchy, share
class and ADR basis, taxonomy, current PER/PBR inputs, as-of and denominator dates, forward consensus
basis, point-in-time or reconstructable history, and contractual rights for storage, derived
statistics, external AI processing, and user display. Missing fields remain `UNKNOWN`; a marketing
coverage number cannot satisfy an entitlement-specific contract.

## Capability Classes

| Class | Providers | Result |
|---|---|---|
| Global institutional | S&P Global MI, FactSet, LSEG, Bloomberg | technically strongest; contract and cost review required |
| KR dedicated | FnGuide FnSpace, DeepSearch | plausible technical fit; licensing and PIT/security fields unresolved |
| US commercial mid-tier | Intrinio | strongest cost/benefit candidate; estimates and display rights are separate entitlements |
| Low-cost US split | Tiingo, FMP, Nasdaq Data Link, SimFin | useful components; no single source proves the full contract |
| Current/supplemental | Massive, Finnhub, Alpha Vantage, KRX | useful current fields or market data; not broad true-PIT peer providers |
| Identity auxiliary | OpenFIGI, SEC EDGAR | useful identifiers/filings; no peer valuation or ADR-ratio proof |

The detailed official-source evidence is in the
[KR matrix](20260818-phase8-3-1-kr-provider-matrix.md) and
[US matrix](20260818-phase8-3-1-us-provider-matrix.md). Scores are an audit aid, not a procurement
decision, in [the scorecard](20260818-phase8-3-1-provider-scorecard.json).

## Point-In-Time Finding

`CURRENT_ONLY`, `HISTORICAL_SERIES`, `POINT_IN_TIME_RECONSTRUCTABLE`, and `TRUE_POINT_IN_TIME` are
not interchangeable. S&P Global MI, FactSet, and LSEG publish the clearest official PIT/history
claims. Intrinio exposes filing and calculation timestamps that may support reconstruction. Tiingo
exposes public release dates. Massive's ratios are explicitly for the most recent trading day, and
the public documents reviewed for FMP, Finnhub, Alpha Vantage, DeepSearch, and NICE do not prove a
true as-known historical snapshot.

Consensus history is a separate requirement. FnGuide, FactSet, S&P Global MI, and LSEG document
consensus history or estimate revisions. A field named `forwardPE` without FY1/NTM, effective date,
analyst count, and share basis remains partial.

## Existing-Credential Probe

The probe stored no raw payload, numeric valuation, or secret and changed no canonical state.

| Provider | Ticker | Observation | Capability result |
|---|---|---|---|
| Massive | MU | environment variable had no value; one request returned malformed authorization | no live entitlement proof |
| Finnhub | MU | 131 metric fields; EPS TTM, PE TTM, PB, and forward PE present; no payload-level metric as-of | current metrics present, PIT/forward basis partial |
| Finnhub | TSM | response identified `2330.TW`; valuation fields present; no ADR ratio or true as-of | ADR/security basis unsafe for canonical use |
| Alpha Vantage | MU | Overview had CIK, exchange, taxonomy, PER/PBR/forward PE/EPS; no explicit as-of | current snapshot only |
| Alpha Vantage | MU | Earnings Estimates returned an empty `estimates` list without provider error | broad consensus coverage not proven |
| OpenFIGI | TSM | one US match with FIGI, composite FIGI, and share-class FIGI | identity useful; issuer ID and ADR ratio absent |

Eight provider requests were attempted: seven returned parseable provider responses and the Massive
request returned an authorization error because no key was configured. Credential exposure: `0`.
All POC results are audit-only.

## Coverage Simulation Boundary

No shortlisted entitlement was available for a 20-stock sample, so measured coverage remains
`0/20`. Institutional product pages imply broad global coverage, and KR/US dedicated products could
plausibly meet the proposed 4-5 KR and 7-8 US targets, but those are target scenarios, not observed
coverage. Phase 8.3.2 must run the exact active universe before assigning a coverage percentage.

Biotech suppression and unsafe subject metrics remain valid exclusions rather than provider
coverage failures. RXRX does not become a PER-attractiveness fixture; CORZ negative denominators,
SK hynix denied trailing PE, and TSM unsafe ADR basis remain blocked until their exact contracts pass.

## Result

The technical front-runners are S&P Global MI, FactSet, and LSEG. The conditional cost-aware path is
FnGuide FnSpace or DeepSearch for KR plus Intrinio for US, with OpenFIGI/SEC used only as identity
auxiliaries. Standard FnSpace/DataGuide terms and individual Intrinio terms do not authorize the
required production use. No provider is selected and Phase 8.3.2 is not open for implementation
until fields, entitlement, and licensing are confirmed in writing.

No code adapter, DB migration, main merge, operating deployment, Telegram send, Scheduled Task
change/run, Pilot mutation, or Production Assist change occurred.
