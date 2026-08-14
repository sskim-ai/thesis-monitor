# AI-Assisted Pilot Operations

## Problem

The user must not receive deterministic and AI versions of the same assessment. AI failure must also
never leave a session held indefinitely or trigger re-collection and re-evaluation.

## Decision

Pilot v3 uses single delivery with a stored deterministic fallback:

```text
deterministic evaluation -> official state + exact rendered fallback -> HOLD
Codex primary/backup -> validator PASS -> AI-assisted set
no valid AI by deadline -> deterministic fallback set
```

The dispatcher only chooses an already-rendered outcome. It does not analyze or reevaluate.

## Why

The user receives one coherent report. The deterministic path remains reliable, while AI success can
add richer market and company interpretation without becoming the official assessment.

## Rejected Alternatives

- Sending deterministic first and AI later during normal Pilot operation.
- Falling back immediately after primary failure instead of allowing backup reclaim.
- Rerunning providers or deterministic evaluation at the fallback deadline.
- Sending a full deterministic set after part of the AI set reached Telegram.
- Automatically enabling Production Assist after five days.

## Safety Constraints

- `AI_REVIEW_MODE=shadow` and Production Assist remain disabled.
- One session delivers AI-assisted or deterministic fallback, never both.
- AI market validation failure causes the whole Pilot session to use deterministic fallback.
- Once any AI chunk is sent, resume that exact AI message from the persisted cursor.
- Late AI after fallback is archive-only.
- Official status, warnings, numbers, and assessment remain deterministic.

## Schedule

All times are Asia/Seoul.

| Market | Deterministic ready | Primary | Backup | Hard fallback |
|---|---:|---:|---:|---:|
| US | 08:05 run; KRX readiness by 08:20 | 08:15 | 08:30 | 08:40 |
| KR | after 16:05 close run | 16:15 | 16:55 | 17:10 |

The US primary polls backend packet readiness for up to five minutes and uses a 10-minute lease, so
an interrupted 08:15 claim can be reclaimed at 08:30. Other workers retain the default 30-minute
lease. A stable packet lock, current claim UUID, and claim-specific temporary file fence old workers
from final promotion.

The backend queries KRX at 08:05 and retries only KRX at 08:10, 08:15, and 08:20. At the deadline it
proceeds with verified partial data or a compact missing-data caution. Codex never fetches KRX data.
If Telegram fails after validation, the persisted rendered set is retried at bounded morning slots
08:22, 08:25, and 08:30. Partial delivery resumes from the stored chunk cursor; analysis is not rerun.

## Cohorts and Counting

Active cohort: `ai-assisted-pilot-v3` with policy `daily-review-v3.7`, schema 4, structure v2, and
renderer v3. State is stored in `data/ai_review/pilot/state-v3.json` and starts KR 0/5, US 0/5.
Earlier state files and history remain immutable.

A market success increments only when:

1. packet is ready;
2. profile and numeric gates pass;
3. Codex completes;
4. validator passes;
5. the full AI-assisted set is delivered;
6. the archive completes.

The 2026-08-14 US run is preserved as a failed-quality live sample. Its messages were manually sent
after the initial network failure before v3.7 activation, but zero numeric claims make it ineligible
for the Pilot counter. US remains 0/5.

Fallback is an operational success but not an AI Pilot success. Each market needs five successful
sessions. Completion returns that market to deterministic delivery; it does not enable Production
Assist.

## Archive

Each session stores packet, deterministic messages, AI review, comparison, validator result, chart
context, chart transition, quantitative-grounding report, market context, market review, market
numeric claims, portfolio transmission, exact AI-assisted messages, fallback report when used, and
delivery result under `data/ai_review/pilot/history`.

## Deployment Gate

Before Day 1:

1. `origin/main`, development checkout, and operating checkout are the same clean commit.
2. Full tests, lint, diff, Knowledge checksums, Skill, schema, renderer, and documentation validation
   pass for that exact commit.
3. All four Scheduled Tasks name Pilot v3, policy v3.7, schema 4, structure v2, and renderer v3.
4. State-v3 has no migrated successes.
5. The fallback LaunchAgent is loaded and single-delivery tests pass.

## Incident Classification

Classify issues as DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING, AI_REASONING, VALIDATION, RENDERER,
or DELIVERY before changing code. Invented facts, wrong numeric semantics, suppressed historical
valuation use, modeled-as-consensus wording, unavailable chart levels, chart/thesis invalidation
confusion, and wrong-company facts invalidate a Pilot sample immediately.
