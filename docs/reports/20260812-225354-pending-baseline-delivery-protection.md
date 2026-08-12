# Pending Baseline Delivery Protection

## Scope

- Base: `fb1f3292f51feab8f29a20028685e9fd369a9de4`
- DB migration: none
- Public Action contract: unchanged (`0.4.5`, 20 unique operationIds)

## Scenario

The protected sequence is:

```text
v1 notification sent
-> v2 initial baseline queued
-> Telegram delivery remains pending, failed, or partial
-> v2 material daily delta is evaluated
-> v2 baseline payload remains the delivery content
-> baseline is sent
-> a later material v2 delta can be queued normally
```

Before this change, the same-version pending refresh replaced the v2 baseline payload
with the latest daily-delta payload. A user could therefore receive a delta without ever
receiving the new thesis version's baseline.

## Delivery Decision

An undelivered baseline is protected only when ticker, assessment date, channel, and
thesis version match; the stored delivery content is `initial_baseline`; the delivery is
not sent; and the current assessment is `daily_delta`.

The existing logical payload stays unchanged. Updating internal stock-notification audit
metadata does not alter the Telegram content fingerprint, so attempt count and persisted
chunk cursor remain intact. A failed row returns to pending under the existing retry
policy without replacing the baseline body.

A newer thesis version's initial baseline still supersedes an older pending baseline. In
that case attempts and Telegram chunk progress reset as before.

## Ordering And Idempotency

- Pending v2 baseline plus v2 delta: baseline payload retained.
- Partial v2 baseline plus v2 delta: baseline chunk cursor retained.
- Sent v2 baseline plus material v2 delta: delta payload queued once.
- Sent v2 delta plus same-v2 rerun: duplicate remains suppressed.
- Pending v2 baseline plus v3 baseline: v3 payload replaces v2 and progress resets.

Investment evaluation, warning state, evidence, and event fingerprints continue to update
independently. This change controls delivery order only.

## Audit Metadata

Internal `_stock_notification` metadata separates:

- `delivery_thesis_version` and `delivery_assessment_mode` for the queued Telegram body;
- `current_thesis_version` and `current_assessment_mode` for the latest assessment;
- delivery protection, retry reason, previous status, and status transition.

The protected state can therefore represent current `daily_delta` assessment data while
the delivery content remains `initial_baseline`. These fields are not rendered into the
Telegram message.

## Partial Retry Validation

The three-chunk regression sends chunk 1, fails on chunk 2, evaluates a daily delta, and
then resumes with chunks 2 and 3. The cursor remains at `next_chunk_index=1`, the attempt
count remains unchanged during queue protection, and the retry does not prepare or send
chunk 1 again.

## History Limitation

`ThesisAssessment` remains unique by `(ticker, assessment_date)`. Same-day assessment rows
for multiple thesis versions are therefore not retained separately. Calculation, renderer,
and notification provenance remain version-correct without a migration; separate same-day
version history would require a future schema change.

## Validation

- Targeted notification and same-day version tests: passed
- Full `pytest`: 413 passed
- `ruff check .`: passed
- `git diff --check`: passed
- GitHub Actions: pending push at report creation
