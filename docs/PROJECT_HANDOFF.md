# Thesis Monitor Project Handoff

This document is the canonical continuation point for the AI-assisted monitoring project. Read it
with [project-state.json](project-state.json) and [NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md)
before changing runtime policy, Knowledge, validation, delivery, or Scheduled Tasks.

## Project Purpose

Thesis Monitor maintains an investment thesis from verified backend facts. The deterministic engine
owns official state. Codex adds a bounded interpretation of the same facts, and Telegram delivers one
integrated market-and-stock set only after validation. The system is research monitoring, not order
execution or an autonomous investment adviser.

## Current Versions

| Component | Contract |
|---|---|
| Branch | `main` |
| Official assessment | Deterministic `ThesisAssessment` |
| AI mode | `shadow` |
| Analysis policy | `daily-review-v3.9` |
| Output schema | `4` |
| OHLCV structure | `ohlcv-structure-v2` |
| Investment Knowledge | `3.0` |
| Chart Knowledge | `1.0` |
| Pilot | `ai-assisted-pilot-v3`, current KR 2/5 and US 1/5 |
| Renderer | `ai-assisted-pilot-renderer-v3` |
| Public Action | `0.4.5`, operationId 20/20 |
| Production Assist | Disabled |
| Financial currency safety | Missing/empty is `unknown`; unsupported units are prose-denied |

Resolve the deployed commit with `git rev-parse HEAD`; a file inside a commit cannot contain that
commit's own final hash. The machine-readable state records `HEAD` plus the last verified base.

## Architecture

```text
Data providers
  -> deterministic normalization, validation, and calculation
  -> official ThesisAssessment
  -> immutable AI Review packet
  -> per-packet claim UUID, lease, flock, and fencing
  -> Investment Knowledge v3 + Chart Knowledge v1
  -> Codex structured review
  -> deterministic numeric-fact binding and canonical formatting
  -> schema, fact, semantic, routing, and grounding validator
  -> integrated market + stock renderer
  -> one AI-assisted Telegram set
     OR one deterministic fallback set
  -> exact immutable archive
```

See [AI_ASSISTED_MONITORING.md](architecture/AI_ASSISTED_MONITORING.md) for ownership boundaries.

## Roles

### Custom GPT

Custom GPT provides interactive initial research and monitoring using Investment Knowledge v3 and
the public Action contract. The repository upload artifact must remain byte-identical to the
canonical Investment Knowledge. Custom GPT Instructions take precedence if a conflict is found.

### Deterministic Backend

The backend collects facts, verifies identity and provenance, calculates financial, valuation,
market, supply, and chart values, and persists the official assessment. It remains the source of
truth for status, warnings, invalidation, canonical numbers, and Telegram fallback content.

### Codex

Codex reads an immutable packet and routed Knowledge only. It connects verified facts into business,
valuation, price, supply, market-structure, and portfolio-transmission interpretations. It does not
browse, collect facts, calculate indicators, create targets, or mutate official state.

### Validator

The backend first resolves draft numeric fact references into canonical prose and schema-4 claims.
The validator then resolves every fact and prose path, enforces industry routing, rejects unsupported
numeric semantics, verifies exact display variants, and checks current claim and policy identity
before atomic promotion. Unknown semantic types and stale or absent facts fail closed.

### Telegram

Telegram is a delivery surface, not a source of truth. During Pilot, validated AI narrative is merged
with deterministic status and numbers. A session sends either the AI-assisted set or the stored
deterministic fallback, never both.
The renderer preserves validated prose and only assembles headings, ordering, escaping, and Telegram
length handling; user-facing terminology must be resolved before validation.

## Monitoring Lifecycle

Initial research establishes a thesis-version baseline. Daily monitoring evaluates only changes after
that baseline. A new thesis version creates a fresh baseline and cannot inherit prior price-state
transitions as today's delta. Fingerprints and warning lifecycles remain deterministic.

```text
Initial research -> baseline -> daily delta -> deterministic assessment -> optional AI interpretation
```

Every final assessment also stores `monitoring-state-v1` under `price_context`: current price
structure, registered-rule lifecycle, supply, valuation, peer availability, the previous final state,
and deterministic delta. This state evolves even when the official business thesis is unchanged.
See [MONITORING_STATE_LIFECYCLE.md](architecture/MONITORING_STATE_LIFECYCLE.md).

## Dual Knowledge

- [Investment Knowledge v3](knowledge/investment-thesis-analysis-monitoring-knowledge-v3.md) governs
  business, industry, earnings, valuation, expectations, macro, risk, and monitoring safety.
- [Chart Knowledge v1](knowledge/stock-chart-value-analysis-knowledge-v1.md) governs interpretation of
  backend-provided OHLCV structure, positioning, and new-observer versus holder context.
- The two documents stay separate. Chart examples never override Investment Knowledge safety or
  backend calculations.

Canonical precedence is:

```text
Backend verified fact/calculation
  > Investment Knowledge v3 safety
  > OHLCV Analyst validated output
  > Chart Knowledge interpretation
  > examples
```

## Industry Routing

Primary industry identity comes from verified company profile fields, not thesis keywords or daily
themes. Structured subtype may refine a broad industry. Themes, customer exposure, and macro links
are secondary. Ambiguous or uncovered profiles stay general/low confidence rather than being forced
into a specialized framework. Production code contains no ticker-specific classification override.

## Numeric Provenance

Every user-facing investment number must bind:

```text
backend fact -> fact_id -> field_path -> value/unit -> semantic_type
  -> exact text_ref -> exact displayed usage
```

The single semantic registry defines unit, labels, formatter, rounding, prose permission, and scope.
Unknown semantics fail closed. Same-number/different-meaning and cross-prose coverage are invalid.
Derived numbers are usable only when the backend has registered them as canonical facts.
Under `daily-review-v3.9`, Codex places `{{numeric:ref_id}}` and selects only the canonical fact,
field, and prose location. The backend owns the value, unit, semantic, source-aware label, display
format, and generated final claim. Legacy manual claims still validate, but the draft binding path is
the production contract. See [NUMERIC_PROVENANCE.md](architecture/NUMERIC_PROVENANCE.md).
Issuer earnings amounts never inherit security price currency. A missing or blank
`financial_currency` becomes `unknown`; the amount remains auditable but has no canonical display and
cannot bind into prose. A non-empty unsupported currency keeps its identity and is also prose-denied.
Currency-independent earnings percentages remain usable.
During Pilot, a market or stock with at least four prose-eligible anchors cannot pass with zero
numeric claims. Sparse packets remain exempt, and every used number still requires exact prose
grounding rather than a quota-driven list.

## OHLCV Structure

`ohlcv-structure-v2` calculates Wilder ATR14, Local-Pivot zones and boxes, an independent Major Swing
stream, tentative Elliott/Fibonacci context, structural invalidation, nearest-resistance risk/reward,
and internal chart state. Correctness constraints are documented in
[OHLCV_STRUCTURE_ENGINE.md](architecture/OHLCV_STRUCTURE_ENGINE.md).

The central boundaries are:

- Local Pivot is not Major Swing.
- Adjusted chart price is not unadjusted historical-valuation price.
- Chart invalidation is not thesis invalidation.
- Chart state is not a buy or sell command.

## Market Intelligence

`daily-review-v3.9` retains the v3.8 market-intelligence and state-aware review contract and adds
deterministic numeric-fact binding, canonical display formatting, correction telemetry, and fallback
hardening.
Verified market facts become selected changes, market structure, verified
portfolio transmission, and next confirmation. Market context may be a tailwind or headwind but never
becomes company fundamental confirmation. Rates, FX, oil, sectors, and flows use distinct semantic
contracts. Details are in [MARKET_INTELLIGENCE.md](architecture/MARKET_INTELLIGENCE.md).

## Stateful Price And Peer Context

Registered thesis price rules remain immutable history. The user-facing price section first uses a
new transition, then current Strong/Medium dynamic zones, current-price RR/invalidation, and only then
a still-relevant registered rule. A crossed confirmation is never promoted to support automatically.

Peer valuation is deterministic and fail-closed. The current repository can only use same-date active
monitored assessments, explicitly labeled as a limited sample. At least three comparable peers are
required, and the median is primary. The 2026-08-14 active universe had no qualifying peer metric, so
no peer number was invented. See [PEER_VALUATION.md](architecture/PEER_VALUATION.md).

## Pilot Architecture

Pilot v3 activated at KR 0/5 and US 0/5; the current count is KR 2/5 and US 1/5. The required task
contract is policy v3.9/schema 4/structure v2. A successful day requires Codex completion, validation
pass, complete AI-assisted delivery, required artifact verification, and a verified atomic
`archive-complete.json` marker. Only then is success recorded. Archive-only recovery reuses the
persisted payload without resending Telegram, and packet/date idempotency prevents duplicate counts.
Fallback days do not increment the counter. Earlier
Pilot cohorts remain history and are never rewritten.

On 2026-08-15 the owning desktop environment verified all four local-project tasks, retained their
08:15/08:30/16:15/16:55 schedules, and migrated their exact prompts to v3.9. All four are ACTIVE,
target the live local operating checkout, use GPT-5.6 Sol with high reasoning, and preserve the US
Primary 300-second readiness wait. No duplicate standalone task was created.

| Market | Primary | Backup | Fallback deadline |
|---|---:|---:|---:|
| US | 08:15 | 08:30 | 08:40 |
| KR | 16:15 | 16:55 | 17:10 |

The US deterministic run and first KRX fetch start at 08:05. KRX-only retries run at 08:10, 08:15,
and 08:20; the packet then proceeds with both contracts, a verified partial pair plus caution, or a
compact unavailable caution. The 08:15 primary may poll backend packet readiness for five minutes.
Detailed recovery and single-delivery rules are in
[AI_ASSISTED_PILOT.md](operations/AI_ASSISTED_PILOT.md).

The 2026-08-14 US v3.6 output had zero numeric claims and its initial Telegram delivery failed. A
manual retry sent the messages before the v3.7 policy was adopted, so delivery cannot be undone; the
session is retained as a failed-quality live sample and does not count toward Pilot totals.

The 2026-08-15 US session completed under v3.8 before the v3.9 deployment: validator PASS, 14/14
AI-assisted messages sent, and archive completion. Runtime state therefore counts it as US Day 1/5.
The later v3.9 same-packet retrospective was archive-only and did not change that count or resend it.
The `e2c9290` plain-language preview was also unsent experimental evidence. Broad renderer-side word
replacement was removed because it crossed the post-validation semantic boundary; the Daily Review
Skill remains responsible for avoiding internal analysis jargon in authored user prose.

The natural 2026-08-15 KR v3.9 Scheduled Task completed packet
`2026-08-15-kr-run-19-919a670464b4`: validator PASS, the market plus seven active stocks delivered
8/8, all required archive hashes verified, and `archive-complete.json` was written before the packet
was recorded exactly once. Runtime state therefore counts it as KR Day 2/5. Experimental v3.10
retrospectives did not send this payload or mutate the count. A Preview label such as KR Pilot 3/5
would be only the next-success candidate until runtime state records another completed session.

## Source Map

- Packet, claim, validation, grounding: `app/services/ai_review_service.py`
- Numeric draft binding: `app/services/numeric_provenance_service.py`
- Market facts and transmission: `app/services/market_intelligence_service.py`
- Numeric semantics: `app/services/numeric_semantic_registry.py`
- Chart structure: `app/services/ohlcv_structure_service.py`
- Monitoring state and peer context: `app/services/monitoring_state_service.py`
- Renderer and delivery: `app/services/ai_assisted_delivery_service.py`
- Skill: `.agents/skills/thesis-monitor-daily-review/SKILL.md`
- Runtime policy: `.agents/skills/thesis-monitor-daily-review/references/daily-review-policy.md`
- Output schema: `.agents/skills/thesis-monitor-daily-review/references/output-schema.json`
- Pilot archive: `data/ai_review/pilot/history`

## Known Gaps

- KR local KOSPI/KOSDAQ facts are not in the AI market packet.
- Market breadth is unavailable for both markets.
- Market-wide investor flow is unavailable.
- Sector coverage is currently SOXX-only.
- POSCO Holdings, Samsung Electronics, LS ELECTRIC, and Hanwha Aerospace are verified profiles whose
  current Knowledge taxonomy coverage can still route general/low; Phase 6 does not force a mapping.
- There is no broad point-in-time peer valuation provider. Limited active-universe comparisons fail
  closed unless at least three comparable peers pass all basis checks.
- Production Assist remains disabled pending a separate decision after successful Pilot evidence.

Never fill data gaps with model knowledge. Add a deterministic fact, semantic contract, and tests
first.

## Milestones

1. Initial baseline and daily-delta isolation.
2. Fact sanitization, warning provenance, and treasury materiality.
3. Historical valuation basis and modeled-versus-consensus safety.
4. Notification ordering, deferred FIFO, and KRX morning gate.
5. Codex Shadow packet, claim UUID, lease, flock, and finalize fencing.
6. Knowledge v3 parity and verified company-profile routing.
7. Prose-level numeric provenance and fail-closed semantic registry.
8. Single-delivery AI-assisted Pilot with deterministic fallback.
9. Dual Knowledge and OHLCV structure v1/v2 correctness hardening.
10. Phase 6 market intelligence and portfolio transmission.
11. Phase 6.1 quantitative hard gate, required night-futures grounding, fast morning pipeline, and
    persisted Telegram delivery retry.
12. Phase 7 durable monitoring state, registered-rule lifecycle, dynamic-price grounding, and
    fail-closed peer valuation.
13. Phase 7.1 deterministic numeric provenance binding, canonical formatter and currency-basis
    hardening, machine correction context, and persisted fallback retry safety.

## Next Steps

1. Keep `origin/main`, development checkout, and operating checkout on the same clean commit.
2. Observe the next naturally scheduled v3.9 session; do not trigger a duplicate manual run.
3. Review five successful sessions per market without changing policy mid-cohort for style alone.
4. Treat DATA, CALCULATION, PACKET, KNOWLEDGE_ROUTING, AI_REASONING, VALIDATION, RENDERER, and DELIVERY
   as separate failure categories.
5. Keep Production Assist disabled until explicit user approval.
