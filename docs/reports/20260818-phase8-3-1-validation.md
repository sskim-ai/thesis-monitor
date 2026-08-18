# Phase 8.3.1 Provider Research Validation

Date: `2026-08-18`
Branch: `codex/phase-8-3-1-broad-peer-provider-research`
Base: `ffafccc9e71619f2ebc16b0e60b9c2d3d3b75f05`
Status: `PASS RESEARCH / PROVIDER SELECTION OPEN / DEVELOPMENT ONLY`

## Scope Result

- Master Workflow dependency: `PASS`; Phase 8.3 contains six KRX plus three peer commits.
- Phase 8.3 contract: unchanged `PASS`.
- Phase 8.3 capability: unchanged `STRONG PARTIAL`.
- user-visible peer coverage: unchanged `0/20`.
- official provider research: KR and US matrices complete.
- point-in-time/current/forward/security/license distinctions: explicit.
- provider selected: `NO`.
- Phase 8.3.2 entry gate: `NOT MET`.

No production peer adapter or schema was added. No existing numeric, denominator, security,
industry, or qualitative validator was relaxed.

## Official Evidence

Capability claims are sourced from official product, API, pricing, and usage/licensing materials.
Marketing coverage is not treated as entitlement-specific proof. Unknown redistribution, external
AI, PIT, ADR, or share-basis fields remain `UNKNOWN` or a hard gate in the matrices.

## Audit-Only Live Probe

Eight minimal provider requests were attempted with existing environment configuration. Seven
returned parseable responses; Massive was unconfigured and returned an authorization error. No raw
response, valuation number, request header, key, or token was persisted. Finnhub, Alpha Vantage, and
OpenFIGI observations remain audit-only and produced zero canonical Facts.

## Validation

| Check | Result |
|---|---|
| Baseline full pytest | 1,079 passed, 1 existing dependency warning |
| Updated documentation focused | 4 passed |
| Updated full pytest | 1,079 passed, 1 existing dependency warning |
| Ruff | PASS |
| Diff check | PASS |
| project-state JSON | PASS |
| provider scorecard JSON | PASS |
| documentation link/secret checks | PASS |
| Investment Knowledge parity | PASS, `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge parity | PASS, `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` |
| operationId | `20/20` unique, zero missing |
| GitHub Actions | exact final SHA result recorded after push |

The warning is the existing Starlette `httpx` TestClient deprecation and is unrelated to this phase.

## Operating Safety

| Mutation | Count/state |
|---|---|
| main merge | 0 |
| operating deployment/restart | 0 |
| DB migration/write | 0 |
| Telegram send | 0 |
| Scheduled Task run/change | 0 |
| Pilot mutation | 0 |
| provider canonical promotion | 0 |
| credential exposure | 0 |
| Production Assist | OFF |
| AI mode | shadow |

Operating main remains `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`. No natural artifact newer
than the 2026-08-18 US/KR fallback runs was present at final local review, so Natural AI-Assisted
Delivery remains `PARTIAL`. KRX telemetry still has one 21:06 KST pending observation; 16:05, 08:05,
and T+1 roles remain `NOT_YET_PROVEN`, and historical remains `SUPPORTED`.

## Decision

Research acceptance passes, but integration acceptance does not. The next peer step requires a user
provider/cost decision, credential or trial, written storage/display/external-AI rights, mandatory
field confirmation, and an exact active-universe POC. An operating blocker still outranks this work.
