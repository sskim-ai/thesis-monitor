# Phase Advancement Readiness

Date: 2026-08-20
Rule: `Phase Advancement Rule v1`
Implementation: `9d105ffb56dd88ef1629cebdcee435522c6d234c`
Implementation CI: GitHub Actions run `32353318455`, Test/Lint PASS

## Decision

`PHASE_9_0A_READY = YES`

This decision authorizes a separate Phase 9.0A Cash Flow / Capital Efficiency Evidence Architecture
task. It does not implement, integrate, or expose OCF, CAPEX, FCF, working-capital, or ROIC values.
Natural AI-assisted delivery remains `PARTIAL` and continues in parallel.

## P0 Safety / Correctness

Open P0: `0`

Run-29 has no unresolved numeric provenance, semantic, identity, denominator, price, RR, delivery,
receipt, archive, or exactly-once correctness error. LS ELECTRIC and Hanwha Aerospace share-basis
valuation stays unavailable because the canonical identity/denominator evidence is unverified; no
unsafe value is promoted.

## P1 Analysis Integrity

Open P1: `0`

Closed retrospectively:

| Issue | User impact | Repair evidence | Roadmap blocking |
|---|---|---|---|
| KR structured supply rows treated as prose repetition | valid AI candidate rejected despite correct canonical tuple | typed `canonical-supply-flow-tuple-v1`; run-29 quality PASS | no |
| Exact current RR duplicated across core and price | repeated number diluted section ownership and produced generic templates | `numeric-primary-owner-v1`; violations 4 -> 0 | no |
| Generic financial caution and inventory/CAPEX-to-FCF/ROIC families | company analysis appeared portfolio-generic | candidate suppression with specific Unknown/next check retained; substantive 2 -> 0 | no |

## P2 Backlog

| Issue | Current safety | Roadmap blocking |
|---|---|---|
| Extreme RR qualitative interpretation | canonical math and invalid-RR guard remain intact | no |
| Legacy fallback prose and fPER source-label polish | fallback remains validated and exactly once | no |
| Explicit current-PBR history lineage reference | equality ownership is safe; explicit ref remains low priority | no |
| KRX breadth integration | telemetry only, user-visible integration 0 | no |
| Inferred KRX identity/share-denominator coverage | dependent valuation is fail-closed | no |

## Required Gate Evidence

- Run-29 repaired replay: semantic/numeric PASS; runtime quality PASS; language PASS; receipt PASS.
- Run-28 regression: PASS.
- Run-27 regression: PASS.
- Full local pytest: `1120 passed`.
- Ruff: PASS.
- `git diff --check`: PASS.
- Investment/Chart Knowledge checksum parity: PASS.
- Public Action: `0.4.5`; operationId `20/20` unique.
- Implementation exact-SHA Actions: Test/Lint PASS.
- Production Assist: OFF.
- Manual Telegram / task / Pilot / DB mutation: `0`.

## Individual Natural Proof

- Reasoning Ownership: `LIVE_PASS_RUN29`; Korean Re security and POSCO/Hyundai framework routes were
  exercised without the run-27 ownership errors.
- US Numeric Summary Ownership: `LIVE_PASS_RUN29`; generic summary and business ownership checks
  were exercised with zero recurrence. This does not by itself prove a US AI delivery.
- Typed Repetition: `LIVE_PASS_RUN29` for the prior typed relation boundary; the new KR structured
  family is tracked separately.
- KR Structured Repetition: `CLOSED_RETROSPECTIVE_PENDING_NATURAL`.
- Night Futures: session basis `CLOSED_RETROSPECTIVE`; numeric preceding-DAY exposure still awaits a
  natural eligible US pair.
- KRX telemetry: natural 16:05 capture recorded, provider pending with HTTP 200/0 rows; 08:05 remains
  pending; user-visible integration 0.

## Parallel Rule

Phase 9.0A architecture and the next natural US/KR proof may proceed in parallel. A new P0 pauses
Phase 9.0A for targeted repair. A material P1 receives bounded repair; P2 remains backlog. KRX
publication completeness does not block Phase 9.0A.
