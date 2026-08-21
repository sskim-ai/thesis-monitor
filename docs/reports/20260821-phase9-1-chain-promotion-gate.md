# 2026-08-21 Phase 9.1 Chain Promotion Gate

## Gate inputs

| Gate | Result |
|---|---|
| KR natural P0 | `0` |
| KR shared-runtime material P1 relevant to 9.1 | `0` |
| KR delivery / exactly-once | PASS, `8/8`, duplicates `0` |
| Phase 9.0E KR negative control | PASS, selected/injected/leaked `0/0/0` |
| KRX telemetry | capture PASS; provider pending, parallel P2 |
| Night-futures safety | PASS; latest unavailable, stale suppressed |
| Night-futures promotion impact | isolated P1, no Phase 9.1/shared-runtime dependency |
| Phase 9.1A P0/P1 / runtime diff | `0/0` / `0` |
| Phase 9.1B P0/P1 / runtime diff | `0/0` / `0` |
| Phase 9.1C P0/P1 / runtime diff | `0/0` / `0` |
| Public Action / schema | `0.4.5` / `4`, unchanged |

## Chain and ancestry

```text
33c2f8be376b2cbb2961ecf9dc3c873715e0a034  main before review
  -> d4a4daf08ff5f68bc1072cc065e69ca5de5da145  Phase 9.1A
  -> 2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6  Phase 9.1B
  -> d0dc76a2446ee5ef9188d1b06dcb241df004c143  Phase 9.1C
```

All three `git merge-base --is-ancestor` transitions passed. The chain is ten commits ahead of the pre-review main; all instruction commits are present.

## CI and local validation

| Final | GitHub Actions | Local evidence |
|---|---|---|
| `d4a4daf...` | run `32447671565`: Test/Lint PASS | Phase 9.1A reports PASS |
| `2ea8c43...` | run `32450583477`: Test/Lint PASS | Phase 9.1B reports PASS |
| `d0dc76a...` | run `32454792051`: Test/Lint PASS | Phase 9.1C reports PASS |

Combined branch validation before promotion: focused working-capital suites `60 passed`; full suite `1324 passed` with one existing Starlette deprecation warning; Ruff PASS; `git diff --check` PASS; project-state JSON PASS. New working-capital modules have no production import path, so runtime/user-visible diff remains `0`.

## Severity and independence

- P0 open: `0`
- P1 open: `1`, night-futures publication-time/attempt-telemetry issue only
- P1 affecting Phase 9.1 or shared promotion safety: `0`
- P2 open: `3`, KR typed-prose quality, KRX same-day publication timing, and optional stale internal-item hardening

The night-futures P1 degrades morning context, but the expected session was correct and stale data was fail-closed. It is operationally and code-path independent from the zero-runtime-diff Phase 9.1 working-capital chain.

## Explicit gate

```text
PHASE_9_1_CHAIN_PROMOTION_READY = YES
```

Promotion method: push the exact Phase 9.1C final `d0dc76a2446ee5ef9188d1b06dcb241df004c143` to `origin/main` by clean fast-forward, then fast-forward the operating checkout. The review-only instruction/reports branch is not part of main promotion.

Promotion result: **PASS**. `origin/main` and the operating checkout were fast-forwarded to `d0dc76a2446ee5ef9188d1b06dcb241df004c143`. Final operating evidence is recorded in `20260821-phase9-1-operating-promotion.md`.
