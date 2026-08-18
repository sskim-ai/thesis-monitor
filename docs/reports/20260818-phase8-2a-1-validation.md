# Phase 8.2A.1 Validation

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Status: EXPERIMENTAL / ARCHIVE ONLY

## Results

- Listing-date root cause: documentation wording error; implementation denominator was correct.
- Universe contract: CLOSED; version remains `krx-kospi-kosdaq-common-share-v1`.
- Aggregate/KOSPI/KOSDAQ denominator change: 0.
- Breadth reconciliation: PASS.
- Current-session readiness state machine: PASS retrospective.
- 2026-08-18 state: `MARKET_COMPLETED_PROVIDER_PENDING`; promotion denied.
- First complete publication observation: NOT_YET_OBSERVED.
- Sector semantic: `sector_price_proxy`; sector breadth promotion 0.
- Market-wide investor flow: UNSUPPORTED; zero substitution 0.
- Numeric registry: 76/76 registered, unsupported 0.

## Breadth After Audit

| Scope | Eligible | Advance | Decline | Unchanged | Advance ratio | Equal weight |
|---|---:|---:|---:|---:|---:|---:|
| Aggregate | 2,532 | 1,441 | 898 | 193 | 56.9% | 0.78% |
| KOSPI | 804 | 575 | 180 | 49 | 71.5% | 1.30% |
| KOSDAQ | 1,728 | 866 | 718 | 144 | 50.1% | 0.53% |

## Validation Commands

- Focused tests: 96 passed
- Full pytest: 1,062 passed; one existing dependency deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action 0.4.5; operationId 20/20 unique: PASS
- Implementation commit: `f90f686fd261a4eb19b6132e79389e8351cc87b2`
- GitHub Actions run `32132655162`: Test/Lint PASS

## Safety

- Main merge: 0
- Operating deployment/restart: 0
- Scheduled Task changes/executions: 0
- Telegram sends: 0
- Pilot mutations: 0
- DB mutations: 0
- Production Assist: OFF

Historical capability remains PASS. Current-session readiness remains PARTIAL until a normal-session
complete observation; this archive result does not replace natural Phase 8.5.x AI-assisted proof.
