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

`krx-publication-readiness-v1` evaluates the four core daily endpoints after XKRX determines the
latest completed session. The states are `MARKET_NOT_COMPLETED`,
`MARKET_COMPLETED_PROVIDER_PENDING`, `PROVIDER_PARTIAL`, `PROVIDER_COMPLETE`, `PROVIDER_ERROR`, and
`STALE_PROVIDER_DATE`. HTTP 200 with zero rows is pending after market completion, not success. A
partial, errored, stale, or pending bundle cannot publish a full current cross-section. Only
`PROVIDER_COMPLETE` is promotable, and Phase 8.2A.1 does not promote individual partial Facts.

The four readiness calls are KOSPI stock daily, KOSDAQ stock daily, KOSPI index, and KOSDAQ index.
Issue reference metadata remains separately cacheable. KRX rows expose `BAS_DD` but no explicit
publication timestamp, so a future shadow observer must retain the first non-empty and first
complete observation times without treating either as a provider-authored timestamp.

`krx-publication-telemetry-v1` supplies that observer boundary. Each point probe is stateless and
records only what was visible at its timezone-aware observation time. It does not label itself the
first observation. Sanitized records are appended to an ignored per-session JSONL file under
`data/telemetry/krx/publication-readiness/`; the API key and request headers are never serialized.
The timeline derives:

- `first_non_empty_at`: the first tracked probe with any core rows;
- `first_complete_at`: the first tracked complete probe only when an earlier non-complete probe is
  present in the same timeline;
- `observed_complete_by`: the earliest complete upper bound, including an initially complete probe;
- `last_empty_at`: the latest tracked all-empty pending probe; and
- `publication_window_start/end`: the interval between the last tracked pending/partial probe and
  the first tracked complete probe.

These are observer timestamps, never a provider-authored publication time. An initial complete probe
has `observed_complete_by` but no `first_complete_at`, preventing false precision.

`krx-time-slot-provider-role-v1` evaluates separate roles rather than calling KRX a universal KR
primary. Evidence is accepted only for explicitly observed normal-session slots:

| Time slot | Candidate role | Supported gate |
|---|---|---|
| 16:05 KST, same session | `SAME_DAY_CLOSE_PRIMARY` | five clean complete sessions |
| 08:05 KST, prior session | `NEXT_MORNING_PRIMARY` | five clean complete sessions |
| T+1 reconciliation | `T_PLUS_1_AUTHORITATIVE_RECONCILIATION` | three clean complete sessions |
| Explicit historical request | `HISTORICAL_ONLY` | existing archive validation |

One complete live-slot observation is only `CANDIDATE`; three observations with no complete result
can establish `NOT_SUPPORTED` for that exact slot. Observations made at other times do not count as
16:05 or 08:05 evidence.

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

Listing-date and comparison-base exclusions are explicit: `new_listing_no_prior_close`,
`future_listing`, `listing_date_missing`, `listing_date_invalid`, and
`missing_comparable_previous_close`. A same-session KRX comparison value can be an offering/reference
comparison rather than a previous exchange close, so it never overrides the listing-date boundary.
Phase 8.2A.1 found that the implementation already used `listing_date < session`; the earlier
capability report contained the reversed wording. The 2026-08-14 denominator is therefore unchanged
and remains `krx-kospi-kosdaq-common-share-v1`.

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
and current-session provider readiness. One normal-session complete observation moves readiness only
to strong partial; 3-5 sessions are recommended before closing it. Proposed observation windows are
15:35, 15:45, 16:00, 16:05, and 16:10 KST, but no production schedule is configured by Phase 8.2A.1.
Kiwoom remains a future reconciliation source; KRX failure does not automatically activate Kiwoom
fallback.

Phase 8.2A.2 keeps the provider experimental and adds no production schedule. Its local observer is
development telemetry, not a Scheduled Task. Same-day, next-morning, and reconciliation roles remain
independent until their own normal-session evidence gates pass.
