# SK hynix Phase 5 Integrated AI Review Validation

## Input

- Assessment: 2026-08-13 KR close
- Deterministic thesis status: `no_material_change`
- Structural risk: elevated
- Market expectation: very high
- Chart quality/basis: fresh / adjusted close
- Algorithm/policy: `ohlcv-structure-v1` / `daily-review-v3.4`
- Validator: schema 3, passed
- Side effects: no DB write, no Telegram send

The Phase 4 comparison message is preserved in
`docs/reports/20260813-000660-integrated-ai-review-validation.md`. Phase 5 reused the same operational
assessment and current OHLCV Analyst data, then added deterministic structure output.

## Structure Result

- Current price: 1,593,000 KRW
- Stored confirmation: 1,550,000 KRW; transition `confirmation_crossed`
- Daily Wilder ATR14: 181,017 KRW
- Nearest dynamic support: 1,190,321-1,301,679 KRW, Weak
- Nearest dynamic resistance: 1,618,575-1,737,425 KRW, Weak
- Box: unavailable
- Major Swing primary: weekly, 6 points
- Elliott: tentative low confidence, excluded from core reasoning
- Fibonacci: long-term, medium-term, and breakout Major-Swing anchors available
- Structural invalidation/RR: unavailable because no Strong/Medium support qualified
- Supply: 20-day distribution
- Chart state: WAIT, medium confidence; this is not a sell instruction

## Validator-Passed Message

```text
🤖 AI 보조 종목 점검 · KR Pilot 1/5

🏢 SK하이닉스(000660)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 높아진 상태
시장 기대: 매우 높음

🎯 핵심 판단
잠정 영업이익률 76.33%는 메모리 수익성 논리를 지지하지만, 현재 PBR 6.8678배와 매우 높은 시장 기대를 함께 보면 기업의 질과 신규 진입 매력은 분리해야 합니다. 현재가 1,593,000원은 상향 확인 가격 1,550,000원을 넘었지만 동적 저항구간 하단 1,618,575원이 가까워, 돌파 유지와 현금 전환을 함께 확인해야 합니다.

📈 사업·실적
잠정 매출 79조3,187억원, 영업이익 60조5,426억원, 영업이익률 76.33%는 현재 이익 강도를 보여줍니다. 다만 잠정실적에는 영업현금흐름, Capex, 재고, FCF, ROIC가 없어 높은 회계이익이 실제 현금과 자본효율로 이어졌는지는 정식 재무에서 확인해야 합니다.

💰 가격·포지셔닝
현재가 1,593,000원은 상향 확인 가격 1,550,000원보다 확인 가격 이격 약 2.77% 위에 있지만, 일봉 20일 거래량비 0.81배라 돌파의 거래량 확인은 아직 약합니다. 일봉 ATR14 181,017원으로 변동성도 큰 가운데 동적 저항구간 하단 1,618,575원과 저항구간 상단 1,737,425원이 가까우며, 동적 지지구간 하단 1,190,321원과 지지구간 상단 1,301,679원은 멀고 강도도 약합니다. 따라서 구조적 무효화와 차트 손익비를 확정하지 않고 재시험·거래량·수급을 봅니다.
• 신규 관찰자: 가까운 저항과 약한 거래량 때문에 추격보다 돌파선의 지지 전환을 관찰합니다.
• 보유자: 사업 논리는 유지되지만 가격 구조는 재시험과 중기 수급 확인이 필요합니다.

📊 수급
당일 외국인 순매수 653,026주와 기관 순매수 159,109주, 5일 외국인 순매수 661,622주와 기관 5일 순매수 522,096주는 단기 기관성 자금 복귀를 시사합니다. 반면 외국인 20일 순매도 2,327,431주와 기관 20일 순매도 428,723주가 남아 있어 중기 분배가 끝났다고 단정할 수 없습니다.

📐 Valuation
현재 PER 6.9712배는 과거 PER 중앙값보다 낮지만 현재 PBR 6.8678배와 PBR 과거 백분위 93.5%는 자산가치 기준 프리미엄을 보여줍니다. 내부 정상화 추정 fPER 15.8601배까지 함께 보면 낮은 trailing PER만으로 저평가라고 판단하기 어렵습니다.

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
• Strong/Medium 동적 지지가 없어 확정하지 않은 구조적 무효화와 차트 손익비
• 낮은 신뢰도로 핵심 판단에서 제외한 Elliott 잠정 count
```

The renderer also retains the existing deterministic warning and data-caution blocks; they were
omitted above only to keep this comparison focused on Phase 5 changes.

## Quantitative Grounding

| Section | Eligible | Used |
| --- | ---: | ---: |
| Core judgment | 161 | 5 |
| Business / earnings | 7 | 3 |
| Price / positioning | 54 | 9 |
| Supply | 11 | 6 |
| Valuation | 22 | 4 |

- Numeric claims: 27
- Chart facts used: daily, price transition, stored rules, ATR, nearest support, nearest resistance,
  chart state
- Grounding flags: 0
- Validation errors: 0

## Phase 4 to Phase 5 Difference

- Phase 4 could only say the stored confirmation was crossed; Phase 5 gives the next dynamic
  resistance and the absence of a strong nearby support setup.
- ATR makes the large adjusted-price volatility explicit without becoming a buy/sell signal.
- Weak zones do not manufacture invalidation or RR; the missing outputs become decision-relevant
  unknowns.
- Local Pivot zones and weekly Major Swing/Fib remain separate analytical layers.
- Daily/5-day buying is still distinguished from negative 20-day institutional positioning.
- Fundamental status remains deterministic `no_material_change`; chart WAIT does not overwrite it.
