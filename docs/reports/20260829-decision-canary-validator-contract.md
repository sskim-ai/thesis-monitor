# Decision Canary Validator Contract

Validation reuses `cross-market-ai-decision-engine-v1` and adds canary ownership checks:

- exact claim ID, packet ID, assessment date, ticker, market, and evidence SHA binding
- `VERY_HIGH` reasoning grade without treating it as confidence
- decision, confidence, timing, horizon, and evidence-ref taxonomy validation
- HOLD two-sided boundary validation
- SELL non-order semantics
- prohibited numeric and unsupported claim rejection
- exact four-subject scope
- rejected-output suppression

The new evidence-bound continuity rule applies only when the canonical evidence SHA is identical.
If a previously accepted classification exists for that exact SHA, unexplained class churn is
rejected. Confidence and timing prose remain independently evidence-owned and are not frozen.

The validator never recomputes or selects the investment decision. It checks ownership,
completeness, and continuity. Threshold relaxation, ticker-value hard-coding, and global decision
visibility are `0`.
