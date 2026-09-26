# Unified Source Owner Interfaces

## R2A-R3 Offline Extension

R2A-R2 below remains the accepted historical baseline. R2A-R3 adds the following
local, opt-in interfaces; none registers a production adapter:

- Google RSS, Naver, SEC submissions and OpenDART event requests can use
  `EventReceiptTransport` and `EventAcquisition`. Each original response is
  bound to run/acquisition, request ordinal, exact bytes, original decoding,
  publication and persisted security identity. A cache read needs its original
  HTTP receipt and raw hash. Prohibited sources are checked before raw access.
  Original date/decoding absence, future publication and failed identity remain
  denied. Nested OpenDART statement requests use the same transport. The
  detached CollectionService branch does not insert Event/financial/telemetry
  rows. The historical get_thesis_events cache/backfill path remains excluded.
- `unified_class_c_owners` inventories all 12 frozen roles. Direct SEC
  companyfacts business fields and OpenDART selected occurrences now preserve
  record/filing/period/unit/currency identity and existing field-owned quality.
  Macro observation projection calls the existing temporal owner, preserving
  reference-only and previous-US-session classifications. Fed projection is
  published context only and excludes stored interpretation/unknown fields.
- Mandatory universe, identity and stored thesis/business metadata are bridged
  to `freeze_run` by `unified_local_seed_bridge`. Frozen selected records are
  revalidated with the real local owner in an isolated in-memory DB; no
  assessment rows or query-time prices enter this replay. This proves a local
  three-role seed, not the complete 24-family source adapter.
- `unified_aggregate_receipt` validates the transitive child graph, original
  body/normalization hashes, run/attempt/acquisition identity, exact ordered
  child inventory and Kiwoom cursor continuity. Composition requires a separate
  aggregate owner callback and equality with child-derived normalization.
  An aggregate cannot go through the single-HTTP-response adapter.

### Remaining R2A-R3 Gates

1. `project_estimate_inventory` is an explicit inventory/denial, not a working
   eligible-estimate selector. The existing Finnhub path in
   `ValuationSnapshotService.fetch` writes provider-defined partial consensus;
   persisted security/period/basis eligibility needs a read-only owner split.
2. `project_canonical_catalog` proves typed lineage only. It explicitly returns
   `consumption_eligible=false`; latest-formal/current cashflow and working-
   capital consumption eligibility is not connected to this run projection.
3. SEC projection covers selected companyfacts revenue/operating-income, not
   every foreign-filing, balance-sheet or derived domain consumed downstream.
   The optional C projections (including macro/Fed) are not all installed as
   immutable, current-cutoff `OwnerAdapter` callbacks.
4. Aggregate integrity mechanics are tested with synthetic receipts. Real
   Kiwoom, KRX, event, Nasdaq and US multi-symbol owner replayers still need to
   implement `project_aggregate_and_validate` and verify their complete planned
   child sets. No callback that simply trusts normalized output is registered.
5. Without those concrete branches there is no whole-adapter transitive
   reachability proof, final complete seed or full network-free prequalification.
   These are code/contract gaps, not permission to run a live canary.

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=false`.
`complete_source_adapter_qualified=false`, `complete_ai_adapter_qualified=false`.
R2B is NOT_GENERATED_NOT_EXECUTED and R3 remains BLOCKED. Existing product retry
times, provider exclusions, prompts, validators, schemas and deployment stay
unchanged. Historical scope tests add only observed `filings.py`/`news.py` drift;
their FAIL result and reviewed acceptance roots remain frozen.

R5F-R2A-R2 is local and opt-in. It does not qualify or register a complete source
adapter. Acquisition classes and product times remain the R2A-REV1 contract.

## Implemented Interfaces

- `OhlcvMarketProvider.collect` accepts the same `OhlcvReceiptObserver` used by
  stock OHLCV. It requires the whole `MARKET_SYMBOLS` plan, completed US session,
  exact symbol/provider/adjusted basis, and fresh observer state. Each successful
  normalization binds its raw response and normalized observation hash.
- `KiwoomRestClient.request` observes data POSTs only. OAuth headers/body are not
  serialized. Each retry/page has durable intent, byte body/hash, response time,
  and response receipt. The frozen market plan is checked before acquisition.
  Cursor hashes and page ordinals bind accepted page sets. The real market owner
  supplies reconciliation, units, session identity and typed normalization.
  In unified mode an optional aggregate/page failure denies flows; it never
  synthesizes zero or erases otherwise valid mandatory indices/breadth/sectors.
- Finnhub earnings, Nasdaq breadth and KRX night expose `RunAcquisitionObserver`.
  Original source/publication/session fields stay in owner output. Query times
  are captured at actual data reads. A consumed observer cannot collect again.
  KRX unified history requires an explicit private directory; Nasdaq unified
  mode avoids the legacy shared cache. No instance is registered by default.
- `evaluate_financial_freshness_records` operates on detached copies. The legacy
  mutating service consumes the same decision and explicitly persists proposed
  chronology/refresh fields. Existing cadence and decision rules are unchanged.
- `project_local_seed` reads the actual universe, security readiness and active
  thesis selection without `ensure`. Exact record IDs/content versions and
  current cutoff eligibility are retained. Watchlist prior assessment fields
  are not projected. No provider receipt is fabricated from a database row.
- `project_financial_freshness` excludes undeclared/future rows and exposes
  original record hashes with the existing freshness decision. This is not full
  SEC/OpenDART metric-lineage or derived-domain consumption qualification.
- CollectionService receives the opt-in policy at its nested registry. Its
  unqualified event/profile/backfill paths stop before database/network access.
  Earnings returns explicit unavailable rather than mock/cache fallback.
  Valuation policy mode avoids mutation-coupled dividend sync and chronology
  validation on attached ORM rows; default legacy mode is preserved.

## Remaining Closure

1. **News/event B owner:** `CollectionService._fetch_provider_events` and
   `collect_events` need real provider-specific wire/cache receipts before the
   unified entry guard can be removed. RawEvent output cannot reconstruct lost
   request bytes, publication identity or nested call failures. No real request
   is needed or authorized merely to design those hooks.
2. **Class C metric projections:** SEC/OpenDART freshness is now read-only, but
   actual selected metric lineage, canonical cashflow/working-capital, estimate
   security basis and publication-macro temporal projections are not all wired
   as `OwnerAdapter.project_and_validate`. Seven other optional C families have
   no new projection in this change. Mandatory local projections are not yet
   serialized into the final immutable source-composition adapter either.
3. **Reachable policy closure:** event paths are safely denied, not functionally
   qualified. Shared historical/macro/event cache selectors must be checked at
   the eventual concrete adapter boundary; a registry allowlist is insufficient.
4. **Aggregate receipt composition:** real Kiwoom page sets and B multi-read
   normalizations cannot be advertised as a single HTTP response. The existing
   composition accepts an individual HTTP response receipt. A source-owner
   aggregate bridge with transitive raw/receipt/hash validation remains needed.

Network-free *whole adapter* prequalification is therefore blocked before
assembly. Synthetic interface and composition tests are not a substitute.
`complete_source_adapter_qualified=false`, `complete_ai_adapter_qualified=false`,
`source_gate=FAILED_CLOSED`, `PIPELINE_PASS=NO`, `READY_FOR_PROMOTION=NO`.
R2B is not generated/executed; R3 remains blocked.

## Proof Boundaries

Genuine KRX raw bytes replay with exact original observations. Saved Kiwoom
payload/page hashes and normalized audit replay exactly; the old archive lacks
original wire bytes/cursor headers, so that replay does not prove wire capture.
Saved Nasdaq publication-pending evidence remains unavailable. None proves a
current Class A/B acquisition or a real 22-subject cohort.

The four historical scope tests continue to assert historical FAIL. Their
explicit observed drift inventories include newly changed source-owner files;
reviewed roots, approved semantic scope, prompts and acceptance pins are intact.
