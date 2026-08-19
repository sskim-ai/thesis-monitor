# Phase 8.5.4.2 Operating State

Observed: `2026-08-19 KST`

## Code And Service

| Item | State |
|---|---|
| Operating checkout | `/Users/sskim/Codex/thesis-monitor` |
| Branch | `main` |
| Calendar repair code | `7e7ab5acee2176bc8a452115da19ac6e14d312ab` |
| Working tree | clean |
| API LaunchAgent | `com.seungsoo.thesis-monitor`, running after restart |
| API endpoint | `127.0.0.1:8766` |
| Health | PASS |
| Policy/schema | `daily-review-v3.10` / `4` |
| AI mode | `shadow` |
| Production Assist | OFF |
| Read-only smoke | `494 passed` |

## Scheduled Tasks

| ID | Status | Schedule | Checkout |
|---|---|---|---|
| `thesis-monitor-ai-review-us-primary` | ACTIVE | 08:15 KST | operating checkout |
| `thesis-monitor-ai-review-us-backup` | ACTIVE | 08:30 KST | operating checkout |
| `thesis-monitor-ai-review-kr-primary` | ACTIVE | 16:15 KST | operating checkout |
| `thesis-monitor-ai-review-kr-backup` | ACTIVE | 16:55 KST | operating checkout |

Configuration changes and manual runs were both zero.

## Night Futures

- XKRX predecessor lookup: PASS for the 2026-08-18 -> 2026-08-14 holiday case.
- Contract match and temporal order: PASS for KOSPI200 and KOSDAQ150.
- Provider raw-change cross-check: PASS for both.
- Current expected 2026-08-19 rows: 0.
- Effective current status: `PROVIDER_DATA_PENDING`; current display suppressed.
- Same-date wrong-session promotion: 0.

## Mutation Audit

- Pilot state SHA256 before/after:
  `caa91f214441b8a6953e70c59f8edf29933cebefb20b63b8955d2d03a302730c`.
- Persisted Pilot: KR 3/5; US 3/5.
- Telegram sends, task runs, Pilot mutations, DB changes, archive rewrites and receipt rewrites: 0.

The next action is read-only review of the next natural US/KR sessions. Retrospective calendar repair
does not close Natural AI-Assisted Delivery.
