# AI-Assisted Monitoring Architecture

## Problem

Deterministic monitoring is reliable and auditable but cannot fully connect business, valuation,
price, positioning, and market context in natural language. Unbounded AI analysis could invent facts,
change official state, or produce duplicate Telegram delivery.

## Decision

Use a deterministic-first pipeline with an immutable AI packet, dual Knowledge routing, explicit
fact and numeric contracts, claim fencing, validation, and a single final delivery decision.

```text
Providers
  -> deterministic validation/calculation
  -> official ThesisAssessment
  -> immutable packet
  -> Codex review using Investment Knowledge v3 + Chart Knowledge v1
  -> validator
  -> integrated market + stock renderer
  -> AI-assisted set OR deterministic fallback
```

The backend owns identity, calculations, status, warning state, and all persisted facts. Codex owns
only interpretation. The validator owns the boundary between them. The dispatcher owns delivery
exclusivity and does not run analysis.

## Why

This arrangement preserves the existing source of truth while gaining deeper interpretation. A
failed AI run degrades to the already-rendered deterministic snapshot without rerunning collection or
evaluation. Exact packet, output, and message artifacts make disagreements auditable.

## Rejected Alternatives

- Letting Codex browse or query providers during a review: breaks immutable-session provenance.
- Letting AI write `ThesisAssessment`, warnings, or price rules: creates competing official states.
- Sending deterministic and AI reports together: duplicates one assessment and confuses the user.
- Having the dispatcher rerun analysis: breaks idempotency and fencing.

## Safety Constraints

- `AI_REVIEW_MODE=shadow`; Production Assist is disabled.
- Public Action remains 0.4.5 with 20/20 operationIds.
- Claim, reclaim, and final promotion use a stable per-packet POSIX `flock` and current claim UUID.
- Schema, policy, Knowledge versions, and packet identity must match at finalization.
- User-facing numbers require exact prose-level provenance and an allowed semantic scope.
- Market context and chart state never mutate the company thesis.
- Only one Telegram set can win a session delivery identity.

## Lifecycle and Isolation

Initial research creates a thesis-version baseline. Monitoring evaluates changes after the baseline.
New thesis versions cannot inherit earlier delta or chart-transition memory. AI history is segmented
by analysis policy, output schema, Knowledge hashes, structure algorithm, and Pilot cohort.

## Runtime Components

| Responsibility | Module |
|---|---|
| Packet and validator | `app/services/ai_review_service.py` |
| Numeric contract | `app/services/numeric_semantic_registry.py` |
| Market intelligence | `app/services/market_intelligence_service.py` |
| OHLCV structure | `app/services/ohlcv_structure_service.py` |
| Delivery and renderer | `app/services/ai_assisted_delivery_service.py` |
| Scheduled CLI | `app/jobs/ai_review.py` |
| Analyst workflow | `.agents/skills/thesis-monitor-daily-review/SKILL.md` |

## Archive Contract

Each Pilot session preserves the packet, deterministic messages, AI review, comparison, validator
result, chart context and transition, quantitative grounding, market context, market numeric claims,
portfolio transmission, exact rendered messages, and delivery result. Late AI after fallback is
archive-only.

