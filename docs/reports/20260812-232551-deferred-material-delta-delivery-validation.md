# Deferred Material Delta Delivery Validation

## Scope

- Base: `0038c44615c0cc691a8e1dec56dafeac9fce202d`
- DB migration: none
- Public Action contract: unchanged (`0.4.5`, 20 unique operationIds)

## Root Cause

Pending-baseline protection retained the initial-baseline payload when a same-version
daily delta arrived. The daily monitor then dispatched the baseline and returned without
queuing the already evaluated material delta a second time. Because the event fingerprint
had already been consumed, a later evaluation could not safely reconstruct that message.

Before:

```text
baseline pending
-> D evaluated and fingerprint consumed
-> baseline protected and sent
-> D notification absent
```

After:

```text
baseline pending
-> D evaluated and fingerprint consumed
-> immutable D logical payload deferred
-> baseline sent
-> D promoted and sent
```

The production-level regression invokes `run_daily_monitor()` with notification queueing
and dispatch enabled. Baseline and D are sent in order without a manual second call to the
stock queue function.

## Storage And Dedupe

Deferred stock notifications are stored inside the existing
`NotificationDelivery.payload._stock_notification` JSON metadata. Each FIFO item contains
the already sanitized and rendered logical notification payload, its SHA-256 hash, thesis
version, assessment mode, queue timestamp, queue reason, and relevant event fingerprints.

The item is self-contained and does not depend on reloading or re-rendering the mutable
same-day `ThesisAssessment` row. Active and deferred logical hashes provide stable dedupe;
repeated queueing of the same D assessment produces one deferred item.

No non-material daily assessment is deferred. A no-news rerun updates audit context while
retaining existing D/E/F payloads.

## Multiple Delta Ordering

Validated FIFO sequence:

```text
active: baseline
deferred: D, E, F
dispatch: baseline -> D -> E -> F
```

The dispatcher fixes its processing budget at the active item plus the deferred count seen
at invocation start. It does not consume an unbounded stream of newly added work.

## Retry And Partial Delivery

- Baseline failure keeps baseline active and D/E deferred; no delta is sent first.
- After baseline succeeds, D is promoted with attempts and Telegram chunk state reset.
- If D fails, D remains active and E/F stay deferred.
- If D partially succeeds, its persisted chunk cursor is retained on retry.
- D must finish before E is promoted; message chunks cannot interleave.
- Changes to queue-only audit metadata do not alter the active Telegram content hash.

The normal Telegram success-response/local-commit crash window remains. This provides
persisted ordered resume and dedupe, not a client-side exactly-once guarantee.

## New Thesis Version

A newer initial baseline supersedes the old version's active and deferred stock messages.
The new baseline becomes active, attempt and Telegram progress reset, and internal audit
metadata records the supersede reason and discarded logical hashes. Event fingerprints are
not rolled back or reintroduced as new facts.

## Fingerprints And Audit

Event fingerprints are consumed during investment evaluation, independently of Telegram
success. Deferred item provenance records the relevant fingerprints, while active delivery
version/mode, current assessment version/mode, active hash, deferred count and hashes,
promotion reason, supersede reason, and retry transition remain internal metadata.

User-facing Telegram text does not expose deferred queue fields, delivery state, logical
hashes, assessment mode, thesis version, provider/parser fields, or other audit metadata.

## History Limitation

`ThesisAssessment` remains unique by `(ticker, assessment_date)`, so same-day rows for
multiple thesis versions are not retained independently. Deferred logical payloads are
immutable with respect to that overwrite, so notification delivery does not depend on a
future schema migration. Separate same-day version history remains a known limitation.

## Validation

- Starting baseline: 413 tests passed
- Targeted stock notification/daily-monitor tests: passed
- Full `pytest`: 419 passed
- `ruff check .`: passed
- `git diff --check`: passed
- GitHub Actions: pending push at report creation
