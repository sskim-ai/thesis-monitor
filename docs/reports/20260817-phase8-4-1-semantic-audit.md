# Phase 8.4.1 Semantic Audit

## Evidence Boundary

- Source packet: `2026-08-16-kr-run-21-049f367f0274`
- Phase 8.4 baseline: `2026-08-16-kr-phase8-4-delta-first-retrospective`
- Phase 8.4.1 packet: `2026-08-16-kr-phase8-4-1-semantic-retrospective`
- Immutable DB copy SHA-256: `d1b4b121d11005952bd050ca5d0c0c1056b310d223afb4f6db57ae00086936fd`
- Provider calls, Telegram sends, DB mutations, and Pilot mutations: `0`
- Human status: `pending_work_human_review`

## Valuation Scope

| Ticker | Phase 8.4 violation | Phase 8.4.1 wording | Result |
|---|---|---|---|
| 005930 | memory business PER/PBR | listed-share basis, whole-company PER/PBR | PASS |
| 005490 | steel/materials mixed-business PER/PBR | consolidated whole-company PER/PBR | PASS |
| 086280 | transport-business PER/PBR | whole listed-company PER/PBR | PASS |
| 003690 | company-level reinsurer wording | whole reinsurer PER/PBR | PASS |
| 000660 | memory-business PBR | listed-share basis, whole-company PBR | PASS |

Before violations: `7`. After violations: `0`. Typed economic-scope coverage is `12/12`: nine
current absolute occurrences and three retained historical occurrences. Test nodes:
`test_company_valuation_scope_accepts_company_wording`,
`test_company_valuation_scope_rejects_segment_wording`,
`test_true_segment_multiple_accepts_segment_wording`, and
`test_pure_play_multiple_remains_listed_security_scope`.

## Denied-Fact Echo

SK hynix Phase 8.4 explained the denial and then referred to company-wide earnings as a qualitative
premise. Phase 8.4.1 keeps only the exclusion explanation and confines the decision to independent
PBR, price, supply, and HBM execution evidence. Denied numeric leakage: `0`; denied qualitative
premise: `0`; accepted denial explanation references: `1`.

Negative nodes cover denied revenue growth, margin improvement, and low-PE wording. The positive
node `test_denial_explanation_is_allowed_with_denied_fact` proves the data-quality explanation is not
globally banned.

## Decision Hierarchy

| Ticker | Candidates | Phase 8.4 primary | Phase 8.4.1 primary | Secondary / reason |
|---|---|---|---|---|
| 005930 | earnings context, mild supply | supply | none | supply; current earnings/valuation leads |
| 005490 | earnings context | none | none | no verified material delta |
| 086280 | earnings context, mild supply | supply | none | supply; earnings relation and entry context lead |
| 003690 | earnings context | none | none | no verified material delta |
| 000660 | mild supply, safe PBR context | supply | supply | best available delta with earnings denied |

No retrospective recovery is described as a new historical event. Tests cover earnings over mild
supply, price transition without safe earnings, deterministic override eligibility, and explicit
no-material-delta handling.

## Historical Valuation

| Ticker | Available and safe | Selected | Suppression reason |
|---|---|---|---|
| 005930 | PE and PBR | PBR 91.6 percentile | PE outside decision band |
| 005490 | PE and PBR | none | both outside decision bands |
| 086280 | PE and PBR | PE 92.8 percentile | PBR suppressed by stronger safe context |
| 003690 | no comparable history | none | comparability unavailable |
| 000660 | PBR; PE denied | PBR 87.0 percentile | PE denied with earnings family |

Safe decision-relevant history suppressed without reason: `0`. Unsafe history used: `0`.
Percentile-as-overvaluation errors: `0`. Stale and failed-comparability fixtures both suppress.

## Samsung Coherence

Classification: `VALID_AND_COHERENT`.

| Metric | Current | Comparison | Basis / period | Formula |
|---|---:|---:|---|---|
| Revenue | 171,499,470,000,000 KRW | 74,566,317,000,000 KRW | CFS, Q2 single quarter | YoY 129.9959%, match |
| Operating income | 89,492,412,000,000 KRW | 4,676,057,000,000 KRW | CFS, Q2 single quarter | YoY 1,813.8435%, match |
| Operating margin | 52.1823% | n/a | same current revenue/op income | exact division match |

Source filing and receipt number: `20260814003699`; statement type: IS; currency: KRW. Current and
comparison account IDs, basis, duration, and currency match. The audit makes no external economic
plausibility inference.

## Observer, Holder, And Next Check

Observer/holder semantic distinction is `5/5`. Role-label-only duplication is rejected. Hyundai
Glovis uses the canonical current Q2 consolidated operating margin 5.7% as the next-check baseline;
fabricated threshold count is `0`.

## Artifact Integrity

| Artifact | SHA-256 |
|---|---|
| Full schema output | `96d8ea8214fc904d691a00ad3cfe563c2d845ae4559ddd5546aac3b623eafa15` |
| Numeric binding | `625b9ba9b70f308a1037c1a511240229d8b606655d50dbca63f641ab606443d6` |
| Runtime receipt | `3aaedc8dd1e30c7ee6d1b1d2531cc423b32ac9817687d4991819e4e4b78ec747` |
| Semantic decision audit JSON | `c837c9f7956ee5d48ff695b4aa1f7b50023397ee043b5557d27c873d63d35005` |
| Exact Preview | `5a76f2a1cdfbb4caaf2961686bf148f7ebce31dc9366519838024fce881e9a65` |
| Validator | `b670a3c0a3abfb6c25830bc1ec5f0c91f21f46d1794f47721cbe27263646befe` |

The Preview and JSON artifacts were generated by
`scripts/build_delta_first_full_preview.py`; messages were not manually edited.
