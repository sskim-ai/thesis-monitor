# Delta-First Rendering

## Decision

`delta-first-rendering-v1` assembles a complete schema-4 stock review around the most
decision-relevant verified evidence. Phase 8.4.1 adds `decision-material-delta-v1`: a changed field
is a candidate, not automatically the primary decision. It does not add a second output schema or a
second renderer. The existing numeric binder, full validator, production stock renderer, and runtime
message-quality receipt remain the delivery boundary.

```text
immutable packet + recovered canonical Facts + monitoring_state.delta
  -> materiality classification
  -> evidence-backed full schema-4 draft
  -> numeric binder and typed valuation validation
  -> adaptive section plan
  -> existing production renderer
  -> final rendered-language and runtime quality gates
```

The contract is experimental and archive-only. It is not registered in the operating Scheduled
Tasks and does not make a retrospective packet Pilot-eligible.

## Materiality

The planner uses deterministic packet state. It does not compare provider values or infer a new
delta inside the renderer.

| Tier | Examples | First rendered evidence |
|---|---|---|
| 1 | thesis/earnings/financial-quality evidence, material event | core judgment |
| 2 | valuation regime or chart/confirmation transition | core or price section |
| 3 | RR or supply/positioning transition | price or supply section |
| 4 | unchanged warning, static unknown, old registered level | compact, suppressed, or later |

A deterministic materiality override may promote an extreme supply or price lifecycle transition.
A mild actor/horizon divergence does not lead merely because it is the latest changed field when
verified earnings and valuation are more decision-relevant current context. If earnings are denied,
safe price, supply, PBR, and execution evidence may lead. When there is no material delta, the core
judgment states that plainly and moves to current decision relevance. The planner never manufactures
a change from retrospective data recovery.

## Adaptive Selection

The input review remains a complete schema-4 object. Rendering chooses an order and may suppress
redundant display sections:

- financial evidence is integrated into the core judgment, so a duplicate business section may be
  suppressed;
- priority-watch bullets are suppressed when the same decision condition is already expressed by a
  concrete next check and unknown;
- deterministic warnings remain available and are rendered only when present;
- price, supply, and valuation remain independent from business-thesis confirmation.

Suppression is recorded in an audit with available, selected, and suppressed sections plus a reason.
It does not delete Facts from the packet or validated review.

## Evidence Rules

- Every user-visible number is produced from a numeric reference and canonical formatter.
- Recovered financial values retain `financial-lineage-v2` period and statement-basis labels.
- Denied financial fields do not become quantitative or qualitative earnings claims.
- Current-price RR and support-entry RR retain distinct semantics.
- KR supply direction is bound for the exact actor and 1/5/20-day horizon.
- Valuation direction remains occurrence-bound. Without historical or peer comparison evidence,
  current PER/PBR are stated neutrally.
- Company/listed-security multiples are never presented as segment multiples without an actual
  segment denominator and scoped Fact.
- Denied financial families cannot return as qualitative premises; an exact denial explanation is
  the sole supported exception.
- Safe, comparable, sufficiently covered own-history context is retained when it crosses a decision
  band, with every suppression reason audited.
- Price and supply context never strengthen or weaken a company thesis by themselves.

## Observer And Holder

The new-observer view addresses entry attractiveness, current RR, nearby zones, and confirmation
conditions. The holder view addresses support or invalidation, thesis evidence, earnings quality,
and risk monitoring. The semantic validator strips role labels, rejects label-only duplicates, and
requires different decision-variable families.

## Unknown And Next Check

Only decision-relevant unknowns are selected. A valid unknown names the missing Fact and explains
which inference it prevents. A valid next check names the evidence and the direction that would
change the current interpretation. Numeric thresholds are allowed only when already canonical.
An existing canonical current value may serve as the reference point; the AI cannot round it into a
new threshold.

Economic scope, denied-family propagation, history retention, and materiality override details are
in [SEMANTIC_SCOPE_AND_DECISION_HIERARCHY.md](SEMANTIC_SCOPE_AND_DECISION_HIERARCHY.md).

## Renderer Boundary

Reasoning owns the sentence and section plan. The renderer owns headings, deterministic warnings,
and exact assembly. It does not calculate, paraphrase, repair particles, replace labels, or change
meaning after validation. The final gate runs on the exact Telegram text and rejects unresolved
placeholders, duplicate labels, particle defects, zone-role errors, and internal implementation
terms.

## Length Goal

There is no hard character cap. The target is fewer repeated sections and fewer duplicated claims,
while retaining the evidence needed for a decision. Audits record character, line, and section
counts against the immutable full-message baseline.

## Retrospective Semantics

Archive-only Preview means: what the historical session could have rendered if the recovered
canonical lineage and this selection contract had existed then. It does not describe recovery as a
new event, refresh prices, call providers, mutate an assessment, send Telegram, or change Pilot
state.

## Activation Boundary

Mechanical PASS is not human approval. Main merge, operating deployment, Scheduled Task use, and
Production Assist eligibility require separate Work review of the exact full-message Preview.
