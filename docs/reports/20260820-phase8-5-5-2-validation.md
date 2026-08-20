# Phase 8.5.5.2 Validation

Date: 2026-08-20

## Immutable Replay

- Run-29 semantic/numeric validation errors: `0`
- Runtime quality: `PASS`
- Final language: `PASS`
- Receipt verification: `PASS`
- Structured supply claims preserved: `PASS`
- Current RR cross-section duplicates: `0`

## Regressions

- Run-28 validation: `[]`; quality `PASS`
- Run-27 quality through run-28 replay: `PASS`
- Numeric provenance: automatic `112`, manual `0`, rejected `0`, unresolved `0`.

## Full Validation

- Focused implementation tests: `50 passed`, one upstream warning.
- Full pytest: `1120 passed`, one upstream warning.
- Ruff: `PASS`.
- `git diff --check`: `PASS`.
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.
- Public Action: `0.4.5`; operationId: `20/20` unique.
- Implementation exact SHA `9d105ffb56dd88ef1629cebdcee435522c6d234c`: Actions Test/Lint `PASS`, run `32353318455`.
- Readiness exact SHA `be2fb8f03175803e2f21f21ffa3e04269fad15fa`: Actions Test/Lint `PASS`, run `32354119221`.

## Operating Verification

- Promotion: clean linear fast-forward to `main` and operating checkout.
- API: restarted; `http://127.0.0.1:8766/health` returned `{"status":"ok"}`.
- Operating smoke: `497 passed`.
- AI mode: `shadow`; policy `daily-review-v3.10`; schema `4`; Production Assist `OFF`.
- Four AI-review tasks: `ACTIVE`, operating checkout, times unchanged at 08:15/08:30/16:15/16:55.
- KRX exact-slot agent: loaded with 08:05/16:05 calendar triggers, last exit `0`, user-visible integration `false`.
- Manual Telegram/task/Pilot/DB mutations, archive/receipt rewrites: `0`.

The final documentation SHA and its exact-SHA Actions result are resolved from Git and the linked
[promotion report](20260820-phase8-5-5-2-shadow-promotion.md); documentation commits do not embed a
self-referential SHA.
