# KRX Publication Evidence Read-Only Snapshot

As-of: 2026-08-20 10:27:56 KST
Repository: `sskim-ai/thesis-monitor`
Scope: committed artifacts, current operating files, logs, LaunchAgents and Codex automations only
Provider calls during snapshot: `0`

## Repository

| Item | Value |
|---|---|
| Main SHA | `006a997789d3e5ebac85ef867ae31296d175056c` |
| Operating SHA | `006a997789d3e5ebac85ef867ae31296d175056c` |
| Initial worktrees | clean / clean |
| KRX evidence branch | `codex/phase-8-2a-krx-market-breadth` |
| KRX evidence commit | `b94f709eb146655a6a2e35377073727aee7cd7ca` |
| Code changes | 0 |
| Main merge / operating integration | 0 / 0 |

This snapshot adds only this report and its JSON companion on an isolated documentation branch. It
does not change KRX implementation, main, operating code, runtime configuration or persistent state.

## Source Boundary

The operating `main` records the summarized KRX state but does not contain the Phase 8.2A provider,
publication observer or schedule. Detailed evidence remains on the preserved experimental branch.
The following exact-commit artifacts are the source of truth:

- Capability: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-krx-capability.md
- Historical audit: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-krx-market-audit.json
- Current-session audit: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-1-audit.json
- Publication audit: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-2-publication-audit.json
- Publication timing: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-2-publication-timing.md
- Provider role: https://github.com/sskim-ai/thesis-monitor/blob/b94f709eb146655a6a2e35377073727aee7cd7ca/docs/reports/20260818-phase8-2a-2-provider-role.md

Ignored raw cache and JSONL telemetry files are not present in either current worktree. This report
uses only committed endpoint metadata and payload hashes; it does not infer missing raw payloads.

## Current Contracts

| Contract | Version |
|---|---|
| Market cross-section | `market-cross-section-v1` |
| Breadth calculation | `market-breadth-v1` |
| Common-share universe | `krx-kospi-kosdaq-common-share-v1` |
| Publication readiness | `krx-publication-readiness-v1` |
| Publication telemetry | `krx-publication-telemetry-v1` |
| Time-slot role | `krx-time-slot-provider-role-v1` |

The existing role gate requires five clean complete normal sessions for 16:05 and 08:05, and three
for T+1 reconciliation. One complete observation is only `CANDIDATE`. Three exact-slot sessions
without a complete result can establish `NOT_SUPPORTED`. No threshold was added by this snapshot.

## Executive Result

| Axis | Result |
|---|---|
| Historical capability | `SUPPORTED` |
| Publication timing reliability | `NOT_YET_PROVEN` |
| Operating integration readiness | `NOT_READY` |
| KRX promotion candidate | `DEFER` |
| Recommendation | `HISTORICAL_ONLY_AND_WAIT_FOR_MORE_EVIDENCE` |

Historical retrieval and deterministic breadth are reproducible. None of the three live publication
roles has one natural exact-slot observation, much less the existing multi-session gate. KRX breadth
must not be attached to the operating KR market digest yet.

## Clean-Session Summary

| Role | Total evidence | Natural observations | Clean | Partial | Zero-row | Error | Stale | Consecutive clean | Latest state |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 16:05 same-day | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `MISSING_OBSERVATION` |
| 08:05 next-morning | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `MISSING_OBSERVATION` |
| T+1 reconciliation | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `MISSING_OBSERVATION` |
| Historical | 1 | 0 | 1 | 0 | 0 | 0 | 0 | N/A | `SUPPORTED_EXPLICIT_HISTORICAL` |

The three zero-row evening probes are intentionally excluded from every live role. They are
`AD_HOC_DIAGNOSTIC`, not exact-slot or natural observations.

## Observation Inventory

| Observed KST | Classification | Natural | Requested date | Provider date | HTTP | Core rows | State | Raw / SHA |
|---|---|---|---|---|---|---|---|---|
| 2026-08-18 20:27:09 | `AD_HOC_DIAGNOSTIC` | no | 2026-08-18 | none | 200 x4 | 0/0/0/0 | `MARKET_COMPLETED_PROVIDER_PENDING` | raw absent / SHA unavailable |
| 2026-08-18 21:02:01 | `AD_HOC_DIAGNOSTIC` | no | 2026-08-18 | none | 200 x4 | 0/0/0/0 | `MARKET_COMPLETED_PROVIDER_PENDING` | raw absent / SHA unavailable |
| 2026-08-18 21:06:36 | `AD_HOC_DIAGNOSTIC` | no | 2026-08-18 | none | 200 x4 | 0/0/0/0 | `MARKET_COMPLETED_PROVIDER_PENDING` | raw absent / sanitized SHA present |
| 2026-08-18, fetch time uncommitted | `HISTORICAL` | no | 2026-08-14 | 2026-08-14 | 200 x6 | full | `SUPPORTED_EXPLICIT_HISTORICAL` | raw absent / six endpoint SHAs present |

The 21:06 empty-result SHA is
`82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90` for each core
endpoint because the sanitized empty response shape was identical. HTTP 200 with zero rows remains
provider-pending and never becomes zero-valued market data or a clean observation.

## 16:05 Same-Day Role

- Natural observations: 0; clean: 0; zero-row/error/stale role observations: 0/0/0.
- Latest exact-slot observation: none.
- Current proof: `NOT_YET_PROVEN`.
- 2026-08-20 16:05 at snapshot time: `NOT_YET_OCCURRED`.
- Required clean sessions under the existing contract: 5; observed: 0.
- The three 20:27-21:06 probes receive no 16:05 credit.

The operating 16:05 LaunchAgent runs `monitor_daily --market kr`, but operating main contains no KRX
breadth provider or publication observer. Therefore that market job cannot create Phase 8.2A
exact-slot telemetry. Current capture state is `TELEMETRY_CAPTURE_GAP`.

## 08:05 Next-Morning Role

- Natural observations: 0; clean: 0; zero-row/error/stale role observations: 0/0/0.
- Latest exact-slot observation: none.
- Current proof: `NOT_YET_PROVEN`.
- 2026-08-20 08:05 KRX breadth observation: `MISSING_OBSERVATION`.
- Required clean sessions under the existing contract: 5; observed: 0.

The operating 08:05 US monitor and its KRX retries concern the existing night-futures path. They do
not run the experimental KRX common-share breadth observer and are not publication-role evidence.

## T+1 Reconciliation Role

The repository defines this as a separate `T_PLUS_1_AUTHORITATIVE_RECONCILIATION` role for the
prior completed market session. It is not inferred from an evening pending probe or historical
retrieval.

- Natural observations: 0; clean: 0; zero-row/error/stale role observations: 0/0/0.
- Source market date / observation date pairs: none.
- Current proof: `NOT_YET_PROVEN`.
- Required clean sessions under the existing contract: 3; observed: 0.
- Capture state: `TELEMETRY_CAPTURE_GAP`.

## Historical Role

Explicit session `2026-08-14` is validated and reproducible:

| Dataset | Raw / eligible | Advance | Decline | Unchanged | Equal-weight return |
|---|---:|---:|---:|---:|---:|
| Aggregate | 2,763 / 2,532 | 1,441 | 898 | 193 | 0.77645% |
| KOSPI | 942 daily / 804 eligible | 575 | 180 | 49 | 1.30484% |
| KOSDAQ | 1,821 daily / 1,728 eligible | 866 | 718 | 144 | 0.53060% |

- Historical retrieval supported: YES.
- Universe contract valid: YES.
- Aggregate breadth reproducible: YES.
- `advance + decline + unchanged == eligible`: PASS for aggregate and both segments.
- Available metrics include advance, decline, unchanged, advance ratio, A/D ratio, median return and
  equal-weight return.
- Historical success receives no 16:05, 08:05 or T+1 publication credit.

## Publication Pattern

The only descriptive pattern supported by evidence is narrow: on 2026-08-18, all four core
endpoints remained HTTP 200 with zero rows from 20:27 through 21:06 KST. First non-empty, first
complete, observed-complete-by and provider publication timestamp are all unavailable.

This single target date and three development-time probes cannot establish when data normally
appears, whether next-morning data is complete, or whether any publication pattern is repeatable.
The correct classification is `INSUFFICIENT_EVIDENCE`, not “late provider” or “T+1 provider.”

## Integration Gap

Future operating breadth requires a complete current KOSPI/KOSDAQ common-share universe, KOSPI and
KOSDAQ breadth/participation, equal-weight return, coherent business date, as-of observation and
`PROVIDER_COMPLETE` readiness. Current timing evidence supplies none of those for a live role.

Market-wide foreign/institution/retail flow remains `UNSUPPORTED`. Sector data remains
`PARTIAL_PRICE_PROXY_ONLY`; it is not security-level sector breadth.

Blocking Unknowns:

- same-day 16:05 completeness and repeatability;
- next-morning 08:05 completeness and repeatability;
- T+1 provider-date coherence and completeness;
- first non-empty and first-complete observation bounds;
- an approved operating exact-slot telemetry capture mechanism.

## Today And Next Evidence

At 10:27 KST, today's 16:05 observation had not occurred. This task did not wait or call the
provider. More importantly, no operating KRX breadth observer or schedule is configured, so today’s
16:05 event is `PENDING_NATURAL_OBSERVATION_BUT_NOT_CONFIGURED_FOR_CAPTURE`.

The next valid evidence must come from a separately approved exact-slot telemetry configuration and
then run naturally at 16:05, 08:05 or the defined T+1 reconciliation slot. This snapshot does not
create that configuration.

## Decision

`KRX_PROMOTION_CANDIDATE = DEFER`

- Historical capability is clean and reproducible.
- All three live publication roles have 0 natural and 0 clean observations.
- Three later ad-hoc probes were all zero-row pending and provide no exact-slot credit.
- Provider publication timing and repeatability remain unknown.
- Operating main has no Phase 8.2A publication telemetry capture path.

Recommendation: `HISTORICAL_ONLY_AND_WAIT_FOR_MORE_EVIDENCE`. Do not integrate KRX breadth into the
operating KR market digest now.

## Persistent-State Review

Current persistent documents already say Historical `SUPPORTED`, 16:05/08:05/T+1
`NOT_YET_PROVEN`, current readiness `PARTIAL`, market-wide flow `UNSUPPORTED`, sector coverage
`PARTIAL_PRICE_PROXY_ONLY`, and operating integration false. That matches the evidence. No
persistent-document correction is proposed.

## Safety Audit

| Mutation | Count |
|---|---:|
| Provider calls | 0 |
| KRX/code implementation changes | 0 |
| Main merge / operating deployment | 0 / 0 |
| API restart | 0 |
| Scheduled Task execution/configuration | 0 / 0 |
| Telegram sends | 0 |
| Pilot mutations | 0 |
| DB mutations | 0 |
| Production Assist changes | 0 |
| Persistent-document changes | 0 |

## Final Answers

1. KRX historical breadth is reproducible for the validated 2026-08-14 fixture: **YES**.
2. Proven live publication roles among 16:05, 08:05 and T+1: **none**.
3. Attach KRX breadth to the operating KR market digest now: **NO; wait for captured, repeated
   exact-slot evidence**.
