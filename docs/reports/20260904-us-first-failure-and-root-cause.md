# US First Failure and Root Cause

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## First material failure

`FIRST_MATERIAL_FAILURE_CLASS = MODEL_TRANSPORT_FAILURE`

The first abnormal transport event was primary's claim-scoped V2 canary `UnknownIssuer` at `08:30:13.659620 KST`. The outer primary had already authored the complete candidate, but waited on the auxiliary canary. During that wait, the scheduled backup reclaimed the expired 10-minute lease at `08:30:39.046046`, making primary stale.

## Primary root cause

The signed-in xhigh CLI could not validate the peer certificate on the Codex response endpoint. Its raw `UnknownIssuer` token was normalized by the wrapper as `LOCAL_NETWORK_CONNECTIVITY_FAILURE`, because the classifier recognizes `unknown issuer` with a space but not `UnknownIssuer` without one. This obscured, but did not create, the TLS failure.

## Secondary effects

- Primary finalization was fenced as `stale_claim_output`.
- Backup reused the same draft and hit the same TLS condition.
- Backup's first and corrected candidates independently failed validator rules, so no accepted AI artifact existed at the 08:40 deadline.
- Deterministic fallback sent all 15 messages exactly once.

## Not causal

- No 08:20 primary-missing check or false-negative identity lookup occurred.
- The earlier shadow call had the same TLS symptom but ended before the natural window and made no production writes.

This task intentionally applies no repair.
