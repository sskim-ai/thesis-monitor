# M12BY Final Readiness

## Result

`M12BY_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY`

Fundamental Core batch/identity closure is implemented and deterministically validated. The new
full22 proof is not complete: it stopped without repair at model-call ordinal 6 on an existing
Stage-2 `maturity_reference_polarity_overlap` hard failure.

## Repository

- Work instruction commit: `fe177a1f5fc5273617055f890e9e8ea192e9e19e`
- Implementation commit: `3a22a8fb167e35da0bba4c2c1681ab70fc65e060`
- Branch: `codex/20260916-m12by-fundamental-core-batch-identity-closure`
- Origin main at start: `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479`
- Main merge / deployment / remote push: `0 / 0 / 0`

## Deterministic Gate

- Focused: `167 passed, 3 skipped`
- Market focused: `94 passed`
- Full: `4035 passed, 63 skipped, 2 warnings`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Old M12BX batch-2 replay: `PASS_FAIL_CLOSED`
- Proof-critical identity free-string gaps: `4 -> 0`

## New Reproof

- Generation: `20260916-uskr22-m12by-20260915T232729Z-3a22a8fb167e`
- Planned calls: `16`
- Started / completed / usable: `6 / 6 / 6`
- Fundamental Core batches completed: `5`
- Fundamental Core subjects represented: `14`
- Cardinality / ticker-set / duplicate / missing / extra / identity failures: all `0`
- IBM present: exactly `1`
- Exact-ref violations: `0`
- Retry / fallback / judge / repair / selective rerun: all `0`

The terminal failure is in US Stage-2 batch 1. CORZ `driver_maturity[2]` included
`decision-evidence:acea5134d19f8ded2449` in both supporting and contradicting refs. The unchanged
Pydantic validator rejected this as `maturity_reference_polarity_overlap`. No output was edited and
no later call was started.

## Market Context

- Kiwoom KOSPI200 9/1-9/3 local replay: `PASS`
- Historical change percentage without basis suppressed: `3/3`
- Authenticated live gateway: `UNAVAILABLE`
- Live read / order calls: `0 / 0`
- KOSDAQ150: `UNAVAILABLE_NOT_YET_PROVEN`
- Treasury DGS3/5/10/30, DFII10, T10YIE: `PASS`
- Parser / bp change / as-of / render / time layers: `PASS`
- Market context readiness: `LOCAL_MARKET_CONTEXT_READY_LIVE_KIWOOM_UNAVAILABLE`

## Decision

Message-model contract readiness is `NO`; deployment readiness is `NO`. The next model scope is a
generic bounded Stage-2 maturity-reference polarity-disjointness review and a completely new full22
proof. Kiwoom read-only gateway enablement remains a separate prerequisite for final live smoke.
