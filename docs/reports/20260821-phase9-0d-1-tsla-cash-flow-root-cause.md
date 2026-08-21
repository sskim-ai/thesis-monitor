# Phase 9.0D.1 TSLA Cash-Flow Root Cause

## Decision

The TSLA production fallback contained an unsupported current financial-state claim. Its final
root-cause branch is **Branch C: provenance unsupported**. Severity before repair is **P0** because
the claim was user-visible and presented generic FCF deficit as current without a financial Fact,
period, or scope.

## Exact Origin

- Source: operating `data/theses/TSLA.json`, field `core_thesis`
- Thesis: version 5, source `custom_gpt`, created `2026-08-10 14:20:17.365948`
- Claims: `FCF 적자` and `FCF 흑자 전환이 증명되어야 한다`
- Persisted or synthesized: persisted saved-thesis prose; fallback rendered it directly
- Packet occurrence: `thesis.core_thesis` in run
  `2026-08-21-us-run-30-5a3b7c1c4390`
- Production occurrence: TSLA `fallback-messages.json`, delivery 224

`warning_backfill_service.py` recognized `FCF 적자` in that prose and created `FCF 적자 확인`.
Its reference was `thesis:TSLA:v5`, provider `saved_thesis`, and provenance state
`backfilled_saved_thesis`. That proves the prose origin only; it is not financial Fact provenance.

## Canonical Context

The exact filing supplies three PPE-only FCF period views ending 2026-06-30:

| Period | Value | Fact ID |
|---|---:|---|
| 2026 H1 YTD | +$352M | `cashflow:68666c261434dab50ab88a8d` |
| 2026 Q2 QTD | -$1.092B | `cashflow:916296c301964400796c7ae6` |
| TTM | +$5.762B | `cashflow:7580fc1716d8a467fb82fda6` |

The natural canary correctly selected H1 YTD as its current-formal primary period. The negative Q2
QTD Fact means the old prose is not “numerically false for every possible period.” It does not save
the production claim: the saved prose has no QTD period, PPE-only scope, source occurrence, or Fact
reference and cannot be deterministically mapped to that quarter.

## Failure Path

```text
custom_gpt thesis prose
  -> saved core_thesis
  -> prose-only warning backfill
  -> assessment warning state
  -> AI packet and deterministic fallback
  -> user-visible unqualified current FCF deficit
```

Phase 9.0D validated the shadow output internally. The prior Unknown gate checked “Fact exists but
message says unavailable”; it did not compare production qualitative sign/currentness/scope with
the shadow's canonical primary Fact. The canary could therefore pass while production prose stayed
inconsistent.

## Repair

`baseline-cash-flow-claim-consistency-v1` now extracts narrow structured semantics, checks
current-formal comparability, and fails closed when legacy current-state prose lacks financial
provenance. The AI packet and fallback share the repair. The runtime canary additionally audits the
packet baseline and final production text by rendered section.

Stored thesis and assessment history are unchanged. The current renderer removes the unsupported
FCF clauses and warning while preserving margin, Robotaxi, price, valuation, and next-check logic.
No canonical cash-flow amount is added.

## Closure

- Root-cause severity before repair: `P0`
- Open P0 after repair: `0`
- Open material P1 after repair: `0`
- Archive rewrites: `0`
- DB or warning-lifecycle mutations: `0`

