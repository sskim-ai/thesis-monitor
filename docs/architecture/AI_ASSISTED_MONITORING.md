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
  -> deterministic numeric-reference binder and formatter
  -> validator
  -> integrated market + stock renderer
  -> runtime-message-quality-v1 gate and hash-bound receipt
  -> atomic validated-payload promotion
  -> AI-assisted set OR deterministic fallback
```

The backend owns identity, calculations, status, warning state, and all persisted facts. Codex owns
only interpretation. The validator owns the boundary between them. The dispatcher owns delivery
exclusivity and does not run analysis.

Korean financial amounts follow the same ownership boundary. `financial-lineage-v2` binds each
OpenDART amount to one filing, statement basis, account, amount period, source column, currency, and
source-row identity before it can become a canonical Fact. Margin and growth are separate derived
Facts with explicit dependency lineages. A failed comparison blocks that derived Fact, not an
independently verified current amount. See [KR_FINANCIAL_LINEAGE.md](KR_FINANCIAL_LINEAGE.md).

Historical source recovery uses the same boundary. The archive-only recovery client supplies exact
recent CFS/OFS occurrences to v2, while pre-existing critical quality conflicts remain authoritative.
Structured ambiguity may enter exact XBRL reconciliation, but unresolved OCF or CAPEX duration is
not converted into a user-visible cash-flow Fact.

`delta-first-rendering-v1` can assemble those safe Facts with monitoring state, dynamic price
structure, actor/horizon supply, and typed valuation into a complete schema-4 review. The packet's
deterministic candidate set is ranked by `decision-material-delta-v1`; a mild latest supply change
does not override more important verified earnings or valuation context without an explicit
materiality reason. `semantic-scope-and-decision-hierarchy-v1` also binds company/listed-security
valuation scope, blocks qualitative echoes of denied financial families, and retains safe
decision-band history. The renderer only assembles the validated sections; it does not select Facts
or rewrite prose. See
[DELTA_FIRST_RENDERING.md](DELTA_FIRST_RENDERING.md).

`valuation-context-wording-v1` records current, own-history, peer, and forward availability
separately from actual use. Its draft-only class is checked against the bound numeric semantics, so
a visible historical percentile cannot coexist with exclusive current-only wording. The metadata is
removed before schema-4 validation.

Final assessments also persist `monitoring-state-v1` current/previous/delta. This is separate from
the slower thesis state and allows the review to evolve price, supply, and valuation context without
rewriting the thesis.

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
- No AI payload becomes delivery-eligible until the rendered full message set passes the runtime
  quality gate and its packet, validated-output, and rendered-set hashes match the persisted receipt.

## Lifecycle and Isolation

Initial research creates a thesis-version baseline. Monitoring evaluates changes after the baseline.
New thesis versions cannot inherit earlier delta or chart-transition memory. AI history is segmented
by analysis policy, output schema, Knowledge hashes, structure algorithm, and Pilot cohort.

## Runtime Components

| Responsibility | Module |
|---|---|
| Packet and validator | `app/services/ai_review_service.py` |
| Numeric contract | `app/services/numeric_semantic_registry.py` |
| Numeric binder | `app/services/numeric_provenance_service.py` |
| Market intelligence | `app/services/market_intelligence_service.py` |
| OHLCV structure | `app/services/ohlcv_structure_service.py` |
| Monitoring state and peers | `app/services/monitoring_state_service.py` |
| Runtime quality gate | `app/services/ai_reasoning_quality_service.py` |
| Delivery and renderer | `app/services/ai_assisted_delivery_service.py` |
| Delta-first full-message planning | `app/services/delta_first_rendering_service.py` |
| Semantic scope and decision hierarchy | `app/services/semantic_decision_service.py` |
| Valuation context class and contradiction validation | `app/services/semantic_decision_service.py` |
| Scheduled CLI | `app/jobs/ai_review.py` |
| Analyst workflow | `.agents/skills/thesis-monitor-daily-review/SKILL.md` |

## Archive Contract

Each new Pilot session preserves the packet, deterministic messages, AI review, comparison,
validator result, chart context and transition, quantitative grounding, market context, market
numeric claims, portfolio transmission, exact rendered messages, `message-quality-receipt.json`,
and delivery result. The receipt binds the exact packet, validated output, and logical rendered
payload set. A mismatch blocks delivery. Network retry reuses the same persisted payload and receipt;
it does not rerun analysis, binding, validation, rendering, or the quality gate. Late AI after
fallback is archive-only. Historical archives remain governed by the contract active when created.

Policy `daily-review-v3.10` uses draft-only `numeric_fact_refs` and backend rendering while preserving
the validated schema-4 shape. See [NUMERIC_PROVENANCE.md](NUMERIC_PROVENANCE.md).

Newly gated output uses `runtime-message-quality-receipt-v2`. Retry and reuse compare the actual
receipt file SHA with every persisted delivery row, then validate contract/schema, packet, policy,
output and rendered-set hashes, message count, check results, errors, and timestamp. Integrity
failure is not a network retry and receipt regeneration is forbidden. Before any AI send, failure
holds AI delivery and keeps one persisted deterministic fallback set eligible. After a partial AI
delivery, failure moves the remaining rows to an explicit partial-integrity state, sends neither more
AI text nor a duplicate deterministic set, and requires manual intervention. Historical archive
markers keep the manifest contract active when they were created.

The final rendered-language check runs on the exact Telegram text before receipt persistence. It
rejects duplicate canonical labels, unsafe particles after bound price phrases, and internal
implementation terms. This is validation only; the renderer does not repair user text after binding.
