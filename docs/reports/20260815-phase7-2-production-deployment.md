# Phase 7.2 Production Deployment

## Status

Phase 7.2 code commit `5f3aa5c37848092bcccf74bbc917604bebae33d4` is deployed. Production
uses `daily-review-v3.10`, schema 4, structure v2, Pilot v3, renderer v3,
`security-identity-v2`, and `financial-quality-taint-v2`. Production Assist remains disabled.
The actual Pilot count remains KR 2/5 and US 1/5. The first naturally scheduled v3.10 Live session
is pending; no manual run was triggered.

## Pre-Merge Correction

Stage 0 made `adr_ratio_direction` fail closed. It is present only for a verified depositary with a
positive ratio and verified ratio-and-direction provenance. CORZ, GOOGL, HUT, IBM, and WULF now have
null direction; SKHY retains ratio 0.1 with `ordinary_shares_per_adr`. US and KR Telegram regression
payloads were unchanged. Stage 0 branch and main integration checks both passed.

## Backups

The local backup set is `data/backups/phase72-production-integration-20260815T2252KST`.

- Consistent database SHA-256: `3418dbcf603d67684864113f975619e1153bf551433a3e92087b3adf9d5a344b`
- Pilot state SHA-256: `5b1bd50eef20e60ec4f13eb84e8b78a0224b11dc876d4f290fb8e04c52b0fccf`
- Target SecurityMaster rows SHA-256: `372e27b311b9a49acc095523db0117b7763a35a7353ec2106631d076c8d07eac`
- Four original Scheduled Task definitions and the prior operating commit are in the same set.

## Remediation

Dry-run and exact-row review preceded each apply. CORZ, GOOGL, HUT, IBM, SKHY, and WULF were updated
from approved SEC evidence. Every second run returned `no_op_already_authoritative`; non-target
SecurityMaster and provider-cache hashes were unchanged. GOOGL is verified Nasdaq Class A common
stock. SKHY is verified Nasdaq ADS, one ADS represents 0.1 ordinary share, and its unverified
current-ADS multiples remain withheld. No FX, ADR EPS, or premium calculation was introduced.

See [remediation evidence](20260815-phase7-2-production-remediation.json).

## Isolated Validation

A post-remediation consistent database copy produced US packet
`2026-08-15-us-run-18-c10358fd3a28`: market 1 plus stocks 13/13, 161 automatic bindings, zero manual
bindings, and full validator PASS with zero errors. GOOGL's independently clean valuation facts
returned; SKHY's unsafe multiples did not. KR packet `2026-08-14-kr-run-17-96464a52322a` retained
market 1 plus stocks 7/7, 141 automatic bindings, zero errors, and no message diff. Deterministic
fallback preserved the same identity boundary.

See [isolated validation](20260815-phase7-2-production-isolated-validation.json).

## Runtime And Tasks

The API and US/KR AI Review health checks passed after restart. Public Action remains 0.4.5 with
20/20 unique operationIds; Knowledge checksums are unchanged. The four existing local-project tasks
were updated in place, remain ACTIVE at 08:15, 08:30, 16:15, and 16:55 KST, and still target the
operating checkout. US Primary retains its five-minute readiness polling and ten-minute lease.

See [Scheduled Task transition](20260815-phase7-2-scheduled-task-transition.json).

## Safety

Deployment validation sent no Telegram messages and did not increment Pilot state. Historical
packets and archives were not rewritten. There was no DB migration or Public Action/schema change.
The next Live result must come from a natural Scheduled Task and must pass validator, complete the
entire delivery, verify `archive-complete.json`, and count exactly once before Pilot state changes.

## Remaining Gaps

1. The first naturally scheduled v3.10 Live Pilot has not occurred yet.
2. SKHY, TSM, and WRD multiples remain unavailable where current-security denominator, share, or
   currency basis is incomplete.
3. KR local index, breadth, market-wide flow, and broad peer coverage remain unavailable.
