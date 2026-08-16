# Phase 7.2.9.1 Experimental Readiness

Date: 2026-08-17

## Status

- Branch: `codex/phase-7-2-9-1-quality-blockers`
- Required base: `78c2f8f2645031183228fa446a0beecc4bbc0973`
- Implementation commit: `936de550d5181e4ee6d1064f4e5fba4edb275e6a`
- Production main and operating checkout: `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5`
- Runtime Pilot: KR 3/5, US 2/5
- Production Assist: OFF
- Production deployment: not performed
- Corrected KR and US human quality: `pending_work_human_review`

Natural KR Day 3 remains an operational success and a human-quality failure. The Phase 7.2.9
corrected KR Preview also remains a human-quality failure, and the Phase 7.2.9 US Preview was not
human-approved. This report records deterministic Phase 7.2.9.1 results only; it does not promote
any retrospective to Production Assist evidence.

## Contracts

- Financial amount period: `financial-amount-period-v1`
- RR basis: `current_price` and `support_entry`
- Valuation interpretation: `typed-valuation-interpretation-v1`
- Valuation coherence: `valuation-coherence-v1`
- Runtime quality: `runtime-message-quality-v1`
- Receipt: `runtime-message-quality-receipt-v2`
- Archive: `ai-assisted-archive-v2` for newly gated output; historical manifests remain valid
- Policy/schema: `daily-review-v3.10` / 4
- Security identity / financial quality: `security-identity-v2` / `financial-quality-taint-v2`

## Financial Amount Period

Filing, statement, and field-level amount periods are now separate. A user-visible financial amount
requires an exact source row, account, statement basis, amount start/end, period type, and compatible
comparison period. Ambiguous or multiply matched rows fail closed.

The Samsung fixture now identifies the amount as 2026 Q2 single-quarter operating income. It no
longer labels KRW 89.4924 trillion as H1 cumulative. The official Samsung announcement is retained
as a validation reference only; runtime logic does not perform a web lookup or branch on ticker.

The KR cross-section audit has 49 field decisions and zero visible period mismatches. SK Hynix's
denied earnings lineage remains unavailable to prose.

## RR Basis

- Current price RR label: `현재가 기준 차트 손익비`
- Support-entry scenario label: `동적 지지 접근 가정 차트 손익비`

The current-price metric is primary for current positioning. A support-entry value is allowed only
as an explicit conditional scenario. Hanwha Aerospace now presents 0.15 as current-price RR and
0.49 as the dynamic-support-entry scenario; a basis-free label or cross-use is rejected.

## Typed Valuation

All accepted valuation interpretations in the corrected payloads carry draft-only typed references
to homogeneous facts and occurrence-level numeric claims. Coverage is 38/38 (KR 14, US 24), with
zero errors. Historical, peer, expectation, and trailing/forward claims require their corresponding
backend evidence. Absolute multiples without comparison evidence remain neutral.

The backend relation fact permits comparable trailing/forward interpretation for GOOGL, IBM, TSLA,
and MU. HUT has no safe trailing relation, so its relationship interpretation remains Unknown.
Korean Re's PBR 0.67 and POSCO Holdings' current multiples are stated without unsupported low/high
or historical-position conclusions.

## Receipt Integrity And Fallback

The receipt verifier now checks the whole receipt file SHA against every persisted delivery record,
as well as contract/schema, packet, policy, output, rendered-set hash, message count, hard check
results, errors, and timestamp. Missing or tampered receipts do not trigger regeneration. AI delivery
is held, deterministic fallback remains eligible, the deadline emits exactly one persisted fallback
set, and Pilot state cannot advance.

Legacy archive completion uses the manifest contract that was active when the marker was written.
Historical archives are not rewritten, replayed, or recounted because they lack the new receipt.

## Retrospective Results

### KR

- Corrected packet: `2026-08-16-kr-run-21-5844682f15da`
- Logical payloads: market 1 + stocks 7
- Numeric binding: automatic 105, manual 0, rejected 0, formatter 0, unresolved 0
- Full validator: PASS, 0 errors
- Runtime quality gate: PASS, 0 errors
- Packet / output / payload / receipt SHA-256:
  `be1e8940...` / `8ee46076...` / `8268192e...` / `b70c59f9...`

### US

- Corrected packet: `2026-08-16-us-run-20-f9b252d77940`
- Logical payloads: market 1 + stocks 13
- Numeric binding: automatic 169, manual 0, rejected 0, formatter 0, unresolved 0
- Full validator: PASS, 0 errors
- Runtime quality gate: PASS, 0 errors
- Packet / output / payload / receipt SHA-256:
  `ef84311b...` / `04b48552...` / `c3f4f087...` / `04bcbdff...`

The old Phase 7.2.9 KR and US outputs fail the new contract in read-only replay. Focused failures
include Samsung's Q2/H1 mismatch, Hanwha's support-entry/current-price RR confusion, Korean Re's
unsupported low-PBR interpretation, and POSCO's unsupported historical-neutral interpretation.

## Isolation

- Source DB copy SHA-256: `4cfd7bb8cef53954de141c8201f510d0c9bd6c2a1ce3299ae22ad42a18826d39`
- Provider/network calls: 0
- Telegram sends: 0
- Operating DB/archive/assessment/Pilot/Scheduled Task mutations: 0
- Pilot-state SHA-256: `8aad97ed4110efb0f7bccd83aa5bd9e78c570e218ef59784c52dcf5cadf24450`
- Operating DB SHA-256: `987bfb4b82c8017054f8c3cef1213177246868f902dd134be0c4f4fd34e3eb78`

## Artifacts

- [KR corrected Preview](20260817-phase7-2-9-1-kr-corrected-telegram-preview.md)
- [US corrected Preview](20260817-phase7-2-9-1-us-corrected-telegram-preview.md)
- [KR amount-period matrix](20260817-phase7-2-9-1-kr-financial-amount-period-matrix.json)
- [Samsung period evidence](20260817-phase7-2-9-1-samsung-amount-period-evidence.json)
- [KR RR audit](20260817-phase7-2-9-1-kr-rr-basis-audit.json)
- [Hanwha RR before/after](20260817-phase7-2-9-1-hanwha-rr-before-after.json)
- [Typed valuation matrix](20260817-phase7-2-9-1-typed-valuation-interpretation-matrix.json)
- [US relation audit](20260817-phase7-2-9-1-us-trailing-forward-relation-audit.json)
- [Receipt integrity matrix](20260817-phase7-2-9-1-receipt-integrity-negative-matrix.json)
- [Fallback audit](20260817-phase7-2-9-1-fallback-single-delivery-audit.json)
- [Legacy archive audit](20260817-phase7-2-9-1-legacy-archive-compatibility-audit.json)
- [Isolation audit](20260817-phase7-2-9-1-isolation-audit.json)

## Remaining Gaps

- Hyundai Glovis's direct Q2 operating-income field is individually eligible, but its aggregate
  earnings interpretation fact also contains denied or unknown comparison fields. The aggregate
  fence therefore withholds the safe amount. This is conservative field-level overblocking, not a
  denied-value leak.
- TSM and WRD remain identity Unknown; authoritative ingestion is outside this phase.
- KR local index, breadth, and market-wide flow gaps remain unchanged.
- The corrected Previews require direct Work review before merge or deployment.
