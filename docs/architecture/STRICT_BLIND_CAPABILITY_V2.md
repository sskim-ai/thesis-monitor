# Strict Blind Capability V2

REV59F changes only the opt-in independent blind contract. Source acquisition,
valuation evaluability, native Core/A/B, B2 economics, comparison, and the
clean-start controller are unchanged.

## Timing

`newbuyer_b2_contract.timing` remains the owner. A selected range is favorable
only when the same-basis current price is inside it. Above/below means waiting
for that range. The blind input now exposes each exact relation, its candidate,
owner receipt, complete range-and-price refs, ref digests, and generation/security
binding. Output schema and semantic validation require one complete relation ref
set. Generic risk/reward or resistance context cannot substitute for that set.
UNRESOLVED remains available; no relation is created to match an earlier answer.

## Risk and Holder

Source observation permissions are explicit, not economic judgments. Existing
adverse observations permit the model to assess materiality; verified persistence
or realized impairment is required for REDUCE. REVIEW and REDUCE both require
active material risk. This bounded contract has no separate watch-only REVIEW.

An exact negative operating-income observation with owned current period can
also expose `REPORTED_OPERATING_LOSS` as absolute-level context. A loss and a
directional improvement can coexist. This context grants no active-risk
permission and does not establish severity, persistence, runway, or impairment.
No threshold, ticker rule, or new investment verdict is introduced.

## Ownership and Verification

`blind-capability-contract-v2`, the rubric, prompt, schema authority and exact
subject digest bind the representation. Production and B2 contracts remain
unchanged. Tests cover complete/missing/wrong relation refs, unavailable timing,
improving losses, Holder coupling, identity drift, contamination, and independent
valuation judgment. Comparison still has no agreement-rate acceptance threshold.

Historical R1 outputs remain v1 outputs. Offline replay reports their original
validation and a separate candidate semantic diagnosis without rewriting labels,
refs, metadata, or raw bytes. That diagnosis cannot admit them as v2 results or
resume the halted formal run. Phase B requires a genuinely new source generation
after full local validation and exact feature-SHA Hosted CI PASS.
