# Custom GPT Regression Prompts

이 문서는 Instructions·Knowledge 변경 후 신규 종목 분석 능력과 모니터링 mode 분리가 유지되는지 수동 또는 자동 평가하기 위한 prompt suite다.

## 공통 판정 기준

- 종목명·티커만 입력한 신규 분석은 최근 뉴스 요약으로 끝나지 않는다.
- bare ticker가 기존 등록 종목으로 확인되면 저장 논리와 최근 delta를 결합한 Current Thesis Review를 사용한다.
- 명시적 등록 요청이 없으면 `monitorStock`을 호출하지 않는다.
- Initial Analysis와 daily delta를 혼동하지 않는다.
- `getTickerAnalysisSnapshot`에 없는 가격·OHLCV·고객·재무 숫자를 만들지 않는다.
- `price.currency`와 `earnings.financial_currency`를 구분하고, `window_return_pct`를 1일·1주·1개월 수익률로 오해하지 않는다.
- Fact, Interpretation과 Unknown을 구분한다.
- 업종에 맞는 재무·Valuation framework를 사용한다.
- 사용자 답변에는 provider·parser·comparability 같은 내부 flag를 기본 노출하지 않는다.

## 1. Bare Korean Ticker

**Prompt**

```text
005930
```

**Expected**

- Mode A: Initial Thesis Analysis
- `getCompanyProfile`, `getEarningsCheckpoints`, 장기 `getThesisEvents`, `getTickerAnalysisSnapshot` 활용
- 한국 종목이면 필요 시 `provider=opendart`, `auto_backfill=true`, `backfill_years=5`, `lookback_days=365`
- 사업 구조, 산업, 재무·이익의 질, 시장 기대, Valuation, 리스크와 다음 숫자 분석
- snapshot의 현재 가격, 최신 earnings context, 가능한 PER/PBR/fPER/fPBR과 역사적 위치 반영
- `daily.actual_count=500`, `daily.window_return_pct=35.0`이면 `500개 일봉 window 기준 약 +35%`로 해석하며 `일간 +35%`라고 쓰지 않음
- `price.supply.available=true`이면 실제 기준일의 수급을 가격과 분리된 단기 포지셔닝으로 해석
- `monitorStock` 호출 금지

**Failure**

- 최근 이벤트 몇 건만 요약
- 자동 모니터링 등록

## 2. Bare US Ticker

**Prompt**

```text
GOOGL
```

**Expected**

- Mode A: Initial Thesis Analysis
- `getTickerAnalysisSnapshot` 사용
- 광고와 Cloud 등 segment economics, AI Capex와 FCF·ROIC, 시장 기대와 Valuation 분석
- 가능한 현재 가격, PER/PBR/fPER과 역사적 Valuation 위치 반영
- `price.supply.available=false`이면 빈 수급 자료 없음 섹션을 만들지 않음
- 최근 뉴스 3개 요약으로 끝나지 않음

## 3. Explicit Initial Analysis

**Prompt**

```text
TSMC 투자 논리 분석해줘
```

**Expected**

- 사업 구조, 고객·기술 위치, 산업 cycle, 재무와 이익의 질
- 시장 기대, 핵심 투자 논리, 업종 적합 Valuation, 촉매와 리스크
- ADR/share-class 정보가 불명확하면 per-share 계산 보류
- Early Warning, Kill Condition과 다음 확인 숫자

## 4. Daily Monitoring

**Prompt**

```text
TSLA 오늘 점검해줘
```

**Expected**

- Mode C: Daily Monitoring
- 최근 delta, 열린 warning, 이익 추정치·Valuation 변화와 가격 관리 중심
- full Initial Thesis Analysis를 매일 반복하지 않음

## 5. Existing Stock Full Review

**Prompt**

```text
SK하이닉스 지금 전체적으로 다시 봐줘
```

**Expected**

- Mode B: Current Thesis Review
- 저장된 핵심 투자 논리의 절대 상태와 최근 delta를 결합
- 현재 기대, 잠정실적을 포함한 재무 context, Valuation, warning과 가격 상태 검토
- `no_material_change` 한 줄로 끝나지 않음

## 6. Start Monitoring

**Prompt**

```text
IBM 분석하고 앞으로 모니터링해줘
```

**Expected**

- Mode A 분석을 먼저 수행
- `getTickerAnalysisSnapshot`으로 등록 전 객관적 가격·실적·Valuation 확인
- 핵심 논리, 검증 지표, 기대, Valuation framework, 강화·약화·무효화 조건과 중요한 거시 노출 구성
- 이후 `monitorStock` 호출
- 저장 ticker와 version 안내

**Failure**

- 분석 없이 바로 등록

## 7. Read-only Analysis

**Prompt**

```text
IBM 분석해줘
```

**Expected**

- Mode A 분석
- `getTickerAnalysisSnapshot` 사용 가능
- `monitorStock` 호출 금지
- `InvestmentThesis`, `ThesisAssessment`, notification 생성 금지

## 8. Specific Event

**Prompt**

```text
POSCO홀딩스 최근 실적 공시 어떻게 봐?
```

**Expected**

- Mode D: Event Analysis
- 해당 공시의 기간·단위·공식 잠정실적 여부와 확인된 숫자 검토
- 기존 투자 논리, 기대, 이익 추정치와 Valuation 영향 평가
- 전체 Initial Thesis template을 억지로 출력하지 않음

## 9. Macro Analysis

**Prompt**

```text
오늘 금리 환경이 반도체에 어떤 영향이야?
```

**Expected**

- Mode E: Macro Analysis
- `getMacroBriefing`, `getMacroRegime`과 필요한 macro Action 활용
- 실질금리의 할인율 영향과 반도체 수요·CAPEX 전달 경로 구분
- 특정 회사의 신규 Initial Analysis로 전환하지 않음

## 10. OHLCV Unavailable

**Prompt**

```text
GOOGL 차트까지 봐줘
```

**Fixture**

`getTickerAnalysisSnapshot`의 가격 공급자가 실패해 `price.available=false`이고 raw OHLCV 자료가 없다.

**Expected**

- 가격 자료가 이번 조회에서 확보되지 않았다고 밝힘
- 가격 실패와 무관하게 가능한 earnings·Valuation 결과는 계속 사용
- RSI, MACD, 지지·저항, 목표가와 손절가를 생성하지 않음
- 기업 분석은 확보된 자료 범위에서 계속 수행 가능

## 11. Biotech

**Prompt**

```text
RXRX 분석해줘
```

**Expected**

- Mode A
- rNPV, 임상 stage·milestone, 성공확률, cash runway, partnership economics와 dilution 중심
- 상업화 전 상태에서 PER를 primary metric으로 사용하지 않음

## 12. Insurance

**Prompt**

```text
코리안리 분석해줘
```

**Expected**

- Mode A
- P/B-ROE, combined ratio, 재보험 요율 cycle, 대형재해 손실, 투자수익, 자본적정성과 배당 중심
- 일반 제조기업의 순차입금·PER template을 기계적으로 적용하지 않음

## 13. Memory Semiconductor

**Prompt**

```text
Micron 분석해줘
```

**Expected**

- Mode A
- cycle-adjusted earnings, ASP, HBM·DRAM, 재고, Capex, FCF와 PBR 중심
- 피크 이익의 낮은 PER만으로 저평가 결론을 내리지 않음

## 14. Price Decline Diagnosis

**Prompt**

```text
이 종목이 20% 빠졌는데 기회야?
```

**Expected**

- 종목 식별과 실제 가격·사건 자료 확인
- `투자 논리 유지 + 가격 하락`과 `투자 논리 약화 + 가격 하락` 구분
- 시장, 업종 multiple, 실적, 고객·주문, 경쟁, 희석, 회계, 부채와 규제로 원인 분해
- 실제 Entry·Target·Stop이 없으면 손익비를 만들지 않음

## 15. Unknown Data

**Prompt**

```text
이 회사 핵심 고객 비중이랑 신제품 수율까지 반영해서 분석해줘
```

**Fixture**

Action 응답에 고객 비중과 수율이 없다.

**Expected**

- 값을 추정해 채우지 않음
- Unknown으로 남기고 중요성과 확인할 자료 설명
- 미확인 값을 투자 논리 강화 근거로 사용하지 않음

## 16. Portfolio Exposure

**Prompt**

```text
SK하이닉스, 삼성전자, Micron을 같이 들고 있는데 공통 위험을 봐줘
```

**Expected**

- 개별 기업 위험과 공통 memory cycle·Hyperscaler CAPEX·고객 집중·환율 노출 구분
- 종목별 분석을 단순 합산하지 않음

## Snapshot Currency / Window Semantics

**Prompt**

```text
TSM 분석해줘
```

**Fixture**

- `price.currency=USD`
- `earnings.financial_currency=TWD`
- `daily.actual_count=500`
- `daily.window_return_pct=42.0`
- `daily.range_position_pct=90.0`

**Expected**

- 거래 가격은 USD, earnings 금액은 TWD 기준으로 해석
- 두 통화를 자동 동일시하거나 임의 환산하지 않음
- 수익률은 `500개 일봉 window 기준 +42%`로 해석
- 범위 위치는 같은 500개 일봉 window의 고가·저가 범위 기준으로 해석

**Failure**

- earnings 금액에 USD를 붙임
- `오늘 +42%`, `1일 수익률 +42%`로 표현
- `range_position_pct`를 오늘 하루 범위로 표현

## ADR Per-Share Basis Safety

**Prompt**

```text
TSM 분석해줘
```

**Fixture**

- `price.currency=USD`
- `earnings.financial_currency=TWD`
- 최신 공식 SEC foreign preliminary에 매출·영업이익·영업이익률이 존재
- 최신 Q2 EPS는 `USD 4.31/ADR`로 current-security basis가 확인됨
- 이전 3개 분기 EPS는 security basis가 불충분
- `valuation.ttm_eps=null`, derived PER denominator 없음
- 공급자 PER/fPER가 있으면 reference multiple로만 존재 가능

**Expected**

- 매출·영업이익 earnings context는 사용 가능
- 최신 earnings period와 영업이익률은 official foreign preliminary를 반영
- local-currency EPS와 USD per ADR/ADS EPS가 함께 있으면 현재 거래 ADR에 직접 대응하는 USD EPS를 우선
- structured table의 현재 분기 exact operating income을 margin 역산값보다 우선하고, 공시 margin은 그대로 유지
- 최신 direct ADR EPS 한 분기만으로 4분기 TTM EPS나 PER를 생성하지 않음
- 최신 분기 EPS는 확인됐지만 이전 분기 기준이 불충분해 TTM EPS/PER 자체 계산을 보류했다고 설명
- unsafe raw EPS로 USD/ADR 가격의 PER를 직접 계산하지 않음
- denominator가 `null`이면 GPT가 raw earnings로 재계산하지 않음
- 공급자 fPER는 derived fPER가 없어도 provenance를 유지하고, denominator를 역산하지 않은 참고값으로 표시 가능
- 단순 `Net Income`을 common/parent 귀속 이익으로 간주하지 않음
- `최근 분기 주당 실적은 확인했지만 이전 분기들의 주당 기준을 확인하지 못해 TTM EPS/PER 자체 계산을 보류했습니다.` 또는 같은 의미의 주의를 한 줄로 표시
- `monitorStock` 자동 호출 금지

**Failure**

- ADR ratio 존재만으로 EPS/BVPS에 일괄 적용
- TWD ordinary-share EPS를 USD ADR 가격과 직접 나눔
- provider PER와 price로 EPS를 역산
- 최신 Q2 주당 기준도 확인하지 못했다고 잘못 설명

## Korean Investor Supply Context

**Prompt**

```text
005930 오늘 점검해줘
```

**Fixture**

- 외국인·기관 20일 누적 순매도, 개인 20일 누적 순매수
- `supply_quality=distribution`
- `supply_primary_signal=foreign_exit_retail_absorption`

**Expected**

- 외국인·기관 매도와 개인 흡수를 단기 수급·포지셔닝 context로 설명
- 실제 수급 기준일을 표시하고 stale 수급을 오늘 수급이라고 표현하지 않음
- 수급만으로 삼성전자의 투자 논리가 약화됐다고 판단하지 않음

**Failure**

- 수급 점수만으로 사업 논리·이익 추정·Valuation·warning을 변경
- 알려지지 않은 enum을 snake_case 그대로 사용자에게 노출

## Korean Initial Analysis With Supply

**Prompt**

```text
005930 분석해줘
```

**Fixture**

- 현재 monitored stock이 아님
- `getTickerAnalysisSnapshot.price.supply.available=true`
- `price.supply.as_of_date`는 실제 latest daily bar 날짜
- 외국인·기관 20일 누적 순매도, 개인 20일 누적 순매수
- `price.supply.quality=distribution`
- `price.supply.primary_signal=foreign_exit_retail_absorption`

**Expected**

- Mode A: Initial Thesis Analysis
- `getCompanyProfile`, `getEarningsCheckpoints`, `getThesisEvents`, `getTickerAnalysisSnapshot` 사용
- 사업 구조, 산업 포지셔닝, 재무·이익의 질, 시장 기대, 핵심 투자 논리, Valuation, 촉매, 리스크, Early Warning/Kill Condition, Macro exposure, 가격·수급/포지셔닝과 다음 확인 숫자를 포함
- 최근 20일 외국인·기관 매도와 개인 흡수를 진입 시점의 단기 수급 부담으로 해석
- 수급을 기업 fundamental 투자 논리의 약화 근거로 사용하지 않음
- `monitorStock` 호출 금지

**Failure**

- Daily Monitoring 또는 Current Review로 routing
- 최근 뉴스나 수급 요약으로만 끝남
- 외국인 순매도를 이유로 투자 논리를 `weakened`로 변경
- 자동 monitoring 등록

**Prompt**

```text
005930 분석하고 앞으로 모니터링해줘
```

**Expected**

- 위 Initial Analysis와 가격·수급/포지셔닝 해석을 먼저 수행
- 투자 논리, 검증 지표, 기대와 Valuation framework를 만든 뒤 마지막에만 `monitorStock` 호출
- `getTickerAnalysisSnapshot` 자체가 등록 side effect를 만들지 않음

## Action Contract Check

Instructions와 Knowledge에서 호출 대상으로 쓰는 이름은 Action schema의 operationId와 일치해야 한다.

필수 확인:

- `getThesisEvents`
- `getCompanyProfile`
- `getEarningsCheckpoints`
- `getTickerAnalysisSnapshot`
- `getMonitoredStock`
- `monitorStock`
- `getThesisAssessmentHistory`
- `listMonitoredStockSummaries`
- `stopMonitoringStock`
- `getMacroBriefing`
- `getMacroBriefingByDate`
- `getMacroRegime`
- `getMacroTheses`
- `getMacroEvents`
- `getTickerMacroImpacts`
- `getMacroProviderStatus`

`getTickerAnalysisSnapshot`은 compact 가격·실적·Valuation 조회이며 raw OHLCV Action이 아니다. 응답에 없는 RSI·MACD와 개별 bar가 있다고 가정하면 실패다.
