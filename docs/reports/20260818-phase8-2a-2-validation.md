# Phase 8.2A.2 Validation

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Base main: `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`
Implementation: `cd284013075d6b846f3614e694517a17a5c755bf`
Status: ENGINEERING PASS / PUBLICATION OBSERVATION PARTIAL / NOT DEPLOYED

## Results

- `krx-publication-readiness-v1`: PASS.
- `krx-publication-telemetry-v1`: PASS.
- `krx-time-slot-provider-role-v1`: PASS.
- HTTP 200 with zero rows remains provider-pending, never success or zero-valued market data.
- Initial complete observation records only `observed_complete_by`; false `first_complete_at` precision
  is denied.
- Pending/partial-to-complete transitions produce an observation interval, not an asserted provider
  publication timestamp.
- Append-only JSONL rejects duplicate/non-monotonic observation times and mixed target sessions.
- Same-day, next-morning, T+1, and historical roles are independently gated.
- No live role can become `SUPPORTED` from one successful session.
- Current row-count plausibility: `NOT_EXERCISED`; all core results were empty, so no complete bundle
  or canonical current snapshot was promoted.

## 2026-08-18 Observation

The completed XKRX session remained `MARKET_COMPLETED_PROVIDER_PENDING` through the formal 21:06:36
KST observer run. All four core endpoints returned HTTP 200 with zero rows and no provider date.
First non-empty, first complete, and observed complete remain `NOT_YET_OBSERVED`. Current-session
readiness therefore remains PARTIAL.

## Provider Roles

| Role | Result |
|---|---|
| 16:05 same-day close primary | `NOT_YET_PROVEN` |
| 08:05 next-morning primary | `NOT_YET_PROVEN` |
| T+1 authoritative reconciliation | `NOT_YET_PROVEN` |
| historical archive retrieval | `SUPPORTED` |

The evening pending observation is not relabeled as exact 16:05 evidence.

## Historical Regression

The immutable 2026-08-14 cache remains unchanged:

- Raw: 2,763
- Eligible: 2,532
- Excluded: 231
- Aggregate: 1,441 advance / 898 decline / 193 unchanged
- KOSPI: 804 eligible / 575 advance / 180 decline / 49 unchanged
- KOSDAQ: 1,728 eligible / 866 advance / 718 decline / 144 unchanged
- `advance + decline + unchanged == eligible`: PASS

Publication telemetry changed no breadth, universe, index, sector, or numeric semantic value.

## Validation Commands

- Focused provider/publication/calendar/cross-section/docs tests: 36 passed
- Full pytest: 1,068 passed; one existing Starlette/httpx deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge canonical/runtime/upload SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge canonical/runtime SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action 0.4.5; operationId 20/20 unique: PASS
- Implementation GitHub Actions run `32135724640`: Test/Lint PASS

## Safety

- Read-only KRX calls: 8 / 10,000 daily limit (0.08%)
- Credential exposure: 0
- Main merge: 0
- Operating deployment/restart: 0
- Production Scheduled Task changes/executions: 0
- Telegram sends: 0
- Pilot mutations: 0
- DB mutations: 0
- Production Assist: OFF

Phase 8.2A.2 does not close current-session readiness or authorize shadow promotion. Natural
Phase 8.5.x AI-assisted delivery proof remains a separate pending operating concern.
