# Phase 8.3 Final TSLA Peer Wording Preview

Date: 2026-08-19
Context: immutable Phase 8.3.2A current free-source audit for the 2026-08-17 US completed session
Scope: qualitative comparison wording only; archive preview, no Telegram

## Before

> 같은 업종의 검증 가능한 3개 peer PER 중앙값은 23.18배이며, 현재 회사 PER 176.72배는 중앙값보다 662.5% 높습니다. 물량·믹스·마진과 잉여현금흐름 차이를 함께 봐야 합니다.

## After

> 동일 자동차 분류에서 PER 비교가 가능한 3개 상장사 중앙값은 23.18배입니다. 현재 PER 176.72배는 이 기초 비교군보다 662.5% 높지만, 사업모델·성장 기대가 달라 직접 동종기업 프리미엄 해석에는 한계가 있습니다.

## Contract Check

| Check | Result |
|---|---|
| Taxonomy/calculation scope stated | PASS: same automotive classification and current-PER eligibility |
| Direct-peer overstatement | 0 |
| Economic comparability limit | explicit |
| Unsupported Robotaxi/software/AI/autonomy narrative added | 0 |
| Cheap/expensive verdict | 0 |
| Quality enum | unchanged `MEDIUM` |
| Generic rule | PASS: framework/classification based, no ticker branch |

## Numeric Stability

| Claim | Before | After | Provenance |
|---|---:|---:|---|
| Eligible independent issuers | 3 | 3 | `valuation:peer`, `fields.pe_sample_count` |
| Peer baseline median PER | 23.18x | 23.18x | `valuation:peer`, `fields.pe_median` |
| Subject current PER | 176.72x | 176.72x | `valuation:current`, `fields.trailing_pe` |
| Subject vs median | +662.5% | +662.5% | `valuation:peer`, `fields.company_pe_vs_median_pct` |

Numeric change: 0. Numeric provenance coverage: 100%.

## Full-Message Regression

| Message | Before chars | After chars | Change |
|---|---:|---:|---:|
| TSLA | 1,319 | 1,448 | +9.78% |
| Other ten representative messages | unchanged | unchanged | 0% |

The sentence remains inside the existing Valuation section and creates no new section. The final
TSLA increase stays within the prior Phase 8.3 +10% recommendation.

The alternative “about 7.6 times the median” is not selected. Although the backend audit retains a
relative-multiple statistic, the prior visible contract uses the registered premium/discount claim;
this finalization does not introduce a new display semantic or renderer calculation.

The generic formatter change affects only future MEDIUM/HIGH visible contexts. In the immutable
representative portfolio, TSLA remains the sole visible peer result, so the other ten Preview
messages have semantic change 0.
