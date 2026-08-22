# Phase 9.0E Natural User-Visible Proof

## Decision

`PHASE_9_0E_NATURAL = LIVE_PASS_SELECTIVE_SUBSET`

Run `2026-08-22-us-run-32-dde10ec6c9eb` naturally delivered nine current-formal, full-FCF contexts through deterministic fallback. Delivery was exactly once and all rendered values equal their canonical `OCF - PPE-only CAPEX` facts.

| Ticker | State | Freshness / materiality | Baseline | Rendered | Canonical FCF Fact | Period | Scope / currency | Path | Quality |
|---|---|---|---|---:|---|---|---|---|---|
| CORZ | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:1b8f3742f33dd3b66f8f7673` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| CRCL | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:402041c63553616360d17391` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MINOR_IMPROVEMENT |
| GOOGL | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:ddb47708bf7d36a4c0b0c7d2` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| HUT | suppressed | CURRENT_FORMAL / OCF-only excluded | PASS | NO | null | FY2026 Q2 YTD | null | none | NO_MEANINGFUL_CHANGE |
| IBM | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:a158304539a9269c66f6d2cb` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MINOR_IMPROVEMENT |
| MU | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:96e9c3b873f3678d4dec0ff3` | FY2026 Q3 YTD, 2025-08-29..2026-05-28 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| RXRX | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:498c289d4304c0822d861ec3` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| SKHY | suppressed | BLOCKED / fact unavailable | PASS | NO | null | null | null | none | NO_MEANINGFUL_CHANGE |
| SNDK | selected | CURRENT_FORMAL / resolved prior Unknown | PASS | YES | `cashflow:1b8db0b46c63ae9369231151` | FY2026 FY, 2025-06-28..2026-07-03 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| TSLA | selected | CURRENT_FORMAL / existing driver | REPAIRED | YES | `cashflow:68666c261434dab50ab88a8d` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |
| TSM | suppressed | FORMAL_LAGGING_PROVISIONAL | PASS | NO | `cashflow:f5f8d7130aaff3c4a0f0a2a1` | FY2024 FY | issuer fact retained, not current | none | NO_MEANINGFUL_CHANGE |
| WRD | suppressed | FORMAL_LAGGING_PROVISIONAL | PASS | NO | `cashflow:46c15133a15f9cb2c4b839c1` | FY2025 Q2 YTD | issuer fact retained, not current | none | NO_MEANINGFUL_CHANGE |
| WULF | selected | CURRENT_FORMAL / existing driver | PASS | YES | `cashflow:6fd003ea029e4d7b03f681f3` | FY2026 Q2 YTD, 2026-01-01..06-30 | PPE-only / USD | fallback | MATERIAL_IMPROVEMENT |

## Safety checks

- Selected contexts: 9; suppressed: 4.
- Exact selected FCF arithmetic: 9/9 correct.
- FCF input lineage: OCF and PPE-only CAPEX IDs present for 9/9.
- PIT/currentness: 9/9 `PASS` and `CURRENT_FORMAL`.
- Period/scope/currency label: 9/9 correct in sent text.
- Contradictory old FCF prose: 0. SNDK's prior FCF Unknown was resolved; TSLA's conflicting baseline claims were suppressed.
- Status or valuation mutation from FCF alone: 0.
- Exactly-once effect: 0; delivery remained 14/14 once.
- Cash-flow canary production parity: PASS, selected 9, error 0, production influence 0.

No ticker is classified `DEGRADED`. A repeated introductory skeleton, “회계연도 … PPE 투자 후 잉여현금흐름은 …”, remains a P2 wording/backlog item because the second sentence is industry-specific and no semantic or numeric distortion resulted.
