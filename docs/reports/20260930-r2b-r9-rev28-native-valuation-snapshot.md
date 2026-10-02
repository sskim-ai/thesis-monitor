# REV28 Provider-Native Valuation Snapshot

Final gate:
`R2B_R9_REV28_PROVIDER_NATIVE_VALUATION_SNAPSHOT_PASS_READY_FOR_FULL_FRESH`.

## Execution Identity

- Base: `9dfbbd04e95b962629ed4f6b0036dca66346735b`.
- Instruction first: `5d35616098faed06af504956d916872bd0f0f610`.
- Acquisition implementation: `e86c7c13419c8b11865732bf11a790eac56c5c12`.
- Replayed/tested implementation: `33615d82b3a820e0a55ca680caa2b393dbab10b6`.
- Branch: `codex/r2b-r9-rev28-native-valuation-snapshot`.
- Generation: `rev28-20260930T022652Z`.
- Sealed plan: `56093e55e0ad8c300693cfb00931a923bf51b633e61f9ef139a3e4d1850232e1`.
- Operating SHA remained `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
- Final documentation-only SHA is in the bundle repository identity receipt.

## Explicit Policy

The instruction authorizes
`PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT = true`.
This permits an atomic ratio from a fresh, exact-security provider response as
`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`. It does not establish same-session
fundamentals or an owned EPS/BPS denominator. Source-derived valuation denials
remain intact and cannot deny an independently qualified atomic snapshot.

The new typed receipt preserves raw/receipt/security hashes, provider field,
snapshot retrieval timestamp, nullable metric-as-of and denominator period,
provider update caveats, display/NewBuyer/Holder context permissions and
`overall_direction_use = false`. The existing entry-price arithmetic flag
remains false. These are context permissions, not AI input injection or a
status change. No model request was composed or transmitted.

## Fresh Bounded Evidence

| Subject | PER | PBR | Qualification |
|---|---:|---:|---|
| 005930 | 41.17 | 4.22 | Kiwoom exact code + latest basic-info snapshot |
| IBM | 19.5016 | 7.6717 | Existing SEC identity + fresh Finnhub profile/metric |

005930 retrieval: `2026-09-30T02:27:13.409769Z`.
IBM metric retrieval: `2026-09-30T02:27:14.194883Z`.
All four metric-as-of values and underlying denominator periods remain null.
These timestamps record acquisition, not the date of financial denominators.

No old valuation value was substituted. REV27 supplied contract/identity
reference evidence and preserved denials only. The old 005930 PER/PBR were
41.33/4.24; REV28 used the actual new 41.17/4.22 response without target fitting.
No signed-price repair, price/EPS arithmetic or price/BPS arithmetic occurred.

### KR

One ka10099 response contained exactly one 005930 code. It matched the
monitored code, local name and ka10001 code/name. Market code `0` is the
documented KOSPI request code; its live stock-list name was `거래소` for all
916 code-0 rows. The generic market-name map now accepts that native name.
The other returned market codes did not confer identity on the target.
The local inferred common/preferred label was not upgraded or persisted.

The market-name alias was added after capture, with a generic non-005930
regression test. Acquisition code/plan remain preserved, and final-owner
replay ran twice on unchanged raw bytes. There was no second collection.
Registry inventory tests were updated to require the added owner, including
its removal-negative case.

Kiwoom PER retains its weekly/earnings-season update caveat. PBR retains the
explicit unknown-as-of caveat. No date was invented.

### US

IBM binds the existing authoritative SEC Capital Stock identity, NYSE, CIK
and class to the fresh profile ticker/exchange/USD filing currency and metric
symbol. Finnhub peTTM is provider-reported TTM P/E; pbQuarterly is
provider-reported quarterly P/B. Neither is same-session recomputation.

MU remains unavailable: no authoritative SEC identity payload existed in the
scoped current cache. No extra identity route was necessary for the two-family
bounded proof, and no MU valuation probe or identity mutation was performed.
This is not a claim that MU can never qualify.

## Denials and Presentation

- TSM/SKHY ADR valuation remains excluded. REV27's home-security mismatch
  evidence is preserved as a historical negative, not refreshed current data.
- fPER remains unavailable. The prior explicit EPS-estimate HTTP 403 receipt
  is preserved; no estimate route/key/account retry or forwardPE fallback.
- Blank/null/missing, zero, negative, malformed and nonfinite values remain
  unavailable. Unowned negative EPS does not create N/M.
- Wrong security/class code, market, name, ticker, exchange, currency, hashes,
  old generations, cache reuse and conflicting source dates fail closed.

Isolated valuation-line controls show:

```text
PER: 41.17배 · Kiwoom snapshot
PBR: 4.22배 · Kiwoom snapshot
PER: 19.50배 · Finnhub TTM snapshot
PBR: 7.67배 · Finnhub quarterly snapshot
```

These are not complete stock messages. The isolated presentation test uses a
declared synthetic price context, never the numerator of the atomic ratios.
Actual stock assembly is tested separately through the common-cohort fixture.
Directional evidence is byte-equivalent with and without the new valuation
input; exact numeric bindings are owned by the Valuation display path only.
Broader detailed-renderer restoration is deferred.

## Validation

Pre-probe source-contract/legacy valuation tests: 97 passed.
Final focused snapshot and registry checks: 98 passed.
Full pytest: 6,991 passed, 63 skipped, 0 failures, 0 errors, 3 warnings
(7,054 collected; 1,246.07 seconds). The two required common-cohort and
production-owner integration tests passed, not skipped. Ruff, diff check,
Investment Knowledge and both Chart Knowledge checks passed. Offline socket
and DNS guards were active during pytest. Existing deprecation warnings are
retained in the complete log; no test threshold was relaxed.

The previous `matrix_native_qualified_source_required` failure closed
through real owner materialization, not a fake source grant. The common-cohort
uses explicitly fictional raw wires through production owners; those fixtures
are not live coverage. Its old unowned-EPS-to-N/M expectation is replaced by
typed unavailable, and null as-of is accepted only by the explicit snapshot
policy with source disclosure.

## Safety and Next Step

Data/API requests: 4. Kiwoom authentication: 1. Public documentation download:
1, separately counted. Planned data ceiling: 8; instruction ceiling: 12.
Only the first list page was needed. Retries and redirects: 0.

Models: 0. Messages: 0/24. Full-fresh: 0. Alpha Vantage: 0. Telegram: 0.
Production DB/warning writes, scheduler mutation, main merge, remote push,
deploy, restart and destructive GC: 0. Operating configuration and scheduler
definition hashes are checked, not a claim of DB byte-level immutability.

REV24 blind artifacts and REV24/25/26/27 immutable archives are preserved and
reverified. Raw source evidence is local/report-only, not committed. Final
ZIP includes changed code, receipts, validation and manifest after secret
scan; complete public documentation pages remain local, with URL/hash receipts
in the archive. Delivery is only iCloud Drive / Thesis Monitor.

With full validation green, REV29 can perform archive-backed GC and a new
full-fresh proof with explicitly acquired eligible valuation snapshots.
REV28 does not start REV29, enable production acquisition, prove all22
valuation coverage, or authorize user-visible delivery.

Official references: [Kiwoom ka10099](https://openapi.kiwoom.com/guide/apiGuideContents/01/ka10099),
[Kiwoom ka10001](https://openapi.kiwoom.com/guide/apiGuideContents/01/ka10001),
[Finnhub API](https://finnhub.io/docs/api).
