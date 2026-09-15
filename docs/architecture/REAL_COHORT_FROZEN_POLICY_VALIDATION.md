# Real-Cohort Frozen Policy Validation

## Status

M12BK-R2 is an offline policy-validation layer. It consumes the sealed M12BJ
monitored shadow and the sealed M12BD fictional proof without re-running a
model or changing a prompt, schema, semantic service, threshold, or renderer.

## Boundary

```text
M12BJ indexed result + frozen raw identities
  + M12BD indexed fictional result
  + frozen policy contracts
        |
        v
exact rationale hashes + canonical evidence refs
        |
        v
case-scoped policy invariants
        |
        v
tolerated boundary OR bounded policy exception
```

Raw prompt, output, receipt, and log files remain under the existing
local-only M12BJ root. They are read only for identity and exact-rationale
verification. The M12BK-R2 package records hashes, canonical references,
decision fields, counters, and classifications, never raw model prose.

## Frozen Contracts

`BusinessDeltaEvidenceView` remains authoritative. `HOLDABLE`, `REVIEW`, and
`REDUCE` retain their established meanings. A 5.5-to-6.0 HOLD-to-BUY/SELL
boundary remains tolerated when Business Delta and both stance contracts are
unchanged and canonical provenance is clean. Same-direction balance or
confidence movement is advisory when all decision stances remain equal.

Issuer-level current valuation is part of the pre-timing fundamental decision
context. It may support a HOLDABLE-to-REVIEW materiality boundary when a
current canonical valuation anchor exists, severity or persistence remains
unresolved, and no price, technical, or supply evidence creates the holder
stance. Configured future conditions and unknowns cannot create REDUCE.

New-buyer stance stays independent from primary direction. M12BK-R2 therefore
uses the FIC-FIN-05 analogue only to verify that identical primary directions
can retain different entry stances; it does not introduce a BUY-to-ATTRACTIVE,
HOLD-to-WAIT, or SELL-to-AVOID mapping.

## Readiness

A clean result hands off only to
`PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN`. It does not
authorize Fresh proof, main merge, deployment, production persistence, or
user-visible changes. Those readiness states remain `NOT_READY`.
