# Macro Thesis Monitoring System Design v2.0

## 0. 설계 요약

이 문서는 기존 `thesis-monitor`를 종목별 공시·뉴스 감시에서 거시경제 Thesis 감시까지 확장하기 위한 구현 설계다. 핵심은 금리, 환율, 유가, 야간선물, FOMC, 경제지표, 빅테크 실적을 단순 요약하는 것이 아니라, 현재 시장이 무엇을 기대하고 있었는지와 실제 결과가 어떻게 달랐는지, 그 차이를 시장이 어떻게 가격에 반영했는지, 그리고 그 변화가 보유 종목과 섹터의 투자 Thesis 및 valuation에 어떤 영향을 주는지를 연결하는 것이다.

전체 처리 순서는 다음과 같다.

```text
원천 데이터 수집
  -> 시계열·이벤트 정규화
  -> 데이터 품질 및 최신성 검증
  -> 시장 기대와 실제 결과 비교
  -> 거시 충격 유형 분류
  -> 시장 반응 교차검증
  -> 거시 레짐 및 Macro Thesis 갱신
  -> 종목·섹터·포트폴리오 exposure 연결
  -> Thesis 영향과 valuation 영향 평가
  -> 오전 브리핑 및 중요 이벤트 알림
```

이 설계에서 가장 중요한 보완점은 다음 여섯 가지다.

1. `거시 레짐`과 별개로 `Macro Thesis`를 일급 객체로 관리한다.
2. `실제 발표값`뿐 아니라 `시장 기대`, `사전 가격 반영`, `발표 후 반응`을 별도로 저장한다.
3. 같은 유가 상승이라도 수요 충격인지 공급 충격인지 구분한 뒤 종목별 영향을 계산한다.
4. 장중 첫 반응, 정규장 종가, 다음 날 한국 시장 반응을 분리해 저장한다.
5. 거시 이벤트가 종목뿐 아니라 섹터와 전체 포트폴리오에 미치는 집중 위험을 계산한다.
6. 모든 판단은 `Fact -> 시장 기대 -> 투자적 해석 -> Thesis 변화 -> Valuation 영향` 순서로 출력한다.

---

## 1. 목적

`thesis-monitor`가 종목별 뉴스와 공시뿐 아니라 금리, 환율, 원자재, 야간선물, 경제지표, 중앙은행 정책, 재정정책, 지정학, 빅테크 실적 등 거시 환경을 매일 평가하도록 확장한다.

시스템의 목적은 다음 질문에 답하는 것이다.

- 현재 시장은 성장, 물가, 유동성, 위험선호 중 무엇을 가장 중요하게 가격에 반영하고 있는가?
- 발표된 지표가 시장 기대보다 실제로 강했는가, 약했는가?
- 좋은 지표인데 주가가 약하거나 나쁜 지표인데 주가가 강한 이유는 무엇인가?
- 금리, 달러, 유가, 신용스프레드, 변동성이 동시에 어떤 방향을 가리키는가?
- 현재 거시 변화가 어떤 종목에는 긍정적이고 다른 종목에는 부정적인 이유는 무엇인가?
- 기존 종목 Thesis가 강화, 유지, 초기 균열, 구조적 악화 중 어디에 있는가?
- 같은 거시 이벤트가 실적 추정치와 적정 valuation multiple에 각각 어떤 영향을 주는가?

핵심 원칙은 거시 정보를 보편적인 호재 또는 악재로 분류하지 않는 것이다. 같은 유가 상승도 공급 차질에 따른 상승인지 수요 회복에 따른 상승인지에 따라 시장과 종목의 영향이 달라진다. 모든 방향 평가는 충격의 원인, 전달 경로, 지속 기간, 종목별 exposure를 기준으로 수행한다.

---

## 2. 설계 원칙

### 2.1 사실과 추론을 분리한다

모든 데이터와 이벤트는 아래 세 항목으로 나눈다.

- `confirmed_facts`: 공식 원문과 시세 데이터에서 확인된 사실
- `inferred_implications`: 규칙 또는 모델 기반 해석
- `unknowns`: 아직 확인되지 않았거나 추가 검증이 필요한 변수

확인되지 않은 내용은 반드시 `추정`으로 표시한다.

### 2.2 시장 기대를 별도로 관리한다

거시 이벤트는 실제 값만으로 해석하지 않는다. CPI가 전월보다 낮아도 시장 컨센서스보다 높으면 매파적 충격일 수 있다. FOMC가 금리를 동결해도 동결이 이미 100% 반영됐다면 핵심은 성명서, 점도표, 기자회견, 향후 금리경로 변화다.

따라서 다음 네 가지를 분리한다.

```text
사전 시장 기대
실제 발표 결과
발표 직후 가격 반응
하루 및 다음 시장까지의 지속 반응
```

### 2.3 가격과 Thesis를 분리한다

주가와 선물이 하락해도 거시 Thesis가 유지되면 단순 변동성 또는 멀티플 압축으로 분류한다. 반대로 시장이 상승해도 실적 추정치와 FCF가 악화되면 Thesis 강화로 보지 않는다.

### 2.4 레짐과 개별 Thesis를 분리한다

`MacroRegimeAssessment`는 전체 시장 환경을 요약한다. `MacroThesis`는 특정 거시 논리를 감시한다.

예시:

- 레짐: 성장 둔화 / 물가 완화 / 유동성 중립 / 위험선호 약화
- Thesis: “미국은 침체 없이 디스인플레이션이 진행돼 연준이 완만하게 완화할 수 있다.”
- 반대 Thesis: “AI 투자와 재정지출이 수요를 지탱해 장기금리가 높은 수준에 고착된다.”

서로 경쟁하는 Thesis를 동시에 저장할 수 있어야 한다.

### 2.5 이벤트 하나로 구조적 결론을 내리지 않는다

단일 CPI, 단일 고용지표, 하루의 유가 급등만으로 거시 Thesis를 자동 무효화하지 않는다. 반복성, 지속성, 다른 지표와의 일관성, 시장 반응을 함께 확인한다.

### 2.6 종목별 전달 경로를 명시한다

거시 변화는 아래 채널을 통해 종목에 전달된다.

- `demand`: 최종 수요와 판매량
- `pricing`: 가격전가력과 ASP
- `cost`: 원재료·인건비·운송비
- `fx`: 환율 환산과 수출채산성
- `discount_rate`: 금리와 valuation multiple
- `funding`: 차입비용과 유동성
- `inventory`: 재고평가와 재고조정
- `capex`: 고객 또는 자사의 투자주기
- `policy`: 규제, 보조금, 관세, 수출통제
- `positioning`: 수급, 옵션, 숏커버
- `counterparty`: 고객·금융기관·국가 신용위험

---

## 3. 범위

### 3.1 포함 범위

- 미국 증시와 주요 업종의 간밤 성과
- 미국 및 한국 금리와 수익률곡선
- 실질금리, 기대인플레이션, 금리경로 기대
- 달러, 원화, 엔화, 위안화 등 주요 환율
- 유가, 천연가스, 금, 구리, 철광석, 석탄, LNG 등 원자재
- KRX 야간시장 선물과 한국 개장 전 지표
- 미국, 한국, 중국, 유럽, 일본의 주요 경제지표
- FOMC, 연준 발언, 한국은행, ECB, BOJ 정책
- 미국 재정, 국채발행, 관세, 수출규제, 제재, 지정학
- VIX, MOVE, 신용스프레드, 변동성 기간구조
- 미국 빅테크, 반도체, 금융, 소비재 주요 기업 실적
- hyperscaler CAPEX와 AI 인프라 수요
- 종목 및 섹터별 거시 exposure
- 포트폴리오 전체의 거시 집중 위험
- 오전 8시 카카오톡 브리핑
- 중요 이벤트 발표 전 사전 알림과 발표 후 이벤트 알림
- 과거 이벤트 replay와 threshold 백테스트

### 3.2 1차 구현에서 제외할 범위

- 주문 실행과 자동 매매
- 초단타용 실시간 틱 데이터
- 거시 이벤트 하나만으로 종목 Thesis 자동 무효화
- 근거 없는 범용 뉴스 감성 점수
- 유료 컨센서스가 없을 때 임의의 시장 예상치 생성
- LLM만으로 원인과 결과를 확정하는 자동 인과추론
- 출처가 불명확한 소셜미디어 루머

---

## 4. 시스템 경계와 모듈 구조

기존 종목 이벤트와 거시 이벤트는 별도 도메인으로 유지하되, `impact` 계층에서 연결한다.

```text
app/providers/*                       종목 뉴스, 공시, IR
app/services/ohlcv_client.py          종목 가격 문맥

app/macro/providers/*                 거시 데이터 수집
app/macro/models.py                   관측값, 이벤트, 기대, 반응, Thesis
app/macro/calendar.py                 거래일·발표일·시간대 정규화
app/macro/quality.py                  최신성, 누락, 상충, revision 검증
app/macro/expectations.py             컨센서스·시장내재 기대
app/macro/shocks.py                   성장·물가·공급·정책 충격 분류
app/macro/reactions.py                이벤트 윈도우 시장 반응
app/macro/regime.py                   레짐 평가
app/macro/theses.py                   Macro Thesis 상태 업데이트
app/macro/exposure.py                 종목·섹터 exposure
app/macro/impact.py                   종목 및 포트폴리오 영향 계산
app/macro/briefing.py                 오전 및 이벤트 브리핑
app/macro/alerts.py                   우선순위, 중복 제거, cooldown
app/macro/replay.py                   과거 이벤트 재생과 백테스트
app/jobs/monitor_macro.py             예약 실행 진입점
```

`ohlcv-analyst`는 개별 주식과 ETF의 일봉·주봉·월봉 분석에 계속 사용한다. 금리, 경제지표, 원자재, 지수, 선물은 거시 provider가 수집한다. 향후 `ohlcv-analyst`가 선물과 지수를 안정적으로 지원하면 시장 가격 호출만 위임할 수 있다.

---

## 5. 핵심 데이터 모델

### 5.1 MacroThesis

거시 논리를 일급 객체로 저장한다.

```text
id
thesis_key
title
description
region
horizon                 short / medium / long
status                  strengthening / intact / weakening / structural_break
confidence              0.0 .. 1.0
base_case_probability   0.0 .. 1.0
bull_case
base_case
bear_case
expected_evidence
weakening_evidence
kill_conditions
valuation_channels
affected_assets
started_at
last_reviewed_at
version
created_at
updated_at
```

예시:

```json
{
  "thesis_key": "us_soft_landing_disinflation",
  "title": "미국 연착륙과 점진적 디스인플레이션",
  "horizon": "medium",
  "status": "intact",
  "confidence": 0.64,
  "expected_evidence": [
    "근원 서비스 물가 둔화",
    "실업률의 완만한 상승",
    "신용스프레드 안정",
    "기업이익 추정치 유지"
  ],
  "weakening_evidence": [
    "임금과 서비스 물가 재가속",
    "실업률 급등",
    "하이일드 스프레드 급등"
  ],
  "kill_conditions": [
    "3개월 평균 비농업고용 급감과 실업률 급등이 동시에 발생",
    "근원 PCE의 3개월 연율이 지속적으로 재가속"
  ]
}
```

### 5.2 MacroThesisEvidence

관측값과 이벤트가 특정 Macro Thesis를 강화하거나 약화한 기록이다.

```text
id
macro_thesis_id
observation_id
event_id
direction               strengthen / weaken / mixed / neutral
weight                  1 .. 5
persistence             temporary / cyclical / structural
confidence              0.0 .. 1.0
half_life_days
rationale
created_at
```

`half_life_days`는 오래된 증거의 영향력을 점진적으로 줄이는 데 사용한다.

### 5.3 MacroObservation

금리, 환율, 지수, 원자재, 스프레드 등 수치형 시계열을 저장한다.

```text
id
series_code
category
provider
observed_at
market_session
value
unit
frequency
previous_value
change_value
change_pct
zscore_20d
zscore_1y
source_url
retrieved_at
vintage_at
is_preliminary
is_revised
quality_status
raw_payload
```

중복 방지 키:

```text
series_code + observed_at + provider + vintage_at
```

수정 발표가 있는 경제지표는 기존 값을 덮어쓰지 않고 새로운 `vintage_at`으로 보존한다.

### 5.4 MacroEvent

경제지표 발표, 정책 결정, 실적, 규제, 지정학 이벤트를 저장한다.

```text
id
event_key
event_type
category
title
country
region
scheduled_at
released_at
event_status            scheduled / released / revised / cancelled
actual
consensus
previous
revised_previous
unit
surprise_value
surprise_score
impact_level
confirmed_facts
inferred_implications
unknowns
provider
source_url
source_reliability
retrieved_at
```

### 5.5 MacroExpectationSnapshot

이벤트 직전 시장 기대를 저장한다.

```text
id
event_key
captured_at
expectation_type        survey / market_implied / model_nowcast
expected_value
expected_range_low
expected_range_high
probability_distribution
source
source_url
confidence
```

예시:

- CPI 컨센서스
- 연방기금 선물 또는 OIS에 반영된 금리 경로
- 국채 입찰 예상 응찰률
- 빅테크 매출·EPS·CAPEX 컨센서스
- 원유 재고 예상치
- 한국은행 금리 동결 또는 인하 확률

서베이 컨센서스와 시장내재 기대는 동일하지 않을 수 있으므로 별도 저장한다.

### 5.6 MacroMarketReaction

발표 후 시장 반응을 이벤트 윈도우별로 저장한다.

```text
id
event_id
asset_code
reaction_window         pre_5m / post_5m / post_30m / close / next_open / next_close
price_before
price_after
return_pct
yield_change_bp
volume_ratio
volatility_change
direction
is_reversal
retrieved_at
```

실적 발표와 FOMC는 첫 반응이 컨퍼런스콜 또는 기자회견 후 뒤집힐 수 있으므로 `is_reversal`을 저장한다.

### 5.7 MacroShockAssessment

관측값과 이벤트가 어떤 종류의 충격인지 저장한다.

```text
id
assessment_date
event_id
shock_type
direction
magnitude               1 .. 5
persistence             temporary / cyclical / structural
confidence
evidence
```

`shock_type` 예시:

- `growth_positive`
- `growth_negative`
- `demand_inflation`
- `supply_inflation`
- `disinflation`
- `monetary_tightening`
- `monetary_easing`
- `fiscal_expansion`
- `fiscal_tightening`
- `liquidity_injection`
- `liquidity_drain`
- `credit_stress`
- `geopolitical_supply_shock`
- `trade_restriction`
- `technology_capex_acceleration`
- `technology_capex_slowdown`

### 5.8 MacroRegimeAssessment

거시 환경을 여섯 축으로 평가한다.

```text
assessment_date
growth_momentum         -2 .. +2
inflation_pressure      -2 .. +2
liquidity_condition     -2 .. +2
financial_conditions    -2 .. +2
risk_appetite           -2 .. +2
earnings_momentum       -2 .. +2
regime_label
confidence              0.0 .. 1.0
persistence_days
summary
evidence
created_at
```

- `growth_momentum`: 경기와 수요의 개선 또는 둔화
- `inflation_pressure`: 물가 압력의 상승 또는 하락
- `liquidity_condition`: 중앙은행·재정·달러 유동성
- `financial_conditions`: 실질금리, 신용스프레드, 대출 여건
- `risk_appetite`: 주식, 변동성, 시장 폭, 크레딧
- `earnings_momentum`: 기업이익 추정치와 가이던스 방향

`regime_label` 예시:

- 골디락스
- 리플레이션
- 스태그플레이션
- 디스인플레이션 둔화
- 경기침체
- 유동성 주도 위험선호
- 정책충격
- 혼합 또는 판단유보

### 5.9 ThesisMacroExposure

투자 Thesis 버전마다 거시 변수에 대한 민감도를 저장한다.

```json
{
  "ticker": "000660",
  "thesis_version": 2,
  "exposures": [
    {
      "factor": "us_10y_real_yield",
      "direction": "negative",
      "weight": 2,
      "channel": "discount_rate",
      "horizon": "short"
    },
    {
      "factor": "hyperscaler_capex",
      "direction": "positive",
      "weight": 5,
      "channel": "demand",
      "horizon": "medium"
    },
    {
      "factor": "usdkrw",
      "direction": "positive",
      "weight": 2,
      "channel": "fx",
      "condition": "export_volume_stable"
    }
  ]
}
```

`condition`을 두는 이유는 환율 상승이 모든 수출주에 무조건 긍정적이지 않기 때문이다. 수요 둔화, 원재료비 상승, 해외생산 비중에 따라 효과가 달라질 수 있다.

### 5.10 SectorMacroExposure

종목 exposure가 아직 없을 때 사용할 섹터 기본값이다.

```text
sector_code
factor
direction
weight
channel
conditions
default_horizon
version
```

예시:

- 항공: 유가 상승 부정, 원화 약세 부정, 여객수요 증가 긍정
- 정유: 유가 방향보다 정제마진과 재고평가 영향이 중요
- 은행: 장단기 스프레드와 대손비용의 상호작용
- 반도체: hyperscaler CAPEX, 재고, 실질금리, 수출통제
- 해운: 운임지수, 선복 공급, 중국 수요, 유가

### 5.11 ThesisMacroImpact

거시 변화가 특정 종목의 Thesis에 미친 영향을 저장한다.

```text
ticker
thesis_version
assessment_date
macro_event_id
macro_thesis_id
direction               strengthen / weaken / mixed / neutral
magnitude               1 .. 5
persistence             temporary / cyclical / structural
confidence              0.0 .. 1.0
channels
affected_thesis_pillars
earnings_estimate_effect
valuation_multiple_effect
rationale
evidence
unknowns
```

`earnings_estimate_effect`와 `valuation_multiple_effect`를 분리한다. 예를 들어 장기금리 상승은 이익 추정치에는 영향이 작지만 고PER 성장주의 valuation multiple을 압축할 수 있다.

### 5.12 PortfolioMacroImpact

모니터링 종목 전체의 거시 집중도를 저장한다.

```text
assessment_date
portfolio_id
factor
gross_exposure
net_exposure
top_contributors
concentration_score
stress_scenario_loss
confidence
```

예시:

- 원화 약세에 양의 exposure가 과도한지
- 유가 상승에 항공·운송 비중이 과도한지
- 미국 장기 실질금리 상승에 성장주 비중이 과도한지
- 중국 경기 둔화에 소재·해운·산업재가 동시에 노출돼 있는지

### 5.13 DataQualityStatus

각 데이터의 신뢰도와 최신성을 관리한다.

```text
provider
series_code
checked_at
status                  ok / stale / missing / conflicted / revised
last_observed_at
expected_frequency
staleness_seconds
source_count
conflict_detail
fallback_used
```

### 5.14 MacroBriefing

브리핑과 발송 상태를 저장한다.

```text
briefing_date
run_type                morning / event / intraday / close
as_of
headline
market_summary
regime_summary
macro_thesis_changes
today_calendar
ticker_impacts
portfolio_risks
data_quality_notes
kakao_text
status
dedupe_key
created_at
```

---

## 6. 수집 대상

### 6.1 간밤 미국 시장

#### 지수와 업종

- S&P 500, Nasdaq 100, Russell 2000
- SPY, QQQ, IWM
- SOXX 또는 SMH
- XLF, XLE, XLV, XLY, XLI, XLP, XLU
- 동일가중 지수와 시가총액 가중 지수
- 주요 팩터 ETF: 성장, 가치, 모멘텀, 저변동성

#### 변동성과 시장 폭

- VIX 현물과 선물 기간구조
- MOVE
- SKEW
- 상승·하락 종목 수
- 52주 신고가·신저가
- 20일·50일·200일 이동평균 상회 종목 비율
- 옵션 거래량과 put/call 비율
- 대형주 집중도와 동일가중 대비 성과

#### 빅테크와 반도체

- NVDA, MSFT, AAPL, GOOGL, AMZN, META, TSLA, AVGO, TSM
- 주요 반도체 장비와 메모리 관련 종목
- 정규장과 시간외 수익률
- 발표 전 종가, 발표 직후, 컨퍼런스콜 후, 다음 날 종가를 분리

### 6.2 금리와 유동성

#### 금리

- 미국 3개월, 2년, 5년, 10년, 30년 국채금리
- 미국 5년 및 10년 실질금리
- 2년-10년, 3개월-10년, 5년-30년 금리차
- SOFR와 연방기금금리
- 기대인플레이션
- 금리 스왑과 OIS 기반 정책경로
- 국채 입찰 결과와 tail, bid-to-cover, 간접응찰 비중

#### 유동성

- 연준 총자산
- 은행 지급준비금
- 재무부 일반계정
- 역레포 잔액
- 머니마켓펀드 자산
- 달러 인덱스와 달러 조달 스트레스
- 주요 크로스커런시 베이시스
- 미국 국채 변동성과 repo stress 지표

### 6.3 신용과 금융여건

- 미국 투자등급 및 하이일드 스프레드
- CDX IG와 HY
- 금융조건지수
- 은행 대출기준과 대출증가율
- 회사채 발행량과 발행금리
- 기업 부도율과 연체율
- 미국 지역은행 또는 금융섹터 스트레스 지표

신용스프레드는 주식지수보다 경기와 유동성 악화를 먼저 반영할 수 있으므로 별도 축으로 관리한다.

### 6.4 환율과 원자재

#### 환율

- DXY
- USD/KRW
- USD/JPY
- EUR/USD
- USD/CNH
- 원화 NDF와 정규장 환율 차이
- 주요 통화 변동성과 carry 지표

#### 에너지

- WTI, Brent
- 천연가스
- LNG 벤치마크
- 원유 선물 기간구조와 calendar spread
- 미국 원유·휘발유·정제유 재고
- 원유 생산량과 정제 가동률
- 정제마진

#### 산업 원자재와 농산물

- 금, 은
- 구리
- 철광석
- 원료탄과 발전용 석탄
- 알루미늄
- 밀, 옥수수, 대두
- 운송과 식품 종목 exposure에 필요한 경우 설탕, 코코아, 팜유

원자재는 가격 방향뿐 아니라 `수요 충격`, `공급 충격`, `재고 변화`, `기간구조`를 함께 본다.

### 6.5 한국 개장 전 시장

- KOSPI200 야간선물
- KOSDAQ150 야간선물
- 미국 달러 선물
- 3년 및 10년 국채선물
- EWY 또는 MSCI Korea
- 한국 관련 미국 상장 종목
- 미국 반도체 ETF
- 원화 NDF
- 한국 CDS와 주요 국채금리
- 외국인 선물 누적 포지션
- 프로그램 매매 또는 개장 전 예상수급이 제공될 경우 참고

야간선물은 유동성과 basis가 낮은 시간대에 왜곡될 수 있으므로 방향 참고용으로만 사용한다. 거래량, 미결제약정, 정규장 선물 대비 basis를 함께 저장한다.

### 6.6 주요 경제지표

#### 미국

- CPI, Core CPI, PPI, PCE, Core PCE
- 비농업고용, 실업률, 임금, 경제활동참가율
- 신규 실업수당, 계속 실업수당, JOLTS
- GDP, GDI, 생산성, 단위노동비용
- ISM 제조업·서비스업과 세부항목
- PMI
- 소매판매, 산업생산, 내구재 주문
- 소비자신뢰, 미시간 기대인플레이션
- 주택착공, 허가, 신규·기존 주택판매
- 은행 대출기준
- 기업재고와 도매재고

#### 한국

- CPI, PPI
- 수출입, 무역수지
- 1일부터 20일까지 수출
- 반도체 수출
- 산업생산, 설비투자, 소매판매
- 기준금리, 통화량, 가계대출
- 원화 환율과 외환보유액
- 기업경기와 소비심리
- 주택가격과 거래량

#### 중국

한국 주식과 원자재·해운 노출을 위해 중국 지표를 1차 범위에 포함한다.

- 제조업 및 비제조업 PMI
- 산업생산, 소매판매, 고정자산투자
- 수출입
- 사회융자총량과 신규대출
- 생산자물가와 소비자물가
- 부동산 판매, 착공, 가격
- 위안화와 중국 국채금리

#### 유럽과 일본

- ECB와 BOJ 정책
- 유로존 PMI와 물가
- 일본 임금, 물가, 산업생산
- 엔화와 일본 국채금리

### 6.7 중앙은행, 재정, 정책

- FOMC 일정, 금리결정, 성명서
- 이전 성명서 대비 변경 문구
- 점도표와 경제전망
- 기자회견
- FOMC 의사록
- 주요 연준 인사 발언
- 한국은행 금융통화위원회와 의사록
- ECB와 BOJ 정책
- 미국 재무부 분기 차입계획
- 국채발행 구성과 만기
- 재정적자, 주요 재정지출과 세제 변화
- 관세, 수출규제, 보조금, 제재, 반독점
- 선거 일정과 정책 시행일
- 지정학과 공급망 차질

중앙은행 발언은 발언자, 투표권 여부, 기존 성향, 직전 발언 대비 변화 여부를 함께 저장한다.

### 6.8 빅테크와 주요 기업 실적

- 발표 예정일과 시각
- 매출 및 EPS actual과 consensus
- 다음 분기 및 연간 가이던스
- hyperscaler CAPEX
- AI 인프라 수요와 공급 제약
- 클라우드 성장률과 마진
- 광고 성장률
- 데이터센터 매출
- 반도체 재고와 리드타임
- 영업이익률과 FCF
- 감가상각과 주식보상
- 자사주 매입과 희석주식 수
- 시간외 가격 반응
- 컨퍼런스콜 핵심 발언
- 경쟁사와 고객에 대한 파급효과

SEC 공시와 회사 IR 자료를 확정 근거로 사용한다. 외부 컨센서스와 뉴스는 보조 근거로만 사용한다.

### 6.9 섹터 특화 거시지표

모든 지표를 매일 수집하지 않고, 보유 종목의 exposure에 따라 선택적으로 활성화한다.

예시:

- 반도체: hyperscaler CAPEX, 서버 출하, 메모리 가격, 수출통제
- 자동차: 미국 SAAR, 인센티브, 중고차 가격, 금리, 관세
- 해운: SCFI, BDI, 선복량, 항만 혼잡, 중국 원자재 수요
- 항공: 유가, 정제마진, 환율, 국제선 수요, 항공화물 운임
- 정유·화학: 유가, 납사, 정제마진, 스프레드, 중국 가동률
- 식품: 곡물, 코코아, 설탕, 환율
- 은행: NIM, 금리곡선, 대손지표, 부동산 신용
- 전력·유틸리티: 연료비, 요금정책, SMP, 전력수요
- 방산: 국가별 국방예산, 환율, 수출규제
- 건설·EPC: 유가, 중동 발주, 금리, 원자재비

---

## 7. 이벤트 처리 수명주기

모든 중요 이벤트는 아래 상태를 거친다.

```text
scheduled
  -> pre_event_snapshot
  -> released
  -> initial_reaction
  -> confirmed_reaction
  -> thesis_review
  -> closed
```

`pre_event_snapshot`, 분 단위 시장 반응, 시장내재 확률은 해당 데이터를 제공하는
provider와 이용 권한이 있을 때만 활성화한다. 데이터가 없으면 값을 추정하거나 보간하지
않고 해당 단계를 `unsupported`로 기록한다. 무료 공식 데이터 기반 MVP는 발표 결과,
일봉 반응, 다음 한국 시장 반응을 우선한다.

### 7.1 사전 단계

이벤트 24시간 전과 60분 전에 다음을 저장한다.

- 컨센서스
- 시장내재 확률
- 관련 자산의 사전 움직임
- 옵션 내재변동성
- 이벤트 위험에 노출된 종목
- 예상 시나리오와 대응 조건

### 7.2 발표 직후

가능한 경우 다음 윈도우를 수집한다.

- 발표 직전 5분
- 발표 후 5분
- 발표 후 30분
- 정규장 종가
- 다음 시장 개장
- 다음 날 종가

### 7.3 사후 확정

첫 반응과 종가 반응이 다르면 `reaction_reversal`로 표시한다. 첫 반응만으로 Thesis 판단을 확정하지 않는다.

---

## 8. 시장 기대와 surprise 계산

### 8.1 단순 surprise

```text
surprise_value = actual - consensus
```

단위와 방향을 고려해 표준화한다.

```text
surprise_score = surprise_value / historical_surprise_std
```

### 8.2 방향 보정

지표마다 높은 값의 의미가 다르다.

- CPI 상회: 물가 압력 상승
- 실업률 상회: 성장 둔화
- 소매판매 상회: 성장 강화
- 원유재고 상회: 공급 여유 또는 수요 약화
- EPS 상회: 실적 개선
- CAPEX 상회: 반도체 수요에는 긍정적일 수 있으나 해당 기업 FCF에는 부정적일 수 있음

### 8.3 시장내재 기대

FOMC와 금리는 발표값보다 시장내재 경로 변화가 더 중요하다.

```text
정책 surprise =
발표 후 OIS 또는 선물 금리경로
- 발표 전 시장내재 금리경로
```

### 8.4 컨센서스가 없는 경우

컨센서스가 없으면 `surprise_score`를 계산하지 않는다. 실제 값, 직전 값, 공식 가이던스, 시장 반응을 이용해 평가하며, confidence를 낮춘다.

---

## 9. 시장 반응 교차검증

중요 이벤트는 아래 자산군의 반응을 동시에 본다.

```text
미국 2년 금리
미국 10년 명목금리
미국 10년 실질금리
달러
주가지수
성장주 대비 가치주
소형주
신용스프레드
VIX와 MOVE
금과 원유
원화와 한국 야간선물
```

예시 해석:

- 고용 강세 + 2년 금리 상승 + 달러 상승 + 성장주 하락
  -> 매파적 성장 충격
- 고용 강세 + 장기금리 안정 + 소형주 상승 + 신용스프레드 축소
  -> 연착륙 기대 강화
- 유가 상승 + 금리 상승 + 주식 하락 + 신용스프레드 확대
  -> 공급발 스태그플레이션 충격 가능성
- 유가 상승 + 산업재·소형주 상승 + 신용스프레드 축소
  -> 수요 회복형 리플레이션 가능성
- CPI 둔화 + 금리 하락인데 주식도 하락
  -> 성장 우려 또는 포지셔닝 청산 가능성

시장 반응은 인과관계의 확정 근거가 아니라 교차검증 수단이다.

---

## 10. 레짐 판정

### 10.1 점수 산출

각 축은 여러 지표의 표준화 점수와 방향을 결합한다.

```text
growth_score
inflation_score
liquidity_score
financial_conditions_score
risk_appetite_score
earnings_momentum_score
```

### 10.2 지속성 조건

하루 변동으로 레짐을 바꾸지 않는다.

- 최소 3개 독립 지표가 같은 방향
- 최소 2거래일 이상 지속
- 신뢰도 0.6 이상
- 핵심 반대 증거가 없을 것

중요 정책 이벤트는 예외적으로 당일 임시 레짐을 생성하되 `provisional=true`로 표시한다.

### 10.3 히스테리시스

레짐 전환과 복귀의 임계치를 다르게 설정해 잦은 뒤집힘을 방지한다.

예시:

- 위험선호 전환: 점수 +1.0 이상 2일
- 위험선호 해제: 점수 0 이하 3일
- 경기침체 경보: 성장 점수 -1.5 이하와 신용 악화 동시 발생

---

## 11. 종목·섹터 영향 계산

### 11.1 기본 공식

```text
impact_score =
    exposure_weight
  * shock_magnitude
  * persistence_factor
  * source_reliability
  * data_confidence
  * market_confirmation
  * horizon_alignment
```

### 11.2 조건부 exposure

유가 상승이 항공주에는 대체로 부정적이지만, 운임 인상과 헤지 비율에 따라 영향이 달라진다. 달러 상승도 수출주에는 긍정적일 수 있으나 해외생산 비중과 원재료 수입 비중에 따라 달라진다.

따라서 exposure에는 조건을 둔다.

```json
{
  "factor": "brent",
  "direction": "negative",
  "weight": 4,
  "channel": "cost",
  "condition": "fuel_hedge_ratio_low AND passenger_yield_flat"
}
```

### 11.3 실적과 valuation 분리

```text
earnings_effect
valuation_effect
liquidity_effect
positioning_effect
```

예시:

- 실질금리 상승: 성장주 valuation 부정, 은행 NIM에는 혼합
- 원화 약세: 수출기업 이익 긍정, 외국인 수급과 할인율에는 부정
- 유가 상승: 정유·에너지 이익 긍정 가능, 항공·운송 원가 부정
- 경기 둔화: 방어주 valuation 상대우위, 경기민감주 이익 부정

### 11.4 영향 등급

```text
0  no_material_change
1  watch
2  mild
3  material
4  high
5  thesis_review_required
```

`4` 이상 또는 Kill Condition 접근은 별도 알림 후보가 된다.

---

## 12. Macro Thesis 판단 형식

모든 Macro Thesis 업데이트는 다음 순서로 출력한다.

1. Thesis 제목
2. 기간과 현재 신뢰도
3. 확정 사실
4. 현재 시장 기대
5. 투자적 해석
6. 기존 Thesis 대비 변화
7. 반대 증거
8. 시장 반응 해석
9. 종목·섹터 영향
10. Valuation 영향
11. 다음 확인 데이터
12. Kill Condition 접근 여부

예시:

```text
[Thesis] 미국 연착륙과 점진적 디스인플레이션
[상태] 유지, 신뢰도 0.64
[Fact] 근원 CPI는 둔화했으나 서비스 물가는 예상보다 높았다.
[시장 기대] 발표 전 시장은 연내 두 차례 인하를 반영했다.
[해석] 물가 하방 경로는 유지되지만 인하 속도 기대는 다소 과도했다.
[시장 반응] 2년 금리 상승, 달러 강세, 성장주 약세.
[Thesis 변화] 약화 2/5.
[Valuation 영향] 장기 성장주 멀티플 압축 가능성.
[다음 확인] Core PCE, 임금, 서비스 ISM 가격지수.
```

---

## 13. 알림 정책

### 13.1 알림 유형

- `morning_briefing`: 매일 오전 브리핑
- `pre_event`: 중요 이벤트 사전 경고
- `event_flash`: 발표 직후 Fact 중심
- `event_confirmed`: 시장 반응 확인 후 해석
- `thesis_change`: Macro Thesis 상태 변화
- `ticker_impact`: 특정 종목 영향
- `portfolio_risk`: 포트폴리오 집중 위험
- `data_quality`: 데이터 장애 또는 stale 경고

### 13.2 우선순위

```text
P0  시스템 장애 또는 핵심 데이터 상충
P1  Kill Condition 발생 또는 구조적 정책 변화
P2  Thesis 상태 변화, magnitude 4 이상
P3  중요한 이벤트와 종목 영향
P4  일일 요약
```

### 13.3 중복 제거

- 같은 원인으로 여러 종목이 영향을 받으면 하나의 묶음 메시지로 발송
- 동일 이벤트는 `event_key + run_type + reaction_window`로 dedupe
- 동일 Thesis 변화는 cooldown 기간 안에 반복 발송하지 않음
- 첫 반응과 확정 반응이 달라질 때만 후속 알림

### 13.4 알리지 않아도 되는 것

- 단순 지수 등락
- 컨센서스 범위 안의 작은 지표 변화
- 방향성이 상충하고 confidence가 낮은 이벤트
- 반복적인 중앙은행 발언
- 실적 수치나 가이던스 변화가 없는 홍보성 발표
- 종목 Thesis exposure가 없는 거시 뉴스
- 하루짜리 원자재 변동으로 Kill Condition을 추정하는 경우

---

## 14. 실행 일정

기본 스케줄은 다음과 같다.

```text
06:10  KRX 야간시장 종료 데이터 정리
06:20  미국 정규장 및 시간외 데이터 수집
06:40  금리·환율·원자재·신용 데이터 갱신
07:00  공식 경제지표와 정책 원문 갱신
07:20  빅테크 실적 및 컨퍼런스콜 결과 반영
07:35  데이터 품질 및 stale 검사
07:45  레짐, Macro Thesis, 종목 영향 계산
07:55  브리핑 생성
08:00  카카오톡 브리핑 발송
08:15  실패 작업 재시도
08:45  최종 재시도
```

이벤트 기반 실행:

```text
T-24h   중요 이벤트 일정 알림
T-60m   사전 기대와 노출 종목 스냅샷
T+5m    Fact 중심 flash
T+30m   초기 시장 반응
시장종가  확정 반응과 Thesis 영향
다음 개장 한국 시장 전파 확인
```

서머타임과 거래소 휴장일을 고려해 스케줄은 고정 UTC가 아니라 거래 캘린더 기반으로 실행한다.

---

## 15. 카카오톡 메시지 형식

### 15.1 오전 브리핑

```text
[시장 레짐]
성장 0 / 물가 +1 / 유동성 -1 / 금융여건 -1 / 위험선호 -1

[간밤 시장]
S&P -0.8%, Nasdaq -1.2%, SOXX -2.1%
미 2Y +7bp, 10Y +9bp, 실질금리 +8bp
DXY +0.6%, USD/KRW NDF +0.7%, WTI +3.4%
VIX +2.8p, HY 스프레드 +6bp

[핵심 원인]
FOMC 매파 발언과 원유재고 감소.
유가 상승은 수요 회복보다 공급 우려 성격이 강함.

[Macro Thesis 변화]
미국 연착륙 Thesis 유지
디스인플레이션 Thesis 약화 2/5
AI CAPEX Thesis 유지

[오늘 일정]
한국 수출, 미국 고용, MSFT 실적

[종목 영향]
SK하이닉스: 실질금리 상승은 valuation 부정, AI CAPEX 유지로 실적 Thesis는 중립
대한항공: 유가와 원화 약세 동시 발생으로 약화 3/5
한국전력: 연료비 상승으로 약화 2/5

[포트폴리오 위험]
원화 약세와 유가 상승에 동시에 취약한 운송 비중이 높음.
```

### 15.2 이벤트 flash

```text
[CPI Flash]
Fact: Headline 0.3% MoM, consensus 0.2%
Core 0.2%, consensus 0.2%
미 2Y +8bp, DXY +0.4%, Nasdaq -0.6%

초기 해석:
Headline 상회는 에너지 영향이 크며 Core는 부합.
정책경로에는 약한 매파적 영향.
확정 판단은 30분 반응과 세부항목 확인 후 갱신.
```

---

## 16. Provider 설계

### 16.1 source hierarchy

출처 우선순위는 다음과 같다.

```text
1. 중앙은행·통계기관·거래소·SEC·회사 IR
2. 공식 API와 공식 원문
3. 신뢰도 높은 시세 및 컨센서스 제공자
4. 주요 통신사와 언론
5. 보조 데이터 소스
```

서로 다른 provider의 값이 충돌하면 공식 원문을 우선한다. 시세는 거래소 시간과 통화, 조정주가 여부를 검증한다.

### 16.2 1차 무료 Provider

| Provider | 용도 | 키 |
| --- | --- | --- |
| FRED | 금리, 실질금리, 신용, 유동성, 경기 시계열 | 필요 |
| U.S. Treasury | 국채 수익률, 입찰, 발행 | 불필요 |
| Federal Reserve | FOMC 일정, 성명서, 의사록, 전망 | 불필요 |
| BLS | CPI, 고용 등 미국 통계 | 선택 |
| BEA | GDP, PCE | 선택 |
| EIA | 원유 재고, 생산, 정제 가동률 | 필요 |
| BOK ECOS | 한국 금리, 물가, 환율, 실물 | 필요 |
| KRX | 거래일정, 상품정보, 공식 시세 가능 범위 | 검증 |
| SEC EDGAR | 미국 기업 공시 | User-Agent 필요 |
| Company IR | 실적과 가이던스 | 불필요 |
| ohlcv-analyst | 미국 ETF, 빅테크, 국내 종목 가격 | 기존 서비스 |
| Alpha Vantage | 환율·원자재 보조 | 기존 키 |
| Finnhub | 일정과 surprise 보조 | 기존 키 |

### 16.3 선택 유료 Provider

- 경제지표 actual/consensus/previous 자동화
- 실시간 및 시간외 미국 시세
- 미국 옵션과 금리선물
- KRX 야간선물과 미결제약정
- 중국 원자재와 해운지수
- 기업이익 추정치 revision breadth
- 포지셔닝과 dealer gamma

Provider별 지원 범위, 지연시간, 라이선스, 재배포 가능 여부를 별도 registry에 기록한다.

### 16.4 fallback

```text
primary provider
  -> secondary provider
  -> latest valid cached value
  -> missing 표시
```

cached 값을 사용할 때는 반드시 `stale=true`와 기준시각을 표시한다.

---

## 17. 시간, 거래일, 데이터 품질

### 17.1 시간대

모든 원시 데이터는 UTC로 저장하고 사용자 표시 시 `Asia/Seoul`로 변환한다.

필수 필드:

```text
observed_at_utc
observed_at_local
source_timezone
market_session
trading_date
```

### 17.2 거래일

- 미국 정규장 종가는 한국 날짜로 다음 날 아침 브리핑에 포함
- 미국 시간외 실적은 발표한 미국 거래일과 한국 브리핑 날짜를 모두 저장
- KRX 야간 세션은 실제 거래소 session_id를 기준으로 정규장과 매핑
- 서머타임 전환일에는 스케줄 테스트를 별도로 수행
- 공휴일과 조기종료 거래일을 캘린더에 반영

### 17.3 품질 규칙

- 발표 예정인데 값이 없으면 `missing`
- 기대 빈도보다 오래되면 `stale`
- 공급자 간 허용오차를 넘으면 `conflicted`
- 수정 발표는 `revised`
- 단위, 통화, basis, 계절조정 여부가 다르면 별도 시계열로 저장
- 시세의 adjusted/unadjusted 여부를 명시

---

## 18. API와 Custom GPT Action

### 18.1 읽기 API

```http
GET /macro/briefings/latest
GET /macro/briefings/{date}
GET /macro/regime/latest
GET /macro/theses
GET /macro/theses/{thesis_key}
GET /macro/events
GET /macro/events/{event_key}
GET /macro/observations
GET /macro/reactions/{event_key}
GET /monitoring-items/{ticker}/macro-impacts
GET /sectors/{sector_code}/macro-impacts
GET /portfolios/{portfolio_id}/macro-risk
GET /macro/calendar
GET /macro/provider-status
```

### 18.2 운영 API

```http
POST /admin/macro-monitor/run
POST /admin/macro-monitor/replay
POST /admin/macro-theses/{thesis_key}/review
POST /admin/macro-exposures/backfill
```

운영 API는 기존 Action API Key 인증을 사용한다. 공개 Custom GPT Action에는 읽기 API만 노출한다.

### 18.3 권장 Custom GPT Action

```text
getMacroBriefing
getMacroRegime
getMacroTheses
getMacroEvents
getMacroCalendar
getTickerMacroImpacts
getPortfolioMacroRisk
getMacroProviderStatus
```

---

## 19. 저장 구조

```text
data/
  macro/
    raw/
      YYYY-MM-DD/
        provider-name/
    observations/
      YYYY-MM-DD.jsonl
    events/
      YYYY-MM-DD.jsonl
    expectations/
      YYYY-MM-DD.jsonl
    reactions/
      YYYY-MM-DD.jsonl
    shocks/
      YYYY-MM-DD.jsonl
    regimes/
      YYYY-MM-DD.json
    theses/
      THESIS_KEY.jsonl
    impacts/
      tickers/
        TICKER.jsonl
      sectors/
        SECTOR.jsonl
      portfolios/
        PORTFOLIO.jsonl
    briefings/
      YYYY-MM-DD/
        morning.json
        event-*.json
```

SQLite를 기본 조회 저장소로 사용하고 JSON·JSONL은 감사, 백업, replay, 사람이 직접 읽는 용도로 원자적 쓰기를 사용해 내보낸다.

권장 테이블:

```text
macro_observations
macro_events
macro_expectations
macro_market_reactions
macro_shock_assessments
macro_regime_assessments
macro_theses
macro_thesis_evidence
thesis_macro_exposures
sector_macro_exposures
thesis_macro_impacts
portfolio_macro_impacts
macro_briefings
macro_alert_outbox
macro_data_quality
provider_registry
```

모든 테이블에 `schema_version`과 `created_at`, `updated_at`을 둔다.

---

## 20. 백테스트와 검증

### 20.1 replay 대상

- 과거 FOMC
- CPI와 고용 surprise
- 유가 급등과 공급충격
- 은행 스트레스
- 엔 캐리 청산
- 관세와 수출통제
- 빅테크 CAPEX 급증 또는 하향
- 주요 지정학 이벤트

### 20.2 평가 지표

- 중요 이벤트 탐지율
- 불필요 알림 비율
- Thesis 상태 변경의 정확성
- 이벤트 후 1일·5일·20일 시장 반응 일관성
- 종목 영향 방향의 적중률
- confidence calibration
- provider 장애 복구율
- 브리핑 지연시간
- 중복 알림 비율

### 20.3 human review

다음 항목은 정기적으로 사람이 검토한다.

- exposure 방향과 weight
- Kill Condition 임계치
- 거시 레짐 전환 기준
- 이벤트 중요도
- 컨센서스 provider 품질
- 실제 투자 판단에 도움이 되지 않는 알림

---

## 21. 보안과 운영

- API 키와 토큰은 `.env` 또는 OS keychain에 저장
- 원문 토큰과 키를 로그에 기록하지 않음
- 공개 Action schema에 운영 endpoint를 포함하지 않음
- provider별 rate limit와 exponential backoff 적용
- outbox와 dedupe key로 중복 발송 방지
- 장애 시 부분 성공을 허용하되 데이터 누락을 브리핑에 명시
- provider 라이선스가 허용할 때만 원시 payload를 보존해 판단 재현 가능성 확보
- 원시 데이터 재저장이 금지된 provider는 출처, 조회시각, 요청 식별자와 내용 hash만 보존
- 로그에는 `run_id`, `provider`, `as_of`, `stale`, `fallback_used` 포함
- 스키마 migration은 비파괴적으로 수행
- 동일 날짜 재실행 시 idempotent 보장

---

## 22. 구현 단계

### Phase 1. 기반 모델과 캘린더

- MacroThesis, Observation, Event, Expectation, Reaction 모델 추가
- 거래일·시간대 정규화
- 데이터 품질 상태 추가
- SQLite와 JSONL 저장

완료 조건:

- 동일 데이터 반복 수집 시 중복 없음
- revision과 vintage 보존
- 미국·한국 거래일 매핑 검증
- 서머타임 테스트 통과

### Phase 2. 공식 데이터 Provider

- FRED, Treasury, Fed, BLS, BEA, EIA, ECOS
- SEC와 회사 IR
- provider registry와 상태 점검
- timeout, retry, fallback

완료 조건:

- 하나의 provider 장애가 전체 실행을 중단하지 않음
- 원문 URL과 수집 시각 보존
- stale 및 conflict 표시

### Phase 3. 시장 데이터와 기대 데이터

- ETF, 금리, 환율, 원자재, 신용, 변동성
- KRX 야간선물 지원 검증
- 컨센서스와 시장내재 기대
- 이벤트 전 스냅샷

완료 조건:

- 오전 8시 기준 미국 시장과 한국 개장 전 스냅샷 생성
- 이벤트별 expected/actual/reaction 연결

### Phase 4. Shock와 레짐 엔진

- 성장, 물가, 유동성, 금융여건, 위험선호, 이익 모멘텀
- shock type 분류
- 지속성, 히스테리시스, confidence
- 시장 반응 교차검증

완료 조건:

- 과거 이벤트 fixture에서 기대한 방향 재현
- 근거가 부족하면 판단 보류
- 하루 변동으로 레짐이 과도하게 뒤집히지 않음

### Phase 5. Macro Thesis 엔진

- Macro Thesis 생성과 버전관리
- evidence weighting과 half-life
- 강화·유지·약화·구조적 붕괴 판정
- Kill Condition 접근 경고

완료 조건:

- 경쟁하는 Thesis를 동시에 유지 가능
- 증거의 방향과 지속성이 기록됨
- 판정 근거를 재현 가능

### Phase 6. 종목·섹터·포트폴리오 연결

- 종목 Thesis에 macro exposure 추가
- 섹터 기본 exposure
- 조건부 전달 경로
- 실적 효과와 valuation 효과 분리
- 포트폴리오 집중 위험 계산

완료 조건:

- 같은 이벤트가 종목별로 다른 방향의 영향을 생성
- 단일 가격 변동으로 자동 무효화하지 않음
- 포트폴리오의 주요 거시 집중도를 설명 가능

### Phase 7. 브리핑과 이벤트 알림

- 오전 브리핑
- pre-event, flash, confirmed alert
- 카카오 길이 제한과 메시지 분할
- outbox, dedupe, cooldown

완료 조건:

- 오전 브리핑 하루 한 번
- 중요한 이벤트는 Fact와 해석이 분리
- 첫 반응이 뒤집히면 후속 알림
- no_material_change는 개별 발송하지 않음

### Phase 8. API와 Custom GPT

- 읽기 endpoint
- Pydantic schema
- 공개 OpenAPI Action schema
- Custom GPT 호출 시나리오

완료 조건:

- 최신 브리핑, Thesis, 이벤트, 종목 영향 조회 가능
- 운영 endpoint는 공개 schema 제외

### Phase 9. Replay와 운영 검증

- 과거 FOMC, CPI, 고용, 유가, 정책충격 replay
- threshold calibration
- LaunchAgent 배포
- 실제 브리핑 1회 검증
- 로그와 장애 복구 확인

완료 조건:

- 테스트와 lint 통과
- 재시작 후 health와 실제 발송 확인
- 키와 토큰이 Git에 포함되지 않음

---

## 23. MVP 우선순위

### MVP 필수

- 하루 한 번 오전 브리핑
- 미국 시장, 금리, 달러, 유가, 변동성
- FRED, EIA, ECOS 핵심 지표
- FOMC와 주요 경제지표
- 빅테크 및 반도체 실적
- Macro Thesis 최소 3개
- 모니터링 종목별 macro exposure
- Fact와 추론 분리
- 데이터 최신성과 누락 표시
- 동일 이벤트 중복 제거

### MVP에 반드시 포함할 Macro Thesis 예시

1. 미국 연착륙과 디스인플레이션
2. 연준의 정책경로와 장기 실질금리
3. AI CAPEX와 반도체 수요
4. 중국 경기와 한국 수출
5. 유가와 공급충격

### 2차

- 시장내재 금리확률
- 이벤트 발표 직후 알림
- KRX 야간선물과 NDF
- 신용스프레드와 MOVE
- 중국 지표
- 포트폴리오 거시 집중 위험
- 빅테크 실적의 섹터 전파

### 3차

- 옵션 포지셔닝과 dealer gamma
- CFTC 포지션
- 이익 추정치 revision breadth
- 경제지표 nowcast
- 자동 scenario stress test
- 웹 대시보드와 레짐 히스토리
- alert precision/recall 대시보드

---

## 24. 필요한 API 키

### 필수

1. `FRED_API_KEY`
   - 발급: <https://fredaccount.stlouisfed.org/apikeys>
   - 용도: 미국 금리, 실질금리, 신용, 유동성, 경기 시계열
2. `EIA_API_KEY`
   - 발급: <https://www.eia.gov/opendata/register.php>
   - 용도: 원유 재고, 생산량, 정제 가동률
3. `ECOS_API_KEY`
   - 발급: <https://ecos.bok.or.kr/api/>
   - 용도: 한국은행 경제통계

### 선택

1. `BEA_API_KEY`
   - 발급: <https://apps.bea.gov/api/signup/>
2. BLS 등록 키
3. 경제지표 컨센서스 provider
4. 실시간·시간외 미국 시세 provider
5. KRX 야간선물 provider
6. 옵션·포지셔닝 provider

키는 채팅에 입력하지 않고 맥미니에서 대화 로그에 남지 않는 방식으로 `.env` 또는 keychain에 저장한다.

---

## 25. 사용자 설정 항목

```yaml
briefing:
  timezone: Asia/Seoul
  morning_time: "08:00"
  send_no_change: true

alerts:
  pre_event: false
  flash: false
  confirmed: false
  min_magnitude: 3
  thesis_review_threshold: 4
  cooldown_minutes: 120

regions:
  - US
  - KR
  - CN
  - EU
  - JP

macro_theses:
  - us_soft_landing_disinflation
  - fed_policy_path
  - ai_capex_cycle
  - china_korea_export_cycle
  - oil_supply_shock

portfolio:
  enabled: false
  exposure_review_required: true
```

초기 기본값은 오전 브리핑만 매일 발송한다. `pre_event`, `flash`, `confirmed`는 실시간
시세와 컨센서스 provider가 준비된 2차 단계에서 활성화한다. 포트폴리오 기능도 보유내역
모델과 사용자 검토 절차가 추가된 뒤 활성화한다.

---

## 26. 최종 설계 판단

기존 설계의 방향은 적절했다. 특히 공식 데이터 우선, Fact와 추론 분리, 종목별 macro exposure, 오전 브리핑, 거시 이벤트와 종목 이벤트의 도메인 분리는 그대로 유지할 가치가 있다.

다만 실제 투자 Thesis 모니터링 시스템으로 사용하려면 단순한 `MacroObservation`, `MacroEvent`, `MacroRegimeAssessment`만으로는 부족하다. 시장 기대, 발표 후 반응, 충격 유형, 경쟁하는 Macro Thesis, 종목과 포트폴리오의 조건부 exposure를 별도 객체로 관리해야 한다. 또한 거시 이벤트는 숫자 자체보다 시장이 무엇을 예상했고 어떤 자산이 어떻게 반응했는지를 함께 보아야 한다.

따라서 구현 우선순위는 다음과 같이 잡는 것이 가장 효율적이다.

```text
1. 데이터 품질과 시간 정규화
2. 시장 기대와 이벤트 반응
3. Macro Thesis와 레짐
4. 종목·섹터 exposure
5. 오전 브리핑
6. 이벤트 기반 알림
7. 포트폴리오 집중 위험
8. replay와 threshold 개선
```

이 순서로 구현하면 단순한 뉴스 요약 시스템이 아니라, 거시 변화가 특정 투자 Thesis를 실제로 강화하는지 약화하는지 감시하는 구조를 만들 수 있다.
