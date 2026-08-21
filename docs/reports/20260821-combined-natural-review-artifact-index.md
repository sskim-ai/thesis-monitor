# 2026-08-21 Combined Natural Review Artifact Index

Review instruction: `docs/work-instructions/20260821-kr-natural-review-phase9-1-promotion-gate-and-night-futures.md`, version `2.0`, commit `65c311a8e49bd1a7d46df92c89e1aa378fc9f21b`.

Paths under `data/` point to the clean operating checkout. Raw artifacts were read only and are not copied into Git.

## KR natural production

Base: `data/ai_review/pilot/history/2026/08/2026-08-21-kr-run-31-27d43ced72a0/`

| Type | Path | SHA-256 | Status |
|---|---|---|---|
| Production packet | `packet.json` | `f83e7670ef4c1df2c56ec342515bbec1fae6d84bd3077f3f5138536ed813a5ce` | original/immutable |
| Runtime-quality rejected AI candidate | `quality-rejected-ai-messages.json` | `2b425a75e37878e07bc6e18f383f04def549f0ba85f62a6858510f650d6d4d41` | original/immutable |
| Numeric/semantic validation | `validation-result.json` | `37226acc517a7c659896df5e44e28370cfa5e8c0be0e56cee95b8cc479fb4af1` | original/immutable |
| Final comparison/finalization | `comparison.json` | `709230771014aec801f6174326aeb52c99de370fa256ff56318c024b2bc1769c` | original/immutable |
| Runtime quality receipt | `message-quality-receipt.json` | `12260bc80aca5e8d1c3325b20d17e565a4e8fc14ea495a3765108364523fcade` | original/immutable |
| Fallback bundle | `fallback-messages.json` | `d62a143871e959507638b35fc01b94c1c7f7e164ee941e4fcfa19606958a2e3b` | original/immutable |
| Delivery result/receipt | `delivery-result.json` | `e06daaf8fa51302ac39f62802e5c85f9617c88941c2127ab0da70ad51bd5d795` | original/immutable |
| Phase 9.0E negative-control terminal | `cash-flow-shadow-canary/cf-canary-cf7efecd2e09c3854e396acc/canary-complete.json` | `758da42d476705c24e96d98a3860d0d870b99fd182a051c8444263022c5944f1` | original/immutable |
| Actual sent rows | `data/thesis_monitor.sqlite3`, `notificationdelivery.id=228..235` | database read only | original operating state |
| Sanitized actual-text bundle | `docs/reports/20260821-kr-natural-sent-message-bundle.md` | computed with final bundle | review output |

## KRX natural telemetry

| Type | Path | SHA-256 | Status |
|---|---|---|---|
| 2026-08-21 16:05 observation | `data/telemetry/krx/publication-readiness/2026-08-21.jsonl`, line 1 | `39cb67d26602b5da2e1272711a00721f5f0c0e59e2c527d1ee6ae5440ce88b7e` | original/immutable |
| Four empty endpoint payloads | refs embedded in the JSONL row | `82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90` | original payload identity |
| Prior 16:05 / next 08:05 evidence | `data/telemetry/krx/publication-readiness/2026-08-20.jsonl` | `5ab11b9333332d0ea7f165074dab2334ebabdcb36484688f82c140409b6e84e2` | original/immutable |

The v1 telemetry row does not emit a standalone observation ID; target date, slot, and line number are the retained identity.

## US morning and night futures

Base: `data/ai_review/pilot/history/2026/08/2026-08-21-us-run-30-5a3b7c1c4390/`

| Type | Path/ref | SHA-256 | Status |
|---|---|---|---|
| US morning packet | `packet.json` | `d52e6545692c26769862b33a3632ab36bd4add8b3ea1fbc205c4f1ae089543f1` | original/immutable |
| Market context / dispatch evidence | `market-context.json` | `5d4c6162db49be7901d58067a606ab964df7469c576b66b08e92c840bce089fe` | original/immutable |
| Final deterministic messages and morning gate | `deterministic-messages.json` | `e266bafd6d8fce38cf7a86d1e6cec3b1213337ef4e74875ad2ee88279962f78c` | original/immutable |
| Morning macro briefing | `data/macro/briefings/2026-08-21.json` | retained operating file | original/immutable |
| Preflight/retry summary | `_morning_gate` in `deterministic-messages.json` | included above | original/immutable |
| Attempt logs | unified LaunchAgent log plus retained `daily.out` lines 65-68 | n/a | natural, read only |
| Per-attempt HTTP/raw payload | not retained | `UNKNOWN` | telemetry gap |
| Latest stale NIGHT source | provider cache/source occurrence for NIGHT `2026-08-20` | `deec12e278599752379a792518e313df6678c11bc8b9c4cab9d63de99cafc753` | original/cached |
| Preceding DAY source | provider cache/source occurrence for DAY `2026-08-19` | `98488c8819932b8b330f366c0ef8c9a5d8e54556e97b701a00a47e5375f89ae1` | original/cached |
| Later natural availability | none found | `UNKNOWN` | not observed |

## Phase 9.1 chain

| Phase | Instruction commit | Final commit | GitHub Actions final run/job | Result |
|---|---|---|---|---|
| 9.1A | `eaaadb1...` | `d4a4daf08ff5f68bc1072cc065e69ca5de5da145` | run `32447671565`, job `96670172419` | Test PASS, Lint PASS, P0/P1 `0/0`, runtime diff `0` |
| 9.1B | `0952bee...` | `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6` | run `32450583477`, job `96678229655` | Test PASS, Lint PASS, P0/P1 `0/0`, runtime diff `0` |
| 9.1C | `613d91d...` | `d0dc76a2446ee5ef9188d1b06dcb241df004c143` | run `32454792051`, job `96689900184` | Test PASS, Lint PASS, P0/P1 `0/0`, runtime diff `0` |

Ancestry checks passed for `33c2f8b -> d4a4daf -> 2ea8c43 -> d0dc76a`. No secret-bearing raw artifact is included in the review bundle.
