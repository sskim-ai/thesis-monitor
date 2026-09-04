# V2 Eligibility Authority

`delivery-eligibility.json` is the single selector/delivery agreement receipt.

It records analysis, accepted-content, selector, and delivery generations; recipient class;
candidate counts; final explicit counts; gate state; and reason code. Artifact presence alone no
longer writes `eligible=true`. The receipt is written as eligible only after the combined rendered
message set passes runtime quality. A quality rejection writes `eligible=false` and zero final
explicit counts.

The final E2E receipt records:

- accepted market review: `1`
- accepted stock reviews: `8`
- candidate stock V2 blocks: `8`
- final explicit AI market: `1`
- final explicit stock V2: `8`
- final explicit AI total: `9`
- delivery-ready: `true`

This keeps rejected-generation delivery eligibility at zero and prevents selector/delivery count
drift.
