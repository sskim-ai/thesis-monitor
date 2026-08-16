# Phase 7.2.9 Runtime Message Quality Gate Readiness

## Status

Phase 7.2.9 is implemented only on `codex/phase-7-2-7-live-quality-reconciliation`.
Production main remains on the Stage A documentation line, with runtime Pilot KR 3/5 and US 2/5,
AI mode `shadow`, and Production Assist disabled. No application code is merged or deployed.

The natural KR Day 3 packet `2026-08-16-kr-run-21-049f367f0274` remains an immutable operational SUCCESS and
human-message-quality FAIL. Its count is not rolled back, and it is not Production Assist evidence.
The corrected retrospectives below are `pending_work_human_review`; deterministic PASS is not a
human approval.

## Root Cause Confirmation

| Finding | Confirmed layer | Evidence |
| --- | --- | --- |
| Six Korean particle errors | numeric provenance / validation / reasoning | old payload replay reports six invalid postpositions |
| Unsupported KR supply directions | reasoning / validation | all 42 foreign/institution 1d/5d/20d cells existed and were eligible; old prose omitted claims yet asserted directions |
| Repeated stock skeleton | reasoning / quality audit | normalized company, ticker, date, and numeric claims reveal substantive repeats |
| Missing financial period | canonicalization / packet / provenance | persisted lineage lacked display metadata; uniquely matched snapshots supply period type/scope |
| Unsupported valuation judgment | reasoning / validation | absolute multiples lacked historical, peer, or expectation comparison Facts |
| CORZ PBR/BVPS conflict | calculation / canonicalization / provenance | positive price and provider PBR conflict with negative BVPS on the same period/currency/security basis |
| RXRX supply absence wording | knowledge routing / validation | a 20-day volume ratio existed; no US investor-flow contract existed |
| Offline-only quality audit | delivery / persistence / policy | delivery did not require a receipt bound to packet, output, and rendered payload hashes |

## Implementation

- Typed numeric postpositions support `와/과`, `은/는`, `이/가`, and `을/를`; raw particles after a
  placeholder reject and the renderer does not rewrite grammar.
- KR supply direction is actor-, horizon-, sign-, and occurrence-specific. Every eligible foreign
  and institution 1d/5d/20d cell in the corrected run is canonically bound.
- Financial amount labels carry the verified amount period. An `H1` filing with `single-quarter`
  amount scope is labeled second quarter; only cumulative evidence produces a half-year label.
- Absolute valuation multiples stay neutral unless homogeneous historical, peer, or independent
  expectation evidence supports a direction.
- `valuation-coherence-v1` denies CORZ PBR and dependent historical PB while retaining independent
  price, revenue, TTM EPS, and volume evidence.
- US stock text cannot use generic Korean-style supply language without an explicit US flow Fact;
  RXRX uses its 20-day relative-volume evidence as participation, not investor flow.
- The runtime path now requires `runtime-message-quality-v1` after deterministic rendering and
  before atomic payload/receipt persistence and delivery.

## Negative Replay

The immutable KR Day 3 output fails the new gate with 25 full-validator errors. Categories include
9 supply-grounding errors, 12 missing financial-period usages, 2 unsupported RR comparisons, and
2 unsupported valuation judgments. The rendered replay also records six particle mismatches,
one substantive repeated sentence, and two repeated template skeletons. Historical delivery,
archive, and Pilot state are unchanged.

## Corrected KR

| Check | Result |
| --- | --- |
| Corrected packet | `2026-08-16-kr-run-21-27d84c4e9795` |
| Completeness | market 1 + stocks 7 |
| Automatic / manual bindings | 117 / 0 |
| Rejected / formatter / unresolved | 0 / 0 / 0 |
| Full validator | PASS, 0 errors |
| Runtime quality gate | PASS, 0 errors |
| Foreign/institution 1d/5d/20d | 7/7, all 42 eligible cells bound |
| Periodless financial amount | 0 |
| Particle mismatch | 0 |
| SK Hynix denied leakage | 0 |
| Observer/holder distinct | 7/7 |
| Substantive/template repeat | 0 / 0 |
| Payload SHA-256 | `67e41477c5dbd221f95344576bfb61d7ab4040e5b0a97c9a40f16ec4ea06abf2` |

## Corrected US

| Check | Result |
| --- | --- |
| Corrected packet | `2026-08-16-us-run-20-53fa21541277` |
| Completeness | market 1 + stocks 13 |
| Automatic / manual bindings | 169 / 0 |
| Rejected / formatter / unresolved | 0 / 0 / 0 |
| Full validator | PASS, 0 errors |
| Runtime quality gate | PASS, 0 errors |
| CORZ PBR/BVPS contradiction visible | 0 |
| RXRX generic supply language | 0 |
| CRCL transition contradiction | 0 |
| KR-style supply language | 0/13 |
| Observer/holder distinct | 13/13 |
| Substantive/template repeat | 0 / 0 |
| Payload SHA-256 | `607bda0367ed71141509c5a6c95836a298b3922c33706a844b89487090fda1cf` |

## Runtime Gate And Retry

The receipt binds the canonical packet, validated output, and exact rendered logical payload set.
A gate failure cannot be promoted to validated AI output or sent; one deterministic fallback set
remains eligible and Pilot success stays blocked. A network retry validates the persisted receipt
against the persisted payload and does not rerun analysis, packet generation, binding, validation,
or rendering. Tampered payload replay returns `quality_receipt_invalid` with zero sends.

## Safety And Contracts

- Provider/network calls: 0
- Telegram sends: 0
- Operating DB, assessment, packet, output, archive, and Pilot mutations: 0
- Scheduled Task changes and API restarts: 0
- Runtime Pilot: KR 3/5, US 2/5
- Production Assist: OFF
- Output schema: 4; Public Action: 0.4.5; operationId: 20/20 unique
- DB migration: none
- Main code merge and operating deployment: not performed

## Artifacts

- [Corrected KR Preview](20260816-phase7-2-9-kr-corrected-telegram-preview.md)
- [KR negative replay](20260816-phase7-2-9-kr-live-negative-replay.json)
- [KR numeric binding](20260816-phase7-2-9-kr-numeric-binding.json)
- [KR validator](20260816-phase7-2-9-kr-validation.json)
- [KR runtime receipt](20260816-phase7-2-9-kr-runtime-quality-receipt.json)
- [KR supply matrix](20260816-phase7-2-9-kr-supply-matrix.json)
- [KR financial period audit](20260816-phase7-2-9-kr-financial-period-audit.json)
- [KR postposition audit](20260816-phase7-2-9-kr-postposition-audit.json)
- [KR template audit](20260816-phase7-2-9-kr-template-similarity-audit.json)
- [Corrected US Preview](20260816-phase7-2-9-us-corrected-telegram-preview.md)
- [US numeric binding](20260816-phase7-2-9-us-numeric-binding.json)
- [US validator](20260816-phase7-2-9-us-validation.json)
- [US runtime receipt](20260816-phase7-2-9-us-runtime-quality-receipt.json)
- [CORZ valuation coherence](20260816-phase7-2-9-corz-valuation-coherence-audit.json)
- [RXRX positioning](20260816-phase7-2-9-rxrx-positioning-audit.json)
- [Delivery/fallback audit](20260816-phase7-2-9-runtime-delivery-fallback-audit.json)
- [Isolation audit](20260816-phase7-2-9-isolation-audit.json)

## Remaining Gaps

1. Work must directly review both corrected full Previews; their human-quality status is pending.
2. TSM and WRD remain identity Unknown without separately approved authoritative evidence.
3. The new runtime gate has not run in a natural production task because this branch is not deployed.
4. KR local index, breadth, and market-wide flow Facts remain unavailable and are explicit Unknowns.
