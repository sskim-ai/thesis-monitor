# KR Price Structure Selective Scope

Scope is the packet-derived monitored KR universe only: `7` subjects.

| Eligibility | Count |
| --- | --- |
| ELIGIBLE_SR_ONLY | 7 |

`ELIGIBLE` renders nearest/major SR plus family-stable Fib/SR. `ELIGIBLE_SR_ONLY` renders SR
without a Fib placeholder. `OMIT_PRICE_STRUCTURE` and `BLOCKED` leave the stock message valid.
US and unmonitored subjects are rejected by the market/scope guard.
