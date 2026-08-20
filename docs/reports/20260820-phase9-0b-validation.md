# Phase 9.0B Validation

## Repository

- Branch: `codex/phase-9-0b-canonical-ocf-capex-fcf-core`
- Base: `970ad2c3a1844e6dcbddbf47dff17d71170852d2`
- Implementation SHA: resolved by `git rev-parse HEAD` after commit
- Main/operating before promotion: `970ad2c3a1844e6dcbddbf47dff17d71170852d2`

## Canonical Evidence

- Active universe: 20; KR 7; US/foreign 13
- OCF: 12 eligible, 7 partial, 1 blocked
- PPE CAPEX: 11 eligible, 6 partial, 2 blocked, 1 not applicable
- FCF: 11 eligible, 8 blocked, 1 not applicable
- Phase 9.0A status drift: 0
- Derived FCF Facts: 191
- Complete input lineage and exact arithmetic: 191/191, 100%
- SEC network calls: 0; stored cache hits: 13
- OpenDART network calls/canonical promotions: 0/0

## Tests

- Canonical core focused suite: 61 passed
- Phase 8.5.x, price/RR, delivery, night-futures, and KRX focused regression: 225 passed
- Full pytest: 1,181 passed; one existing Starlette/httpx deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Project-state JSON and documentation links: PASS

## Contract Parity

- Investment Knowledge SHA: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`, three-way parity PASS
- Chart Knowledge SHA: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`, two-way parity PASS
- Public Action: `0.4.5`
- operationId: 20/20 unique
- Output schema: 4, unchanged
- Production packet/API/job imports of Phase 9.0B services: 0

## Operating Read-Only

- API health before promotion: PASS on `127.0.0.1:8766`
- Four AI Scheduled Task definitions/configuration changes: 0
- KRX telemetry LaunchAgent: 08:05/16:05 calendar-loaded, last exit 0
- Latest natural KRX 16:05 capture: HTTP 200, zero rows, `MARKET_COMPLETED_PROVIDER_PENDING`
- KRX user-visible integration: 0
- Manual Telegram / Scheduled Task / Pilot / DB / archive mutations: 0 / 0 / 0 / 0 / 0
- Production Assist: OFF

## Pending Exact-SHA Gate

Implementation and final documentation GitHub Actions Test/Lint must pass before main and operating fast-forward. No deployment occurs inside the 07:55-08:40 KST protection window.

Local P0 open: 0. Local P1 open: 0.

`PHASE_9_0C_READY = YES_CANDIDATE_PENDING_EXACT_SHA_CI`

`PHASE_9_0C_SCOPE = CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY`
