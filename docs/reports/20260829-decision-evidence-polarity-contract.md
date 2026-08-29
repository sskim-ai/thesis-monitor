# Decision Evidence Polarity Contract

Contract: `decision-evidence-polarity-v1`

Structured fields:

- `buy_case_evidence`: `BULLISH`
- `sell_case_evidence`: `BEARISH`
- `neutral_context_evidence`: `NEUTRAL`
- `reason_role`: `FUNDAMENTAL`, `VALUATION`, `TIMING_ONLY`, `DATA_QUALITY`, `MARKET`,
  `TECHNICAL`, or documented other

Every selected claim owns canonical `evidence_refs`; each selected ref must retain `source_ref`
and `as_of`. DATA_QUALITY is neutral, timing-only evidence cannot solely own a long-horizon side,
and one ref cannot appear on both directional sides.

The general shape supports up to three material claims per side. The compact bounded canary selects
exactly one strongest claim per side so all selected evidence is rendered within the existing
2,200-character block budget. No selected claim is silently omitted.

Decision-relative support/opposition remains available for adjudication but is never used by the
BUY/SELL section renderer.
