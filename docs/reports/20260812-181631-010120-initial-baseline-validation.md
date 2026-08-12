# 010120 Initial Baseline Validation

## Scope

- Ticker: `010120` (LS일렉트릭)
- Validation date: `2026-08-12`
- DB migration: none
- Public Action contract: unchanged (`0.4.5`, 20 operationIds)

## Initial Baseline

Before:

- First assessment was stored/rendered as `needs_review`.
- Historical backfill evidence appeared as a current-day change.

After:

- The first assessment for each `(ticker, thesis_version)` is
  `assessment_mode=initial_baseline`.
- Stored delta fields are `no_material_change`, `none`, `unchanged`, and
  neutral Valuation impact.
- All eligible backfill fingerprints are consumed, but backfill events do not
  contribute to strengthen/weaken/review scoring.
- A subsequent new fingerprint is evaluated normally as `daily_delta`.

Expected user header:

```text
🏢 LS일렉트릭(010120)
투자 논리: 초기 설정
```

The initial message uses `📌 초기 근거` and does not use `🔄 중요한 변화`.

## User Fact Sanitization

Raw audit facts remain stored, including OpenDART parser lineage. The Telegram
renderer never falls back to strings containing `OpenDART`, `fs_div`, `sj_div`,
`period_scope`, `amount_scope`, or `report_code`.

Actual structured rendering from the 2026 Q2 snapshot:

```text
📌 초기 근거
• 2026년 2분기 잠정 매출 1조5,770억원
• 영업이익 1,785억원 · 영업이익률 11.3%
• 북미 데이터센터용 연료전지 전력설비 공급 PJT · 계약금액 3,190억원
```

## Capital Allocation Materiality

The 2026-07-15 treasury-stock disposal was evaluated with generic thresholds,
not a ticker exception.

| Item | Result |
|---|---:|
| Transaction shares | 32,520 |
| Common shares outstanding | 29,738,491 |
| Share ratio | 0.1094% |
| Transaction / market cap | 0.0984% |
| Purpose | 직원 주식보상 |
| Result | `immaterial` |

The event remains in event history and its fingerprint is consumed. It is not
used for daily scoring, `needs_review`, a user-facing important change, or a new
warning. Capital raises, convertible bonds, and warrants bypass this treasury
filter and retain their existing material-event handling.

Default thresholds:

- Review: 0.5% of shares or market cap
- Material: 2.0% of shares or market cap

## Historical Valuation Diagnosis

The OHLCV Analyst contract was queried for the same 300 weekly observations with
`adjusted=true` and `adjusted=false`. In November 2020 the adjusted close was
about one fifth of the unadjusted close, while recent closes were identical.
The old implementation combined the adjusted historical price with
contemporaneous per-share denominators.

Production now keeps adjusted prices for technical ranges and uses a separate
`adjusted=false` weekly series for historical valuation.

| Metric | Before | After |
|---|---:|---:|
| Price basis | adjusted | unadjusted |
| Cache algorithm | `weekly_last_valid_close` | `weekly_last_valid_close_unadjusted_v2` |
| Observation count | 300 | 300 |
| Historical PER median | 4.2741x | 20.6217x |
| Historical PBR median | 0.3412x | 1.7059x |
| Current PER percentile | 89.6 | 22.1 |
| Current PBR percentile | 96.2 | 67.8 |
| Comparability | normal (incorrect basis) | normal (verified basis) |

Old-algorithm rows are fully rebuilt; old and new bases are not mixed. If the
unadjusted source or latest-point sanity check cannot be verified, historical
statistics are withheld while current PER/PBR remain available.

## Forward Valuation Wording

Actual modeled rendering:

```text
fPER = 현재가 ÷ 내부 정상화 ROE 추정 EPS = 208,500원 ÷ 9,829.88원 = 21.2배
fPBR = 현재가 ÷ 내부 FY1 추정 BVPS = 208,500원 ÷ 69,541.91원 = 3.0배
※ 내부 모델 추정치이며 시장 컨센서스가 아닙니다.
```

Consensus denominators use `시장 예상 EPS/BVPS`. Provider-only forward
multiples continue to render only the multiple and never reverse-engineer EPS.

## Result

- Initial baseline behavior: validated
- Backfill fingerprint consumption: validated by automated tests
- Next-day new-event delta: validated by automated tests
- Raw fact leakage: blocked by renderer tests
- Treasury materiality: `immaterial` for the LS일렉트릭 employee-compensation case
- Historical valuation: validated with unadjusted weekly prices
- Thesis version: not changed
- Production notification: not sent by this validation
