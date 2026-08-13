# Thesis-monitor 상세 분석 지침 · Knowledge · 계산식 · API Reference v2.0

## 0. 문서 목적

이 문서는 Thesis-monitor가 종목과 거시환경을 분석할 때 사용하는 상세 판단 체계, 계산 공식, 데이터 우선순위, Action/API 활용 규칙, valuation framework, 이벤트 해석 방식, OHLCV와 기업가치의 결합 원칙을 정리한 운영 매뉴얼이다.

핵심 질문은 하나다.

> 이 종목을 사야 한다고 생각하게 만든 핵심 투자 논리가 시간이 지나면서 강화되는가, 유지되는가, 약해지는가, 아니면 깨지는가?

기본 판단 순서:

```text
Fact → 시장 기대 → 투자적 해석 → 투자 논리 변화
→ 이익 추정치 영향 → Valuation 영향 → 가격 실행 여부
```

핵심 철학:

> 좋은 회사와 좋은 주식은 다르다. 좋은 주식과 좋은 매수가격도 다르다.


## 1. 분석 데이터 계층

### 기업 펀더멘털
- 사업부별 매출·이익
- 고객·지역·산업 노출
- 경쟁력·경제적 해자
- 가이던스
- 영업이익률·순이익률
- 영업현금흐름·FCF
- 재고·매출채권
- Capex·ROIC
- 부채·현금·순차입금
- 주식보상·희석
- 배당·자사주·자본배분

### 가격·수급
- 일봉 500 / 주봉 300 / 월봉 100
- MA / Bollinger / RSI / MACD / Histogram / OSC
- 거래량·거래대금
- 지지·저항
- 손익비
- 외국인·기관·개인 수급

### 거시
- 성장·물가·유동성·금융여건·위험선호·이익 모멘텀
- 금리·실질금리·환율·유가·신용스프레드
- 미국시장·빅테크 실적·FOMC
- 중국 경기·한국 수출·Hyperscaler CAPEX


## 2. Fact / Interpretation / Unknowns

### Confirmed Facts
OpenDART, SEC, 회사 IR, 거래소, 중앙은행, 공식 통계로 확인된 사실만 사용한다.

### Inferred Implications
Fact에서 파생한 투자 해석. 반드시 추정/해석임을 명시한다.

### Unknowns
확인되지 않은 고객 비중, 수주 마진, 수율, ROI, 고객 재고, M&A 시너지 등은 Unknown으로 유지한다.


## 3. Source Hierarchy

| 우선순위 | 출처 | 용도 |
|---|---|---|
| 1 | OpenDART / SEC / 회사 공시 | 확정 Fact |
| 2 | 회사 IR / Earnings Release / Conference Call | 방향성 |
| 3 | 거래소 / 중앙은행 / 공식 통계 | 시장·거시 Fact |
| 4 | 컨센서스 / 신뢰도 높은 리서치 | 시장 기대 |
| 5 | 주요 언론 / 통신사 | 맥락 |
| 6 | 루머 / 커뮤니티 | 원칙적으로 제외 |

한국 종목은 6자리 코드, 미국 종목은 ticker를 사용한다.


## 4. Action / API 활용 규칙

### 종목
- `getThesisEvents`: 최근 Thesis 관련 공시·뉴스·실적·수주·자본조달
- `getCompanyProfile`: 회사 구조
- `getEarningsCheckpoints`: 실적 체크포인트
- `monitorStock`: 투자 논리와 검증지표 저장
- `getMonitoredStock`: 현재 저장 논리
- `getThesisAssessmentHistory`: 날짜별 평가
- `stopMonitoringStock`: 이력 보존 중단

한국 종목 일상 점검 기본:

```json
{
  "ticker": "005930",
  "provider": "opendart",
  "auto_backfill": false,
  "lookback_days": 90
}
```

최초 장기 분석:

```json
{
  "ticker": "005930",
  "provider": "opendart",
  "auto_backfill": true,
  "backfill_years": 5,
  "lookback_days": 365
}
```

오류 시 1회 재시도:
- 6자리 코드
- `auto_backfill=false`
- `lookback_days=30`

### 거시
- `getMacroBriefing`
- `getMacroBriefingByDate`
- `getMacroRegime`
- `getMacroTheses`
- `getMacroEvents`
- `getTickerMacroImpacts`
- `getMacroProviderStatus`

### 공식/외부 데이터 참고 API
- OpenDART: 한국 공시·잠정실적·재무제표
- SEC EDGAR: 미국 10-K, 10-Q, 8-K
- FRED: 미국 금리·실질금리·신용·유동성
- EIA: 원유 재고·생산·정제 가동률
- BOK ECOS: 한국 금리·환율·물가·통화
- Federal Reserve: FOMC 성명서·의사록·SEP
- 회사 IR: 실적·가이던스·컨퍼런스콜
- ohlcv-analyst: 가격·OHLCV·기술지표


## 5. 핵심 재무 계산식

### 성장률

```text
YoY Growth = (Current - Previous) / Previous
QoQ Growth = (Current Quarter - Previous Quarter) / Previous Quarter
CAGR = (Ending / Beginning)^(1 / Years) - 1
```

### 수익성

```text
Gross Margin = Gross Profit / Revenue
Operating Margin = Operating Income / Revenue
Net Margin = Net Income / Revenue
EBITDA Margin = EBITDA / Revenue
```

### 현금흐름

```text
FCF = Operating Cash Flow - Capex
FCF Margin = FCF / Revenue
FCF Yield = TTM FCF / Market Cap
Capex Intensity = Capex / Revenue
```

### 운전자본

```text
DSO = Average AR / Revenue × Days
Inventory Days = Average Inventory / COGS × Days
DPO = Average AP / COGS × Days
CCC = DSO + Inventory Days - DPO
```

### ROE / ROIC

```text
ROE = Net Income attributable to common / Average Common Equity

NOPAT = EBIT × (1 - Effective Tax Rate)

Invested Capital =
Equity + Interest-bearing Debt - Excess Cash

ROIC = NOPAT / Average Invested Capital

ROIC Spread = ROIC - WACC
```

### 부채·유동성

```text
Net Debt = Interest-bearing Debt - Cash
Net Debt / EBITDA = Net Debt / TTM EBITDA
Interest Coverage = EBIT / Interest Expense
Current Ratio = Current Assets / Current Liabilities
```

### EPS / BVPS

```text
EPS =
Net Income attributable to common shareholders
/ Weighted Average Diluted Shares

BVPS =
Common Equity attributable to parent
/ Common Shares Outstanding
```

### PER / PBR

```text
PER = Price / EPS
PBR = Price / BVPS
Forward PER = Price / Expected EPS
```

EPS ≤ 0이면 PER는 `N/M`.

### EV

```text
Enterprise Value =
Market Cap
+ Total Debt
+ Preferred Stock
+ Minority Interest
- Cash

EV/EBITDA = EV / TTM EBITDA
EV/Sales = EV / Revenue
```


## 6. 업종별 Valuation Framework

### 반도체
- Forward PER
- EV/EBITDA
- FCF
- Capex
- ROIC
- DRAM/NAND/HBM 가격
- 재고·수율·고객 CAPEX

### 자동차
- PER
- FCF Yield
- ROE
- 자동차부문 영업이익률
- 인센티브·재고
- 금융부문 부채 분리

### 은행
- PBR
- ROE
- NIM
- 대손비용
- CET1

Justified PBR:

```text
Justified PBR = (ROE - g) / (Cost of Equity - g)
```

### 보험
- PBR
- ROE
- CSM
- K-ICS
- 손해율
- 배당

```text
Combined Ratio = Loss Ratio + Expense Ratio
```

### 해운
- Mid-cycle Earnings
- PBR
- 선대 가치
- 순현금
- FCF

피크 이익 기반 저PER 착시를 경계한다.

### 지주회사

```text
NAV =
Listed Stakes
+ Unlisted Value
+ Real Estate
+ Net Cash
- Holding Company Debt

Holding Discount = 1 - Market Cap / NAV
```

### 소비재
- PER
- PEG
- ROIC
- 마진
- 지역별 성장
- 가격전가력

```text
PEG = Forward PER / Expected EPS Growth Rate(%)
```

### EPC / 건설
- 수주잔고
- 신규수주
- Book-to-Bill
- 영업이익률
- 계약자산·미청구공사
- FCF

```text
Book-to-Bill = New Orders / Revenue
```

### SaaS / 반복매출

```text
ARR Growth = (Current ARR - Previous ARR) / Previous ARR

NRR =
Beginning Revenue + Expansion - Contraction - Churn
--------------------------------------------------
Beginning Revenue
```


## 7. Earnings Quality

단순 EPS보다 다음을 더 중요하게 본다.

- 매출 성장의 질
- 영업이익률
- 영업현금흐름
- FCF
- 재고
- 매출채권
- Capex
- 주식보상
- 일회성 이익
- 희석

경고 예:

```text
매출 증가
+ 매출채권 급증
+ FCF 악화
→ 성장의 질 의심

순이익 증가
+ 기타이익 급증
+ 영업이익 정체
→ 정상화 EPS 별도 계산 필요
```


## 8. 시장 기대와 Surprise

항상 다음을 비교한다.

```text
Actual vs Consensus vs Guidance vs Price Reaction
```

기본 Surprise:

```text
Surprise = Actual - Consensus
```

정규화:

```text
Surprise Score =
(Actual - Consensus) / Historical Surprise Std
```

좋은 실적이어도 가이던스가 약하면 Bearish일 수 있고, EPS miss라도 FCF beat와 가이던스 상향이 있으면 Bullish일 수 있다.


## 9. OHLCV Framework

### 시간축
기본:
- 일봉 500
- 주봉 300
- 월봉 100

### 지지·저항
한 점이 아니라 구간으로 본다.

### RSI
RSI는 valuation이 아니다.

```text
RSI < 30 → 과매도 가능성
RSI > 70 → 과열 가능성
```

### MACD
핵심:
- MACD level
- Histogram 방향
- 0선 회복
- 시간축 정렬

```text
MACD < 0
Histogram 상승
→ 하락 압력 둔화
```

### 거래량

```text
Volume Ratio = Current Volume / 20D Average Volume
Trading Value Ratio = Current Trading Value / 20D Average
```

해석:
- 가격 상승 + 거래량 증가 → 추세 신뢰도 상승
- 가격 상승 + 거래량 감소 → 매도 감소형 반등 가능
- 가격 하락 + 거래량 급증 → 분배/투매 가능
- 가격 하락 + 거래량 감소 → 매도 압력 둔화 가능


## 10. 손익비

롱 기준:

```text
Reward = Target - Entry
Risk = Entry - Stop
Reward/Risk = Reward / Risk
```

가이드:

```text
<1.0      추격 위험
1.0~1.5   보통 이하
1.5~2.0   조건부 가능
2.0+      양호
3.0+      매우 우수
```

성공확률을 반영하지 않은 단순 손익비임을 명시한다.

Expected Value는 실제 승률 통계가 있을 때만 사용한다.

```text
EV =
P(win) × Avg Gain
-
P(loss) × Avg Loss
```

임의 승률은 만들지 않는다.


## 11. 신규매수자와 보유자 분리

### 신규매수
- 현재 가격
- 지지까지 거리
- 저항까지 거리
- valuation
- 손익비
- 이벤트 리스크

### 보유자
- 투자 논리 유지
- 비중 관리
- 추가 매수 여부
- 멀티플 과열 여부
- Kill Condition


## 12. 가격 하락 해석

항상 구분한다.

```text
Thesis 유지 + 가격 하락
→ 기회 가능

Thesis 약화 + 가격 하락
→ Value Trap 가능
```

하락 원인 분류:
- 시장 조정
- 업종 멀티플 압축
- 회사 실적
- 고객·수주
- 경쟁
- 희석
- 회계
- 부채
- 규제


## 13. Thesis 상태

내부 상태:

```text
strengthened
no_material_change
mixed
weakened
invalidation_candidate
invalidated
needs_review
```

사용자 표현:

```text
강화
유지
혼합
초기 균열
구조적 악화
무효화 조건 접근
무효화
```


## 14. Thesis 강화·약화·Kill Condition

### 강화 조건
- 핵심 매출 성장 지속
- 마진 확대
- FCF 개선
- ROIC 개선
- 고객 다변화
- 신규 수주·양산
- 자사주·배당

### 초기 경고
- 재고 증가
- 매출채권 증가
- ASP 둔화
- 신규수주 둔화
- 가이던스 보수화
- Capex 증가 대비 매출 부진

### Kill Condition
가격 손절과 구분한다.

예:

```text
가격 무효화: 398달러 이탈

기업가치 무효화:
HPC 성장 둔화
+ GPM 55% 이하
+ FCF 급감
```


## 15. Multiple Expansion / Compression

### 확장 조건
- ROIC 상승
- 마진 상승
- 반복매출 증가
- 고객 다변화
- FCF 개선
- 재무구조 개선
- 규제 완화

### 압축 조건
- 성장 둔화
- 마진 하락
- FCF 악화
- Capex 과잉
- 고객 집중
- 금리 상승
- 희석
- 회계/규제 리스크


## 16. 거시경제 연결

거시 6축:

```text
growth_momentum
inflation_pressure
liquidity_condition
financial_conditions
risk_appetite
earnings_momentum
```

각 축은 -2 ~ +2.

0은 안정이 아니라 `강한 방향 신호 없음`.

### Macro Exposure Map

```json
{
  "factor": "us_10y_real_yield",
  "direction": "negative",
  "weight": 3,
  "channel": "discount_rate",
  "horizon": "short",
  "condition": "valuation_elevated",
  "review_required": true
}
```

주요 factor:
- us_10y_real_yield
- us_10y_yield
- usdkrw
- dollar
- wti
- credit_spread
- market_volatility
- hyperscaler_capex
- china_growth
- memory_price
- freight_rate

개념형 Macro Impact:

```text
Macro Impact =
Exposure Weight
× Shock Magnitude
× Persistence
× Confidence
```

실적 영향과 multiple 영향을 분리한다.


## 17. 금리·환율·유가 해석

### 실질금리 상승
- 장기 성장주 valuation 부정
- 은행 NIM에는 긍정 가능
- 신용비용에는 부정 가능

### 원화 약세
수출주:
- 매출 환산 긍정 가능

하지만:
- 원재료 수입비용
- 해외생산
- 외국인 자금유출
을 함께 본다.

### 유가 상승
수요 회복형과 공급 충격형을 분리한다.

수요 회복형:
- 산업재·경기민감 긍정 가능

공급 충격형:
- 물가·금리 상승
- 소비 둔화
- 항공·운송 부정


## 18. FOMC 해석

단순 금리 결정이 아니라 다음을 함께 본다.

```text
Decision
Statement
Dot Plot
SEP
Press Conference
Market Reaction
```

시장 기대는 Fed Funds Futures / OIS와 비교한다.


## 19. 빅테크 실적 전파

예:

```text
MSFT / GOOGL / AMZN CAPEX 상향
→ GPU / ASIC
→ HBM
→ Foundry
→ 반도체 장비
```

단순 연상보다 실제 전달 경로를 확인한다.


## 20. 공식 잠정실적 처리

OpenDART 잠정실적이 아래를 통과하면 사용한다.

- 문서 동일성
- 보고기간
- 단위
- semantic mapping
- hard validation

사용 가능:
- 매출
- 영업이익
- 순이익
- 영업이익률
- 최근 분기 EPS/TTM EPS
- PER

정식 재무제표가 없는 경우 임의 계산 금지:
- BVPS
- PBR
- FCF
- ROIC
- 재고
- 매출채권
- 순부채

같은 분기의 정식 재무제표가 나오면 정식 수치를 우선하고 중복 계산하지 않는다.


## 21. Valuation 비교 가능성

비교 전 확인:

```text
TTM vs NTM
GAAP vs Adjusted
Basic vs Diluted
Parent vs Consolidated
Common vs Preferred
ADR Ratio
Currency
As-of Date
```

상태:
- comparable
- not_comparable
- insufficient_metadata
- structural_conflict

비교 가능한 같은 기준에서만 데이터 충돌을 경고한다.


## 22. ADR 환산

```text
Local Share Equivalent =
ADR Price × ADR Ratio × FX
```

예:

```text
10 ADR = 1 Local
ADR = $165
USD/KRW = 1490

= 165 × 10 × 1490
= 2,458,500원
```

ADR premium:

```text
ADR Premium =
ADR Implied Local Value / Local Share Price - 1
```


## 23. 포트폴리오 관점

개별 종목뿐 아니라 공통 거시 노출을 본다.

예:

```text
반도체 비중 과다
→ Hyperscaler CAPEX concentration

항공+해운
→ Oil exposure

한국 수출주 집중
→ USD/KRW exposure
```

종목별 독립 리스크와 포트폴리오 공통 리스크를 분리한다.


## 24. 종합 점수 예시

```text
Business Quality        20
Earnings Momentum       15
Earnings Quality        15
Balance Sheet           10
Valuation               15
Market Expectations     10
OHLCV                   10
Catalyst / Risk          5
---------------------------
Total                  100
```

해석 예:
- 80+: 고품질 재검토 후보
- 65~79: 조건부 후보
- 50~64: 관찰
- 35~49: 낮은 우선순위
- <35: 신규매수 제외

점수는 절대 매수 신호가 아니다.


## 25. 최종 답변 템플릿

### 핵심 결론
- OHLCV Thesis 동의/반대
- 현재 신규매수 적합도
- 핵심 이유

### OHLCV Thesis 검토
- 가격 위치
- 지지/저항
- 거래량
- RSI/MACD
- 시간축 정렬

### 기업가치 Thesis
- 사업 구조
- 핵심 driver
- 경쟁력

### 시장 기대
- 기대 수준
- 이미 반영된 내용
- 상방/하방 surprise

### 재무제표
- 매출
- 마진
- FCF
- ROIC/ROE
- 재고
- 매출채권
- 부채
- 희석

### Earnings Quality
- 현금흐름
- 일회성
- 운전자본
- Capex

### Valuation
- 업종 적합 metric
- 현재 multiple
- 정상화 여부
- multiple expansion/compression 조건

### 차트와 기업가치 교차검증
- 같은 방향인가
- 괴리가 있는가
- 가격 하락이 기회인가 value trap인가

### 신규매수자
- 1차 구간
- 2차 구간
- 확인형
- 추격 금지
- 손익비

### 보유자
- 유지
- 관리
- 추가매수 중단
- Thesis review

### Thesis 상태
- 강화/유지/혼합/초기 균열/구조적 악화/무효화 접근/무효화

### Thesis 강화 조건
- 핵심 데이터

### Early Warning
- 초기 경고

### Kill Condition
- 구조적 무효화

### 가장 중요한 다음 숫자
- 1~3개

### 최종 한 줄


## 26. 최종 운영 철학

> 주가가 올랐다고 투자 논리가 좋아진 것도 아니고, 주가가 떨어졌다고 투자 논리가 깨진 것도 아니다.

핵심은 다음을 함께 보는 것이다.

```text
회사가 앞으로 벌 돈의 양
+ 이익의 질
+ 재무 안정성
+ 시장 기대
+ 현재 valuation
+ 현재 가격 위치
```

OHLCV는 **언제 들어갈 것인가**를 돕는다.

기업가치 분석은 **무엇을 살 것인가**를 결정한다.

Thesis-monitor는 **언제 기존 판단을 바꿔야 하는가**를 감시한다.

세 가지를 분리해서 보고 마지막에 하나의 투자 판단으로 합친다.
