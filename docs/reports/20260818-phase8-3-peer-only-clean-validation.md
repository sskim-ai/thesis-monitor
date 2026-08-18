# Phase 8.3 Peer-Only Clean Integration Validation

Date: `2026-08-18`
Branch: `codex/integration-phase-8-3-peer-only`
Base: `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d` (`origin/main`)
Status: `PREPARED / VALIDATED / NOT PROMOTED`

## Construction

The Phase 8.3 implementation commit `37a7854` replayed cleanly onto the latest operating main as
`9828bb1`. The branch contains peer implementation, tests, architecture, and immutable peer evidence.
It contains none of the KRX provider, publication-readiness, telemetry, observer, or Phase 8.2A test
files from the six-commit KRX experimental chain.

## Dependency Result

The original Phase 8.3 branch has KRX Git ancestry, but the peer implementation has no KRX import,
schema, provider, readiness-state, or runtime symbol dependency. Classification:
`GIT_ANCESTRY_ONLY`, with KRX lane references confined to mixed persistent documentation outside
this clean reconstruction.

## Behavioral Equivalence

A read-only replay against the immutable 2026-08-18 operating assessment archive matched the
original Phase 8.3 audit for assessment count, market counts, snapshot metric statuses, mandatory
fixtures, all peer states, and safety fields:

- assessments: `20` (`7 KR`, `13 US`);
- user-visible peer states: `0`;
- ticker hard-code, renderer calculation, AI calculation, Telegram send, DB mutation, deployment: `0`.

Fail-closed suppression is therefore behaviorally identical. The result does not make the feature
operating or solve the broad-provider gap.

## Validation

- focused peer/monitoring/industry tests: `47 passed`;
- full clean-branch suite: `1,054 passed`, one existing Starlette/httpx deprecation warning;
- Ruff: `PASS`;
- diff check: `PASS`;
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`;
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`;
- Public Action version: `0.4.5`; operation IDs: `20/20` unique;
- KRX implementation leakage: `0 files`;
- main merge, operating deployment, DB migration, Telegram, Scheduled Task, Pilot: `0`.

The original Phase 8.3 chain has 25 additional KRX tests, explaining its `1,079` total. This branch
is a promotion-ready path only; any future promotion still requires explicit approval and exact-SHA
CI at that time.
