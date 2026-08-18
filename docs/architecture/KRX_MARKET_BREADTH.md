# KRX Market Breadth

Phase 8.2A implements an experimental, archive-only KRX Open API provider for the existing
`market-cross-section-v1` and `market-breadth-v1` contracts. It is not registered in the operating
runtime and does not change Scheduled Tasks, Telegram, Pilot, or Production Assist.

## Ownership

```text
KRX Open API raw rows
  -> endpoint/date/identity validation
  -> explicit KOSPI/KOSDAQ common-share universe
  -> official return and activity normalization
  -> deterministic breadth calculation
  -> MarketCrossSection
  -> canonical market Facts
  -> numeric semantic registry
  -> Market Intelligence selection
```

The backend owns every calculation. AI may interpret emitted Facts but cannot calculate breadth,
infer missing flow, or turn a sector-index move into company evidence.

## Official Endpoints

| Purpose | Endpoint |
|---|---|
| KOSPI daily trading | `sto/stk_bydd_trd` |
| KOSDAQ daily trading | `sto/ksq_bydd_trd` |
| KOSPI issue metadata | `sto/stk_isu_base_info` |
| KOSDAQ issue metadata | `sto/ksq_isu_base_info` |
| KOSPI index series | `idx/kospi_dd_trd` |
| KOSDAQ index series | `idx/kosdaq_dd_trd` |

Authentication uses the `AUTH_KEY` header. The key is read from `KRX_OPEN_API_KEY`; it never enters
URLs, cache envelopes, logs, reports, or committed files.

## Session Contract

`basDd` must equal the explicitly requested XKRX session. Every response row carrying `BAS_DD`
must match it. Empty, duplicate, wrong-date, malformed, or non-positive required values fail closed.
An `expected_session_date` mismatch fails before a provider call.

Current-session emptiness is not permission to reuse an older session. Historical sessions are used
only when the caller explicitly requests archive-only validation.

## Universe

The denominator version is `krx-kospi-kosdaq-common-share-v1`.

Eligible rows require:

- a KOSPI or KOSDAQ daily row;
- an exact six-character short-code match to issue basic information;
- security group `주권`;
- certificate type `보통주`;
- a listing date before the requested session;
- no official SPAC segment or residual `스팩` issue-name marker;
- valid close, official comparison base, and official return.

Preferred shares, REITs, infrastructure funds, investment companies, foreign shares, depositary
receipts, SPACs, and same-session new listings are excluded. ETF, ETN, and ELW data belong to
separate KRX services and never enter this universe.

KRX Open API does not expose a suspension flag in these responses. An otherwise eligible zero-volume
row remains in the unchanged denominator. Coverage is therefore `partial`, and the limitation is
preserved in quality metadata.

## Calculations

The official `FLUC_RT` value is the return source. The comparable base is reconstructed only as
`close - CMPPREVDD_PRC`; no external previous close or unadjusted price is mixed in.

For aggregate KR, KOSPI, and KOSDAQ separately:

```text
advance_count   = count(return > 0)
decline_count   = count(return < 0)
unchanged_count = count(return == 0)
advance_ratio   = advance_count / eligible_count
ad_ratio        = advance_count / decline_count, or unavailable when decline_count = 0
median_return   = median(official returns)
equal_weight    = arithmetic mean(official returns)
```

Official `ACC_TRDVOL` and `ACC_TRDVAL` are retained as shares and KRW. Missing units are unavailable,
never zero.

## Index And Sector Boundary

Major identities are exact: KOSPI, KOSPI 200, KOSDAQ, and KOSDAQ 150. Selected KOSPI 200 and
KOSDAQ 150 industry index returns are emitted as `sector_price_proxy`. They are not security-level
sector breadth, do not share the company-profile taxonomy, and cannot confirm company earnings.

## Unsupported Capability

The approved KRX Open API catalog has no market-wide foreign, institution, and retail net-buy
service. `market_flows` remains empty and coverage remains unavailable. Stock-level flow cannot fill
this gap.

## Cache

Raw envelopes are stored under ignored `data/cache/krx/market/YYYY-MM-DD/`. Each envelope contains
endpoint, request date, fetch time, HTTP status, permitted rate-limit headers, row count, payload
SHA-256, and raw rows. Atomic writes prevent partial cache promotion. Git ignores all cache data.

## Future Promotion

Promotion requires separate approval after natural Phase 8.5.x live review, KRX preview human review,
and current-session provider readiness. Kiwoom remains a future reconciliation source; KRX failure
does not automatically activate Kiwoom fallback.
