# Thesis Monitor Knowledge Guide

## 시스템 목적

Thesis Monitor는 특정 종목의 투자 논리와 근거를 버전별로 저장하고 매일 점검한다. 동시에
금리, 물가, 유동성, 신용, 유가, 환율, 미국 주식시장, 빅테크 실적과 중앙은행 이벤트를
수집해 Macro Thesis와 종목별 영향을 평가한다.

이 시스템은 리서치와 의사결정 보조 도구이며 주문을 실행하지 않는다. 결과는 투자 권유나
수익 보장이 아니다.

## 데이터 계층

### 종목 계층

- 모니터링 종목과 활성 여부
- 버전이 있는 투자 Thesis
- 강화·약화·무효화 조건
- 날짜별 평가와 누적 근거
- 신규 매수자, 기존 보유자, 가격 위치 관점
- Thesis 버전별 거시 exposure

### 거시 계층

- FRED: 미국 금리, 실질금리, 기대인플레이션, 신용스프레드, VIX, 유가, 달러, 유동성
- EIA: 미국 원유 재고, 생산, 정제 가동률
- ECOS: 한국은행 기준금리, 원/달러 환율, CPI, M2 핵심 통계
- Federal Reserve: 통화정책 발표와 공식 문서
- Finnhub: 주요 빅테크 실적 일정
- ohlcv-analyst: 미국 지수·섹터 ETF와 빅테크 가격 변화

## 거시 레짐의 여섯 축

1. `growth_momentum`: 경기와 수요의 개선 또는 둔화
2. `inflation_pressure`: 물가 압력 상승 또는 하락
3. `liquidity_condition`: 중앙은행·달러 유동성 환경
4. `financial_conditions`: 실질금리와 신용 여건
5. `risk_appetite`: 주식, 변동성, 시장 폭의 위험선호
6. `earnings_momentum`: 기업 실적과 가이던스 방향

각 축은 -2에서 +2로 평가한다. 레짐은 하루 변동으로 쉽게 바꾸지 않으며, 근거가 부족한
전환은 `provisional` 또는 판단 유보로 표시한다.

## Macro Thesis

기본적으로 다음 경쟁 가설을 동시에 유지한다.

- 미국 연착륙과 점진적 디스인플레이션
- 연준 정책경로와 장기 실질금리
- AI CAPEX와 반도체 수요
- 중국 경기와 한국 수출 사이클
- 유가와 공급충격

상태는 `strengthening`, `intact`, `weakening`, `structural_break`로 표현한다. 단일 지표가
아니라 반복성, 지속성, 독립적인 교차 근거, 시장 반응을 함께 평가한다.

## 종목별 거시 영향

거시 변화는 종목마다 다른 전달 경로를 가진다.

- 실질금리 상승: 장기 성장주의 valuation에는 대체로 부정적
- 원/달러 상승: 수출 비중에는 긍정적일 수 있으나 수입 비용과 해외생산 조건을 확인
- 유가 상승: 항공·운송에는 비용 부담, 에너지 생산자에는 가격 효과 가능
- 신용스프레드 확대: 자금조달 민감 기업과 경기민감주에 부정적
- Hyperscaler CAPEX 확대: HBM·AI 반도체 수요 Thesis에 긍정적

방향만 단정하지 않고 exposure의 `weight`, `channel`, `condition`, `horizon`을 적용한다.
영향 결과는 `strengthen`, `weaken`, `mixed`, `neutral`과 magnitude 0에서 5로 저장된다.

## 데이터 품질

- `fresh`: 기대 빈도 안에 있는 최신 데이터
- `stale`: 기대 갱신 주기를 지난 데이터
- `partial`: 일부 provider가 누락된 브리핑
- `provisional`: 신뢰도나 지속성이 부족한 임시 레짐
- `revised`: 과거 발표치가 수정된 데이터

출처 누락이나 품질 경고가 있으면 결론의 강도를 낮춘다. 출처 URL과 기준 날짜가 없는
정량 판단은 확정 사실로 취급하지 않는다.

## 오전 모니터링

- 기본 실행: 매일 08:00 Asia/Seoul
- 재수집: 08:15, 08:45
- 공급자 하나의 실패는 전체 종목 모니터링을 중단시키지 않는다.
- 오전 Macro briefing은 날짜별 한 번만 카카오로 발송한다.
- 개별 종목의 `no_material_change`는 저장하지만 별도 카카오 알림을 보내지 않는다.
- SQLite와 `data/` 아래 JSON 기록에 날짜별 이력을 누적한다.

## Action 이름

- `getHealth`: 서버 상태
- `getProviderStatus`: 종목 자료 provider 상태
- `monitorStock`: 종목별 상세 논리·검증 지표·짧은 신호·구조화된 `price_rules`를 버전형으로 등록 또는 갱신
- `market_expectations`: 기준일의 시장 기대 수준과 이미 반영된 내용
- `valuation_framework`: 종목별 적정 평가법과 핵심 입력값
- `multiple_expansion_signals` / `multiple_compression_signals`: 멀티플 변화 조건
- `listMonitoredStockSummaries`: 모니터링 목록과 종목별 핵심 투자 논리
- `listMonitoredStocks`: 전체 상세 목록(대량 목록 조회에는 사용하지 않음)
- `getMonitoredStock`: 특정 종목의 현재 Thesis
- `stopMonitoringStock`: 이력을 보존하며 모니터링 중단
- `getThesisAssessmentHistory`: 종목의 날짜별 평가
- `getCompanyProfile`: 회사 기본 정보
- `getEarningsCheckpoints`: 실적 점검 항목
- `getThesisEvents`: Thesis 관련 최근 사건
- `getMacroBriefing`: 최신 오전 거시 브리핑
- `getMacroBriefingByDate`: 특정 날짜 거시 브리핑
- `getMacroRegime`: 최신 거시 레짐
- `getMacroTheses`: 경쟁 Macro Thesis 목록
- `getMacroEvents`: 거시·정책·실적 이벤트
- `getMacroProviderStatus`: 거시 provider 설정과 기능 상태
- `getTickerMacroImpacts`: 특정 종목의 거시 영향 이력
