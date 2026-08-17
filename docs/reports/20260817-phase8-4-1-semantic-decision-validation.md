# Phase 8.4.1 Semantic & Decision Validation

## Executive Conclusion

| Dimension | Result |
|---|---|
| Engineering | PASS |
| Full schema-4 validator | PASS |
| Runtime final-message receipt | PASS |
| Valuation scope | PASS |
| Denied-fact echo | PASS |
| Decision hierarchy | PASS on five-stock retrospective |
| Historical context | PASS on five-stock retrospective |
| Work human-quality approval | `pending_work_human_review` |
| Ready for automatic main merge | NO |
| Production Assist evidence eligible | false |

The implementation fixes the four Phase 8.4 semantic blockers while retaining the integrated full
message and adaptive renderer. This is mechanical and provisional review evidence, not Work's final
investment-message approval.

## Repository And Safety

- Branch: `codex/phase-8-4-1-semantic-decision-hardening`
- Required base: `ea74e2633ee1ef137a3a9d1c535d80612d817156`
- Production main: `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5`
- Implementation commit: `e6e1fda`
- DB migration: none
- Public Action: 0.4.5, operationId 20/20 unique
- Investment Knowledge and Chart Knowledge: unchanged
- Runtime Pilot: KR 3/5, US 3/5
- Production Assist: OFF; AI mode: shadow
- Main merge, deployment, API restart, Scheduled Task execution/change: `0`
- Provider calls, Telegram sends, operating DB/archive/assessment/Pilot mutations: `0`

## Architecture

`semantic-scope-and-decision-hierarchy-v1` adds draft-only economic scope and supporting-Fact
references. `decision-material-delta-v1` ranks verified candidate deltas before the existing
renderer. Historical context selection is deterministic and records every selection or suppression
reason. Public output remains schema 4.

## Five-Stock Result

| Ticker | Scope | Denied echo | Primary decision | History | Provisional score |
|---|---|---|---|---|---:|
| 005930 Samsung Electronics | PASS | n/a | no material delta; earnings/valuation context | PBR retained | 18/20 |
| 005490 POSCO Holdings | PASS | n/a | no material delta | outside decision band | 17/20 |
| 086280 Hyundai Glovis | PASS | n/a | no material delta; earnings/RR context | PER retained | 18/20 |
| 003690 Korean Re | PASS | n/a | no material delta | unavailable | 17/20 |
| 000660 SK hynix | PASS | PASS | supply; earnings denied | safe PBR retained | 17/20 |

Provisional average: `17.4/20`. These scores are Codex review evidence only and remain pending Work
review. Critical semantic issues detected after correction: `0`.

## Message Length

| Ticker | Phase 8.4 chars | Phase 8.4.1 chars | Lines | Sections |
|---|---:|---:|---:|---:|
| 005930 | 1,137 | 1,213 | 30 -> 29 | 6 -> 6 |
| 005490 | 1,173 | 1,167 | 32 -> 32 | 7 -> 7 |
| 086280 | 1,142 | 1,234 | 30 -> 29 | 6 -> 6 |
| 003690 | 1,003 | 1,009 | 29 -> 29 | 6 -> 6 |
| 000660 | 1,133 | 1,197 | 36 -> 36 | 8 -> 8 |

Portfolio characters increase 4.2%, lines decrease 1.3%, and sections are unchanged. The average
character increase stays within the Phase 8.4.1 recommendation.

## Mechanical Evidence

- Complete stock reviews: 5/5; rendered logical messages: market 1 + stocks 5
- Automatic numeric bindings: 86
- Manual/rejected/formatter/unresolved: 0/0/0/0
- Typed valuation occurrences: 12 accepted, 0 errors, economic scope 12/12
- Semantic denial references: 1 accepted, 0 errors
- Full validator: PASS, 0 errors
- Runtime receipt: PASS, 0 errors
- Final language: particle 0, duplicate label 0, internal term 0
- Template/sentence substantive repeats: 0
- SK hynix denied numeric and qualitative leakage: 0
- Safe historical context lost without reason: 0
- Fabricated thresholds: 0

## Tests

Focused semantic, integrated-rendering, typed-valuation, and stock-validator suite: `198 passed`.
Full suite after implementation: `974 passed`, one third-party deprecation warning. Ruff and
`git diff --check`: PASS. Final exact-commit CI is recorded in the completion report after push.

## Persistent Gap Status

| Gap | Status |
|---|---|
| Valuation scope | CLOSED |
| Denied Fact echo | CLOSED |
| Decision-material delta | CLOSED for retrospective; natural live OPEN |
| Historical valuation retention | CLOSED for current contract |
| Integrated full message | CLOSED for retrospective |
| Investment meaning | PARTIAL |
| Industry reasoning | PARTIAL |
| Observer/holder | CLOSED for retrospective |
| Unknown quality | PARTIAL |
| Next-check quality | PARTIAL |
| Message length | PARTIAL |
| Korean UX | PARTIAL |
| Peer valuation | OPEN |
| Cash flow | OPEN |
| Natural live validation | OPEN |

## Recommendation

Engineering is ready for Work to review the exact Preview. If approved, Phase 8.5
industry-specific reasoning is the default next phase. If KRX approval is available first, insert
Phase 8.2A KRX Market Breadth Primary. Main merge, shadow deployment, and any operating policy change
remain separate approvals.

Evidence: [exact full Preview](20260817-phase8-4-1-semantic-decision-preview.md),
[semantic audit](20260817-phase8-4-1-semantic-audit.md),
[binding result](20260817-phase8-4-1-numeric-binding.json), and
[runtime receipt](20260817-phase8-4-1-runtime-quality-receipt.json).
