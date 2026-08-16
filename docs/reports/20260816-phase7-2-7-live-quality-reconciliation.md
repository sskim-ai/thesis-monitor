# Phase 7.2.7 Live Quality Reconciliation

## Status

Phase 7.2.7 was validated on branch
`codex/phase-7-2-7-live-quality-reconciliation` from required base
`ff577e4a31d19f855d2f5c1ccb2eb10567244dc8`. It is not merged or deployed. Production remains on
that base with policy `daily-review-v3.10`, Pilot KR 2/5 and US 2/5, AI mode `shadow`, and
Production Assist disabled.

The natural US packet `2026-08-16-us-run-20-6c15d0003955` remains an immutable operational success:
validator PASS, 14/14 delivery, 13/13 required archive artifacts, completion marker, and exactly-once
state recording. Its separate human message-quality disposition remains **FAIL**. It is not eligible
evidence for Production Assist.

## Root Cause

### CRCL confirmation transition

`monitoring_state.delta.confirmation_transition` is
`failed_breakout_to_not_reached`, with previous state `failed_breakout` and current state
`not_reached`. The core judgment reversed that meaning while the price section stated it correctly.
This is `AI_REASONING / VALIDATION`.

The packet now supplies a homogeneous `monitoring:confirmation_transition` fact. Validation checks
explicit previous/current direction, current-state assertions, and conflicting transition claims
across every prose field. The rule is generic and has no ticker branch.

### SKHY identity versus valuation basis

SKHY is `verified_depositary`: Nasdaq ADS with an official depositary ratio. The unavailable items
are the current-ADS earnings denominator, share basis, and currency basis. The live prose called the
security identity itself unverified. This is `AI_REASONING / VALIDATION / PACKET_SEMANTICS`.

The packet now separates `security_identity:current` from `security_basis:current`. Validation
rejects a verified identity described as unverified, an unknown identity described as verified, and
a verified common share described as ADR/ADS. Unverified per-security basis continues to withhold
multiples and qualitative multiple inference.

### US supply routing

All 13 US stock sections imported the KR daily/short/medium investor-horizon frame. This is
`KNOWLEDGE_ROUTING / AI_REASONING / VALIDATION`.

The Skill now makes 1-day/5-day/20-day foreign and institutional flow a KR-only contract when those
facts exist. US reviews use verified volume, relative volume, or explicit packet positioning. The
validator rejects KR horizon language and unsupported investor-flow prose in US reviews. The quality
audit also fails repeated substantive supply sentences and synonym-only missing-flow templates.

### TSM and WRD identity persistence

The Phase 7.2.6 cross-section incorrectly treated legacy `local+openfigi` affirmative depositary
fields as verified. The natural production rows had been normalized to `identity_quality=inferred`,
Tier D, at the 2026-08-15 nightly refresh. Neither ticker has an authoritative security-identity
cache row. OpenFIGI mapping and issuer filing caches do not establish authoritative current-security
identity on their own.

The natural packet's `unknown` state is therefore the correct fail-closed result. The legacy
affirmative promotion path was removed. No production remediation was attempted. TSM and WRD
multiples remain withheld until authoritative identity and current-security denominator/share/
currency basis are independently verified. This is
`DATA / CANONICALIZATION / PACKET / PERSISTENCE / SECURITY_IDENTITY`.

## Pilot Reconciliation

The two dimensions are now explicit:

```text
Operational Pipeline Success != Human Message Quality Approval
```

For the natural US packet:

- `operational_pipeline_success = true`
- `human_message_quality_status = failed`
- `production_assist_evidence_eligible = false`

The persisted US count stays 2/5. No successful packet ID, assessment date, archive, delivery row,
or Pilot state was edited. A deterministic quality gate can pass on an experimental correction, but
Production Assist evidence remains false until direct human approval and a later approved deployment.

## Original Replay

The immutable live output was replayed through the new validator without rebinding or rendering.
It rejected with 31 errors:

| Finding | Count |
| --- | ---: |
| CRCL transition direction | 1 |
| SKHY verified identity described as unverified | 2 |
| US stock KR-style horizon language | 13 |
| Unsupported US investor-flow prose | 15 |

There were no unrelated identity or numeric false positives.

## Corrected US Retrospective

The isolated experiment packet is `2026-08-16-us-run-20-b2339f14d78d`, derived from the immutable
live packet without provider calls or operating writes.

| Check | Result |
| --- | --- |
| Completeness | market 1 + stocks 13 |
| Automatic bindings | 171 |
| Manual bindings | 0 |
| Rejected bindings | 0 |
| Formatter errors | 0 |
| Unresolved placeholders | 0 |
| Full validator | PASS, 0 errors |
| Numeric label/source/instrument mismatch | 0 |
| CRCL contradiction | 0 |
| SKHY identity/basis conflation | 0 |
| US KR-style supply horizon | 0/13 |
| Unsupported US investor flow | 0 |
| Repeated substantive supply sentence across 3+ stocks | 0 |
| Observer/holder distinct | 13/13 |
| Unsafe multiple leakage | 0 |

The binding count increased from 158 to 171 because each stock now uses its canonical 20-day volume
ratio once in the supply section. No raw or manually bound number was added. `US Pilot 3/5` in the
Preview is only the next-success candidate label; persisted runtime remains US 2/5.

See [the corrected full US Preview](20260816-phase7-2-7-us-corrected-telegram-preview.md) and
[the compact audit](20260816-phase7-2-7-live-quality-audit.json).

## KR Regression

The latest completed KR source packet is natural v3.9 packet
`2026-08-15-kr-run-19-919a670464b4`: market 1 plus all seven active stocks. Reconstructing its old
final output as a draft exposed the v3.9 redundant authored numeric labels. The regression removed
only those already-canonical duplicate labels before automatic rebinding.

| Check | Result |
| --- | --- |
| Completeness | market 1 + stocks 7 |
| Automatic bindings | 91 |
| Manual bindings | 0 |
| Rejected bindings | 0 |
| Formatter errors | 0 |
| Full validator | PASS, 0 errors |
| KR 1-day/5-day/20-day supply coverage | 7/7 stocks |
| US-routing false positives | 0 |
| Rendered byte identity | no; 8/8 messages remove v3.9 duplicate labels only |

The supply interpretation, dynamic price structure, financial-quality fences, and observer/holder
content were otherwise retained. See
[the full KR regression Preview](20260815-phase7-2-7-kr-regression-preview.md).

## Isolation Evidence

Original hashes at the start of the retrospective:

| Artifact | SHA-256 |
| --- | --- |
| live packet | `83b33aa94f5c5428adb9cb7b0a6810142829ea2fa091c65265d7ec0c40180ec0` |
| validated live output | `2b3fc7047fb716ea3535c3d2a94652e58ebc129e0ac65e8b6d7e6f91bcc5f621` |
| archive completion marker | `ddce83e262e85e74d8459bb2d82795b5cd0b014699823a41e4aebaaa838179b6` |
| Pilot state | `4f8600322a5b08a9eb58708dbf9146854dd4b4f40b5ccd345892de8fdb064076` |

Telegram sends, operating database writes, operating archive writes, official assessment writes,
Pilot mutations, Scheduled Task changes, Production Assist changes, and operating checkout changes
were all zero. Four existing Scheduled Tasks remain ACTIVE at 08:15, 08:30, 16:15, and 16:55 on
policy v3.10.

The packet, validated output, archive completion marker, Pilot state, and operating database hashes
were recomputed after the experiment and remained byte-identical to the hashes above.

## Validation and Contracts

- Full test suite: 778 passed, one third-party deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Skill and output schema 4 contract: PASS
- Documentation relative paths and JSON parsing: PASS
- Public Action: 0.4.5 with 20/20 unique operation IDs
- Investment Knowledge canonical/runtime SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge canonical/runtime SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- DB migration: none

## Remaining Gaps

1. Work must directly approve the corrected US and KR Preview before main merge or deployment.
2. TSM and WRD require authoritative identity ingestion before their state can move from `unknown`;
   this branch does not invent or apply that evidence.
3. The broader non-supply substantive sentence audit still reports repeated monitoring phrases.
   They are recorded for human review but are outside this focused safety patch.
4. The next natural Live result must be evaluated after a separately approved deployment. This
   retrospective does not count and does not change the operational 2/5 counters.
