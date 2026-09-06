# Direction Timing Root Cause

| Gate | Value |
| --- | --- |
| contract | direction-timing-root-cause-v1 |
| observed | {"hold_lean_flip": "PLTR regression observation only", "price_dominated_sell": "NKE regression observation only"} |
| repair | generic evidence-domain and field ownership separation |
| root_cause_class | DIRECTION_TIMING_OWNERSHIP_LEAKAGE |
| ticker_specific_rule_count | 0 |

Machine proof: `20260906-direction-timing-ownership-proofs/direction-timing-root-cause.json`.

The prior single-stage candidate allowed technical evidence to become the dominant investment direction owner. The repair fences non-price issuer evidence into Directional Core and routes price, OHLCV, and supply evidence only to execution timing. No PLTR- or NKE-specific rule is present.
