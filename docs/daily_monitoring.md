# Daily Thesis Monitoring

## Custom GPT behavior

When the user says a phrase such as "종목 앞으로 모니터링해줘":

1. Resolve the company to a canonical ticker.
2. Read company profile, earnings checkpoints, and recent thesis events.
3. Draft a concrete thesis with strengthening, weakening, and invalidation signals.
4. Call `monitorStock` with the ticker, company, and structured thesis.
5. Confirm the stored thesis version to the user.

When the user asks to stop monitoring, call `stopMonitoringStock`. Deactivation preserves all thesis
versions and assessment history.

## Daily decision rules

- `strengthened`: provide separate new-buyer and holder-management views.
- `weakened`: distinguish thesis damage from price support and assign a risk level.
- `mixed`: preserve both positive and negative evidence for review.
- `invalidation_candidate`: alert but keep monitoring until the evidence is strong enough.
- `invalidated`: only confirmed when an explicit invalidation signal matches a high-relevance filing
  from OpenDART, SEC EDGAR, or company IR. The watchlist item is then deactivated, not deleted.
- `no_material_change`: store history without sending a notification.

All assessments preserve confirmed evidence URLs and keep technical price position separate from
fundamental fair-value conclusions.

Each dated assessment also stores a cumulative `thesis_snapshot`: the approved base thesis, current
status, and deduplicated supporting, weakening, and invalidation evidence known on that date. The base
thesis changes only when the user or Custom GPT submits a revised version.

## Runtime and recovery

- Primary schedule: every day at 08:00 Asia/Seoul.
- Retry schedule: 08:15 and 08:45.
- Provider calls retry with exponential backoff.
- OHLCV and event-provider partial results are retained.
- Notification delivery uses a persistent outbox and remains `dry_run` until Kakao is configured.
- Successful date-level runs are idempotent.
