# AI Review Project Handoff

This is the durable continuation point for thesis-monitor AI Review work. Read it before
changing the review pipeline, Scheduled Tasks, Pilot delivery, or Knowledge references.

## Current contract

| Component | Active contract |
|---|---|
| Official assessment | Deterministic `ThesisAssessment` |
| AI mode | Shadow with separately gated single-delivery Pilot |
| Analysis policy | `daily-review-v3.6` |
| Output schema | `4` |
| OHLCV structure | `ohlcv-structure-v2` |
| Investment Knowledge | v3.0, SHA-256 `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge | v1.0, SHA-256 `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Pilot renderer | `ai-assisted-pilot-renderer-v3` |
| Public Action | 0.4.5, operationId 20/20 |
| Production Assist | Disabled |

The operating checkout must be an exact clean checkout of the pushed `origin/main` commit.
The latest phase report records the deployment commit; do not infer it from this document.

## Non-negotiable boundaries

- AI never changes official thesis status, warnings, valuation state, or deterministic facts.
- AI never collects external facts or browses the web for a review.
- Every prose number is bound to its exact fact, field, semantic, location, and approved display.
- Unknown numeric semantics fail closed.
- Investment Knowledge v3 remains the safety and valuation authority.
- Chart Knowledge is separate; Codex never calculates chart indicators or structure.
- Local Pivot is not Major Swing; chart invalidation is not thesis invalidation.
- Market context is not company fundamental confirmation.
- One session sends AI-assisted output or deterministic fallback, never both.
- Production Assist requires an explicit separate user decision.

## Runtime flow

```text
deterministic monitoring
  -> immutable AI packet
  -> per-packet claim and flock
  -> Codex dual-Knowledge review
  -> schema, fact, numeric, routing, and grounding validation
  -> one AI-assisted delivery
     OR deterministic fallback at the hard deadline
  -> immutable Pilot archive
```

Market review adds a second internal flow:

```text
verified market observations
  -> deterministic fact catalog and relative performance
  -> important-change selection
  -> verified profile exposure groups
  -> allowed market-to-portfolio transmission
  -> validated market narrative and next confirmation
```

## Scheduled Tasks

All times are Asia/Seoul. Lease is 30 minutes.

| Task | Time | Owner |
|---|---:|---|
| US primary | 08:50 | `us-primary` |
| US backup | 09:30 | `us-backup` |
| KR primary | 16:15 | `kr-primary` |
| KR backup | 16:55 | `kr-backup` |

Fallback deadlines are US 09:45 and KR 17:10. Keep the existing claim UUID, stable
per-packet POSIX `flock`, claim-specific temporary output, and finalize fencing. Task prompts
must require the active policy, structure version, and output schema exactly.

## Source map

- Packet, claim, validation, grounding: `app/services/ai_review_service.py`
- Market facts and portfolio transmission: `app/services/market_intelligence_service.py`
- Explicit numeric semantics: `app/services/numeric_semantic_registry.py`
- Single delivery and rendering: `app/services/ai_assisted_delivery_service.py`
- Deterministic chart structure: `app/services/ohlcv_structure_service.py`
- Skill workflow: `.agents/skills/thesis-monitor-daily-review/SKILL.md`
- Runtime restrictions: `.agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md`
- Output contract: `.agents/skills/thesis-monitor-daily-review/references/output-schema.json`
- Operations: `docs/ai_review_operations.md`
- Pilot history: `data/ai_review/pilot/history`
- Retrospectives: `data/ai_review/pilot/retrospectives`

## Pilot continuation gate

Count a market day only when Codex completed, validation passed, the complete AI-assisted
set was delivered, and the archive completed. A deterministic fallback is operationally
successful but does not increment the AI Pilot counter. Preserve old cohorts and policy
versions; never rewrite earlier days.

Before allowing a new cohort day, confirm:

1. `origin/main`, development checkout, and operating checkout are aligned.
2. Full tests, lint, and diff checks are green for that exact commit.
3. All four Scheduled Tasks use the exact active policy/schema/structure contract.
4. Knowledge checksums match their runtime manifests.
5. AI remains shadow and Production Assist remains disabled.
6. Single-delivery/fallback and partial Telegram resume tests are green.

## Current verified data gaps

- KR local index levels/returns are not in the AI market packet.
- Market breadth is unavailable for both markets.
- Market-wide foreign/institution/retail flows are unavailable.
- Sector market coverage is currently SOXX-only.
- A stale broad-dollar observation is excluded rather than backfilled.
- Some verified diversified profiles correctly remain in the general group.

Do not fill these gaps in prompts or prose. Add deterministic backend facts and explicit
numeric semantics first, then update packet coverage and tests.

## Review triage

Classify failures before changing code: `DATA`, `CALCULATION`, `PACKET`,
`KNOWLEDGE_ROUTING`, `AI_REASONING`, `VALIDATION`, `RENDERER`, or `DELIVERY`.
Preserve the packet, deterministic report, AI output, validator result, comparison, exact
message, and delivery result. Critical factual or semantic failures invalidate the Pilot
sample; stylistic dissatisfaction alone does not justify changing the engine mid-review.

