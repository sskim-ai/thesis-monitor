# Phase 8.5.2 Shadow Release Validation

As of: `2026-08-17 20:14 KST`

## Executive Result

Phase 8.5.1 was promoted to `origin/main` and the operating shadow checkout by a clean
fast-forward. The API and operating smoke tests are healthy, all four Codex Scheduled Tasks remain
ACTIVE on the exact operating path, and no task was manually run. Production Assist remains OFF and
AI mode remains shadow.

This release makes the next natural session valid deployment evidence. It does not itself close
Natural Live Validation or the current-price RR live gap.

## Repository

| Item | Result |
|---|---|
| Previous main | `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5` |
| Source branch | `codex/phase-8-5-1-runtime-current-price-rr-repair` |
| Source final / promoted code | `2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf` |
| Release evidence branch | `codex/phase-8-5-2-shadow-release-promotion` |
| Integration | clean fast-forward, 31 commits |
| Operating checkout | `/Users/sskim/Codex/thesis-monitor` |
| Operating code HEAD | `2cd78de4f87a1c875d8ee94d546bf6d4a48c8acf`, clean |
| DB migration | none |
| Main documentation SHA | resolve with `git rev-parse origin/main` after this report commit |

`origin/main` was an ancestor of the source final. The required Phase 7.2.9.2, 8.0A, 8.1, 8.1.1,
8.1.2, 8.4, 8.4.1, 8.4.1.1, 8.5, and 8.5.1 implementation commits are present in that ancestry.
No cherry-pick fragmentation or conflict resolution was used.

## Validation

| Check | Result |
|---|---|
| Pre-promotion full pytest | `1026 passed, 1 warning` |
| Ruff | PASS |
| Diff check | PASS |
| Operating focused smoke | `89 passed` |
| Investment Knowledge parity | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge parity | `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` |
| operationId | `20/20` unique |
| Output schema | `4` |
| OHLCV | `ohlcv-structure-v2` |
| Exact code-SHA Actions | run `32023730416`, Test PASS, Lint PASS |

Actions: <https://github.com/sskim-ai/thesis-monitor/actions/runs/32023730416>

The operating smoke set covers exchange-session handling, runtime RR packet completeness,
industry-specific reasoning, reasoning quality, and AI-assisted delivery/receipt behavior.

## Operating Deployment

The API LaunchAgent uses `/Users/sskim/Codex/thesis-monitor`, was restarted after the fast-forward,
and is running on port 8766. `GET /health` returned `{"status":"ok"}`. US AI Review health reports
the completed, validated natural US packet. KR AI Review health correctly preserves run-23 as
rejected and incomplete; deployment did not rewrite that immutable result.

Feature presence in the operating checkout was confirmed for:

- `financial-lineage-v2`;
- `delta-first-rendering-v1`;
- `valuation-context-wording-v1`;
- `industry-specific-reasoning-v1`;
- exchange-calendar session selection;
- `runtime-current-price-rr-packet-preflight-v1`;
- `current_price_risk_reward_ratio` registry and validator paths.

## Scheduled Tasks

| Task | Status | Time KST | Checkout | Contract |
|---|---|---:|---|---|
| US Primary | ACTIVE | 08:15 | operating checkout | policy v3.10, schema 4 |
| US Backup | ACTIVE | 08:30 | operating checkout | policy v3.10, schema 4 |
| KR Primary | ACTIVE | 16:15 | operating checkout | policy v3.10, schema 4 |
| KR Backup | ACTIVE | 16:55 | operating checkout | policy v3.10, schema 4 |

All four use GPT-5.6 Sol with high reasoning and the project path
`/Users/sskim/Codex/thesis-monitor`. Manual Scheduled Task executions during promotion: `0`.

The deterministic 08:05 US and 16:05 KR LaunchAgents, fallback agent, and persisted-delivery retry
agent also target the same checkout. They were inspected only; idle scheduled agents report last
exit code zero.

## Runtime Policy

| State | Result |
|---|---|
| Production Assist | OFF |
| AI Review mode | shadow |
| Pilot | KR 3/5, US 3/5 |
| Pilot mutation from promotion | 0 |
| Telegram sends from promotion | 0 |
| Scheduled Task manual runs | 0 |
| DB migration or mutation | 0 |
| Delivery policy | one validated AI-assisted set or one deterministic fallback set |

## Natural Validation Plan

The next natural US flow must prove the promoted SHA through exchange/session selection, packet
generation, Phase 8.5 framework routing, full validation, receipt, single delivery/fallback, archive,
and human review.

The next natural KR flow must additionally verify current-price, support/resistance, RR availability
classification, and exact paths for calculable stocks, especially `005490`, `010120`, `012450`, and
`086280`. Unavailable-by-contract controls must not acquire synthetic RR. A genuine non-RR validator
failure must be classified separately.

## Persistent Gaps

| Gap | Status |
|---|---|
| Natural Live RR | PARTIAL |
| Natural Live Validation | OPEN |
| Industry-specific reasoning | STRONG PARTIAL |
| Peer/sector valuation | OPEN/PARTIAL |
| KRX primary approval | PENDING/UNKNOWN from repository evidence |
| Human-approved production evidence | INSUFFICIENT |

## Recommendation

Wait for the next natural US and KR sessions and inspect their exact packets, validators, receipts,
delivery/archive state, and final messages. If no operating blocker appears, start Phase 8.3 from the
latest main. If KRX approval is explicitly confirmed first, ask whether Phase 8.2A should take
priority. Production Assist remains a separate later decision.
