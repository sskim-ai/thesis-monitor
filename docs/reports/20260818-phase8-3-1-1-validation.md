# Phase 8.3.1.1 Validation

Date: `2026-08-18`
Status: `PASS / PHASE 8.3.2 BLOCKED ON PROVIDER DECISION / NO PRODUCTION INTEGRATION`

## Repository

- research branch: `codex/phase-8-3-1-1-peer-provider-decision`;
- base: `ae41d5d2df71e41ac1e3ce3ad31621e6b1cdd905`;
- research commit: `07d4d89a190817a7209946bf58aaf0f9710207cc`;
- clean peer-only branch: `codex/integration-phase-8-3-peer-only`;
- clean base: `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d` (`origin/main`);
- clean validation commit: `e17d992c4c5d40030294eff5a74504e88ab35911`;
- main merge and operating deployment: `0`.

The original Phase 8.3 chain includes the six-commit KRX experimental ancestry. Direct code and
schema inspection plus a clean cherry-pick prove the peer contract has `GIT_ANCESTRY_ONLY`, not a
KRX code or schema dependency. The clean branch is two commits ahead of main: peer implementation
and clean-path documentation. It contains zero KRX provider, readiness, publication, observer, or
Phase 8.2A test files.

## Provider Decision

No provider passes every hard gate from public evidence alone. S&P Global Market Intelligence,
FactSet, and LSEG are technically viable but require entitlement-specific confirmation for derived
end-user display, external LLM processing, storage, and the exact purchased datasets. FnSpace's
standard license is not suitable for production display/database use. DeepSearch remains
commercially and PIT-contract unknown. Intrinio Startup/Enterprise is the most concrete lower-cost
US candidate, but the Order Form must explicitly authorize hosted-LLM processing and Telegram
derived output, and its ADR-ratio/PIT reconstruction fields still require a POC.

Result: `BLOCKED_ON_PROVIDER_DECISION`. The next action is a vendor commercial inquiry and
entitlement decision, not an adapter. Trailing peer data may later enter as Phase 8.3.2A and
consensus history as 8.3.2B.

## Contract Results

- historical series was not mislabeled as true point-in-time;
- fundamentals PIT and consensus PIT were evaluated separately;
- TSM/SKHY ADR ratios remain `PARTIAL/UNKNOWN`, never inferred;
- GOOG/GOOGL issuer dedup support was evaluated separately from ticker coverage;
- user-visible display, redistribution, AI input/output, and storage rights were separated;
- unpublished institutional pricing was not invented;
- marketing coverage was not converted into measured coverage;
- measured visible peer coverage remains `0/20` and meaningful broad-provider coverage remains
  `NOT_YET_MEASURED`.

## Clean-Branch Equivalence

Read-only replay of the immutable 2026-08-18 active universe matched the original Phase 8.3 audit:
20 assessments, 7 KR, 13 US, zero visible peer states, identical fixture/metric/state/safety data.
The clean branch therefore preserves fail-closed behavior without importing KRX experimental code.

## Validation

- research branch local suite: `1,079 passed`, one existing Starlette/httpx warning;
- clean branch local suite: `1,054 passed`, the same warning;
- clean focused peer replay/tests: `47 passed`;
- Ruff and `git diff --check`: `PASS` on both branches;
- JSON parsing and persistent-document tests: `PASS`;
- Investment Knowledge SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`;
- Chart Knowledge SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`;
- Public Action: `0.4.5`; operation IDs: `20/20` unique;
- clean exact-SHA GitHub Actions Test/Lint:
  [run 32147478094](https://github.com/sskim-ai/thesis-monitor/actions/runs/32147478094), `PASS`;
- research exact-SHA GitHub Actions Test/Lint:
  [run 32147674683](https://github.com/sskim-ai/thesis-monitor/actions/runs/32147674683), `PASS`.

Official product, API, pricing, legal, entitlement, and redistribution sources were used. Public
links resolved; S&P pages returned bot-protection responses to command-line checks but were
retrievable through the official browser-facing pages. Unknown legal rights remain explicitly
`UNKNOWN_REQUIRES_VENDOR_CONFIRMATION`.

## Operating Boundary

Operating main remains clean at `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`. No DB migration,
Telegram send, Scheduled Task run/configuration, Pilot mutation, credential exposure, restart, or
Production Assist change occurred. Production Assist remains `OFF`; AI mode remains `shadow`.

No newer natural US/KR artifact was present beyond the known 2026-08-18 sessions, so Natural
AI-Assisted Delivery remains `PARTIAL`. KRX's latest committed exact-slot evidence remains four core
endpoints at HTTP 200/zero rows and `MARKET_COMPLETED_PROVIDER_PENDING`; 16:05, 08:05, and T+1 roles
remain `NOT_YET_PROVEN`.

