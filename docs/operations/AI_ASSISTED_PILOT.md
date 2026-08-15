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
- Any final AI validation rejection leaves the held deterministic payload fallback-eligible and does
  not increment the Pilot counter.
- Once any AI chunk is sent, resume that exact AI message from the persisted cursor.
- A deterministic fallback network retry uses the same persisted payload and a bounded retry counter;
  it does not recollect, regenerate, reanalyze, or reformat.
- Late AI after fallback is archive-only.
- Official status, warnings, numbers, and assessment remain deterministic.
- Validated AI prose is not semantically rewritten by the renderer. User-friendly terminology is
  authored before validation under the Daily Review Skill contract.

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

Active cohort: `ai-assisted-pilot-v3` with policy `daily-review-v3.9`, schema 4, structure v2, and
renderer v3. State is stored in `data/ai_review/pilot/state-v3.json`; the current successful count is
KR 2/5 and US 1/5.
Earlier state files and history remain immutable.

A market success increments only when:

1. packet is ready;
2. profile and numeric gates pass;
3. Codex completes;
4. validator passes;
5. the full AI-assisted set is delivered;
6. all required archive artifacts and `delivery-result.json` are present, parseable, and consistent;
7. an atomic `archive-complete.json` marker is written and verified.

Only after step 7 may the packet ID and assessment date be recorded as a Pilot success. If delivery
finishes but archive completion fails, retry only archive completion using the already-persisted
payload. Do not resend Telegram, rerun analysis, regenerate the packet, or rerender the message. The
packet ID and assessment date are idempotency keys, so successful recovery increments exactly once.

The 2026-08-14 US run is preserved as a failed-quality live sample. Its messages were manually sent
after the initial network failure before v3.7 activation, but zero numeric claims make it ineligible
for the Pilot counter.

The 2026-08-15 US live session passed validation, completed 14/14 delivery, and completed its archive,
so it is the first US Pilot success. Later v3.9 retrospective and renderer previews were not sent and
do not count. In particular, the preview committed at `e2c9290` was an experiment; its broad renderer
word replacement is not part of the operating contract.

The natural 2026-08-15 KR v3.9 Scheduled Task packet
`2026-08-15-kr-run-19-919a670464b4` passed validation, delivered the market plus seven stocks 8/8,
verified every required artifact hash, and wrote `archive-complete.json` before the success record.
The packet and assessment date occur once in state, so it is KR Day 2/5. Experimental v3.10 output
did not send or count this session. A renderer may show the next candidate day, but only persisted
state after verified archive completion is the actual count.

Fallback is an operational success but not an AI Pilot success. Each market needs five successful
sessions. Completion returns that market to deterministic delivery; it does not enable Production
Assist.

## Archive

Each session stores packet, deterministic messages, AI review, comparison, validator result, numeric
binding telemetry, chart context, chart transition, quantitative-grounding report, market context,
market review, market numeric claims, portfolio transmission, exact AI-assisted messages, fallback
report when used, delivery retry state, and delivery result under `data/ai_review/pilot/history`. A
successful AI Pilot archive also contains `archive-complete.json` with the packet, policy/schema,
validator and delivery status, completion time, and hashes for required artifacts.

## Deployment Gate

Before Day 1:

1. `origin/main`, development checkout, and operating checkout are the same clean commit.
2. Full tests, lint, diff, Knowledge checksums, Skill, schema, renderer, and documentation validation
   pass for that exact commit.
3. All four Scheduled Tasks name Pilot v3, policy v3.9, schema 4, structure v2, and renderer v3.
4. State-v3 has no migrated successes.
5. The fallback LaunchAgent is loaded and single-delivery tests pass.

## Incident Classification

Classify issues as DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING, AI_REASONING, VALIDATION, RENDERER,
or DELIVERY before changing code. Invented facts, wrong numeric semantics, suppressed historical
valuation use, modeled-as-consensus wording, unavailable chart levels, chart/thesis invalidation
confusion, and wrong-company facts invalidate a Pilot sample immediately.
