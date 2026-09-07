# New Issuer Holdout Selection Pre-Execution Readiness Review

Date: 2026-09-07 KST

## Decision

- Selection review: `PASS`
- Readiness: `READY_FOR_SEPARATELY_AUTHORIZED_NEW_HOLDOUT_PROOF`
- Next scope: `NEW_ISSUER_HOLDOUT_FINAL_FREEZE_AND_OWNERSHIP_PROOF`
- Ownership generalization: `NOT_ESTABLISHED`
- Proof executed: `false`

## Provenance

- Task base: `edd24c8bd0bf1d79d8bd49a875bf609eb90752eb`
- Work-instruction commit: `6ee6767001e3de2ea0ad98dd73b6e81772448e13`
- Review-policy commit: `1644b3dc0d157b4c7e1835e157299e723aa544e2`
- Implementation freeze: `f56b7a69cc3bdfd085151d12c43f3a08791554de`
- Accepted input ZIP SHA-256: `12ed21a8fcd378036fb86e08193fcffb5b3e0f9f0710f92602a2f3c595c18cf4`
- Selection policy SHA-256: `c66583d78dc9155e454df172730691040778a25f5c8e4ab33da63919a172d574`
- Non-executable review manifest SHA-256: `6bba480d63661967c80192af6d80287bb3bb9c4d9cf31084eaeeb6a45358b99c`

## Proposed Cohort

US4, in preserved order:

`NVMI`, `SKYH`, `WKSP`, `EROC`

KR12, in preserved order:

`373160`, `452200`, `389470`, `380550`, `008970`, `047080`, `068270`, `475830`, `033160`, `079940`, `103140`, `278280`

The context grouping is one US4 group followed by three KR4 groups. The review
manifest is explicitly non-executable, does not authorize a model adapter, and
is not a proof source lock.

## Reconciliation

- US unseen supported issuers: 25
- US source-sufficient proposed issuers: 4
- US known source failures: 2
- US globally untested issuers: 19
- US untested within the first-24 diagnostic budget: 18
- KR unseen supported issuers: 2,491
- KR reviewed/source-sufficient issuers: 12/12
- Canonical exclusion issuers preserved: 85
- Exclusion registry mutation: 0

All selected subjects retain their exact filing period and source provenance.
NVMI remains `2025-FY`; it was not relabelled as a current quarter. Exact raw
SEC/OpenDART response bytes were not present in the accepted bundle, so the
review reports normalized facts and source-payload hashes without claiming raw
provider-byte custody. All 16 subjects are price-ready with technical context
classified `PARTIAL_SAFE`.

## Model-Free Preflight

- Accepted fictional baseline contexts: 64
- Real-packet request rehearsals: 64
- Total model-free contexts: 128
- Fresh and resumed runtime identities: `PASS`
- FIRST/A/B/C request construction: `PASS` in both modes
- Directional Core and Price-Timing stages: `PASS`
- Identity, market, preservation, ownership, renderer, and hard-safety gates: `PASS`
- Real investment model invocations: 0
- Real subject outputs: 0
- FIRST/A/B/C real executions: 0
- Exposure-registry leaks: 0

## Validation

- Focused tests: 46 passed
- Full test suite: 2,660 passed, 2 warnings
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Model-backed tests: 0

Production code, stores, schedules, Telegram delivery, V2 activation, and Night
Futures were unchanged. A future proof task must freeze a new executable source
lock, recheck source freshness and live-workload coexistence, then obtain separate
authorization before any real model invocation.
