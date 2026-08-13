# KRX Night Futures Morning Retry Gate Validation

## Scope

- Base: `d41830cfa0bf6fbca33a05cdba9a005675ba663e`
- DB migration: none
- Public Action schema: unchanged (`0.4.5`, 20 operationIds)
- Production source: official KRX night-futures provider only
- Kiwoom capability probe: not connected to production

## Scheduling

- U.S. evaluation: 07:50 KST
- First night-futures gate query: 08:00 KST
- Retry interval: 5 minutes
- Hard deadline: 08:45 KST
- Scheduled gate slots: 08:00, 08:05, 08:10, 08:15, 08:20, 08:25,
  08:30, 08:35, 08:40, 08:45

The 07:50 macro run excludes the KRX provider. It still performs the existing macro calculations and
U.S. stock assessments, then queues the digest and stock notifications with dispatch disabled. Gate
slots call only the KRX provider, patch the stored morning briefing's night-futures observations,
re-render the existing digest, and dispatch the already queued U.S. morning delivery scope.

## Readiness

The gate reuses the XKRX expected latest completed session calculation. Before the deadline, release
requires both canonical series to be fresh for that exact session:

- `KRX_KOSPI200_NIGHT_FUT`
- `KRX_KOSDAQ150_NIGHT_FUT`

An older verified pair remains stale. A one-contract result remains waiting before 08:45. At 08:45,
fresh partial data is rendered and the missing contract receives one compact caution. If neither
contract is fresh, the price section is omitted and one unavailable caution is rendered.

## Isolation

Gate retries do not call:

- event collection
- OHLCV collection
- valuation collection
- thesis evaluation
- macro six-axis calculation

The stored 07:50 assessment remains the source for every non-night-futures part of the message.
NotificationDelivery status is the restart and duplicate-prevention source of truth. A released gate
with a Telegram failure retries only pending delivery state and does not refetch KRX or reset chunk
progress.

## Telemetry

The morning briefing market summary and digest's internal `_morning_gate` metadata preserve:

- expected session
- first query time
- first fresh time for each product
- first complete time
- retry count
- deadline state
- dispatch time

This metadata is excluded from logical Telegram hashes and is never rendered to the user.

## Fixture Results

### Immediate success

- 08:00 query: both products fresh
- retry count: 1
- first complete: 08:00
- dispatch: 08:00
- later duplicate job: no KRX fetch and no Telegram resend

### Delayed success

- 08:00 / 08:05 / 08:10: unavailable
- 08:15: KOSPI200 only
- 08:20: both products fresh
- first complete: 08:20
- dispatch: 08:20
- thesis/macro re-evaluation count during gate retries: 0

### Deadline

- one fresh product at 08:45: fresh product displayed, missing product cautioned
- no fresh product at 08:45: section omitted, one compact caution, dispatch proceeds
- no 08:50 slot exists

### Rendered fixture

```text
🌙 한국 야간선물 · 08/13 기준
• KOSPI200 최근월물 431.25 · +2.85pt (+0.67%)
• KOSDAQ150 최근월물 1,432.50 · -4.20pt (-0.29%)
```

## Validation

- Baseline before change: 446 tests passed
- After change: 455 tests passed
- `ruff check .`: passed
- `git diff --check`: passed
- GitHub Actions: pending at report creation

## Live 2026-08-14 Check

The implementation and LaunchAgent schedule are ready to record the first live production gate on
2026-08-14. That session has not occurred at report creation time. The first query, per-product first
availability, first complete time, retry count, deadline state, and dispatch time must be read from the
persisted gate telemetry after that run; no live result is claimed in advance.
