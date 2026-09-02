# 2026-09-02 Decision Consistency Integration

## Contract

`accepted-decision-consistency-v1` records, per ticker:

- current and prior evidence fingerprints
- prior accepted decision
- fresh candidate
- adjudication status and recommendation
- fresh accepted decision
- evidence-fingerprint delta state
- accepted-decision change and explanation status

The prior baseline contract does not retain the complete prior evidence packet. A changed hash is
therefore reported conservatively as `FINGERPRINT_CHANGED_UNCLASSIFIED`, not promoted to a
proven material business change. A changed accepted decision still requires valid final
adjudication. Same-evidence accepted drift remains fail-closed.

## Frozen Integration Result

Sources:

- prior: `20260830-v2-accepted-decisions.json`
- fresh: `20260902-run51-v2-accepted-artifact.json`

Results:

- Fresh US subjects: `14`
- Comparable prior subjects: `13`
- New subject without prior baseline: `1` (`CPNG`)
- Accepted decision changes: `1` (`GOOGL`, BUY to HOLD)
- GOOGL canonical evidence fingerprint changed: `YES`
- GOOGL final adjudication: `KEEP_V2`, valid
- Unexplained accepted decision drift: `0`
- Raw candidate used as final: `0`
- Daily review overriding valid V2 accepted plan: `0`

The fresh distribution is `0 BUY / 11 HOLD / 3 SELL`. It is not forced to match a prior model
distribution; the guard audits ownership and explanation rather than imposing deterministic model
output.

## Gate

`UNEXPLAINED_ACCEPTED_DECISION_DRIFT = 0`

`RAW_CANDIDATE_USED_AS_FINAL = 0`

`DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED = 0`
