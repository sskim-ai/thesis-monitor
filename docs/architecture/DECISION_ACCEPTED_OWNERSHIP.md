# Decision Accepted Ownership

The canonical implementation is documented in `V2_ACCEPTED_DECISION_OWNERSHIP.md`. This companion
contract records the four-track integration guard added on 2026-09-02.

## Final Authority

Only a valid `accepted_plan` may own the rendered BUY, HOLD, or SELL decision. Raw candidates,
secondary daily-review prose, market-message enrichment, and deterministic fallback text cannot
replace that authority.

## Evidence Drift

The integration diagnostic compares prior and current evidence fingerprints. Fingerprint change is
recorded conservatively as unclassified evidence change; it is not automatically called a material
business change. If the accepted decision changes, final adjudication must be valid. An unexplained
accepted-decision drift blocks readiness.

## Isolation

Diagnostics are attached to internal runtime artifacts and audit reports. They do not write
accepted history, assessments, warnings, delivery ledgers, or packet ownership state.
