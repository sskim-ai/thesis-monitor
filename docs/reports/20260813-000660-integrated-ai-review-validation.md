# 000660 Integrated AI Review Validation

## Validation Input

- Assessment: 2026-08-13 KR close
- Deterministic business status: `no_material_change`
- Structural risk: elevated
- Market expectation: very high
- Chart quality: fresh
- Chart basis: adjusted close
- Price-rule basis: stored close rules
- Historical valuation: separate unadjusted weekly basis, comparability normal
- Validator: schema 3 / `daily-review-v3.3`

The live dry-run used the operational assessment, current OHLCV Analyst output, and existing thesis
price rules without writing the DB or sending Telegram.

## Before

Pilot v1 described strong earnings, high expectations, valuation premium, and the need to verify cash
generation, then appended the complete deterministic price, supply, valuation, holder, and new-observer
blocks. Its AI review used no numeric claims and repeated the same holder/new-buyer content below the
price block.

Representative AI text:

> 강한 잠정실적은 기존 논리와 양립하지만 높은 기대와 프리미엄이 이미 반영돼 있다.
> 현금창출과 자본효율의 추가 확인 전에는 투자 논리와 가치평가를 유지한다.

## After: Validator-Passed Integrated Message

```text
🤖 AI 보조 종목 점검 · KR Pilot 1/5

🏢 SK하이닉스(000660)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 높아진 상태
시장 기대: 매우 높음

🎯 핵심 판단
잠정 영업이익률 76.33%는 메모리 수익성 논리를 지지하지만, 현재 PBR 6.8678배와 매우 높은 시장 기대를 함께 보면 기업의 질과 신규 진입 매력은 분리해야 합니다. 현재가 1,593,000원은 상향 확인 가격 1,550,000원을 넘었으므로 이제 돌파 유지와 현금 전환이 핵심입니다.

📈 사업·실적
잠정 매출 79조3,187억원, 영업이익 60조5,426억원, 영업이익률 76.33%는 현재 이익 강도를 보여줍니다. 다만 잠정실적에는 영업현금흐름, Capex, 재고, FCF, ROIC가 없어 높은 회계이익이 실제 현금과 자본효율로 이어졌는지는 정식 재무에서 확인해야 합니다.

💰 가격·포지셔닝
현재가 1,593,000원은 상향 확인 가격 1,550,000원보다 확인 가격 이격 약 2.77% 위에 있습니다. 일봉 20일 거래량비 0.81배로 돌파의 거래량 확인은 아직 약해, 같은 기준의 지지 전환과 재시험이 다음 가격 논점입니다.
• 신규 관찰자: 동적 지지구간이 제공되지 않아 추격보다 돌파선의 지지 전환을 관찰합니다.
• 보유자: 기존 상승 시나리오는 유지되지만 거래량과 중기 수급이 따라오는지 재점검합니다.

📊 수급
당일 외국인 순매수 653,026주와 기관 순매수 159,109주, 5일 외국인 순매수 661,622주와 기관 5일 순매수 522,096주는 단기 기관성 자금 복귀를 시사합니다. 반면 외국인 20일 순매도 2,327,431주와 기관 20일 순매도 428,723주가 남아 있어 중기 분배가 끝났다고 단정할 수 없습니다.

📐 Valuation
현재 PER 6.9712배는 과거 PER 중앙값보다 낮지만 현재 PBR 6.8678배와 PBR 과거 백분위 93.5%는 자산가치 기준 프리미엄을 보여줍니다. 내부 정상화 추정 fPER 15.8601배까지 함께 보면 낮은 trailing PER만으로 저평가라고 판단하기 어렵습니다.

⚠️ 기존 경고
• 유상증자에 따른 희석·자본조달 경제적 영향

⚠️ 데이터 주의
• 이번 분기 이익률이 과거보다 매우 높아 일회성 손익과 지속 가능성을 추가 확인합니다.

👁 핵심 감시
• 돌파 가격의 지지 전환과 거래량 동행
• 단기 기관성 매수의 중기 누적 전환
• 높은 마진의 현금 전환과 자본효율

📌 다음 확인
• 정식 재무의 영업현금흐름·Capex·재고·FCF·ROIC
• 돌파선 재시험과 기관성 수급의 지속 여부
• 메모리 수익성 유지가 현재 장부가치 프리미엄을 정당화하는지

⚠️ 미확인
• 잠정실적에 없는 영업현금흐름, Capex, 재고, FCF와 ROIC 변화
• 동적 지지·저항과 ATR 등 현재 수집되지 않은 차트 요소
```

## Quantitative Grounding

| Section | Eligible | Used |
| --- | ---: | ---: |
| Core judgment | 116 | 4 |
| Business / earnings | 7 | 3 |
| Price / positioning | 54 | 4 |
| Supply | 11 | 6 |
| Valuation | 22 | 4 |

- Numeric claims: 21
- Chart facts used: daily, stored price rules, price transition
- Grounding flags: 0
- Output validation: passed
- Telegram sent: no; this was a read-only acceptance dry-run

## Difference

- The confirmation condition is treated as completed; the next issue is hold/retest/volume/supply.
- Daily and 5-day institutional buying are separated from still-negative 20-day positioning.
- Low trailing PER is explicitly weighed against high PBR, historical PBR percentile, and modeled fPER.
- Missing OCF, Capex, inventory, FCF, and ROIC are tied to a concrete next financial review.
- Holder and new-observer views are integrated into price/positioning instead of repeated later.
- The full deterministic report is no longer appended below the AI narrative.
