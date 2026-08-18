# Free-Source Current Peer Valuation

## Decision

Phase 8.3 uses `FREE_ONLY` provider policy. Paid and institutional provider research remains
historical reference, but it is `CLOSED_BY_POLICY` on the current roadmap. The free path targets a
current peer cross-section only; historical peer point-in-time reconstruction is
`DEFERRED_BY_FREE_ONLY_POLICY`, and forward consensus remains optional.

The contract is `free-source-current-peer-v1` layered on `peer-sector-valuation-v1` and
`verified-profile-peers-v2`.

Phase 8.3 is finalized as `SELECTIVE_OPTIONAL_CONTEXT`. Its selection, safety, statistics,
provenance and audit tooling remain available, but broad runtime expansion is stopped because the
measured free-source value is `LOW_ROI`. Operating integration remains `NO`.

## Pipeline

```text
verified profile and taxonomy
    -> same-market candidate universe
    -> issuer/security identity
    -> free current price and denominator lineage
    -> PER/PBR eligibility
    -> at least 3 independent issuers
    -> Phase 8.3 distribution statistics
    -> industry-aware display metric
    -> selective Valuation sentence
```

Candidate and eligible states are separate. A provider peer result is not automatically a
valuation sample. The subject is removed, issuer share classes are deduplicated, preferred and
depositary securities are excluded when their basis is not proven, and broad sector groups remain
`LOW` regardless of row count.

## Free Sources

| Source | POC role | Boundary |
|---|---|---|
| OpenDART | KR issuer and official industry code; existing financial lineage | no broad current peer multiple feed |
| KRX Open API archive | KR common-share identity evidence | no peer PER/PBR assumed; publication role remains experimental |
| Existing canonical snapshots | subject current PER/PBR | active subjects only |
| Finnhub free entitlement | US peer discovery, profile, basic financials, quote | personal/free entitlement; archive POC only, no production display license claim |
| SEC | US CIK and issuer dedup evidence | no market valuation multiple |
| OpenFIGI | listed-security type and share-class evidence | no ADR ratio or valuation denominator |
| Alpha Vantage | optional forward research | not called after trailing POC failed the value gate |

Official evidence, accessed 2026-08-19:

- [Finnhub API documentation](https://finnhub.io/docs/api)
- [Finnhub pricing and free entitlement](https://finnhub.io/pricing)
- [OpenDART company overview API](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019002)
- [OpenDART terms](https://opendart.fss.or.kr/intro/terms.do)
- [OpenFIGI API documentation](https://www.openfigi.com/api/documentation)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Alpha Vantage documentation](https://www.alphavantage.co/documentation/)
- [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/)
- [KRX Open API service list](https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd)
- [KRX Open API Korean terms](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO002.jsp)
- [KRX Open API English terms](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO005.jsp)

The KRX links above are deliberately copyable persistent references. They do not change the
separate Phase 8.2A publication-timing or operating-integration status.

## Current Multiple Assembly

The preferred source is an existing canonical safe multiple. A free derived PER requires the
completed-session security price, positive TTM EPS, matching currency, safe per-security basis and
a denominator period no more than 180 days old. PBR applies the equivalent rules to positive BVPS.
Provider PER/PBR is not reverse-engineered into EPS/BVPS and conflicting providers are never
averaged.

For the US POC, Finnhub `quote.pc` is accepted only when the quote observation session is the next
specified completed session, so the previous close can be tied to 2026-08-17. Top-level TTM EPS or
quarterly BVPS is paired with the latest dated quarterly series period. Missing as-of, currency,
identity, denominator or session evidence excludes the metric.

## Industry Boundary

Provider labels such as `Technology`, `Media`, and `Financial Services` are broad sector groups and
cannot create visible peer statistics. `Semiconductors` is also too broad for a memory-specific
subject. A memory subject therefore falls back to `LOW` unless memory peers are independently
verified. An exact provider `Automobiles` taxonomy can qualify, but interpretation still requires
volume, mix, margin, CAPEX and FCF context.

A qualifying taxonomy and safe multiple prove a calculation-eligible baseline group, not full
economic comparability. User-facing wording therefore calls it a same-classification `기초 비교군`
and states that business-model and growth-expectation differences limit direct peer-premium or
peer-discount interpretation. The formatter applies this rule by verified classification, never by
ticker. It does not add unverified company narratives.

Biotech, HPC/crypto infrastructure, SaaS and holding-company frameworks remain
`NOT_MEANINGFUL` for generic PER/PBR under this free-source contract. Relative discount is not
`cheap`, and relative premium is not `overvalued`.

## Statistics And Provenance

The existing Phase 8.3 engine calculates median, mean, quartiles, IQR, range, sample count,
relative multiple, premium/discount and cross-sectional percentile. The renderer calculates
nothing. A visible sentence reads a preselected metric and exact `valuation:current` plus
`valuation:peer` fields. Each displayed value records `fact_id`, `field_path`, raw value, unit,
semantic type, `text_ref` and usage.

## Measured Result

The immutable 2026-08-18 active universe produced one `MEDIUM` user-visible state among 20
subjects, or 5.0%. Excluding five subjects where generic peer PER/PBR is not economically
meaningful, coverage is 1/15, or 6.67%. KR is 0/7. US is 1/13 overall and 1/8 meaningful subjects.
Only TSLA qualifies, with three independent eligible automotive PER peers. Ten of eleven full
message fixtures remain byte-for-byte unchanged; TSLA grows 8.34% and adds no new section.

## Continuation Decision

The free-source combination is technically safe but has low analytical return for a broad feature.
Phase 8.3 is closed on the current roadmap as selective optional context. Keep the tooling and clean
peer-only branch, but do not add runtime integration, daily broad collection, taxonomy widening,
forward-consensus expansion or historical PIT work. Reopen only if verified taxonomy or free current
valuation coverage improves naturally, a new safe free source appears, an exact industry group
reliably reaches three clean issuers, or operating-message review establishes a new peer need.
