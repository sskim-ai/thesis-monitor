# Cash-Flow Baseline Consistency

## Decision

`baseline-cash-flow-claim-consistency-v1` prevents current qualitative cash-flow prose from
contradicting comparable current-formal canonical evidence. It validates or removes legacy prose;
it does not expose canonical OCF, PPE CAPEX, or FCF numbers.

## Problem

Phase 9.0B made canonical PPE-only FCF reproducible and Phase 9.0D proved its delivery-isolated
runtime canary. Run 30 then exposed a separate problem: a saved qualitative thesis could continue
to assert an unqualified current FCF sign without a financial Fact reference. Numeric correctness
inside the canary could not catch that contradiction because production prose and shadow evidence
were validated independently.

## Why

A canonical cash-flow pipeline is insufficient if unbound legacy prose can still reach a user-visible
fallback and assert a different current state. The production baseline and detached shadow evidence
must therefore share a structured consistency check while retaining their separate delivery paths.

## Rejected Alternative

We rejected replacing the unsupported TSLA sentence with the latest canonical amount. That would
have introduced cash-flow numbers into production before the selective user-visible integration
phase. We also rejected ticker-specific wording, mutation of stored thesis history, and treating a
saved-thesis reference as financial Fact provenance.

## Safety Constraint

The repair may keep, qualify, or suppress recognized qualitative claims, but it cannot invent a
period, scope, source occurrence, currency, or amount. It cannot mutate persisted thesis, assessment,
warning, archive, task, or delivery state, and it cannot feed canonical cash-flow values into the
production AI packet.

## Contract

Each recognized baseline claim records:

- ticker, text reference, section owner, origin type and version;
- metric semantic, sign/state, period type, scope and currentness;
- provenance references and provenance validity;
- comparable canonical Fact ID, comparability and consistency result;
- render action, suppression reason or required qualifier.

The consistency states are `CONSISTENT`, `QUALIFIER_REQUIRED`, `STALE_CONFLICT`,
`UNSUPPORTED_CLAIM`, `NOT_COMPARABLE`, and `NO_CANONICAL_CHECK_AVAILABLE`. Render actions are
`KEEP`, `QUALIFY`, and `SUPPRESS`.

## Recognition Boundary

Legacy prose recognition is a narrow compatibility layer for explicit FCF/OCF sign language,
implied FCF turn-positive requirements, explicit high/increasing cash burn, and cash-flow
unavailability. It is not general sentiment analysis. A bare metric reference such as “cash burn
is a key check” is not converted into a current negative state.

Period, scope and currentness are read from the claim's sentence, not the whole rendered message.
This prevents an unrelated valuation label such as `TTM EPS` from being assigned to an earlier FCF
claim. Rendered message headings recover ownership for core, business/earnings, warnings, data
cautions, persistent risks, next checks and Unknowns. Future risk and next-check sections remain
conditional rather than current-state assertions.

## Comparability

Canonical comparison is permitted only for the same issuer and a current-formal eligible Fact.
Generic FCF has unknown scope and is never silently declared equivalent to either management FCF
or backend PPE-only FCF. A sign-consistent generic FCF claim therefore needs a deterministic period
and PPE-scope qualifier. Management-defined FCF remains not comparable unless its own definition
and provenance are verified.

Historical claims require their own period and provenance. A previous negative quarter cannot be
used as an unqualified current substitute for a positive YTD primary Fact. When no current
canonical check is available, only a claim with valid financial provenance may survive.

## Legacy Provenance

A thesis reference such as `thesis:TSLA:v5` proves where prose came from; it does not prove the
financial state asserted by that prose. `saved_thesis`, `custom_gpt`, and
`backfilled_saved_thesis` are therefore not accepted as financial Fact provenance. Historical
thesis and assessment rows remain immutable.

## Runtime Surfaces

The same repair contract is used in three places:

1. AI packet construction sanitizes saved core, assessment summaries and warning/caution inputs.
2. Deterministic fallback rendering sanitizes the current core and warning lists before rendering.
3. The detached Phase 9.0D canary audits packet baseline and final production text against the
   point-in-time shadow context, including qualitative sign, period, scope and currentness.

The canary stores `baseline-consistency.json` in its own attempt namespace. Any unresolved
qualifier, unsupported claim, stale conflict or non-comparable unqualified claim contributes a
semantic validation error. It still has zero production influence.

## Safety

- No ticker, date, value or TSLA exception participates in eligibility.
- No canonical amount is added to production prose.
- No thesis, assessment, warning lifecycle or database state is changed.
- Future signals remain future conditions and do not become current-state claims.
- Negative OCF/FCF and explicit cash burn remain valid when comparable evidence supports them.
- OCF-only, lagging-formal, blocked and not-applicable cases remain fail-closed.
- Public Action `0.4.5`, output schema `4`, Scheduled Tasks, KRX telemetry, CCC and ROIC are
  unchanged.

## Source Instruction

- Path: `docs/work-instructions/20260821-phase-9-0d-1-baseline-cash-flow-consistency-repair.md`
- Version: `1.0`
- Immutable instruction commit: `20367c056e6d1da7db3edee37818210c070e1e7d`
