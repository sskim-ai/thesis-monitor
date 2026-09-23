# M12DS-R6-R1-REV1 Local Source and Price-Basis Closure

Instruction commit: `88ce447a35698a1ed02257b89184556537218bcd`.
Base: `ff15917d3182e299faa8c292dee7f1485e5ffd51`.

## Boundary

No main merge, push, deployment, production persistence, notification, warning or
scheduler mutation. No model call until a NEW generation passes the full
information coverage gate. Earlier partial-source authorization does not apply.

Standing Thesis Monitor transport: official signed-in `gpt-5.6-sol` / `xhigh`,
600 seconds per process attempt, maximum three attempts per logical request.
Only byte-identical typed transient transport/process retries; no schema,
semantic, source-use, identity, policy or security retries. Existing repeat
controller implements this policy; legacy frozen experiments remain immutable.

## Price Basis

`current_price_basis_service` is the shared producer/validator/renderer/capture
owner. Phase is INTRADAY or CLOSE; adjustment is RAW or ADJUSTED. Four legacy
labels have exact mappings; unknown labels and mismatched typed metadata fail.
No adjustment or investment value is computed by this mapping. The existing
OHLCV adjusted request/response owns adjustment semantics. Fresh KR8 diagnostics
confirmed response metadata adjusted=true for every subject.

Intraday dates must equal the assessment date. Close dates must equal the
explicit completed-session date when provided. Legacy contexts without that
date retain the existing non-future check; no arbitrary age threshold is added.
Contract, availability, basis and date failures have independent typed errors.

## Publication Freshness

The official FRED series page supplies expected observation, publication and
next-release dates. No host-day age threshold is used. Verified observations
aligned to the completed session are CURRENT_BY_PROVIDER_CALENDAR; verified
latest publications from an earlier period are LATEST_PUBLISHED_WITH_LAG.
Missing/expired/unverified receipts are fail-closed as STALE_UNEXPECTED with an
explicit reason, not a claim that the upstream publisher definitely missed a
deadline. For series without a verified release clock, the start of the declared
release date is a conservative expiry, not an invented publication time.

Lagged facts may be shown with observation dates and the latest-published/lag
label. They cannot populate current-direction supporting/contradicting refs in
the model schema or validator. Stale/unverified rows are excluded from the
current numeric block. Stock decision labels, thresholds and economics remain
unchanged.

## Source Diagnosis and Stop

The bounded 2026-09-23 12:53 KST diagnostic found current US raw bars, but no
latest-bar settled-close/finality authority in the existing Kiwoom projection.
The existing completed-session gate remains unchanged. All 22 are classified
UNRESOLVED_PROVIDER_FAILURE, specifically missing completed-close authority;
this is not a claim that raw current bars are absent or that the parser is wrong.

KR current-only TR rows were from the ongoing session while the target was the
previous completed session. Native value/date reconciliation correctly failed.
Classification remains UNRESOLVED for parser repair: no parser defect was proved.
The noon observation does not prove the cause of the earlier morning failures.

The full information gate remains closed. No fresh Market/Core/A/B or 24-message
success is claimed. Raw diagnostic evidence is local outside Git. Exact-price
migration checks preserve historical scope baselines without path exemptions.
