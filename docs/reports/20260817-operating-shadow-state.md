# Operating Shadow State

Observed: `2026-08-17 20:14 KST`

## Code

| Item | State |
|---|---|
| Repository | `sskim-ai/thesis-monitor` |
| Operating checkout | `/Users/sskim/Codex/thesis-monitor` |
| Operating branch | `main` |
| Promoted code SHA | `2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf` |
| Operating worktree | clean |
| Exact code-SHA Actions | PASS, run `32023730416` |
| Final docs SHA | resolve with `git rev-parse origin/main` after release docs merge |

## Services

| Service | State | Path / result |
|---|---|---|
| Thesis Monitor API | running after restart | operating checkout, `/health` PASS |
| US deterministic monitor | loaded, idle | 08:05/08:10/08:15/08:20, last exit 0 |
| KR deterministic close | loaded, idle | 16:05/16:20/16:50, last exit 0 |
| AI fallback | loaded, idle | 08:40/17:10, last exit 0 |
| Persisted delivery retry | loaded, idle | configured bounded slots, last exit 0 |

## Codex Scheduled Tasks

| Task | Status | Schedule | Model | CWD |
|---|---|---|---|---|
| Thesis Monitor AI Review US Primary | ACTIVE | 08:15 KST | GPT-5.6 Sol/high | `/Users/sskim/Codex/thesis-monitor` |
| Thesis Monitor AI Review US Backup | ACTIVE | 08:30 KST | GPT-5.6 Sol/high | `/Users/sskim/Codex/thesis-monitor` |
| Thesis Monitor AI Review KR Primary | ACTIVE | 16:15 KST | GPT-5.6 Sol/high | `/Users/sskim/Codex/thesis-monitor` |
| Thesis Monitor AI Review KR Backup | ACTIVE | 16:55 KST | GPT-5.6 Sol/high | `/Users/sskim/Codex/thesis-monitor` |

Each task requires Pilot v3, policy v3.10, schema 4, OHLCV structure v2, renderer v3, security
identity v2, and financial-quality taint v2. Manual executions during this release: `0`.

## Safety State

- Production Assist: OFF.
- AI mode: shadow.
- Runtime Pilot: KR 3/5, US 3/5.
- Telegram sends caused by promotion: 0.
- Pilot mutation caused by promotion: 0.
- DB migration: none.
- Scheduled Task configuration change: none.
- Single-delivery, fallback, receipt, and exactly-once contracts: unchanged.

## Latest Immutable Runtime

- US packet `2026-08-17-us-run-22-217ce9f324b9`: completed and validation passed under the prior
  operating code; it remains US Pilot Day 3/5.
- KR packet `2026-08-17-kr-run-23-378ee562573e`: pre-send validation rejected, AI send zero,
  deterministic fallback sent, Pilot unchanged. Its immutable status was not rewritten.

The promoted RR repair has passed read-only replay but has not yet run in a natural KR session.
Current-Price RR Packet/Numeric Path therefore remains PARTIAL and Natural Live Validation remains
OPEN.

## Next Natural Observation

1. Confirm the packet/runtime metadata comes from the promoted operating checkout.
2. Verify exchange-calendar session and OHLCV freshness.
3. Verify Phase 8.5 framework routing and full schema validation.
4. For KR, verify exact RR Fact, semantic, binder, and claim paths when RR is calculable.
5. Verify receipt, one-set delivery or fallback, archive completion, and exactly-once Pilot ordering.
6. Human-review the full message; operational success alone is not Production Assist evidence.
