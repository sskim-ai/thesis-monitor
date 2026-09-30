# Provider-Native Valuation Snapshot

REV28 explicitly authorizes
`PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT = true`.
This is a named product policy, not a relaxation of source-derived EPS/BPS,
share-class, split or completed-session price ownership.

## Boundary

The pure `provider_native_valuation_snapshot` owner consumes raw bytes and
receipts from one current acquisition generation. It never fetches, caches,
persists, trades, schedules or sends messages. The new input contract must be
explicit; legacy native inputs retain their previous fail-closed behavior.
No production collector is enabled by this change.

Atomic PER/PBR do not claim an owned numerator or denominator. The existing
price in CurrentMultiple is context only; `entry_use_eligible` stays false
because it confers price/arithmetic rights. Separate snapshot permissions
allow display and NewBuyer/Holder valuation context, never Overall business
direction. No FCF or forward multiple is added.

## Exact Identity

KR: ka10099 exact six-digit code, expected market, compatible name and current
page-chain receipts bind to ka10001's identical code/name. KRX in the local
master is the exchange umbrella; a concrete KOSPI/KOSDAQ request and matching
provider market code/name must agree. No ordinary/preferred sibling transfer,
or inferred textual share-class upgrade, occurs. The existing master is not
mutated. A duplicated/missing code is denied.

US: the existing authoritative SEC identity payload, canonical security,
listing, class, CIK and source provenance must agree with the fresh Finnhub
profile and metric symbol. Profile currency is company filing currency, not
proof of a quote-currency conversion. Only direct US common securities with
matching USD profile context qualify. ADRs remain excluded.

## Snapshot Time

Fresh acquisition timestamps prove when the response was retrieved, not when
its EPS/book inputs were measured. Missing metric dates remain null. Explicit
stale/cache metadata or conflicting metric dates block use. No arbitrary
age threshold is introduced and no source-derived denominator is selected.

Kiwoom PER retains the documented weekly/earnings-season update caveat. PBR
retains the unknown-metric-as-of caveat. Finnhub peTTM and pbQuarterly mean
provider-reported TTM P/E and quarterly P/B only. Both preserve an unknown
metric date when none is provided. Snapshot rendering identifies the provider
and scope; it cannot imply same-session recomputation.

Blank/null/missing, zero, negative, malformed and nonfinite native fields
remain unavailable. Zero is not cheap, and negative EPS/native ratios do not
bootstrap N/M without the separate denominator owner. Each metric qualifies
independently. Generic forwardPE remains unused; the existing estimate-route
entitlement denial is preserved as evidence, not refreshed.

## Replay and Validation

Typed snapshots bind exact raw/receipt/identity hashes and use permissions.
CurrentValuationView binds those receipts to the current security and run.
Source-derived denial receipts remain intact alongside a qualified atomic
snapshot. Numeric bindings retain null metric-as-of plus a separate retrieval
timestamp. The numeric view is not inserted into directional fact evidence.

The common-cohort fixture uses the production owner with clearly fictional
SEC and provider wires. Its former N/M-from-unowned-EPS expectation is replaced
by an unavailable expectation; null metric-as-of is allowed only through the
new explicit policy and snapshot label. No fixture serves as live evidence.

Official references: [Kiwoom ka10099](https://openapi.kiwoom.com/guide/apiGuideContents/01/ka10099),
[Kiwoom ka10001](https://openapi.kiwoom.com/guide/apiGuideContents/01/ka10001),
[Finnhub API](https://finnhub.io/docs/api).
