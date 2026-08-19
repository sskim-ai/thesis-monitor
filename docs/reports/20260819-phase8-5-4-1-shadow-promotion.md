# Phase 8.5.4.1 Operating Shadow Promotion

As of: `2026-08-19 KST`

## Repository

| Item | Result |
|---|---|
| Previous main | `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d` |
| Source branch | `codex/phase-8-5-4-natural-live-targeted-repair` |
| Validated source | `3a6547e394452e6e1b986a8193f56c98fd07ef89` |
| Promotion method | clean linear fast-forward |
| Main code | `3a6547e394452e6e1b986a8193f56c98fd07ef89` before this documentation commit |
| Operating code | same validated source, clean |
| Documentation branch | `codex/phase-8-5-4-1-operating-shadow-promotion` |
| Experimental leakage | KRX 8.2A: 0; Phase 8.3: 0 |

## Pre-Promotion Validation

- Full pytest: `1063 passed`, one third-party deprecation warning.
- Focused repair suite: `379 passed`.
- Ruff and `git diff --check`: PASS.
- Investment/Chart Knowledge checksum parity: PASS.
- Public Action `0.4.5`; operationId `20/20` unique.
- Exact source-SHA Actions run `32203088676`: Test/Lint PASS.

## Operating Validation

- Thesis Monitor API restarted from `/Users/sskim/Codex/thesis-monitor`.
- LaunchAgent state: running; health: `{"status":"ok"}`.
- Operating read-only smoke: `430 passed`.
- Runtime policy/schema: `daily-review-v3.10` / `4`.
- AI mode: `shadow`; Production Assist: OFF.
- Four Codex Scheduled Tasks remain ACTIVE with unchanged schedules and checkout.

## Night Futures

The latest expected 2026-08-19 KRX response was empty. Both KOSPI200 and KOSDAQ150 are currently
`LIVE_PAIR_UNAVAILABLE` and will be suppressed. A stale 2026-08-14 NIGHT -> 2026-08-13 DAY pair is
valid for both matching contracts. Same-date wrong-session promotion remains zero.

## PBR Lineage Follow-Up

Current-PBR binding uses an equality-checked redirect from history `current_value` to the canonical
`fields.price_to_book` Fact. An explicit `source_current_fact_id` edge is absent. Status:
`CURRENT_PBR_HISTORY_LINEAGE_EXPLICIT_REF: OPEN_LOW_PRIORITY`.

## Safety

- Manual Telegram sends: 0.
- Scheduled Task manual runs/configuration changes: 0/0.
- Pilot mutations: 0; persisted counts remain KR 3/5 and US 3/5.
- DB migrations/mutations: 0/0.
- Original run-26 archive/receipt rewrites: 0/0.
- Force push/history rewrite/branch deletion: 0/0/0.

Natural AI-Assisted Delivery remains `PARTIAL`. The next state is
`WAIT_FOR_NATURAL_US_KR_PROOF`; Cash Flow / Capital Efficiency remains pending.

