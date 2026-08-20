# Phase 9.0A Validation

Date: 2026-08-20 KST

Branch: `codex/phase-9-0a-cash-flow-capital-efficiency-architecture`

Base: `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9`

## Evidence

- Active universe: 20, loaded read-only from the operating database
- Official SEC Company Facts: 12 network requests, 12 successes, 1 pre-existing payload
- OpenDART live requests: 0; committed Phase 8.1.1 evidence reused
- Paid sources / new API keys: 0 / 0
- OCF: 12 eligible, 7 partial, 1 blocked
- PPE CAPEX: 11 eligible, 6 partial, 2 blocked, 1 not applicable
- FCF: 11 eligible, 8 blocked, 1 not applicable
- Full CCC / standard ROIC eligible: 0 / 0; both fail closed or defer

## Tests

- Cash-flow contract and generator fixtures: 35 passed
- Focused financial, security, AI quality, delivery, night-futures, and KRX regression: 278 passed
- Full pytest: 1,155 passed; 1 existing Starlette/httpx deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Project-state JSON and Phase 9.0A JSON artifacts: PASS

## Repository Contracts

- Investment Knowledge v3 parity: PASS,
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1 parity: PASS,
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: `0.4.5`
- operationId: 20/20 unique
- Existing static Action exports changed: 0

## Runtime Boundary

- Imports from the new contract into production services/jobs/API: 0
- Packet, prompt, fallback, renderer, provider scheduler, DB schema changes: 0
- User-visible runtime behavior diff: 0
- Manual Telegram / Scheduled Task / Pilot / DB mutations: 0 / 0 / 0 / 0
- Production Assist: OFF
- Four AI-review automations: ACTIVE at 08:15, 08:30, 16:15, 16:55 KST
- KRX telemetry LaunchAgent: calendar-loaded at 08:05 and 16:05, last exit 0
- KRX user-visible integration: 0
- API restart: 0, not required for an unimported architecture-only contract

## Gate

Open P0: 0. Open P1: 0.

`PHASE_9_0B_READY = YES`

`PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`

Exact implementation/final SHA and Actions results are resolved in the final promotion section of
the complete report bundle after GitHub validation.
