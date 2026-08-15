# KR v3.9 / v3.10 Comparison

## Comparison Boundary

The selected latest completed KR trading session is `2026-08-14`. The `2026-08-15` assessment was a closed session and retained `2026-08-14` prices, so it was not used as the experimental source session.

No same-date v3.9 output exists. The nearest archived v3.9 result is `2026-08-15-kr-run-19-919a670464b4`, which is preserved in [20260814-kr-v39-baseline-preview.md](20260814-kr-v39-baseline-preview.md). It is a comparison aid, not a same-Fact prompt A/B test.

- v3.9 canonical Fact hash: `117d70520d052d3348195f833c6f38d451fd2e7401f0b9d8db52cb8b4ffdcd04`
- v3.10 canonical Fact hash: `7d55a0525e0d9664cc29864afe6cc9cf2df36ef62e17e2431158a05575eda0fa`
- Both price bases are as of `2026-08-14`, but the complete Fact payloads differ.

## Quantitative Comparison

| Area | Archived v3.9 | Experimental v3.10 |
| --- | ---: | ---: |
| Stock messages | 7 | 7 |
| Automatic numeric bindings | 91 | 143 |
| Manual bindings | 0 | 0 |
| Repeated numeric labels under current audit | 42 | 0 |
| Substantive sentences repeated across 3+ stocks | 2 | 0 |
| Maximum substantive repeat | 3 stocks | 0 |
| Observer/holder distinct | 7/7 | 7/7 |
| Stock-specific next checks | 21 | 7 |
| Generic next checks | 0 | 0 |
| Stock-specific Unknowns | 7 | 7 |
| Supply claims per stock | Mostly foreign 5d/20d | Foreign/institution 1d/5d/20d |
| Historical validator | PASS | N/A |
| Current v3.10 validator | Not rerun as same Fact | PASS, 0 errors |

The v3.10 next-check count is lower because each stock selects one decision-changing check instead of repeating a three-item checklist. This is intentional compression, not reduced provenance.

## Representative Changes

### Memory / Semiconductor: SK hynix

The archived message repeated authored and canonical labels such as `영업이익 영업이익` and `현재 PBR 현재 PBR`. The experimental message uses `매출 79조3,187억원`, `영업이익률 76.3%`, `현재 PER 7.2배`, `내부 추정 fPER 16.38배`, and `PBR 역사적 백분위 93.9%` without duplicated labels.

Supply interpretation also changes from a two-horizon summary to the complete transition: short-term foreign buying and recent institutional buying are set against medium-term foreign and institutional net selling. That is described as a short-term return that has not yet erased medium-term distribution, not as fundamental confirmation.

### Non-semiconductor Earnings and Valuation: POSCO Holdings

The experimental message connects `매출 성장률 9.7%`, `영업이익 성장률 34.9%`, and `영업이익률 4.3%` to the need for inventory, investment-spending, and cash-conversion evidence. It also contrasts `현재 PER 18.75배` with `현재 PBR 0.44배` and keeps the historical percentiles near the middle of the company's own range rather than calling the stock automatically cheap.

The current dynamic zone and `차트 손익비 0.17배` are primary. The registered confirmation level remains a transition reference and is not promoted to support.

### Supply Divergence: Hyundai Glovis

The experimental message states the full horizon structure:

- Day: foreign and institution both net buyers
- Recent: foreign net buying, institution net selling
- Medium term: foreign and institution both net buyers

This supports the narrower conclusion that medium-term positioning is constructive while recent institutional flow is weaker. It does not change the business thesis.

Price analysis now leads with `현재가 211,000원`, dynamic support `197,803원` to `210,197원`, resistance `223,397원` to `230,603원`, current-price RR `0.47배`, and chart invalidation `184,407원`. The registered `200,000원` confirmation is explicitly retained only as the original transition reference.

### Data-limited Valuation: Hanwha Aerospace

The experimental output does not invent PER/PBR or peer medians. It uses the available revenue, operating income, margin, dynamic price structure, and all verified supply horizons, while leaving comparable valuation and project cash conversion as explicit Unknowns.

## Numeric Labels

The v3.10 binder owns the complete label-plus-value phrase. The current audit reports:

- Redundant authored labels: 0
- Repeated bound labels: 0
- Source-label mismatches: 0
- Instrument-label mismatches: 0
- Unresolved placeholders: 0

## Full Outputs

- [Archived v3.9 comparison preview](20260814-kr-v39-baseline-preview.md)
- [Experimental v3.10 preview](20260814-kr-v310-telegram-experimental-preview.md)
- [Numeric binding](20260814-kr-v310-numeric-binding.json)
- [Validation](20260814-kr-v310-validation.json)
- [Quality audit](20260814-kr-v310-quality-audit.json)
- [Isolation audit](20260814-kr-v310-isolation-audit.json)
