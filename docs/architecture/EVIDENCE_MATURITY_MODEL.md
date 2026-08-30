# Evidence Maturity Model

Contract: `evidence-maturity-pricing-v2`

Evidence maturity is assessed per business driver before any overall summary. Allowed values are
`EARLY`, `PARTIAL`, `CONFIRMED`, `MIXED`, and `UNKNOWN`. Every driver carries exact supporting and
contradicting evidence refs, an as-of date, and what remains unproven.

Maturity is neither confidence nor a decision. `PARTIAL + MEDIUM + BUY` and
`CONFIRMED + HIGH + HOLD` are both valid when the evidence-bound pricing and asymmetry analysis
supports them. No backend map or weighted score connects these fields.
