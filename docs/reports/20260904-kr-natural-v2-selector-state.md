# 2026-09-04 KR Natural V2 Selector State

## Predicate

`_load_delivery_accepted_v2()` resolves the claim-bound `decision-v2-accepted.json` path, then validates that artifact against the exact packet and claim. Missing, malformed, or mismatched artifacts become `V2_DECISION_SUPPRESSED_SAFE`.

Generation separately requires the completion receipt and V2 message-quality checks before writing the accepted artifact. Renderer blocks can only come from that accepted artifact.

## Today

- Engine: `v2_accepted`
- `V2_ELIGIBLE=NO`
- Candidate stock V2 count: 0
- Explicit stock V2 count: 0
- Failed requirement: exact claim-bound accepted V2 artifact absent
- Selector state: `V2_DECISION_SUPPRESSED_SAFE`
- Eligibility reason: `accepted_daily_review_ready_explicit_v2_unavailable`
- Regular AI-assisted delivery remained eligible: YES

The selector behaved fail-closed; it did not cause the first failure and did not relax its predicate.
