# Daily Review v3.2 Shadow Activation

## Identity

- Analysis policy: `daily-review-v3.2`
- Output schema: `2`
- Knowledge version: `3.0`
- Knowledge SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- AI review mode: `shadow`
- Production Assist: disabled
- GitHub Actions: pending at report creation

## Activation Gate

A packet is now `ready_for_ai=true` only when both runtime gates pass:

1. Every active company has a complete profile record: verified identity, documented partial identity,
   or documented ambiguity. Missing/unavailable identity blocks activation.
2. Every numeric entry emitted by that packet is explicitly registered. Audit-only values may be
   registered with `prose_allowed=false`; an unregistered value blocks activation.

The packet records the profile and semantic gate counts under `shadow_cohort`. A failed gate returns
`shadow_cohort_activation_gate_failed` and does not write a claimable inbox packet.

## Gate Results

| Gate | Result |
| --- | --- |
| Active company discovery | 20 total: US/foreign 13, KR 7 |
| Profile population | 20 complete, 0 missing, 0 unavailable |
| Routing smoke | 8 specialized, 12 verified general |
| Production US numeric coverage | 236/236 registered, unsupported 0 |
| Unknown semantic behavior | hard reject |
| Knowledge parity | checksum unchanged and matching |
| Official assessment mutation | none |
| NotificationDelivery mutation | none |
| Telegram mutation | none |

## Scheduled Tasks

The existing schedule and lease remain unchanged:

| Task | Schedule (KST) | Model | Reasoning |
| --- | --- | --- | --- |
| US Primary | 08:50 | GPT-5.6 Sol | high |
| US Backup | 09:30 | GPT-5.6 Sol | high |
| KR Primary | 16:15 | GPT-5.6 Sol | high |
| KR Backup | 16:55 | GPT-5.6 Sol | high |

Task prompt migration to `daily-review-v3.2` and exact operational-checkout deployment were pending at
report creation and are verified separately after push.

## Cohort Boundary

All `daily-review-v3.1` outputs remain in history and are pre-v3.2 Shadow. The new quality window does
not back-count earlier runs. Shadow Day 1 begins with the first successful, gate-eligible live packet
created after the exact v3.2 commit is deployed and all four Scheduled Tasks use the v3.2 contract.

Track at least 5 trading days, preferably 10, across both markets. Review specialized/general routing,
framework mismatch, numeric claim totals, unsupported semantic rejects, uncovered occurrences,
hallucinated facts or derived numbers, and AI-versus-deterministic differences. No automatic promotion
to Production Assist is permitted.
