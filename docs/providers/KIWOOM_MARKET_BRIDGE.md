# Kiwoom KR Market Bridge

## Decision

Kiwoom OpenAPI+ is a Windows OCX API. The macOS thesis-monitor process does not load it directly.
The only accepted shape is:

```text
Windows OpenAPI+ process
  -> authenticated local gateway
  -> strict market-only JSON
  -> KiwoomKrMarketProvider on macOS
  -> market-cross-section-v1 (shadow)
```

Current status is `NOT_CONFIGURED`; no KR market gateway URL or credential is installed. The provider
role remains `bridge_shadow`.

## Gateway Contract

The reusable gateway paths are:

- `GET /v1/kr-market/capabilities`
- `GET /v1/kr-market/snapshot?date=YYYY-MM-DD`

Capability rows name the exact TR/function, request scope, rows per request, worst-case pages,
pagination, KOA Studio verification, and denominator-semantics verification. A metric cannot be
`SUPPORTED` without exact verified evidence. An all-stock contract also needs bounded row/page
evidence; per-ticker polling is never an efficient breadth capability.

Gateway payloads must not contain account number, HTS ID, app key, certificate, credential,
password, secret, or token. The URL cannot contain user info, query credentials, or fragments. The
consumer sends `KIWOOM_GATEWAY_API_KEY` only in `X-Gateway-API-Key`.

## Official Documentation Evidence

OpenAPI+ developer guide v1.7 documents:

- `CommKwRqData`, a multi-symbol request whose input is a semicolon-separated code list;
- `GetCodeListByMarket`, with market codes including KOSPI, KOSDAQ, ETF, REIT, and KONEX categories;
- the `업종지수` real-time type with index close/change/return/volume/trading-value FIDs;
- the `업종등락` real-time type with advance, decline, unchanged, upper/lower-limit, traded-issue,
  volume, trading-value, and participation FIDs.

This proves documented primitives, not that the needed real-time type is registrable for every target
index, that its denominator matches the desired common-equity universe, or that an efficient historical
snapshot TR exists. Those items remain `PARTIAL` until KOA Studio and gateway live evidence exist.

Official guide: [Kiwoom OpenAPI+ developer guide v1.7](https://download.kiwoom.com/web/openapi/kiwoom_openapi_plus_devguide_ver_1.7.pdf).

## Rate Limit Gate

The gateway contract records 5 requests/second, 100/minute, and 1,000/hour limits. A design requiring
2,000-3,000 ticker requests is rejected. Production bridge eligibility requires a direct market
summary or bounded multi-row pagination. The initial planning ceiling is 20 pages per snapshot, at
most 20 requests/session and comfortably below all three limits; the actual bound must be verified by
KOA Studio before status can become `SUPPORTED`.

## KRX Transition

After KRX approval, KRX becomes primary and Kiwoom remains reconciliation/secondary. No automatic
fallback occurs until five trading days establish metric-by-metric comparability. Provider-specific
taxonomy and universe exclusions remain explicit.
