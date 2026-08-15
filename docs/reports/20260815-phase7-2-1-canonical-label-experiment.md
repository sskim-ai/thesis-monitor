# Phase 7.2.1 Canonical Numeric Label Experiment

Date: 2026-08-15

Branch: `codex/phase-7-2-relational-reasoning`

Required branch base: `7596769f81e8dbc0272be76026b13c84ed0b766b`

Operating main: `7d9f59fa1b5bc6034ea5cc9620482b39e4a96f07`

Experimental policy / output schema: `daily-review-v3.10` / `4`

Status: experimental, not merged, not deployed, not sent

## Problem And Decision

The retained Phase 7.2 preview proved the relational reasoning direction but exposed three numeric
label defects. Draft prose pre-authored labels in front of placeholders, the label router recognized
`consensus` instead of the actual `consensus_forward` enum, and identity-sensitive market metrics
could fall back to another instrument's first approved label.

The binder now treats a placeholder as the complete numeric phrase: canonical label plus canonical
formatted value. A draft such as `현재 PER {{numeric:pe}}` is rejected instead of being repaired.
Forward labels are selected from the verified source enum, while index and futures labels are selected
from verified series identities. Unknown source or instrument identity has no first-label fallback and
is not allowed in prose. The renderer remains a layout layer and performs no semantic rewriting.

## Source Matrix

| Verified identity | Canonical label behavior |
|---|---|
| `modeled_forward` | `내부 추정 fPER`, `내부 추정 EPS`, `내부 추정 fPBR`, or `내부 추정 BVPS` |
| `consensus_forward` | `시장 예상 fPER`, `시장 예상 EPS`, `시장 예상 fPBR`, or `시장 예상 BVPS` |
| Unknown forward source | No modeled/consensus inference; prose binding fails closed |
| `SPY` | `S&P500 등락률` |
| `QQQ` | `Nasdaq 등락률` |
| `IWM` | `Russell 2000 등락률` |
| `SOXX` relative to `SPY` | `S&P500 대비 반도체 상대수익률` |
| `KRX_KOSPI200_NIGHT_FUT` | Product-specific KOSPI200 close, point-change, or return label |
| `KRX_KOSDAQ150_NIGHT_FUT` | Product-specific KOSDAQ150 close, point-change, or return label |

The mapping is based on backend identity fields, not provider prose or ticker-specific production
branches.

## Binder And Validation

Before binding, the binder compares the immediately preceding draft context with the registry row's
approved and canonical labels. Redundant authored labels fail with
`numeric_fact_ref_redundant_authored_label`. After binding, deterministic checks reject repeated bound
labels, source-label mismatches, and instrument-label mismatches. The full validator independently
checks the same final-prose boundary and rejects modeled/consensus reversals for PE/EPS and PBR/BVPS.

The quality audit now records:

- `redundant_authored_label_count`
- `repeated_bound_label_count`
- `source_label_mismatch_count`
- `instrument_label_mismatch_count`
- `hard_checks_passed`

These checks do not claim to judge overall prose quality. Human review remains the approval boundary.

## Retrospective Isolation

The experiment used the same 2026-08-15 SQLite-consistent operating-data backup and copied profile
data as Phase 7.2. Live providers were disabled. The copied database SHA-256 remained
`173b543be83504ec8961175623297e0e40c5b63c87147126835a4c7a24c35894` before and after packet and
review generation.

New packet: `2026-08-15-us-run-18-dca26c59bb82`

The run produced one market review and 13 stock reviews. It made zero Telegram sends and zero changes
to the operating database, operating archive, official assessments, Scheduled Tasks, or Pilot state.
The verified operating Pilot state remains KR 1/5 and US 1/5.

## Before And After

The previous flawed preview is retained unchanged as historical experiment evidence. Direct matching
of the known duplicated forms found 25 visible occurrences before and zero after. Rescoring the old
validated output against the new canonical registry found 23 repeated labels, 16 source-label
mismatches, and 3 instrument-label mismatches. The corrected output has zero in all four label-quality
categories.

| Measure | Previous preview | Corrected preview |
|---|---:|---:|
| Known visible duplicate-label occurrences | 25 | 0 |
| Redundant/repeated label hard checks | Failed | 0 / 0 |
| Source-label mismatches | 16 | 0 |
| Instrument-label mismatches | 3 | 0 |
| Automatic bindings | 168 | 168 |
| Manual bindings | 0 | 0 |
| Formatter errors | 0 | 0 |
| Full validator errors | 0 under old contract | 0 under hardened contract |

## Representative Results

### Market

`S&P500 등락률 -0.2%` is distinct from
`S&P500 대비 반도체 상대수익률 -0.1%`. The Korean opening context renders as
`KOSPI200 야간선물 등락률 -0.32%` and `KOSDAQ150 야간선물 등락률 +1.67%` without a generic product
label.

### CORZ

`매출 $164.2M와 매출 성장률 108.8%` replaces `매출 매출 ...` while preserving the connection to
colocation billing and post-capex cash flow.

### CRCL

The packet source is `consensus_forward`. The corrected text says
`현재 PER 42.41배보다 시장 예상 fPER 68.94배가 더 높아` and does not relabel the value as an
internal estimate.

### MU

The packet source is also `consensus_forward`. The text uses `시장 예상 fPER 5.87배` against
`현재 PER 19.86배`, preserving the memory-cycle interpretation rather than treating the lower forward
multiple as automatic cheapness.

### RXRX

`매출 QoQ 18.5%와 매출 성장률 -60.1%` is rendered once per semantic. The loss-making biotechnology
framework continues to avoid a forced PER conclusion.

### TSM

`매출 NT$1.27T와 영업이익률 60.3%` preserves TWD issuer financials and the separate USD ADR price
basis. No currency or ADR conversion is performed.

### WRD And WULF

WRD renders `현재가 $5.85와 현재 PBR 2.45배`; its unsafe monetary revenue remains excluded. WULF
renders `현재 PBR 58.88배와 PBR 역사적 백분위 100%` and does not call the percentile a 100%
overvaluation measure.

## Relational Quality Retained

| Measure | Result |
|---|---:|
| Substantive sentences repeated across 3+ stocks | 0 |
| Maximum substantive repeat | 0 |
| Distinct new-observer / holder pairs | 13/13 |
| Stock-specific next checks | 13 |
| Generic next checks | 0 |
| Stock-specific Unknowns | 13 |
| Generic Unknowns | 0 |

All 13 core judgments retain at least two canonical numeric facts. Removing duplicated labels did not
remove the numbers or weaken relational reasoning.

## Artifacts

- [Corrected full Telegram preview](20260815-us-v310-telegram-canonical-label-preview.md)
- [Relational and label quality audit](20260815-phase7-2-1-canonical-label-audit.json)
- [Focused label audit](20260815-phase7-2-1-label-audit.json)
- [Numeric binding result](20260815-phase7-2-1-numeric-binding.json)
- [Full validator result](20260815-phase7-2-1-validation.json)
- [Previous flawed preview](20260815-us-v310-telegram-experimental-preview.md)

## Validation

- Focused tests: 132 passed
- Full tests: 687 passed
- Ruff: passed
- Git diff check: passed
- Investment Knowledge canonical/runtime SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge canonical/runtime SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

## Remaining Gaps

- Work must inspect all 14 corrected messages for usefulness and tone before any approval.
- Exact branch commit GitHub Actions Test and Lint must pass after push.
- This experimental branch remains unmerged and undeployed. Scheduled Tasks continue to use
  `daily-review-v3.9` from operating main.
- A later approved merge still requires a separate deployment decision and a natural live Pilot
  session; this retrospective cannot increase the Pilot count.
