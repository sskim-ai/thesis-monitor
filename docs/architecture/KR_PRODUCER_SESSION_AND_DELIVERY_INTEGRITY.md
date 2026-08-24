# KR Producer Session And Delivery Integrity

## Contracts

- Session target: `xkrx-role-target-v1`, role `kr_daily_production`
- Delivery intent: `packet-bound-delivery-intent-v1`
- Incident maintenance: `kr-orphan-delivery-reconciliation-v1`

The KR producer uses the same XKRX calendar resolver as the existing publication and night roles.
It does not implement weekday arithmetic or a separate holiday table.

## Producer Entry Order

Every 16:05, 16:20, and 16:50 entry resolves `kr_daily_production` before reading or mutating the
monitoring run. Production is eligible only when the observed KST date is an XKRX session, the
regular session is complete, and the resolved business date equals the requested run date.

The fail-closed order is:

```text
producer entry
-> XKRX role target
-> analysis decision
-> KR close context
-> company analysis and provider calls
-> immutable AI-review packet
-> packet-bound provisional delivery intents
-> AI-assisted hold
```

No target, an incomplete target, a run-date mismatch, or resolver failure returns a normal
`safe_noop` before KR-close collection, provider calls, `MonitorRun`, assessments, packet writes,
or notification rows.

## Packet And Delivery Invariant

For an active KR AI-assisted pilot, `run_daily_monitor` persists analysis with notification queuing
disabled. The producer then accepts only packet results whose status is `created` or
`already_exists` and whose returned packet path is an existing file.

Only after that check does it queue the digest and stock intents. Each pending payload is committed
with packet ID, market, assessment date, contract version, and provisional state
`packet_bound_pending_hold`. This provisional state is non-deliverable. The hold step promotes it
to `held`; retry and fallback selection require an identity-matching packet file.

If a production persistence condition fails:

```text
analysis evidence = preserved
packet = absent
new delivery intent = 0
Telegram = 0
result = packet_not_ready
```

Shadow readiness is separate under `shadow-cohort-readiness-v1`. When production is safe but the
shadow cohort is not ready, the immutable packet still persists, delivery intents are bound and
held, AI claimability remains false, and deterministic fallback remains reachable. The packet
records the shadow suppression reason with production influence `none`.

A process failure after provisional intent creation remains safe: the packet already exists, the
intent is not selected for delivery, and the next producer attempt can idempotently queue and hold
the same unique rows.

## Pending Semantics

`raw_pending_rows` means database rows whose status column is `pending`. It is not a delivery
eligibility claim.

`deliverable_pending` means a raw pending row whose AI metadata has a retryable state and whose
packet file exists with matching packet ID, market, and assessment date.

`held_session_pending` is the count returned by AI fallback/retry for packet-bound rows in a held,
AI-pending, or fallback-pending session. The fallback `pending_count` reports this value, not the
number of all database rows with `status=pending`.

Thus the 2026-08-22 incident could have raw pending rows while fallback correctly returned zero
held-session pending rows. Packet-less raw rows fail closed and cannot be selected by AI retry or
fallback.

## Retry And Fallback

The three producer entries independently resolve the same role target. On non-trading days all
three return `safe_noop`. The 16:22/16:25/16:30 delivery retry and 17:10 fallback inspect only valid
packet bindings; packet-less raw rows produce `no_pending_ai_delivery` or `no_held_session` with
zero sends.

On a valid day, producer retries reuse the unique monitor run, packet identity, and notification
unique keys. They cannot create duplicate delivery intents. Persisted AI or fallback retries retain
their existing bounded exactly-once contracts.

## Orphan Reconciliation

`python -m app.jobs.reconcile_kr_orphan_deliveries` is dry-run by default. It requires an exact run
ID/date/packet ID and expected stock/digest counts. It verifies the successful `daily_kr` run,
derives stock identities from immutable run details, selects only those rows plus the KR digest
marker, rejects any sent row or `sent_at`, rejects packet linkage or packet artifacts, and prints
sanitized IDs and payload hashes.

`--apply` changes only the verified rows to the existing `failed` terminal state with reason
`non_trading_day_orphan_no_packet`. It never changes `sent_at`, never marks a row sent, and never
deletes history. A second apply returns `already_reconciled` with zero changes.

The Stage A report counted seven stock rows. The evidence lock found one companion KR digest row,
so the exact incident contract verifies `stock=7`, `digest=1`, and reconciles all eight in one
transaction.

## Natural Proof Lifecycle

After deterministic validation and deployment:

```text
KR_NON_TRADING_DAY_PRODUCER_REPAIR = DEPLOYED_PENDING_NATURAL
KR_NON_TRADING_DAY_NATURAL_PROOF = PENDING
```

A later weekend or XKRX holiday may become LIVE PASS only when producer analysis, provider calls,
notification rows, packet writes, and Telegram sends are all zero and every scheduled path exits
normally. No manual production run is valid proof.
