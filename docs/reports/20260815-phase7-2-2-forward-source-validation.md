# Phase 7.2.2 Forward-Source Validation

## Scope

This experimental-branch change fixes a secondary validator false positive. It does not change canonical source mapping, numeric binding, output schema, renderer behavior, or production policy.

## Root Cause

The previous `_forward_source_language_errors()` searched an entire sentence independently for PE-family terms, PBR-family terms, consensus wording, and modeled wording. A correct sentence such as `시장 예상 fPER ... 내부 추정 fPBR ...` could therefore attach both source words to both metric families.

The affected layer was `VALIDATION`. Canonical facts and binder-generated source labels were already correct.

## Decision

Source wording is now associated with the nearest metric-local phrase inside each sentence:

- PE family: fPER, forward PE, EPS
- PBR family: fPBR, forward PBR, BVPS
- Source labels farther than the bounded local gap are not assigned to a metric.
- An equal-distance ambiguous source label is not guessed.
- Validation remains fail-closed for a source label that is locally attached to the wrong metric.

Canonical binder labels remain the hard boundary:

- `modeled_forward` -> `내부 추정`
- `consensus_forward` -> `시장 예상`
- unknown/unavailable -> neither label is allowed

## Matrix

The committed matrix at [20260815-phase7-2-2-forward-source-matrix.json](20260815-phase7-2-2-forward-source-matrix.json) contains 16 cases; all 16 passed.

| Case family | Result |
| --- | --- |
| Single-source modeled/consensus PE and PBR | PASS |
| Consensus fPER + modeled fPBR in one sentence | PASS |
| Modeled fPER + consensus fPBR in one sentence | PASS |
| Consensus EPS + modeled BVPS | PASS |
| Modeled EPS + consensus BVPS | PASS |
| Wrong modeled/consensus PE and PBR labels | REJECT |
| Unknown source labeled modeled/consensus | REJECT |
| Source wording in another sentence | No cross-talk |
| Unrelated internal-model prose | No cross-talk |

The binder regression also verifies that mixed-source fPER/fPBR/EPS/BVPS placeholders generate four occurrence-level claims with their original source identities.

## US Revalidation

Packet `2026-08-15-us-run-18-dca26c59bb82` was revalidated without rerunning reasoning, binding, or rendering.

- Previous validator: PASS
- New validator: PASS, 0 errors
- Automatic bindings: 168
- Manual bindings: 0
- Unresolved placeholders: 0
- Source/instrument/repeated-label mismatches: 0
- Telegram payload code blocks: byte-identical
- Telegram sends and operating mutations: 0

The complete result is in [20260815-phase7-2-2-us-revalidation.json](20260815-phase7-2-2-us-revalidation.json).

The superseded label-quality baseline now uses the portable repository path `docs/reports/20260815-us-v310-telegram-experimental-preview.md` and records baseline commit `7596769f81e8dbc0272be76026b13c84ed0b766b`; no runtime archive was rewritten.

## Safety

- No validator rule was removed.
- No renderer rewriting was added.
- No source enum is inferred.
- No ticker-specific branch was added.
- Production remains on `daily-review-v3.9`; this branch remains experimental at `daily-review-v3.10`.
