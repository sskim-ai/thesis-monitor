# 2026-08-24 Macro AI/Fallback Temporal Parity

## Shared Source

Both paths consume the same `temporal_eligibility` object embedded in `MacroBriefing.market_summary`.
The deterministic digest reads per-observation roles directly. Market intelligence carries those
roles into Fact fields and partitions Fact IDs into current, prior-session, and reference sets.
The AI packet receives the same aggregate contract plus current-only key-change and transmission
candidates.

| Dimension | Deterministic fallback | AI | Mismatch after repair |
|---|---|---|---:|
| Temporal role | observation sidecar | Fact field + aggregate context | 0 |
| Source date | observation `observed_at` | Fact `as_of_date` | 0 |
| Today-signal eligibility | current-only axes | current Fact IDs | 0 |
| Important-change eligibility | current/prior-labeled | current key IDs; prior explicit only | 0 |
| Prior-session label | `직전 거래일(M/D)` | prompt contract + validator | 0 |
| Reference/stale suppression | deterministic selector | key/transmission selector + validator | 0 |
| Night-futures authority | existing gate | required night Fact contract | 0 |

## Run-35

The actual run delivered deterministic fallback; no repaired AI output was delivered or generated.
Archive replay proves the common context contract and semantic boundary without rewriting the packet,
claim, candidate, validation receipt, delivery receipt, or message archive. This is retrospective
parity evidence, not natural live proof.
