# Natural Live Message Hardening

Phase 8.5.3 closes two retrospective runtime defects without changing schema 4, price calculations,
or quality thresholds:

1. otherwise safe AI messages repeated methodology-only prose across stocks and failed the runtime
   quality gate;
2. deterministic fallback rendered stored thesis price rules while ignoring current dynamic price
   structure already present in monitoring state.

## Ownership

The backend owns Facts, calculations, monitoring state, and canonical display values. Codex selects
and interprets supplied evidence. The validator owns safety and portfolio-level quality. The
renderer assembles selected semantics and never calculates RR, levels, or lifecycle state.

## Runtime Specificity

`runtime-message-specificity-v1` is built from each immutable stock packet before prose generation.
It exposes:

- deterministic decision candidates;
- the verified industry framework and confidence;
- available and missing driver families;
- observer and holder decision variables;
- a concrete next confirmation;
- required current-price Fact IDs;
- methodology phrases that should remain internal.

The plan favors company evidence and industry-specific missing drivers. It does not impose a numeric
quota, invent facts, or force artificial diversity. A synonym-only rewrite of repeated safety prose
remains a semantic duplicate.

The final `runtime-message-quality-v1` threshold is unchanged. Literal, normalized-skeleton, and
generic-methodology-family telemetry are evaluated at portfolio level. Bounded correction receives
the affected stocks and safe plan context; failure still routes to deterministic fallback.

## Current Price Context

`current-price-context-v1` selects, but does not calculate:

1. current price;
2. nearest valid dynamic support;
3. nearest valid dynamic resistance;
4. canonical current-price RR;
5. chart invalidation;
6. chart state;
7. relevant registered-rule lifecycle.

AI packets and deterministic fallback consume this same selection contract. RR remains the backend
Fact `chart:structure:risk_reward:current_price` with semantic
`current_price_risk_reward_ratio`. Scenario RR is a different semantic and cannot substitute.

## Registered Rule Lifecycle

A registered confirmation is immutable thesis history, not a perpetual future trigger. The selector
classifies it for rendering as a future trigger, active transition, historical reference, limited
reference, or unavailable according to the existing monitoring lifecycle.

- Crossed or holding-above confirmation may be shown compactly as already crossed.
- It is never labeled as a future `상향 확인 가격`.
- Crossing does not promote it to support.
- Current dynamic levels take priority when available.
- A legacy packet without dynamic structure retains fail-safe registered-rule behavior.

## RR Availability

Available canonical RR is rendered with the existing deterministic formatter. Structural absence
remains unavailable and may expose a compact backend reason such as missing valid resistance or
invalidation. The renderer must not fill zero, reuse stale RR, calculate from displayed zones, or
choose a farther resistance.

## Validation

Fallback semantic validation rejects:

- crossed confirmation rendered as a future trigger;
- omitted valid dynamic support or resistance;
- omitted available current-price RR;
- registered confirmation promoted to support;
- RR semantic or unit mismatch.

AI validation retains all numeric provenance, financial lineage/quality, security identity,
valuation scope, denied echo, industry reasoning, message-quality, receipt, and exactly-once gates.

## Final Language And Intra-Message Dedup

Phase 8.5.3.1 extends the same fail-closed quality report without lowering any portfolio repetition
threshold. The final rendered-language audit rejects mismatched Korean object particles for Hangul
terms and a bounded canonical metric vocabulary, incomplete predicates, and malformed KR
actor-flow fragments. It does not apply a global particle replacement or guess arbitrary Latin
pronunciation.

`priority_watch` owns ongoing thesis drivers and risks. `next_checks` owns the next filing,
earnings release, or other time-bound confirmation that could change the judgment. Exact copies,
event-oriented watch items, and semantic overlap without a distinct event condition fail quality;
either section may be suppressed when it adds no new decision information.

Numeric dedup is based on `fact_id` plus `field_path`, not surface text. One exact number has one
primary owner section and may appear twice only when its second use has a distinct decision role.
Three or more occurrences in one stock message fail quality. Current-price RR is normally owned by
price positioning, while core judgment and observer prose carry its supported meaning without
printing the same value again.

## Evidence Boundary

The 2026-08-18 immutable US/KR replay is retrospective evidence only. A PASS does not update Pilot,
send Telegram, mutate archives, or close natural AI-assisted delivery. The code must be separately
promoted to operating shadow and then pass a naturally scheduled US/KR session.
