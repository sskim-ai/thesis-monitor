# KIS Research Snapshot Offline Contract

REV35 separates KIS research estimate EPS from financial-ratio reported EPS.
The REV34 mismatch remains immutable evidence. It is not the mandatory scale
oracle for the research family. No live conversion is approved by this change.

`scripts/kis_research_snapshot.py` is offline-only and has no production imports.
Its inputs are trusted, frozen operator reviews and their preserved artifacts,
not arbitrary model claims. Hash receipts detect mutation; they do not replace
the reviewer's responsibility to check official provenance and full extraction.

## Binding And Calibration

- Exact KIS security tuple remains owned by the existing identity contract.
- Preserved official page and attachment hashes, a linked attachment, and
  matching security/analyst/date/title/type/report identity are mandatory.
- Reviewed EPS/PER tables retain every displayed period, units and page/section.
- Each metric independently requires at least two exact period matches and one
  fixed positive terminating-decimal transform across all overlapping periods.
- Outside-API periods remain explicit, not compared with another year. No
  price, financial-ratio EPS, tolerance or period-specific fit is used.
- Partial EPS uses all ordered row pairs and the signed growth denominator.
  A rounding rule must already exist in independently reviewed official
  documentation. No live rounding rule is currently qualified.
- Missing API PER cannot be replaced with report-only PER.
- Stage B consumes the frozen global metric transform, exact security and
  existing fiscal/forecast owners. No per-ticker calibration is introduced.

## Consumption Boundaries

The result is a KIS house-research snapshot, not consensus or a current-session
PER. Estimate date and retrieval time are distinct. Reused Stage-A data cannot
verify the latest snapshot today; no day-count freshness threshold is invented.
Valuation/NewBuyer/Holder roles only; overall direction and business evidence
roles remain prohibited.

Current-price FY1 fPER remains denial-only. The existing repository has no
configured KIS/KSD action-window owner. Neither a caller-supplied no-action flag
nor any price can enable this optional metric. A later source-qualified
corporate-action contract is required before a completed-session price may be
used. The generic production security-basis contract is unchanged.

## REV35 Actual Outcome

Official research metadata acquisition failed within six attempts across local,
web-fetch and browser transports. No report attachment was retrieved. Therefore
all actual metric bindings remain unavailable and Stage B is not admitted.
Positive tests are explicitly synthetic contracts, not empirical KIS proof.
No new KIS API/auth, corporate-action, model or message calls are made.
