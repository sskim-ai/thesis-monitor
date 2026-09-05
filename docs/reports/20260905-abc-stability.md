# A/B/C Stability

`STATUS = NOT_MEASURED_STOPPED_B_GATE`

| Run | Validated | Message quality | Result |
| --- | ---: | --- | --- |
| FIRST | 22/22 | PASS | Gate passed |
| A | 22/22 | PASS | Gate passed |
| B | 17/22 | FAIL | Gate failed; experiment stopped |
| C | 0/22 | NOT_RUN | Correctly suppressed after B failure |

No complete A/B/C set exists, so `STABLE_COUNT`, `BOUNDARY_UNCERTAINTY_COUNT`, and `UNSTABLE_COUNT` are `NOT_MEASURED`. Majority vote, decision averaging, partial-C inference, and candidate repair are all `0`.
