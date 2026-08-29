# Decision Canary Churn Analysis

The first fresh xhigh pass returned `003690 HOLD / 000660 SELL / GOOGL HOLD / RXRX HOLD` even though
all four evidence packets were byte-identical to the calibrated canonical packets. The changed
`000660` and `RXRX` classifications were therefore unexplained model churn, not evidence delta.
One initial US response also contained an unknown/truncated evidence reference and was rejected;
one bounded xhigh correction produced a schema-valid candidate.

This material P1 was closed by an evidence-bound continuity contract. For the same evidence SHA,
the backend requires continuity with the previously accepted classification and rejects unexplained
class changes. A fresh xhigh run under that contract produced `HOLD / HOLD / HOLD / SELL` and all
four candidates passed the canonical validator.

Rejected and pre-continuity outputs remain in the completion bundle. They were not sent to any
production recipient. Post-repair unexplained canary decision churn: `0`.
