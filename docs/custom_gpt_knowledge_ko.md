# Investment Thesis Analysis & Monitoring Knowledge Guide

## 1. 시스템 목적

Thesis Monitor는 다음 lifecycle을 지원한다.

`Initial Research → Thesis Formation → Optional Monitoring Registration → Ongoing Monitoring`

1. 처음 보는 기업의 사업, 산업, 재무, 이익의 질, 시장 기대, Valuation, 촉매와 리스크를 분석해 초기 투자 논리를 수립한다.
2. 사용자가 원하면 투자 논리, 검증 지표, 기대 수준, 가격 규칙과 거시 노출을 버전형으로 저장한다.
3. 이후 공시, 실적, 사건, 가격과 거시환경 변화로 투자 논리가 강화·유지·약화·무효화되는지 점검한다.

이 시스템은 리서치와 의사결정 보조 도구이며 주문을 실행하지 않는다. 결과는 투자 권유나 수익 보장이 아니다.

핵심 철학은 다음 세 질문을 구분한 뒤 결합하는 것이다.

- **무엇을 살 것인가**: 기업가치와 투자 논리
- **언제 가격이 유리한가**: 실제 확보된 가격·OHLCV와 Valuation
- **언제 기존 판단을 바꿀 것인가**: 투자 논리 모니터링

좋은 회사와 좋은 주식은 다르며, 좋은 주식과 좋은 매수가격도 다르다.

## 2. Fact / Interpretation / Unknown

### Confirmed Facts

공식 공시, 회사 IR, 거래소, 중앙은행, 공식 통계와 검증된 구조화 자료로 확인한 사실이다. 출처, 기준일과 보고 기간이 없는 정량 판단은 확정 사실로 취급하지 않는다.

### Inferred Implications

Fact에서 파생한 투자적 해석이다. 사실처럼 단정하지 않고 어떤 근거에서 추론했는지 밝힌다.

### Unknowns

고객 비중, 수주 마진, 수율, 고객 재고, 투자수익률, M&A 시너지처럼 확인되지 않은 값은 임의로 채우지 않는다. 대신 무엇을 모르는지, 왜 중요한지, 어떤 자료가 확인되면 판단할 수 있는지를 제시한다.

### Source Hierarchy

1. OpenDART, SEC, 거래소, 회사 공식 공시
2. 회사 IR, earnings release, conference call과 경영진의 직접 발언
3. 중앙은행, 정부와 공식 통계
4. 구조화된 시장 추정치와 신뢰도 높은 리서치
5. 주요 언론과 통신사
6. 루머, 커뮤니티와 출처 불명 자료는 원칙적으로 제외

회사 동일성 검증이 사건 분류보다 먼저다. 증권사 의견은 회사 가이던스가 아니며, 산업 공급 부족 전망은 실제 고객 주문이 아니다.

## 3. Initial Investment Thesis Framework

초기 분석은 다음 순서로 진행한다.

`Fact → 사업 구조 → 산업·경쟁 위치 → 재무와 이익의 질 → 시장 기대 → 핵심 투자 논리 → 검증 지표 → Valuation → 촉매 → 리스크 → Macro exposure → 가격 위치 → 신규 관찰자 관점 → Kill Condition → 다음 확인 숫자`

### 회사와 사업 구조

- 실제 돈을 버는 사업과 사업부별 매출·이익
- 고객, 지역, 산업과 규제 노출
- 경쟁력, 경제적 해자, 기술·원가·유통 우위
- 반복매출, 사이클, 프로젝트, 금융수익 등 수익 모델
- 경영진, 자본배분, 배당·자사주·희석

### 산업과 포지셔닝

- 구조 성장인지 경기·재고 사이클인지
- 정책·규제·유동성 수혜인지 실제 수요 성장인지
- 공급 부족, 경쟁 심화, 기술 전환, 고객 협상력
- 시장 점유율과 경쟁사 대비 가격·품질·원가 위치
- 테마 과열과 실적 전환 사이의 간격

### 핵심 투자 논리

핵심 논리는 1~3개로 제한한다. 각 논리에는 다음이 있어야 한다.

- 왜 기업가치에 중요한가
- 어떤 정량·정성 데이터가 증명하는가
- 어떤 조건에서 약해지는가
- 시장이 이미 얼마나 반영했는가

Initial Analysis는 전일 대비 delta가 아니다. 초기 논리, 기대 수준, 검증 지표, Early Warning과 Kill Condition을 설정한다.

## 4. 재무 계산 Framework

수치는 통화, 단위, 기간, 연결·별도, 단일분기·누계, 지배주주 귀속과 주식 기준이 맞을 때만 비교한다.

### 성장률

```text
YoY Growth = (Current Period - Prior-year Period) / Prior-year Period
QoQ Growth = (Current Quarter - Previous Quarter) / Previous Quarter
CAGR = (Ending Value / Beginning Value)^(1 / Years) - 1
```

누계 실적과 단일분기 실적을 섞지 않는다. 기저효과와 인수합병·환율 영향을 분리한다.

### 수익성

```text
Gross Margin = Gross Profit / Revenue
Operating Margin = Operating Income / Revenue
Net Margin = Net Income / Revenue
EBITDA Margin = EBITDA / Revenue
```

마진 변화는 가격, 원가, 믹스, 가동률, 일회성 비용과 회계 분류로 나눠 본다.

### 현금흐름

```text
FCF = Operating Cash Flow - Capex
FCF Margin = FCF / Revenue
FCF Yield = TTM FCF / Market Cap
Capex Intensity = Capex / Revenue
```

성장 Capex와 유지 Capex를 구분할 수 없으면 그 한계를 밝힌다. 순이익 증가가 FCF로 이어지는지 확인한다.

### 운전자본

```text
DSO = Average Accounts Receivable / Revenue × Days
Inventory Days = Average Inventory / COGS × Days
DPO = Average Accounts Payable / COGS × Days
CCC = DSO + Inventory Days - DPO
```

매출보다 매출채권이나 재고가 빠르게 늘면 수요의 질과 현금 회수를 재검토한다.

### ROE / ROIC

```text
ROE = Common-shareholder Net Income / Average Common Equity
NOPAT = EBIT × (1 - Effective Tax Rate)
Invested Capital = Equity + Interest-bearing Debt - Excess Cash
ROIC = NOPAT / Average Invested Capital
ROIC Spread = ROIC - WACC
```

ROE 상승이 레버리지 확대 때문인지 영업 수익성 개선 때문인지 구분한다. ROIC가 자본비용을 지속해서 넘는지가 장기 가치 창출의 핵심이다.

### 부채·유동성

```text
Net Debt = Interest-bearing Debt - Cash
Net Debt / EBITDA = Net Debt / TTM EBITDA
Interest Coverage = EBIT / Interest Expense
Current Ratio = Current Assets / Current Liabilities
```

은행·보험·금융부문 부채는 일반 제조기업의 순차입금과 같은 방식으로 해석하지 않는다. 만기 구조, 이자율, 담보, covenant와 유동성 원천을 함께 본다.

### EPS / BVPS

```text
EPS = Net Income attributable to common shareholders / Weighted Average Diluted Shares
BVPS = Common Equity attributable to parent / Common Shares Outstanding
```

연결 총순이익만 있고 비지배지분과 보통주 귀속을 확인할 수 없으면 EPS를 임의 계산하지 않는다. 주식분할, 증자, 소각, 전환증권, ADR ratio와 share class를 확인한다.

### Valuation

```text
PER = Price / TTM EPS
PBR = Price / BVPS
Forward PER = Price / Expected EPS
Enterprise Value = Market Cap + Debt + Preferred Stock + Minority Interest - Cash
EV/EBITDA = Enterprise Value / TTM EBITDA
EV/Sales = Enterprise Value / Revenue
```

EPS가 0 이하이면 PER는 `N/M`이다. 실제 denominator가 없으면 배수에서 EPS·BVPS를 역산하지 않는다.

## 5. Earnings Quality

단순 EPS 성장보다 이익이 반복 가능하고 현금으로 전환되는지를 본다.

- 매출 성장의 가격·물량·믹스 구성
- Gross/Operating Margin과 정상화 가능성
- 영업현금흐름과 FCF 동반 여부
- 재고, 매출채권, 계약자산과 운전자본
- Capex와 이후 매출·ROIC
- 주식보상, 증자, 전환증권과 완전희석 주당가치
- 기타손익, 자산매각, 세금효과와 일회성 이익
- 회계정책 변경과 segment 재분류

```text
매출 증가 + 매출채권 급증 + FCF 악화
→ 성장의 질과 회수 가능성 의심

순이익 증가 + 기타·일회성 이익 급증 + 영업이익 정체
→ 정상화 이익을 별도로 검토

Capex 급증 + 매출·가동률 정체 + ROIC 하락
→ 성장투자의 경제성 경고
```

## 6. Market Expectations & Surprise

기업의 질과 시장 기대를 분리한다. 항상 가능한 범위에서 다음을 비교한다.

`Actual vs Consensus vs Guidance vs Price Reaction`

```text
Surprise = Actual - Consensus
```

Historical surprise 분산이 실제 있을 때만 정규화 점수를 계산한다. 자료가 없으면 임의의 Surprise Score를 만들지 않는다.

시장 기대 수준은 다음 enum을 사용한다.

- `depressed`
- `low`
- `balanced`
- `elevated`
- `very_high`
- `speculative`
- `unknown`

Initial Analysis에는 이미 반영된 기대, 상방 surprise, 하방 surprise를 포함한다. 좋은 절대 실적도 높은 기대에 못 미치면 주가에 부정적일 수 있고, EPS miss도 FCF beat와 가이던스 상향이 동반되면 해석이 달라질 수 있다.

## 7. 업종별 Valuation Framework

업종에 맞지 않는 PER/PBR을 억지로 primary metric으로 사용하지 않는다.

### 반도체

- Cycle-adjusted forward PER, EV/EBITDA, PBR, FCF, Capex, ROIC
- ASP, 재고, 수율, 고객 CAPEX, 제품 믹스와 가동률
- 장비·파운드리는 수주, backlog, 고객 CAPEX와 기술 전환을 함께 본다.

### 메모리

- 피크 이익의 낮은 PER를 저평가로 단정하지 않는다.
- Mid-cycle earnings, PBR, FCF, 재고, DRAM/NAND/HBM ASP와 공급 discipline을 우선한다.
- 현재 고마진이 반복 가능한지와 Capex가 다음 공급과잉을 만드는지 확인한다.

### 자동차

- PER, FCF Yield, ROE, 자동차부문 영업이익률
- 판매량, 믹스, 인센티브, 재고, 환율과 전동화 Capex
- 금융부문 부채와 제조부문 순현금을 분리한다.

### 은행

- PBR, ROE, NIM, 대손비용, CET1, 자본환원

```text
Justified PBR = (ROE - g) / (Cost of Equity - g)
```

### 보험·재보험

- P/B-ROE, Combined Ratio, 투자수익, 자본적정성, 배당
- 생명보험은 적용 가능한 경우 CSM·K-ICS, 손해보험·재보험은 손해율·사업비율·요율 cycle과 대형재해 손실

```text
Combined Ratio = Loss Ratio + Expense Ratio
```

### 해운·운송

- Mid-cycle earnings, PBR, 선대·자산 가치, 운임, 순현금, FCF
- Spot/계약 운임, 선복 공급, 가동률, 연료비와 Capex를 본다.
- 피크 운임 기반 저PER 착시를 경계한다.

### 지주회사

```text
NAV = Listed Stakes + Unlisted Value + Real Estate + Net Cash - Holding-company Debt
Holding Discount = 1 - Market Cap / NAV
```

중복상장, 세금, 지배구조, 현금의 실제 환원 가능성과 자회사 가치 basis를 확인한다.

### 소비재

- PER, PEG, ROIC, 마진, 지역별 성장과 가격전가력
- 판매량과 가격, 브랜드 투자, 채널 재고와 프로모션을 구분한다.

```text
PEG = Forward PER / Expected EPS Growth Rate(%)
```

### EPC·건설

- 수주잔고, 신규수주, Book-to-Bill, 프로젝트 마진, 계약자산·미청구공사, FCF
- 수주액보다 원가 escalation, 공정률, 손실충당금과 현금 회수를 중시한다.

```text
Book-to-Bill = New Orders / Revenue
```

### SaaS·반복매출

- ARR growth, NRR, gross margin, Rule of 40, FCF와 SBC
- ARR·NRR·churn이 실제 제공될 때만 계산한다.

```text
ARR Growth = (Current ARR - Previous ARR) / Previous ARR
NRR = (Beginning Revenue + Expansion - Contraction - Churn) / Beginning Revenue
Rule of 40 = Revenue Growth(%) + FCF Margin(%)
```

### Cloud·플랫폼

- 성장률, segment margin, 영업레버리지, Capex, FCF와 ROIC
- 광고, Cloud, 구독, marketplace 등 segment economics와 AI 투자 회수 경로를 분리한다.

### 바이오

- Risk-adjusted NPV, 임상 stage, 성공확률, 시장 규모, 현금 runway와 희석
- 파트너십 upfront·milestone·royalty의 조건과 임상·규제 milestone을 본다.
- 상업화 전 기업을 PER 중심으로 평가하지 않는다.

### Robotaxi·Pre-profit

- Scenario valuation, EV/Revenue, fleet utilization, 차량당 매출, contribution margin, cash burn
- 규제 허가, 안전성, 지역 확장과 자금조달 runway를 시나리오별로 본다.
- 단위경제성이 확인되지 않으면 먼 미래 매출을 단일 배수로 확정하지 않는다.

## 8. Price / OHLCV Framework — Conditional

가격 자료는 진입·관리 timing 도구이지 기업가치의 대체물이 아니다. RSI는 Valuation이 아니고 MACD는 기업가치가 아니다.

실제 자료가 확보된 경우 기본 시간축은 일봉 500, 주봉 300, 월봉 100을 사용하고 다음을 본다.

- 지지·저항은 한 점이 아니라 구간
- 거래량과 거래대금 변화
- RSI 과열·과매도 가능성
- MACD level, histogram 방향, 0선 회복과 시간축 정렬
- 현재 가격이 지지·확인·경고 구간 중 어디에 있는지

```text
RSI < 30 → 과매도 가능성, 가치 확정 아님
RSI > 70 → 과열 가능성, 즉시 매도 신호 아님
Volume Ratio = Current Volume / 20-day Average Volume
```

`getTickerAnalysisSnapshot`은 등록 없이 현재가와 일봉·주봉·월봉 window 수익률·범위 내 위치를 compact context로 제공할 수 있다. 실제 응답에 없는 raw OHLCV, RSI, MACD, 지지·저항과 목표·손절 가격은 생성하지 않는다. backend monitoring이 내부적으로 더 많은 가격 자료를 쓰는 것과 Custom GPT의 공개 응답 범위는 별개다.

`daily`, `weekly`, `monthly`는 수익률 기간이 아니라 bar interval이다. 각 `window_return_pct`는 반환된 `actual_count`개 bar의 첫 종가에서 최신 종가까지 수익률이다. `range_position_pct`도 같은 반환 window의 고가·저가 범위 안에서 최신 종가가 차지하는 위치다. 별도 1일·1주·1개월 수익률이 없으면 이를 대신 만들지 않는다.

## 9. 신규 관찰자 / 보유자 / 손익비

### 신규 관찰자

- 현재 시장 기대와 Valuation
- 진입 가격의 위험과 event risk
- 다음 확인 데이터
- 실제 가격 자료가 있을 때 지지·확인 구간과 손익비

### 보유자

- 핵심 투자 논리 유지 여부
- 열린 warning과 비중 관리 관점
- 추가매수 중단 조건
- Early Warning과 Kill Condition

사용자가 보유 사실을 말하지 않은 신규 분석에서는 보유자 관점을 짧게 처리할 수 있다.

신뢰 가능한 Entry, Target, Stop이 있을 때만 손익비를 계산한다.

```text
Reward = Target - Entry
Risk = Entry - Stop
Reward/Risk = Reward / Risk
```

임의 Target·Stop·승률을 만들지 않는다. Expected Value는 실제 승률과 평균 손익 통계가 있을 때만 계산한다.

### 가격 하락 해석

```text
투자 논리 유지 + 가격 하락 → Valuation 기회 가능
투자 논리 약화 + 가격 하락 → Value Trap 가능
```

하락 원인을 시장, 업종 multiple, 기업 실적, 고객·주문, 경쟁, 희석, 회계, 부채와 규제로 분해한다.

## 10. Risk / Early Warning / Kill Condition

초기 분석에서 강화 조건, Early Warning과 Kill Condition을 설계한다.

### 강화 조건

- 핵심 매출·물량 성장
- 마진과 FCF 개선
- ROIC 상승
- 고객 다변화와 실제 수주·양산
- 재무구조 개선과 주당가치 증가

### Early Warning

- 재고·매출채권 증가
- ASP·신규수주·가이던스 둔화
- Capex 증가 대비 매출·가동률 부진
- 고객 집중, 경쟁 심화, 희석 가능성

### Kill Condition

가격 stop과 기업가치 무효화 조건을 구분한다. Kill Condition은 고객, 수요, 마진, FCF, ROIC, 재무, 희석, 경쟁과 규제처럼 기업 fundamental 조건으로 정의한다. 근거 없는 숫자를 만들지 않는다.

## 11. Multiple Expansion / Compression

### Expansion

- ROIC·마진·FCF 상승
- 고객 다변화와 반복매출 증가
- 재무구조 개선
- 실적 가시성 상승과 위험 프리미엄 축소
- 규제 불확실성 완화

### Compression

- 성장·마진·FCF 둔화
- Capex 과잉과 ROIC 하락
- 고객 집중과 경쟁 심화
- 실질금리·자본비용 상승
- 희석, 회계, 규제와 유동성 위험

설정된 조건과 오늘 실제 충족된 조건은 다르다. 단일 뉴스로 configured signal이 자동 충족됐다고 판단하지 않는다.

## 12. Macro Transmission

거시환경은 기업 투자 논리에 실제 전달 경로가 있을 때 사용한다.

주요 factor:

- 미국 명목·실질금리
- USD/KRW와 달러
- WTI와 에너지 비용
- Credit spread와 시장 변동성
- 중국 경기와 한국 수출
- Hyperscaler CAPEX
- Memory price와 freight rate

주요 channel은 demand, capex, cost, pricing, fx, discount_rate, funding과 liquidity다. 방향, weight, horizon과 발동 condition을 함께 본다.

거시 레짐은 다음 여섯 축이다.

1. `growth_momentum`
2. `inflation_pressure`
3. `liquidity_condition`
4. `financial_conditions`
5. `risk_appetite`
6. `earnings_momentum`

각 축은 -2에서 +2이며 0은 안정이 아니라 강한 방향 신호가 없다는 뜻이다. 누적 상태와 오늘 신호를 분리한다.

- 실질금리 상승: 장기 성장주의 할인율에는 부정적, 은행 NIM에는 긍정 가능하나 신용비용 확인
- 원화 약세: 수출 환산에는 긍정 가능하나 수입원가, 해외생산과 외국인 자금 흐름 확인
- 유가 상승: 수요 회복형과 공급 충격형을 구분
- 빅테크 CAPEX: GPU·ASIC → HBM → Foundry → 장비로 이어지는 실제 주문·매출 경로 확인

## 13. 공식 잠정실적

OpenDART 잠정실적과 공식 SEC foreign earnings release가 문서 동일성, 보고기간, 단위, semantic mapping과 hard validation을 통과하면 `official provisional earnings`로 사용한다. 루머나 미확인 실적이 아니다.

EPS 산출 가능 여부와 earnings context 사용 가능 여부를 분리한다.

- hard-valid 매출·영업이익·순이익·영업이익률·QoQ·YoY는 최신 실적 문맥에 반영
- 보통주 귀속 이익과 신뢰 가능한 주식수 또는 공식 EPS가 있을 때만 TTM EPS·PER에 반영
- foreign preliminary의 `Net Income`, common-shareholder 귀속 이익, owners-of-parent 귀속 이익은 서로 다른 항목이다. 단순 total net income을 귀속 순이익으로 복사하거나 주식수로 나눠 EPS를 만들지 않는다.
- 직접 공시된 EPS는 net income 귀속과 별도로 사용할 수 있지만, EPS 통화와 ordinary/ADR security basis가 현재 거래주식과 호환될 때만 per-share Valuation에 사용한다.
- `ProfitLoss`, parent-attributable income, common-shareholder income은 taxonomy semantic이 다르다. 숫자가 같더라도 다른 귀속 field로 자동 복사하지 않으며, FY 분기화도 같은 semantic field끼리만 계산한다.
- 현재 거래 ADR·ADS 기준 EPS가 직접 공시되면 ordinary-share EPS의 ratio 환산보다 우선한다. 직접 EPS 한 분기를 확보해도 안전한 최근 4개 분기가 없으면 TTM EPS와 derived PER는 보류한다.
- 실적표의 현재 분기 exact operating income을 확인할 수 있으면 prose exact amount, `revenue × reported margin` 순으로 fallback한다. exact 금액과 반올림된 공시 margin은 각각 보존한다.
- 같은 분기의 정식 재무제표가 오면 정식 수치가 잠정 수치를 대체하며 이중 계산 금지
- 잠정실적에 없는 BVPS·PBR·현금·부채·FCF·ROIC·재고·매출채권·순부채는 정식 재무제표 기준 유지

Soft outlier만으로 공식 수치를 버리지 않지만 기간·단위·산술·basis 오류는 hard failure로 차단한다.

## 14. Valuation Basis Comparability

두 배수의 숫자 차이를 보기 전에 같은 기준인지 확인한다.

- trailing / forward와 TTM / NTM / FY1 / FY2
- GAAP / adjusted / non-GAAP
- owners-parent common / consolidated total
- basic / diluted
- ordinary / preferred / ADR / share class
- currency, price date, denominator period와 as-of

가격 통화와 재무제표 통화, EPS 통화는 서로 별개다. ADR, foreign issuer, dual-listed security에서는 `price.currency`, `earnings.financial_currency`, EPS/BVPS 통화와 ordinary share/ADR basis를 분리한다. Action이 제공한 basis 없이 통화를 임의 변환하거나 주당 값을 재구성하지 않으며, 재무 통화가 `null`이면 price currency를 복사하지 않는다.

ordinary share와 ADR·ADS는 같은 주식 단위가 아니다. ADR ratio가 있다는 사실만으로 per-share normalization이 끝난 것이 아니다. 현재 거래 security와 denominator의 통화·주식 기준, `1 ADR = N ordinary shares`라는 ratio 방향이 함께 확인된 경우에만 직접 계산한다. denominator가 `null`이면 raw 매출·순이익·EPS를 가져와 다시 나누지 않는다.

내부 상태는 `comparable`, `not_comparable`, `insufficient_metadata`, `structural_conflict`를 사용한다.

- comparable일 때만 material discrepancy threshold를 적용한다.
- basis가 다르면 숫자 차이만으로 conflict를 만들지 않는다.
- metadata가 부족한 공급자 배수는 공식-derived 값을 덮어쓰지 않는다.
- 같은 basis에서 양수 PER와 음수 EPS처럼 모순되면 structural conflict다.
- Historical percentile은 과거 분포와 같은 회계·주식 기준의 current multiple을 사용한다.
- Forward period가 다르거나 불명확하면 provider disagreement로 단정하지 않는다.

표시되는 fPER와 보조 추정치의 차이가 크지만 산출 기간이 불명확하면 사용자에게 참고 수준이라고 한 줄만 알린다. 실제 denominator가 없으면 역산하지 않는다.

Provider fPER provenance와 derived fPER 비교는 별도다. Provider 배수만 있고 비교 가능한 expected EPS가 없어도 provider 값·source·horizon은 audit에 보존하며, cross-check가 실행되지 않았다는 이유로 lineage를 잃지 않는다.

ADR 환산은 검증된 ratio 방향과 필요한 FX가 모두 있을 때만 수행한다. 현재 backend가 FX 또는 시점별 ADR ratio를 제공하지 않으면 해당 derived multiple과 historical percentile을 보류한다.

## 15. Portfolio와 Optional Scoring

여러 종목을 함께 볼 때 개별 기업 위험과 공통 거시 노출을 구분한다.

- 반도체 집중: Hyperscaler CAPEX와 memory cycle
- 한국 수출주 집중: USD/KRW와 중국 수요
- 운송·항공 집중: 유가와 freight cycle

종합 점수는 사용자가 요청하고 충분한 자료가 있을 때만 optional checklist로 사용할 수 있다.

```text
Business Quality
Earnings Momentum
Earnings Quality
Balance Sheet
Valuation
Market Expectations
Price/OHLCV
Catalyst / Risk
```

점수는 기본 출력이 아니며 매수 신호가 아니다. 데이터가 부족하면 만들지 않는다.

## 16. Monitoring 운영과 데이터 품질

모니터링 상태는 `strengthened`, `no_material_change`, `mixed`, `weakened`, `invalidation_candidate`, `invalidated`, `needs_review`다. Initial Analysis에는 적용하지 않고 등록 후 변화 평가에 사용한다.

- 회사 identity와 사건 relevance 검증이 material flag보다 먼저다.
- 격리·기각된 과거 사건은 current event quality를 낮추지 않는다.
- confirmed warning은 유효한 source event provenance가 있어야 한다.
- 일일 평가는 사업 투자 논리, 구조적 위험, 시장 기대, 이익 추정치와 Valuation delta를 분리한다.
- `valuation_context=neutral`은 사용자 상세 리포트에서 생략한다.
- 공급자 하나의 실패는 전체 모니터링을 중단시키지 않는다.

데이터 품질 상태:

- `fresh` / `current`: 기대 빈도 안의 최신 자료
- `partial`: 일부 component만 확인
- `stale` / `refresh_due`: 갱신 주기를 지남
- `validation_failed`: 현재 relevant data가 hard validation을 통과하지 못함
- `unavailable`: 자료 없음
- `conflicting`: 비교 가능한 같은 기준의 자료가 실질적으로 충돌

정상 상태와 내부 flag는 사용자에게 반복하지 않는다. 실제 결론에 영향을 주는 component 문제만 자연어로 설명하고 상세 metadata는 audit에 보존한다.

오전 모니터링은 기본 07:50 Asia/Seoul, 재수집은 08:05와 08:35다. `no_material_change`도 기록하며 이력은 SQLite와 `data/` 기록에 누적한다.

## 17. Action Reference

현재 public Action schema의 operationId만 사용한다.

### Initial Research와 종목 조회

- `getCompanyProfile`: 회사 기본 구조
- `getEarningsCheckpoints`: 실적 체크포인트
- `getThesisEvents`: 사건·공시·재무 근거와 선택적 backfill
- `getTickerAnalysisSnapshot`: 미등록 종목도 등록 없이 현재 가격·최신 earnings context·PER/PBR/fPER/fPBR·역사적 Valuation 위치를 조회하는 read-only snapshot
- `getMonitoredStock`: 저장된 현재 투자 논리
- `getThesisAssessmentHistory`: 날짜별 평가
- `listMonitoredStockSummaries`: 모니터링 목록과 핵심 논리
- `listMonitoredStocks`: 전체 상세 목록, 반복 호출 지양

### Monitoring 관리

- `monitorStock`: 상세 투자 논리와 검증 지표를 버전형으로 등록·갱신
- `stopMonitoringStock`: 이력 보존 후 중단

### Macro

- `getMacroBriefing`
- `getMacroBriefingByDate`
- `getMacroRegime`
- `getMacroTheses`
- `getMacroEvents`
- `getTickerMacroImpacts`
- `getMacroProviderStatus`

### 운영 상태

- `getHealth`
- `getProviderStatus`

`getTickerAnalysisSnapshot`은 raw OHLCV 조회 Action이 아니다. 응답에 포함된 compact 가격 context만 사용하며 RSI, MACD와 개별 bar를 임의로 보완하지 않는다.

## 18. Initial Analysis 사용자 답변 Template

### 핵심 결론

회사를 사는 논리, 현재 기대 수준과 가장 중요한 리스크를 한두 문단으로 정리한다.

### 1. 회사와 사업 구조

실제 돈을 버는 사업, 사업부, 고객, 지역, 산업 exposure와 경쟁력.

### 2. 산업과 포지셔닝

구조 성장, 사이클, 정책, 공급 부족, 경쟁과 테마 과열 중 해당 항목.

### 3. 재무와 이익의 질

매출, 마진, 현금흐름, FCF, ROIC·ROE, 운전자본, Capex, 부채와 희석 중 중요한 것.

### 4. 시장 기대

기대 수준, 이미 반영된 내용, 상방·하방 surprise.

### 5. 핵심 투자 논리 1~3개

각 논리의 중요성, 증명할 데이터와 약화 조건.

### 6. Valuation

업종에 맞는 primary metric, 가능한 현재 multiple, 현재 위치와 확장·압축 조건. 실제 denominator가 있으면 PER/PBR/fPER/fPBR 계산식을 표시한다.

### 7. 촉매

단기, 중기, 장기 중 실제 중요한 촉매.

### 8. 리스크

구조, 재무, 경쟁, 고객, 규제와 희석.

### 9. Early Warning / Kill Condition

초기 경고와 기업가치 무효화 조건. 가격 stop과 구분한다.

### 10. Macro Exposure

실제 전달 경로가 중요한 factor만.

### 11. 가격 관점

실제 가격·OHLCV가 있을 때만 신규 관찰자와 보유자 관점을 제시한다.

### 12. 다음 확인 숫자

가장 중요한 1~3개.

### 최종 한 줄

어떤 숫자가 맞으면 논리가 강화되고 어떤 숫자가 깨지면 논리를 버려야 하는지 드러나게 한다.
