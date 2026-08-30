# V2 Production Rollback Readiness

Rollback is selector-based: set the visible stock decision engine back to `v1_canary`. The V1 code
and configuration remain available, while V2 candidate, adjudication, accepted-plan, and delivery
history remain immutable.

Rollback triggers include raw-candidate visibility, accepted-decision mismatch, polarity or ticker
identity failure, numeric provenance regression, Price Structure/valuation diff, mixed-language
core output, duplicate/orphan delivery, truncation, or systematic NOT_READY coverage.

Rollback does not resend an already delivered message and does not rewrite state. The next eligible
cycle is corrected unless a separately authorized emergency communication exists.

`V1_ROLLBACK_AVAILABLE = true`; rollback smoke: `PASS`.
