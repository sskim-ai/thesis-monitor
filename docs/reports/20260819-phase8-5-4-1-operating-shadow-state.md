# Phase 8.5.4.1 Operating Shadow State

Observed: `2026-08-19 KST`

## Code And Service

| Item | State |
|---|---|
| Operating checkout | `/Users/sskim/Codex/thesis-monitor` |
| Branch | `main` |
| Phase 8.5.4 code | `3a6547e394452e6e1b986a8193f56c98fd07ef89` |
| Worktree | clean |
| API LaunchAgent | `com.seungsoo.thesis-monitor`, running after restart |
| API endpoint | `127.0.0.1:8766` |
| Health | PASS |
| Policy/schema | `daily-review-v3.10` / `4` |
| AI mode | `shadow` |
| Production Assist | OFF |

## Codex Scheduled Tasks

| ID | Status | Schedule | Checkout |
|---|---|---|---|
| `thesis-monitor-ai-review-us-primary` | ACTIVE | 08:15 KST | operating checkout |
| `thesis-monitor-ai-review-us-backup` | ACTIVE | 08:30 KST | operating checkout |
| `thesis-monitor-ai-review-kr-primary` | ACTIVE | 16:15 KST | operating checkout |
| `thesis-monitor-ai-review-kr-backup` | ACTIVE | 16:55 KST | operating checkout |

All four prompts retain Pilot v3, policy v3.10, schema 4, renderer v3, security identity v2 and
financial quality v2. Configuration changes and manual runs were both zero.

## Runtime State

- Pilot state SHA256 before/after:
  `caa91f214441b8a6953e70c59f8edf29933cebefb20b63b8955d2d03a302730c`.
- Persisted Pilot: KR 3/5; US 3/5.
- Latest natural packet remains run-26 fallback evidence; promotion caused no delivery.
- Telegram sends, DB migrations, Pilot mutations and archive rewrites: all zero.

The operating checkout is prepared for the next natural US/KR evidence. No feature phase starts
before that review.

