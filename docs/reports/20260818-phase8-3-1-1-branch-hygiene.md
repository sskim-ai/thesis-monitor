# Phase 8.3.1.1 Branch Hygiene

Date: `2026-08-18`
Status: `PASS / CLEAN PEER-ONLY PATH PREPARED / NO PROMOTION`

## Graph At Start

All refs share merge base `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d` with `origin/main`.

| Ref | SHA at audit | Behind main | Ahead main | Unique scope |
|---|---|---:|---:|---|
| `origin/main` and operating | `e925ee0` | 0 | 0 | Phase 8.5.x operating shadow baseline |
| KRX experimental final | `b94f709` | 0 | 6 | three KRX implementation and three KRX docs/evidence commits |
| Phase 8.3 final | `ffafccc` | 0 | 9 | six KRX plus three peer commits |
| Phase 8.3.1 final | `ae41d5d` | 0 | 11 | KRX, peer, and two provider-research commits |

## Commit Classification

| Class | Commits |
|---|---|
| KRX-only implementation | `0bf8921`, `f90f686`, `cd28401` |
| KRX docs/tests/evidence | `52d37dd`, `b4c70c8`, `b94f709` |
| workflow shared/mixed | `82b95cd` |
| peer implementation/tests/evidence | `37a7854` |
| peer docs with mixed KRX lane state | `ffafccc` |
| provider research/docs | `711204a`, `ae41d5d` |

## Hidden Dependency Result

The peer implementation, evidence script, and focused tests contain no imports or references to the
KRX provider, publication service, readiness state machine, telemetry observer, market cross-section
provider, or Phase 8.2A scripts. The Phase 8.3 implementation commit cherry-picked onto latest main
without conflict. Result: `GIT_ANCESTRY_ONLY`.

Mixed persistent docs have `DOC_DEPENDENCY` because they report the KRX lane. There is no
`CODE_DEPENDENCY` or `SCHEMA_DEPENDENCY`.

## Clean Branch

`codex/integration-phase-8-3-peer-only` was created from exact `origin/main`. Phase 8.3 implementation
commit `37a7854` replayed as `9828bb1`, then the minimum peer architecture navigation and clean-branch
validation evidence were added. The branch intentionally excludes every KRX provider/readiness/
publication file and all six KRX commits.

Read-only behavioral replay matched the original Phase 8.3 audit for all material objects: 20
assessments, 7 KR, 13 US, zero visible peer states, all mandatory fixtures, metric status counts,
state audits, and safety flags.

## Promotion Paths

- Path A, KRX first: `main -> separately approved KRX chain -> reviewed peer chain`.
- Path B, peer first: `main -> codex/integration-phase-8-3-peer-only`; KRX commits excluded.

The clean branch is available, not approved, merged, deployed, or active. Existing branches were
preserved. Remote deletion, force push, history rewrite, tag rewrite, main merge, and operating
deployment are all `0`.
