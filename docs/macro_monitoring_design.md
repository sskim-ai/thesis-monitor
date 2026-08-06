# Macro Monitoring Design

## 1. 목적

`thesis-monitor`가 종목별 뉴스와 공시뿐 아니라 금리, 환율, 원자재, 야간선물,
경제지표, 중앙은행 정책, 빅테크 실적 등 거시 환경을 매일 평가하도록 확장한다.

시스템은 거시 이벤트를 독립적으로 저장하고 다음 순서로 처리한다.

```text
거시 데이터 수집
  -> 시장 및 경제 이벤트 정규화
  -> 거시 레짐 평가
  -> 종목별 macro exposure와 연결
  -> 기존 투자 Thesis 영향 평가
  -> 오전 8시 카카오톡 브리핑
```

핵심 원칙은 거시 정보를 보편적인 호재 또는 악재로 분류하지 않는 것이다. 같은 유가
상승도 에너지 생산자에는 긍정적일 수 있고 항공, 운송, 화학 기업에는 부정적일 수 있다.
모든 방향 평가는 종목의 투자 논리와 전달 경로를 기준으로 수행한다.

## 2. 범위

### 2.1 포함 범위

- 미국 증시와 주요 업종의 간밤 성과
- 미국 및 한국 금리와 수익률 곡선
- 달러, 원화, 엔화 등 주요 환율
- 유가, 천연가스, 금, 구리 등 원자재
- KRX 야간시장 선물
- 미국 및 한국 주요 경제지표
- FOMC, 연준 발언, 한국은행 등 통화정책
- 관세, 수출규제, 제재, 지정학, 공급망 이벤트
- 미국 빅테크와 주요 반도체 기업 실적
- 거시 변화가 모니터링 종목의 Thesis에 미치는 영향
- 매일 오전 8시 카카오톡 거시 브리핑

### 2.2 1차 구현에서 제외할 범위

- 주문 실행 및 포트폴리오 자동 조정
- 초단타용 실시간 틱 데이터
- 거시 이벤트 하나만으로 투자 Thesis 자동 무효화
- 근거 없는 범용 뉴스 감성 점수
- 유료 컨센서스 데이터가 없을 때 컨센서스 값 추정

## 3. 시스템 경계

기존 종목 이벤트와 거시 이벤트는 별도 도메인으로 유지한다.

```text
app/providers/*                 종목 뉴스, 공시, IR
app/services/ohlcv_client.py    종목 가격 문맥

app/macro/providers/*           거시 데이터 수집
app/macro/models.py             거시 관측값과 이벤트
app/macro/regime.py             거시 레짐 평가
app/macro/impact.py             종목 Thesis 연결
app/macro/briefing.py           오전 브리핑 생성
app/jobs/monitor_macro.py       예약 실행 진입점
```

`ohlcv-analyst`는 한국 및 미국 개별 주식과 ETF의 일봉, 주봉, 월봉 분석에 계속 사용한다.
금리, 경제지표, 원자재, 지수, KRX 야간선물은 `thesis-monitor`의 거시 provider에서
수집한다. 향후 ohlcv-analyst가 선물과 지수를 지원하면 시장 데이터 호출만 위임할 수
있다.

## 4. 데이터 모델

### 4.1 MacroObservation

금리, 환율, 지수, ETF, 원자재 등 수치형 시계열을 저장한다.

```text
id
series_code
category
provider
observed_at
value
unit
frequency
previous_value
change_value
change_pct
source_url
retrieved_at
vintage_at
raw_payload
```

`series_code`, `observed_at`, `provider`, `vintage_at` 조합으로 중복을 방지한다. 수정 발표가
발생할 수 있는 경제지표는 기존 값을 덮어쓰지 않고 vintage를 추가한다.

### 4.2 MacroEvent

경제지표 발표, 정책 결정, 실적, 규제, 지정학 이벤트를 저장한다.

```text
id
event_key
category
title
country
scheduled_at
released_at
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

공식 자료에는 컨센서스가 없을 수 있다. 이 경우 `consensus`, `surprise_value`,
`surprise_score`를 `null`로 저장하고 실제 값과 시장 반응만 평가한다.

### 4.3 MacroRegimeAssessment

하루의 거시 환경을 네 축으로 평가한다.

```text
assessment_date
growth_momentum       -2 .. +2
inflation_pressure    -2 .. +2
liquidity_condition   -2 .. +2
risk_appetite         -2 .. +2
confidence            0.0 .. 1.0
summary
evidence
created_at
```

- `growth_momentum`: 실물 경기와 기업 수요의 개선 또는 둔화
- `inflation_pressure`: 물가 압력의 상승 또는 하락
- `liquidity_condition`: 금리, 실질금리, 달러, 신용 여건의 완화 또는 긴축
- `risk_appetite`: 주식, 변동성, 신용, 시장 폭으로 본 위험선호

### 4.4 ThesisMacroExposure

투자 Thesis 버전마다 거시 변수에 대한 민감도를 명시한다.

```json
{
  "ticker": "000660",
  "thesis_version": 2,
  "exposures": [
    {
      "factor": "us_10y_real_yield",
      "direction": "negative",
      "weight": 2,
      "channel": "discount_rate"
    },
    {
      "factor": "hyperscaler_capex",
      "direction": "positive",
      "weight": 5,
      "channel": "demand"
    },
    {
      "factor": "usdkrw",
      "direction": "positive",
      "weight": 2,
      "channel": "fx"
    }
  ]
}
```

신규 모니터링 등록 시 Custom GPT가 exposure 초안을 함께 생성한다. 기존 Thesis는 핵심
논리와 강화, 약화, 무효화 조건에서 초안을 생성하되 최초 1회 검토 대상으로 표시한다.

### 4.5 ThesisMacroImpact

거시 관측값 또는 이벤트가 특정 종목에 미친 영향을 저장한다.

```text
ticker
thesis_version
assessment_date
macro_event_id
direction             strengthen / weaken / mixed / neutral
magnitude             1 .. 5
persistence           temporary / cyclical / structural
confidence            0.0 .. 1.0
channels
affected_thesis_pillars
rationale
evidence
```

### 4.6 MacroBriefing

오전 브리핑과 발송 상태를 저장한다.

```text
briefing_date
as_of
headline
market_summary
regime_summary
today_calendar
ticker_impacts
kakao_text
status
dedupe_key
created_at
```

## 5. 수집 대상

### 5.1 간밤 미국 시장

- 지수 대용 ETF: SPY, QQQ, IWM
- 업종: SOXX 또는 SMH, XLF, XLE, XLV, XLY, XLI
- 빅테크: NVDA, MSFT, AAPL, GOOGL, AMZN, META, TSLA, AVGO, TSM
- 변동성: VIX
- 시장 폭: 상승 및 하락 종목 수, 신고가 및 신저가
- 상대 성과: 동일가중 지수 대비 시가총액 가중 지수

수집 필드는 종가, 전일 대비, 장중 고가와 저가, 거래량, 데이터 기준시각이다. 빅테크
실적일에는 정규장과 시간외 반응을 구분한다.

### 5.2 금리와 유동성

- 미국 2년, 10년, 30년 국채금리
- 미국 5년 및 10년 실질금리
- 2년-10년, 3개월-10년 금리차
- 기준금리 및 SOFR
- 기대인플레이션
- 하이일드 신용스프레드
- 연준 자산, 재무부 일반계정, 역레포 잔액

### 5.3 환율과 원자재

- DXY
- USD/KRW, USD/JPY, EUR/USD
- WTI, Brent, 천연가스
- 금, 구리
- 원유 선물 기간구조
- 미국 원유, 휘발유, 정제유 재고
- 미국 원유 생산량과 정제 가동률

### 5.4 한국 개장 전 시장

- KOSPI200 야간선물
- KOSDAQ150 야간선물
- 미국 달러 선물
- 3년 및 10년 국채선물
- MSCI Korea 또는 EWY 대용 지표
- 한국 관련 미국 상장 종목과 반도체 ETF

KRX 야간시장은 18:00부터 다음 날 06:00까지의 세션을 기준으로 수집한다. 거래일은
야간 세션 종료일 기준으로 정규장 날짜와 맞춘다.

### 5.5 주요 경제지표

미국:

- CPI, Core CPI, PPI, PCE, Core PCE
- 비농업고용, 실업률, 임금, 신규 실업수당, JOLTS
- GDP, ISM 제조업 및 서비스업, PMI
- 소매판매, 산업생산, 내구재 주문
- 소비자신뢰, 미시간 기대인플레이션
- 주택착공, 허가, 기존 및 신규 주택판매

한국:

- 소비자물가와 생산자물가
- 수출입과 무역수지
- 1일부터 20일까지의 수출
- 산업생산과 설비투자
- 기준금리와 통화량
- 원화 환율과 외환보유액

### 5.6 중앙은행과 정책

- FOMC 일정, 금리 결정, 성명서
- 이전 성명서 대비 변경 문구
- 점도표, 경제전망, 기자회견
- FOMC 의사록과 주요 연준 인사 발언
- 한국은행 금융통화위원회 결정과 의사록
- ECB와 BOJ의 주요 정책 변화
- 관세, 수출규제, 보조금, 제재, 반독점 정책

### 5.7 빅테크 실적

- 발표 예정일과 발표 시각
- 매출 및 EPS actual과 consensus
- 다음 분기 및 연간 가이던스
- 클라우드, AI, 데이터센터 매출 성장률
- CAPEX와 감가상각
- 영업이익률과 잉여현금흐름
- 재고, 공급 제약, 수요 가시성
- 시간외 가격 반응
- 컨퍼런스콜 핵심 발언

SEC 공시와 회사 IR 자료를 확정 근거로 사용한다. 외부 컨센서스와 뉴스는 보조 근거로만
사용한다.

## 6. Provider 설계

### 6.1 1차 무료 Provider

| Provider | 용도 | 키 |
| --- | --- | --- |
| FRED | 금리, 실질금리, 신용, 유동성, 경기 시계열 | 필요 |
| U.S. Treasury | 공식 국채 수익률 곡선 | 불필요 |
| Federal Reserve | FOMC 일정, 성명서, 의사록, 전망 | 불필요 |
| BLS | CPI, 고용 등 미국 통계 | 불필요, 등록 선택 |
| BEA | GDP, PCE 발표문 | 불필요 |
| EIA | 원유 재고, 생산, 정제 가동률 | 필요 |
| BOK ECOS | 한국 금리, 물가, 환율, 실물 지표 | 필요 |
| KRX | 야간시장 일정과 상품 정보 | 불필요 |
| SEC EDGAR | 미국 기업 공시 | 기존 User-Agent 사용 |
| Company IR | 실적 발표와 가이던스 | 불필요 |
| ohlcv-analyst | 미국 ETF, 빅테크, 국내 종목 가격 | 기존 서비스 사용 |
| Alpha Vantage | 환율, 원자재, 보조 시계열 | 기존 키 사용 |
| Finnhub | 실적 일정과 surprise 보조 | 기존 키 사용 |

### 6.2 선택 유료 Provider

- 경제지표 `actual / consensus / previous` 자동화가 필요하면 Finnhub Economic Calendar
  또는 동급 데이터 공급자를 사용한다.
- 실시간 및 시간외 미국 시세가 필요하면 거래소 권한이 포함된 시세 공급자를 사용한다.
- KRX 야간선물이 기존 키움 API에서 제공되지 않으면 국내 파생상품 시세 공급자를
  별도로 선정한다.

유료 provider는 무료 공식 데이터 기반 MVP가 안정화된 뒤 결정한다.

## 7. 판정 규칙

### 7.1 사실과 해석 분리

모든 이벤트는 다음 세 항목을 별도로 저장한다.

- `confirmed_facts`: 공식 원문에서 확인된 사실
- `inferred_implications`: 모델 또는 규칙 기반 해석
- `unknowns`: 아직 확인되지 않은 변수

### 7.2 영향 점수

종목별 거시 영향 점수는 아래 요소로 계산한다.

```text
impact = exposure_weight
       * event_magnitude
       * persistence_factor
       * source_reliability
       * confidence
```

- magnitude: 변동 폭 또는 surprise의 크기
- persistence: 일시적, 순환적, 구조적
- source reliability: 공식 자료가 가장 높음
- confidence: 데이터 완전성과 전달 경로의 명확성

하루의 단일 가격 변동은 원칙적으로 Thesis 무효화 근거로 사용하지 않는다. 구조적 정책
변경이나 반복된 수요 훼손이 명시된 무효화 조건과 일치할 때만 `invalidation_candidate`로
올린다.

### 7.3 시장 반응 교차 확인

중요 경제지표는 발표 숫자만으로 방향을 결정하지 않는다.

```text
발표 결과
  + 미국 2년 및 10년 금리 반응
  + 달러 반응
  + 주가지수 및 업종 반응
  + 원자재 반응
  = 시장이 해석한 정책 및 경기 효과
```

## 8. 실행 일정과 장애 복구

```text
07:40  시장 및 거시 데이터 수집
07:50  공식 문서와 경제 일정 갱신
07:55  거시 레짐 및 종목별 영향 평가
08:00  카카오톡 브리핑 발송 및 종목 Thesis 평가
08:15  실패 작업 재시도
08:45  최종 재시도
```

- provider별 지수 백오프를 적용한다.
- 일부 provider 실패 시 확보된 데이터로 브리핑을 생성한다.
- 누락된 데이터와 stale 데이터는 브리핑에 명시한다.
- `briefing_date + run_type`으로 실행 중복을 방지한다.
- 카카오 알림은 outbox와 `dedupe_key`로 중복 발송을 방지한다.

## 9. 카카오톡 메시지

매일 브리핑은 한 건을 기본으로 한다.

```text
[시장 레짐] 성장↓ / 물가↑ / 유동성↓ / 위험선호↓
[간밤 시장] Nasdaq -1.2%, SOXX -2.1%, 10Y +9bp, WTI +3.4%
[핵심 원인] FOMC 매파 발언, 원유재고 감소
[오늘 일정] 미국 고용, MSFT 실적
[Thesis 영향] SK하이닉스 약화 2/5, 항공주 약화 3/5
```

알림 정책:

- 오전 거시 브리핑은 매일 1건 발송
- 같은 원인으로 여러 종목이 영향을 받으면 묶어서 발송
- magnitude 4 이상 또는 무효화 후보는 별도 강조
- 데이터 부족 자체는 장애 알림으로 분리
- `no_material_change` 종목은 개별 메시지를 보내지 않음

## 10. API와 Custom GPT Action

추가할 읽기 API:

```http
GET /macro/briefings/latest
GET /macro/briefings/{date}
GET /macro/regime/latest
GET /macro/events
GET /macro/observations
GET /monitoring-items/{ticker}/macro-impacts
```

운영 API:

```http
POST /admin/macro-monitor/run
```

운영 API는 기존 Action API Key 인증을 사용한다. Custom GPT Action에는 최신 브리핑,
이벤트, 종목별 거시 영향 조회만 노출한다. 관리자 실행 API는 공개 Action schema에서
제외한다.

## 11. 로컬 저장 구조

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
    regimes/
      YYYY-MM-DD.json
    impacts/
      TICKER.jsonl
    briefings/
      YYYY-MM-DD.json
```

SQLite를 기본 조회 저장소로 사용하고 JSON 및 JSONL은 감사, 백업, 사람이 직접 읽는
용도로 원자적 쓰기를 사용해 내보낸다.

## 12. 필요한 API 키

### 12.1 필수

1. `FRED_API_KEY`
   - 발급: <https://fredaccount.stlouisfed.org/apikeys>
   - 용도: 미국 금리, 실질금리, 신용, 유동성, 경기 시계열

2. `EIA_API_KEY`
   - 발급: <https://www.eia.gov/opendata/register.php>
   - 용도: 원유 재고, 생산량, 정제 가동률

3. `ECOS_API_KEY`
   - 발급: <https://ecos.bok.or.kr/api/>
   - 용도: 한국은행 경제통계

### 12.2 선택

1. `BEA_API_KEY`
   - 발급: <https://apps.bea.gov/api/signup/>
   - 상세 NIPA 및 GDP 원자료가 필요할 때 사용

2. BLS 등록 키
   - 키 없이 MVP 구현 가능
   - 요청량이 증가할 때 등록

3. Finnhub Economic Data 구독
   - 기존 Finnhub 키를 사용하되 유료 권한 필요
   - 경제지표 컨센서스 자동화가 필요할 때만 선택

키는 채팅에 붙이지 않는다. 발급 완료 후 맥미니에서 대화 로그에 남지 않는 입력
방식으로 `.env`에 저장한다.

## 13. 작업 계획

### Phase 1. 기반 모델 및 저장소

- 거시 모델과 인덱스 추가
- 기존 SQLite에 비파괴적 테이블 생성
- `data/macro/` 내보내기 구현
- 날짜, provider, vintage 단위 중복 방지

완료 조건:

- 동일 데이터를 반복 수집해도 중복 레코드가 생기지 않는다.
- 수정 발표는 이전 값을 보존한 새 vintage로 저장된다.

### Phase 2. 공식 데이터 Provider

- FRED, Treasury, Fed, BLS, BEA, EIA, ECOS provider 구현
- provider 상태와 설정 API 추가
- 타임아웃, 재시도, 부분 실패 처리
- 원문 URL과 수집 시각 보존

완료 조건:

- 각 provider fixture 테스트 통과
- 하나의 provider 장애가 전체 실행을 중단하지 않는다.

### Phase 3. 시장 데이터 Provider

- ohlcv-analyst로 ETF와 빅테크 종가 수집
- Alpha Vantage로 환율과 원자재 보완
- 키움 API의 KRX 야간선물 지원 여부 검증
- unsupported 항목은 누락 경고로 처리

완료 조건:

- 오전 8시 기준 미국 시장과 한국 개장 전 스냅샷을 생성한다.
- 데이터 기준시각과 stale 여부를 확인할 수 있다.

### Phase 4. 거시 레짐 엔진

- 성장, 물가, 유동성, 위험선호 점수 구현
- 전일, 주간 변화와 임계치 계산
- 경제지표 surprise와 시장 반응 교차 확인
- 사실과 추론 분리

완료 조건:

- 과거 데이터 fixture에서 기대한 레짐 방향이 재현된다.
- 근거가 없는 경우 confidence를 낮추고 판단을 보류한다.

### Phase 5. 종목 Thesis 연결

- Thesis 버전에 macro exposure 추가
- 신규 종목 등록 시 exposure 초안 생성
- 기존 종목 exposure 백필 및 검토 상태 추가
- 거시 영향과 종목 이벤트 점수를 결합

완료 조건:

- 같은 이벤트가 종목별로 다른 방향의 영향을 만들 수 있다.
- 단일 거시 가격 변동으로 Thesis가 자동 무효화되지 않는다.

### Phase 6. 브리핑과 알림

- 오전 브리핑 생성기 구현
- 카카오 메시지 포맷과 길이 제한 처리
- macro outbox와 dedupe key 추가
- 08:00, 08:15, 08:45 실행 연결

완료 조건:

- 오전 브리핑이 하루 한 번만 전송된다.
- 네트워크 복구 후 대기 중인 알림이 재전송된다.

### Phase 7. API와 Custom GPT

- 거시 조회 endpoint 추가
- Pydantic 응답 schema 추가
- 공개 OpenAPI Action schema 갱신
- Custom GPT 호출 시나리오 테스트

완료 조건:

- Custom GPT가 최신 브리핑과 종목별 거시 영향을 조회할 수 있다.
- 관리자 endpoint는 공개 schema에 포함되지 않는다.

### Phase 8. 검증과 배포

- 단위, 통합, 장애 복구 테스트
- 과거 FOMC, CPI, 고용, 유가 급등 사례 재생 테스트
- LaunchAgent 설치와 로그 점검
- localhost 및 `/thesis` 공개 endpoint 검증
- 커밋, 푸시, Custom GPT schema 재등록 안내

완료 조건:

- 전체 테스트와 Ruff 통과
- LaunchAgent 재시작 후 health와 실제 1회 브리핑 검증
- 키와 원시 토큰이 Git에 포함되지 않음

## 14. 구현 우선순위

### MVP

- 무료 공식 데이터 기반
- 하루 한 번 오전 브리핑
- ETF 기반 미국 시장 요약
- FRED, EIA, ECOS 핵심 지표
- FOMC와 빅테크 실적 원문
- 모니터링 종목별 거시 영향

### 2차

- 컨센서스 데이터 구독
- KRX 야간선물 실시간 또는 준실시간 시세
- 시간외 미국 주식 반응
- 이벤트 발표 직후 추가 알림
- 레짐 및 종목 영향 백테스트 화면

예상 구현 범위는 MVP 기준 8~12 개발일이다. 무료 공식 데이터 MVP를 먼저 안정화한 뒤
유료 컨센서스와 실시간 선물 데이터를 추가한다.

## 15. 사용자 준비사항

1. FRED API 키 발급
2. EIA API 키 발급
3. 한국은행 ECOS API 키 발급
4. 경제지표 컨센서스 유료 구독 여부 결정
5. 야간선물의 1차 대상이 KOSPI200, KOSDAQ150, 달러, 국채선물이 맞는지 확인
6. 오전 브리핑은 매일 발송하고 종목별 알림은 유의미한 변화만 발송하는 정책 확인

