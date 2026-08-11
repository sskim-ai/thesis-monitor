# Custom GPT Regression Prompts

이 문서는 Instructions·Knowledge 변경 후 신규 종목 분석 능력과 모니터링 mode 분리가 유지되는지 수동 또는 자동 평가하기 위한 prompt suite다.

## 공통 판정 기준

- 종목명·티커만 입력한 신규 분석은 최근 뉴스 요약으로 끝나지 않는다.
- bare ticker가 기존 등록 종목으로 확인되면 저장 논리와 최근 delta를 결합한 Current Thesis Review를 사용한다.
- 명시적 등록 요청이 없으면 `monitorStock`을 호출하지 않는다.
- Initial Analysis와 daily delta를 혼동하지 않는다.
- 실제 Action 응답에 없는 가격·OHLCV·고객·재무 숫자를 만들지 않는다.
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
- `getCompanyProfile`, `getEarningsCheckpoints`, 장기 `getThesisEvents` 활용
- 한국 종목이면 필요 시 `provider=opendart`, `auto_backfill=true`, `backfill_years=5`, `lookback_days=365`
- 사업 구조, 산업, 재무·이익의 질, 시장 기대, Valuation, 리스크와 다음 숫자 분석
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
- 광고와 Cloud 등 segment economics, AI Capex와 FCF·ROIC, 시장 기대와 Valuation 분석
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
- `monitorStock` 호출 금지

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

public Action 응답에 가격·OHLCV 자료가 없다.

**Expected**

- 가격 자료가 이번 조회에서 확보되지 않았다고 밝힘
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

## Action Contract Check

Instructions와 Knowledge에서 호출 대상으로 쓰는 이름은 Action schema의 operationId와 일치해야 한다.

필수 확인:

- `getThesisEvents`
- `getCompanyProfile`
- `getEarningsCheckpoints`
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

직접 OHLCV 조회 Action은 현재 contract에 없으므로 존재한다고 가정하면 실패다.
