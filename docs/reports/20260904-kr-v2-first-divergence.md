# 2026-09-04 KR V2 First Divergence

`V2_FIRST_DIVERGENCE=CANDIDATE_INCOMPLETE`

| Stage | Explicit V2 | KR Pilot 5/5 | Today's owner |
|---|---|---|---|
| Candidate | batch 1 started; 0 persisted | regular market 1 + stocks 8 | regular accepted AI |
| Validation | not reached | rejected 17, corrected once, final PASS | regular validator |
| Accepted | no claim-bound artifact | accepted 9/9 | regular schema-4 finalizer |
| Selector | `V2_DECISION_SUPPRESSED_SAFE` | AI-assisted eligible | delivery eligibility service |
| Renderer | no V2 blocks | compatibility/adaptive renderer | Pilot renderer v3 |
| Delivery | 0 V2 | 9 AI-assisted | authoritative primary delivery |

The first divergence is earlier than selector suppression: the outer automation interrupted V2 generation before `candidate_batch_created`. Selector suppression is the correct downstream effect.
