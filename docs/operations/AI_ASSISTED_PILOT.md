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
| US | after 07:50 run and 08:00-08:45 KRX gate | 08:50 | 09:30 | 09:45 |
| KR | after 16:05 close run | 16:15 | 16:55 | 17:10 |

The claim lease is 30 minutes. Backup starts after the lease plus safety margin. A stable packet lock,
current claim UUID, and claim-specific temporary file fence old workers from final promotion.

## Cohorts and Counting

Active cohort: `ai-assisted-pilot-v3` with policy `daily-review-v3.6`, schema 4, structure v2, and
renderer v3. State is stored in `data/ai_review/pilot/state-v3.json` and starts KR 0/5, US 0/5.
Earlier state files and history remain immutable.

A market success increments only when:

1. packet is ready;
2. profile and numeric gates pass;
3. Codex completes;
4. validator passes;
5. the full AI-assisted set is delivered;
6. the archive completes.

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
3. All four Scheduled Tasks name Pilot v3, policy v3.6, schema 4, structure v2, and renderer v3.
4. State-v3 has no migrated successes.
5. The fallback LaunchAgent is loaded and single-delivery tests pass.

## Incident Classification

Classify issues as DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING, AI_REASONING, VALIDATION, RENDERER,
or DELIVERY before changing code. Invented facts, wrong numeric semantics, suppressed historical
valuation use, modeled-as-consensus wording, unavailable chart levels, chart/thesis invalidation
confusion, and wrong-company facts invalidate a Pilot sample immediately.

