# Canonical Swing Structure Candidate

## Contract

`canonical-swing-structure-candidate-v1` is the backend-owned input domain for variable Fibonacci
selection. Candidates are deterministic structures derived from confirmed, completed-bar pivots.
The AI selects IDs and never supplies anchor prices, dates, or Fibonacci numerics.

Each candidate preserves ticker, timeframe, mode, ordered pivot references, correction pivot,
anchor chronology, confirmation timestamps, and source evidence references. Both retracement and
extension structures are enumerated where the canonical pivot evidence supports them.

## Selection Bounds

- Monthly: at most 8 structures.
- Weekly: at most 10 structures.
- Daily: at most 12 structures.

Bounds preserve structural diversity rather than only a global rank. The list retains maximum
magnitude and most-recent candidates per mode plus representatives across correction and high
pivots. Omitted canonical IDs remain auditable with reason `BOUNDED_CANDIDATE_LIMIT`.

## Validation

A selected ID must exist in the same ticker/timeframe packet and pass pivot identity, chronology,
completed-bar, confirmation-cutoff, and security/corporate-action basis checks. A selected structure
never carries backend SR ownership. Validation failure is local to its timeframe and cannot change
independent timeframe SR or Fibonacci eligibility.

The closure trial omitted none of the prior material selected structures from the bounded candidate
set. Candidate limits and existing merge tolerances were unchanged.

