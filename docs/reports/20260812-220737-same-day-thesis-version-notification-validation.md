# Same-Day Thesis Version Notification Validation

## Scope

- Base: `7db678526043014b6641f0c704d6a83c330c4c54`
- DB migration: none
- Public Action contract: unchanged (`0.4.5`, 20 unique operationIds)

## Before

`NotificationDelivery` is unique by ticker, assessment date, and channel. A sent v1
daily stock delivery therefore blocked the same-day v2 initial-baseline message even
though the assessment and renderer had moved to v2.

## After

The delivery payload records the current thesis version and assessment mode. A sent,
pending, failed, or partially delivered row is reset only when all of these are true:

- same ticker, assessment date, and channel;
- the stored delivery belongs to a different thesis version;
- the current assessment is the new version's `initial_baseline`.

The row is reused without a schema change, but the message is rendered entirely from
the current assessment. The v1 payload and Telegram chunk cursor are not reused.

## Delivery Audit

The internal `_stock_notification` payload metadata records:

- previous and current thesis version;
- current assessment mode;
- previous delivery status;
- requeue reason;
- status transition into pending.

Validated transition:

```text
v1 / sent
-> v2 / initial_baseline
-> pending / new_thesis_version_initial_baseline
-> sent once
```

The rendered Telegram text contains `투자 논리: 초기 설정` and does not expose raw
`thesis_version`, `assessment_mode`, requeue reason, or delivery-state metadata.

## Idempotency And Retry

- A completed v2 baseline followed by the same-v2 force rerun remains sent.
- A same-v2 material event follows the existing daily notification policy; the version
  change exception does not force another stock message.
- A stale v1 pending/failed/partial delivery is replaced by the v2 payload, with attempts
  and Telegram chunk progress reset.
- Same-content retry and ordinary Telegram partial resume remain unchanged.

## Warning Semantics

Assessment-generated v1 warning state is not carried into v2. A ticker-level unresolved
`CanonicalIssue` remains available to rebuild current factual baseline risk independently.

## History Limitation

`ThesisAssessment` remains unique by `(ticker, assessment_date)`, so same-day v1 and v2
assessment rows are not both retained. Calculation, rendering, and notification provenance
are version-correct without a migration, while separate same-day assessment history remains
a known schema limitation.

## Validation

- `pytest`: 409 passed
- `ruff check .`: passed
- `git diff --check`: passed
- GitHub Actions: pending push at report creation
