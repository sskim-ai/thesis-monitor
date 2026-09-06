# Track F — New Unseen FIRST + A/B/C Generalization

After source-enrichment freeze:
- select final issuer-distinct holdout
- assemble source-sufficient immutable packets
- freeze one source lock
- reverify decision-engine hashes
- run FIRST once

No same-generation repair.

Proceed to A/B/C only if FIRST has:
0 validator false positives
0 schema failures
0 hard-safety regressions
0 source-sufficiency escapes.

Run A/B/C on exact same source lock.

Measure STABLE / BOUNDARY_UNCERTAINTY / UNSTABLE.

Also audit whether BUY/SELL is dominated solely by price despite available fundamentals.
Do not change the decision engine in this task.
