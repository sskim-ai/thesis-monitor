# Phase 7.2.5 Security Identity Readiness

## Status

- Experimental branch: `codex/phase-7-2-relational-reasoning`
- Required Stage B base: `58fa317a252d58248a41023ba179447252e4a3aa`
- Implementation commit: `b85a8bd57a963accbae3fac04b904986981d7fa4`
- Production main after Stage A documentation reconciliation: `4ce7bb29d8698efa2ad1d31ce80f6e75efa411f8`
- Production policy: `daily-review-v3.9`
- Experimental policy: `daily-review-v3.10`
- Schema / structure / Pilot / renderer: `4` / `v2` / `v3` / `v3`
- Actual Pilot count: KR `2/5`, US `1/5`
- Production Assist: disabled
- Merge/deployment status: experimental branch is not merged or deployed

The commit containing this report is the final documentation commit for Phase 7.2.5. Its exact
commit and exact GitHub Actions run are recorded in the completion report because a file cannot
contain the hash of the commit that contains itself.

## Stage A: Production Pilot Reconciliation

Natural production packet `2026-08-15-kr-run-19-919a670464b4` was audited read-only before the
main documentation update.

- Policy/schema: `daily-review-v3.9` / `4`
- Validator: PASS, zero errors
- Delivery: one market plus seven stock messages, `8/8` sent
- Rejected draft: archived and not delivered
- Archive completion: required artifacts and their completion-marker hashes matched
- Ordering: the archive completion marker preceded the Pilot success record
- Exactly once: the packet appears once in successful sessions and was not counted by a retry
- Runtime state after the natural session: KR `2/5`, US `1/5`
- Mutations performed by the audit: zero

Main documentation commit `4ce7bb29d8698efa2ad1d31ce80f6e75efa411f8` records that runtime
state. It changed documentation and one documentation assertion only; no service restart was
needed. Exact Actions run: https://github.com/sskim-ai/thesis-monitor/actions/runs/31882226074

## Root Cause

Legacy valuation eligibility treated `is_depositary_security=false` as evidence that a security
was non-depositary. SKHY instead had conflicting evidence: its profile name identified an ADR,
while SecurityMaster classified it as a domestic common stock. The provider-native consensus
contract therefore admitted `fPER 6.9509` without a verified current-security denominator or
share basis.

The defect was DATA / SECURITY_IDENTITY at origin and propagated through canonicalization,
packet eligibility, numeric provenance, and validation. It was not an AI wording or renderer
problem.

## Decision

`security-identity-v1` replaces negative inference with four affirmative states:

- `verified_depositary`
- `verified_non_depositary`
- `conflict`
- `unknown`

Identity uses Watchlist and SecurityMaster issuer/security metadata, identifiers, ratio metadata,
provider quality/warnings, listing provenance, and explicit profile ADR/ADS hints. Missing ADR
evidence and a legacy false flag cannot establish non-depositary identity. Conflicting evidence is
preserved rather than overwritten.

Only a verified identity can enter the provider-native multiple contract. `conflict` and `unknown`
make security/share-basis-dependent valuation rows prose-ineligible, remove canonical displays and
approved variants, reject placeholders and raw claims, and block number-free valuation inference.
The dedicated identity Fact remains available for a concrete Unknown explanation.

The same boundary is applied to deterministic fallback. Price, OHLCV, chart structure, volume,
KR supply, and independently verified issuer monetary facts remain available. No ADR ratio,
currency conversion, premium, or discount is inferred.

## Old-Packet Validator Replay

The prior corrected packet `2026-08-15-us-run-18-39f4b8810c45` was passed unchanged to the new
validator. It was rejected with four identity errors and no unrelated errors:

- `GOOGL:security_identity_denied_fact_used:valuation:current`
- `GOOGL:security_identity_denied_numeric_claim:valuation:current`
- `SKHY:security_identity_denied_fact_used:valuation:consensus_forward_earnings`
- `SKHY:security_identity_denied_numeric_claim:valuation:current`

The SKHY errors are the required regression. GOOGL revealed a separate real SecurityMaster
issuer/security-type conflict; it is failed closed rather than treated as a validator false
positive.

## US Isolated Revalidation

- New packet: `2026-08-15-us-run-18-ac1f8a4d0253`
- Packet SHA-256: `e6bbe0e3109917b79062e6ac4d6608f5d03bcdf1eda7b9968b13fd3d5fd04334`
- Completeness: one market plus 13/13 active stocks
- Automatic bindings: `158` (prior corrected result: `162`)
- Manual bindings / rejected bindings / formatter errors / unresolved placeholders: `0/0/0/0`
- Full validator: PASS, zero errors
- Preview SHA-256: `3f7e03636d3178e5df7a17fc535d23eb8372b8c21c87a234e1dc780e3127ba01`

The four-binding reduction is fully explained. GOOGL removed five valuation claims and added two
independent core price/volume claims, net `-3`. SKHY removed two fPER claims, retained/rebound the
price claim and added volume to core judgment, net `-1`.

Only GOOGL and SKHY messages changed. SKHY retains current price `$166.33` and 20-day volume ratio
`0.43x`, while trailing PER, PBR, and market-expected fPER are withheld. It states the profile ADR
versus SecurityMaster common-stock conflict and performs no conversion. TSM retains TWD issuer
financials and USD ADR price separation; TSLA and WRD still expose no unsafe monetary amount.

## KR Regression

- New packet: `2026-08-14-kr-run-17-a1dc3dbdc6a9`
- Packet SHA-256: `6f455037f3999bc2fc5d04ce97e6e20090fb7e2d2cbdee11ecf4ec9a3cb82b7c`
- Completeness: one market plus 7/7 active stocks
- Automatic bindings: `141`
- Manual bindings / rejected bindings / formatter errors / unresolved placeholders: `0/0/0/0`
- Full validator: PASS, zero errors
- Preview SHA-256: `6cc9f52f314ec7ace385622b7a8ab4d25431eadfb66547d30e903d2599fb8ed2`

All eight raw payloads differ only because the experimental Preview advances the candidate label
from `KR Pilot 2/5` to `KR Pilot 3/5`. After normalizing that candidate label, payload identity is
`8/8`. Actual persisted Pilot state remains KR `2/5`, US `1/5`. SK hynix unsafe earnings/PER
blocking, dynamic price structure, 1/5/20-day supply, and verified PBR interpretation are unchanged.

## Isolation

- Source DB backup SHA-256: `23451ab3ac99b08b203c6dd736f31aac1ced1f1603be2a387d2ce2a0d22018a1`
- Live provider calls: zero
- Telegram sends: zero
- Operating DB/archive/assessment writes: zero
- Pilot counter mutations: zero
- Scheduled Task changes: zero
- Production Assist changes: zero
- Production main mutations by Stage B: zero
- Operating checkout changes by Stage B: zero

The isolated queue state marked the newly assembled packets `ready_for_ai=false`; the immutable
packet payloads were consumed directly by the archive-only validation harness. This did not alter
the official queue and is not represented as a natural scheduled claim.

## Artifacts

- [Architecture](../architecture/SECURITY_IDENTITY_RESOLUTION.md)
- [Identity eligibility matrix](20260815-phase7-2-5-identity-eligibility-matrix.json)
- [SKHY identity evidence](20260815-phase7-2-5-skhy-identity-evidence-audit.json)
- [Old US validator replay](20260815-phase7-2-5-old-us-validator-replay.json)
- [US corrected full Preview](20260815-us-v310-security-identity-corrected-preview.md)
- [US before/after](20260815-phase7-2-5-us-before-after.json)
- [US numeric binding](20260815-phase7-2-5-us-numeric-binding.json)
- [US validator](20260815-phase7-2-5-us-validation.json)
- [KR regression full Preview](20260814-kr-v310-security-identity-regression-preview.md)
- [KR byte comparison](20260814-phase7-2-5-kr-byte-comparison.json)
- [KR numeric binding](20260814-phase7-2-5-kr-numeric-binding.json)
- [KR validator](20260814-phase7-2-5-kr-validation.json)
- [Fallback matrix](20260815-phase7-2-5-fallback-matrix.json)

## Remaining Gaps

1. SKHY needs authoritative security identity and a verified current-security denominator/share
   basis before provider-native multiples can return to user prose. This remains a safe Unknown.
2. GOOGL has a separate SecurityMaster issuer/security-type conflict (`domestic_us` versus
   `Depositary Receipt`). It is now safely withheld but the underlying DATA record needs correction
   in a separate provider/identity task.
3. `daily-review-v3.10` still requires explicit Work approval, main merge, production deployment,
   Scheduled Task transition, and a natural Live Pilot. None occurred in this phase.
