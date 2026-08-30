# V2 Accepted Decision Ownership

Contract: `v2-accepted-decision-ownership-v1`

```text
candidate_decision
  -> material disagreement?
  -> final adjudication when required
  -> accepted_decision_plan
  -> renderer / validator / test sink / migration readiness
```

A candidate is never final after a material disagreement. No disagreement resolves with source
`CANDIDATE`; final KEEP_V1 and KEEP_V2 adjudications resolve with explicit adjudication sources.
Missing, invalid, or non-final required adjudication returns `NOT_READY` and cannot fall back to
the candidate.

Candidate, adjudication, and accepted records have separate deterministic identities and evidence
fingerprints. KEEP_V1 remains a v2 accepted record: it preserves the adjudication rationale and
compatible v2 maturity/pricing context while suppressing rejected candidate-only directional
flags. In particular, rejected pre-confirmation BUY cannot remain active in accepted HOLD output.

The renderer consumes an accepted plan. The validator checks that same plan and cannot select or
recompute a winner. Historical candidate artifacts remain immutable audit evidence only.
