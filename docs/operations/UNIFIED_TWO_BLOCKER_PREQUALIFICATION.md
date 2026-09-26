# R2A-R5 Offline Closure

R2A-R4 remains the accepted acquisition/consumption boundary. This extension is
not registered as a live source adapter and changes no scheduler or delivery
behavior. A5/B4/C12/D3, prompts, thresholds and historical FAIL pins are unchanged.

## KRX Acquisition and History Replay

`unified_krx_history_replay` accepts an independently pinned historical plan and
the existing `AggregateReceipt` / `AggregateChild` / `ArtifactBinding` graph.
Children are original `krx-night-raw-response-receipt-v1` records. They are not
fabricated HTTP acquisition receipts. `verify_aggregate` for live source use
continues to reject them. The schema has not changed.

The plan binds the original source manifest, generation, probe, candidate,
original raw history/probe bytes and owner fingerprints. Receipt hash, byte size,
field set, query date, original acquisition time and exact ordered child set are
checked. An older original raw receipt is permitted only when the bound probe
independently records the same date/hash. This preserves the history store's
first-acquisition semantics; no timestamp is rewritten.

The existing `fetch_live_probe` runs against a declared-byte transport with no
network fallback. The replay must consume exactly the planned query sequence.
The parsed probe must match the original. The original source-capture flag means
saved original bytes exist, not that this task performed a live fetch.

Only declared historical raw responses are reparsed and persisted in a new
temporary directory. The same `materialize_night_probe` function used by the live
provider runs `persist_live_probe_history` and `build_same_contract_timeframes`.
Both configured products and all D/W/M dependencies must reproduce. Temporary
state is removed even on error. Production history and databases are never used.

The historical candidate used `str(datetime)` and added `telemetry.month_history`
after the native provider owner. Comparison therefore freezes a separate typed
native-owner projection: timestamps go through `MacroProviderResult` validation;
only the archive acquisition-audit annotation is excluded. Its original bytes
remain hash-bound and its monthly coverage is separately compared with the real
owner output. No numeric, reference-basis, finality or D/W/M field is dropped.
Historical request counts are not presented as new provider calls.

## Stock Materialization Remains Blocked

The explicitly declared 2026-09-23 source archive contains no standalone original
OHLCV response with the owner's `periods` / `resolved_symbol` envelope. There is
no request/response/normalization chain for the required four roles per subject:
adjusted daily, weekly, monthly and unadjusted weekly valuation. This affects all
US14/KR8 subjects (88 role bindings). Normalized chart fingerprints are not raw
source receipts.

The complete pure stock materializer is **not implemented or qualified** by this
task. No generic dictionary, synthetic assessment, prior packet, rendered prose
or mocked wire response is substituted for the missing originals. Existing R4
component mechanics remain available, but cannot establish full stock lineage.

The required source-only owner graph remains:

1. Exact frozen local universe/security/thesis projections.
2. Four same-attempt, subject/session/basis-bound original OHLCV roles, replayed
   by `replay_ohlcv_role` and the existing price/technical owners.
3. At least one observed-business proposition from an accepted event or selected
   financial owner. Thesis conditions and cautions are not observations.
4. Existing financial current-formal/PIT/taint selection, including exact unit,
   currency, statement period and occurrence identity.
5. Existing typed evidence packet and numeric registry contracts, with no prior
   assessment, implicit cache, renderer or delivery dependency.

Optional forward estimates remain unavailable without an exact denominator;
provider forwardPE is not EPS. CF/WC remain unavailable unless independent formal
source binding is proven. Optional absence does not add whole-packet blockers.

The next bounded repair must provide the 88 genuine role receipt chains under an
explicit acquisition authorization (or recover their exact original artifacts),
then complete the pure materializer and its business-union/financial/numeric
negative tests. No acquisition or R2B execution is authorized by this document.

## Gate

Because STOCK_MATERIALIZATION remains, full US/KR packet assembly is not reached.
Run-seed and final packet hashes stay null. KRX component proof hashes are not
substituted for whole-packet hashes. Network-free source prequalification, live
source qualification and AI qualification remain false. R2B is not generated;
R3 remains blocked. No optional source is made mandatory to enlarge this gap.
