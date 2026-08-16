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

Active cohort: `ai-assisted-pilot-v3` with policy `daily-review-v3.10`, schema 4, structure v2, and
renderer v3. State is stored in `data/ai_review/pilot/state-v3.json`; the current successful count is
persisted as KR 3/5 and US 2/5. The 2026-08-16 US session is operationally counted but failed the
required human message-quality review. The 2026-08-16 KR session is operationally counted, while its
human message-quality disposition is `failed`. Neither session is currently
eligible as Production Assist evidence.
Earlier state files and history remain immutable.

A market success increments only when:

1. packet is ready;
2. profile and numeric gates pass;
3. Codex completes;
4. validator passes;
5. the rendered full set passes `runtime-message-quality-v1` and a hash-bound receipt is persisted;
6. the full AI-assisted set is delivered;
7. all required archive artifacts and `delivery-result.json` are present, parseable, and consistent;
8. an atomic `archive-complete.json` marker is written and verified.

Only after step 8 may the packet ID and assessment date be recorded as a Pilot success. If delivery
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

The natural 2026-08-16 KR v3.10 Scheduled Task packet
`2026-08-16-kr-run-21-049f367f0274` also passed validation, delivered 8/8, verified all 13 required
archive artifacts, and wrote its completion marker before the exactly-once state update. It is KR
Day 3/5 operationally. Its human-quality status was subsequently set to FAIL by Work. Six
numeric-postposition defects, unsupported actor/horizon
supply claims, repeated core-judgment structure, missing financial period labels, and unsupported
valuation conclusions block evidence eligibility. The review did not mutate the counter, and the
session is not Production Assist evidence. See
[the Work human review](../reports/20260816-third-natural-kr-v310-work-human-review.md).

Fallback is an operational success but not an AI Pilot success. Each market needs five successful
sessions. Completion returns that market to deterministic delivery; it does not enable Production
Assist.

## Archive

Each new session stores packet, deterministic messages, AI review, comparison, validator result, numeric
binding telemetry, chart context, chart transition, quantitative-grounding report, market context,
market review, market numeric claims, portfolio transmission, exact AI-assisted messages, fallback
report when used, `message-quality-receipt.json`, delivery retry state, and delivery result under
`data/ai_review/pilot/history`. Gate failure keeps the deterministic fallback eligible and sends no
rejected AI text. A network retry verifies and reuses the same payload and receipt. A
successful AI Pilot archive also contains `archive-complete.json` with the packet, policy/schema,
validator and delivery status, completion time, and hashes for required artifacts.

## Deployment Gate

Before Day 1:

1. `origin/main`, development checkout, and operating checkout are the same clean commit.
2. Full tests, lint, diff, Knowledge checksums, Skill, schema, renderer, and documentation validation
   pass for that exact commit.
3. All four Scheduled Tasks name Pilot v3, policy v3.10, schema 4, structure v2, renderer v3,
   security identity v2, and financial quality v2.
4. State-v3 has no migrated successes.
5. The fallback LaunchAgent is loaded and single-delivery tests pass.

On 2026-08-15 Phase 7.2 was deployed after exact-commit checks. The six approved authoritative
identity remediations were applied and were all idempotent no-ops on the second pass. Four existing
tasks were updated in place to v3.10 without changing schedules, checkout, or claim options. This
deployment and its isolated validation did not send Telegram or increment Pilot state; the first
naturally scheduled v3.10 Live session occurred on 2026-08-16.

US packet `2026-08-16-us-run-20-6c15d0003955` passed the final validator after one permitted
correction, delivered 14/14 AI-assisted messages, verified 13/13 required archive hashes, and wrote
`archive-complete.json` before the exactly-once success record. Runtime advanced US from 1/5 to 2/5.
Human review nevertheless failed the message-quality gate because CRCL's transition text contradicted
the packet delta, SKHY's text denied a verified ADS identity rather than only the unverified
current-security denominator, and all 13 US stock messages repeated a KR-style investor-flow frame.
The audit made no counter mutation. Operational pipeline success and human quality approval are
separate dimensions; 5/5 operational sessions cannot enable Production Assist without resolved
blocking findings and explicit user approval.

Phase 7.2.7 adds deterministic transition-direction, identity-versus-basis, and market-aware supply
validation. Its corrected retrospective passed its automated gates, but its KR regression selected a
v3.9 artifact from a closed KR session and later human review found additional blocking safety and
language issues. It remains failed-review evidence and did not change the then-current KR 2/5 or
US 2/5.

Phase 7.2.8 uses a fresh current-code packet from the completed 2026-08-14 KR after-hours session and
keeps the original natural US artifacts immutable. Its corrected isolated US 14-message and KR
8-message sets pass binder, full validator, financial-quality, label/instrument, zone-role,
postposition, identity, comparison, supply, and repetition hard checks. This is still experimental:
it is unmerged, undeployed, not human-approved, and ineligible for Production Assist evidence. It
did not send Telegram or change the then-current KR 2/5 or US 2/5; only the later natural KR Day 3
session advanced current runtime to KR 3/5.

## Incident Classification

Classify issues as DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING, AI_REASONING, VALIDATION, RENDERER,
or DELIVERY before changing code. Invented facts, wrong numeric semantics, suppressed historical
valuation use, modeled-as-consensus wording, unavailable chart levels, chart/thesis invalidation
confusion, and wrong-company facts invalidate a Pilot sample immediately.
