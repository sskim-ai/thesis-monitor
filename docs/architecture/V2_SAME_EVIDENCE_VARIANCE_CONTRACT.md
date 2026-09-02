# V2 Same-Evidence Variance Contract

## Purpose

`v2-same-evidence-balance-variance-v1` measures model variance without turning repeated model calls into production voting. The harness is diagnostic and non-production. Natural production remains one fresh candidate, required adjudication, and one accepted plan.

## Frozen Identity

Every compared observation must share ticker, packet ID, evidence fingerprint, and candidate-input fingerprint. At least three independent ephemeral executions are required. An identity mismatch or fewer executions fails the audit.

## Distance

Because BUY plus SELL always equals 10, distance is `abs(buy_A - buy_B)`. Pairwise maximum distance is classified as:

| Distance | Classification |
| ---: | --- |
| at most 0.5 | `MINOR_VARIANCE` |
| 1.0 | `MODERATE_VARIANCE` |
| at least 1.5 | `MATERIAL_VARIANCE` |

Candidate and accepted labels are audited separately. Any pair of different labels is a `LABEL_BOUNDARY_CROSS` and increments the boundary-cross count.

## Accepted Stability

Candidate variance may be visible while accepted output remains stable through adjudication. A material accepted-balance distance or accepted-label boundary cross under identical evidence is `unexplained_same_evidence_accepted_drift` and fails readiness. The audit records candidate and accepted outcomes; it never selects a majority label.

## Isolation

The evidence runner uses frozen packets, isolated signed-in Codex CLI state namespaces, and archive output. It creates no Telegram send, production intent, assessment, accepted runtime state, warning, or thesis mutation.
