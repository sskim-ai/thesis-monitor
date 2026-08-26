# 2026-08-26 US Morning Exact Natural Messages

- Evidence class: `NATURAL_PRODUCTION`
- Packet: `2026-08-26-us-run-39-d55fe527c8e9`
- Route: `deterministic_fallback`
- Delivered: `14/14`
- Ordering: actual `NotificationDelivery.id` order (`308` through `321`)
- Telegram message IDs: not retained in the stored receipt; no identifier is inferred.
- Text integrity: each DB `payload.text` matched its persisted deterministic payload byte-for-byte.

## 1. US_MARKET

- Entity: `🌎 미국 종목 점검 · 2026-08-26`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:308`
- Sent at UTC: `2026-08-25 23:40:06.854250`
- Content SHA-256: `7e3718f3e76450459c53f76695f8ee68ade3a099d64acf7110e5884afba5106d`

### Exact Text

```text
🌎 미국 종목 점검 · 2026-08-26
현재 환경: 혼합

🎯 오늘 한 줄
시장 방향이 엇갈려 가격 움직임보다 기업별 실적과 현금흐름 근거를 우선 확인할 환경입니다.

📈 중요한 변화
• 반도체가 S&P500을 1.2%p 웃돌았습니다. 가격 반응은 수요 심리 신호일 뿐, 실제 AI CAPEX 투자 논리 변화는 주문과 실적으로 확인해야 합니다.
• 그 외 주가지수·변동성에서는 투자 판단을 바꿀 정도의 큰 변화가 없었습니다.

🧭 현재 시장 상황
• 경기: 소형주와 경기민감 가격 신호가 함께 개선됐지만 실제 경기지표 개선이 확인된 것은 아닙니다.
• 물가: 물가 재가속과 빠른 안정 중 어느 방향도 뚜렷하지 않습니다.
• 유동성: 글로벌 유동성 방향을 바꿀 뚜렷한 달러 신호가 없습니다.

💡 투자적 의미
현재는 경기 확장 하나로 모든 위험자산이 오르는 시장이라기보다, 위험선호와 할인율 신호가 함께 가격을 결정하는 시장입니다.
실적이 실제로 개선되는 기업에는 상대적으로 우호적이지만, 높은 기대와 멀티플 확장에 의존하는 종목은 금리와 현금흐름을 함께 확인해야 합니다.

🔄 시장 가정
미국 연착륙과 점진적 디스인플레이션
→ 상태: 유지
→ 현재 신호: 약한 긍정
→ 이유: 성장 급락과 물가 재가속의 동시 신호가 없음
AI CAPEX와 반도체 수요
→ 상태: 유지
→ 현재 신호: 약한 긍정
→ 이유: 반도체 가격 신호는 우호적이나 실제 CAPEX·주문 확인 전 강화하지 않음
중국 경기와 한국 수출 사이클
→ 상태: 유지
→ 현재 신호: 약한 긍정
→ 이유: 성장민감 가격 신호는 우호적이나 한국 수출·중국 실물 확인 필요

📊 13종목 상태
투자 논리 · 강화 0 · 유지 13 · 약화/검토 0 · 무효화 0
Valuation · 확장 0 · 중립 13 · 혼재 0 · 압축 0 · 판단 자료 부족 0
전체 13개 종목 평가 완료

📅 오늘/근접 일정
오늘:
• NVDA quarterly earnings

⚠️ 데이터 주의
• eia: WCRFPUS2: ReadTimeout
• ohlcv_analyst: XLC: HTTPStatusError
• 한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해 오늘 개장 전 신호에서 제외했습니다.
누락·지연 데이터가 관련 시장 판단의 강도를 낮췄습니다.
```

## 2. CORZ

- Entity: `🏢 Core Scientific, Inc.(CORZ)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:309`
- Sent at UTC: `2026-08-25 23:40:07.936300`
- Content SHA-256: `ad1bc0cb49fc044c858fd30e17cfdf9a2ed58d139793a69f4a98df57cd557e3e`

### Exact Text

```text
🏢 Core Scientific, Inc.(CORZ)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 매우 높음

🎯 핵심
Core Scientific은 비트코인 채굴 중심 사업에서 AI/HPC 데이터센터 코로케이션 중심으로 전환 중이며, 2026년 2분기 매출의 약 83%가 colocation에서 발생하고 colocation gross margin이 약 59%까지 올라온 점이 핵심 근거다. 이미 437MW가 billing 중이고 총 leased customer power가 약 1.1GW, 잠재 계약가치가 240억달러 이상으로 확대되어 세 종목 중 '계약→가동→청구→매출' 전환이 가장 많이 증명됐다.

📈 사업·실적
2026 회계연도 상반기 누계 build-out 단계의 PPE 투자 후 잉여현금흐름은 $-723.29M입니다. 전년 비교기간보다 음수 폭이 커졌고 build-out 재투자는 가동·청구 전환과 자금조달을 함께 봅니다.

👁 핵심 감시
• 가동 지연 또는 계약 변경
• CAPEX·부채 증가 대비 매출 전환 지연
• 대규모 희석과 내부통제 문제 지속

💰 가격
현재가: $18.03 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $17.45~$18.38
• 동적 저항: $18.20~$18.73
• 가까운 지지·저항 구간이 겹쳐 현재가 기준 차트 손익비는 계산하지 않습니다.
보유자:
• 차트 무효화 가격: $16.70
• 동적 지지 유지 여부: $17.45~$18.38
가격 규칙 이력:
• 등록 확인선 $22.40은 아직 도달하지 않았습니다.

📐 Valuation
PER: N/M
fPER: N/M
과거 대비:
PBR 중앙값 0.5배
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증 가능한 현재 배수가 없어 Valuation 해석을 보류합니다.

📌 다음 확인
• colocation 매출 성장률과 gross margin
• billing MW와 leased MW의 분기별 증가
• 1.1GW 계약용량의 준공·가동 일정 준수 여부
```

## 3. CRCL

- Entity: `🏢 Circle Internet Group(CRCL)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:310`
- Sent at UTC: `2026-08-25 23:40:08.989737`
- Content SHA-256: `8918639560279a45e2bbcab6207be0873a8d98b356c8a52401a538665b9454a0`

### Exact Text

```text
🏢 Circle Internet Group(CRCL)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
USDC 유통량과 온체인 사용 증가가 장기 성장의 핵심이지만, reserve income 의존도를 낮추고 비이자성 플랫폼·결제 수익이 반복 가능한 이익으로 전환되는지가 재평가의 핵심이다. 금리 하락 시 reserve yield가 낮아져도 USDC 성장과 비이자 수익 확대가 adjusted EBITDA와 FCF를 방어할 수 있어야 한다.

📈 사업·실적
2026 회계연도 상반기 누계 준비금·플랫폼 사업의 PPE 투자 후 잉여현금흐름은 $528.12M입니다. 전년 비교기간보다 늘었고 준비금 수익과 비이자 플랫폼 수익의 현금전환을 함께 봅니다.

👁 핵심 감시
• USDC 점유율 둔화
• reserve yield 하락과 수익배분 부담으로 정상화 이익 하락
• 현재 금리 수익을 구조적 이익으로 오인할 위험

💰 가격
현재가: $92.02 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $82.01~$86.53
• 가까운 유효 저항이 없어 현재가 기준 차트 손익비는 계산하지 않습니다.
보유자:
• 차트 무효화 가격: $79.07
• 동적 지지 유지 여부: $82.01~$86.53
가격 규칙 이력:
• 기존 $72.70 확인선은 이미 돌파한 상태입니다.

📐 Valuation
PBR = 현재가 ÷ BVPS = $92.02 ÷ $12.85 = 7.2배
과거 대비:
PBR 중앙값 5.4배
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PBR과 과거 장부가 배수 분포를 함께 확인하며, 이익 기반 배수는 사용하지 않습니다.

📌 다음 확인
• USDC 유통량과 점유율
• 온체인 거래량
• 비이자성 매출 비중
```

## 4. GOOGL

- Entity: `🏢 Alphabet Inc. Class A(GOOGL)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:311`
- Sent at UTC: `2026-08-25 23:40:10.055683`
- Content SHA-256: `74b2b3b171d7cf5c591a794dc545caf1caf70051889825c8552d130e435b5089`

### Exact Text

```text
🏢 Alphabet Inc. Class A(GOOGL)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 높음

🎯 핵심
Search 광고의 견조한 성장과 Google Cloud의 고성장·마진 개선, AI 수요 확대가 이익 성장을 지지한다. 다만 대규모 AI CAPEX로 FCF 변동성이 커질 수 있어 Cloud 성장·backlog 확대와 CAPEX 대비 ROIC·FCF 회복이 핵심이다.

📈 사업·실적
2026 회계연도 상반기 누계 AI·Cloud 확장의 PPE 투자 후 잉여현금흐름은 $4.26B입니다. 전년 비교기간보다 줄었고 AI·Cloud 투자 회수는 Cloud 성장·마진과 함께 봅니다.

👁 핵심 감시
• Search 수익화 약화
• CAPEX 증가가 FCF와 ROIC를 장기간 훼손
• AI 투자비와 감가상각 시차

💰 가격
현재가: $346.96 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 유지 여부 점검
신규 관찰자:
• 동적 지지: $343.65~$353.79
• 동적 저항: $370.37~$378.79
• 현재가 기준 차트 손익비: 3배
보유자:
• 차트 무효화 가격: $339.16
• 동적 지지 유지 여부: $343.65~$353.79
가격 규칙 이력:
• 등록 확인선 $375은 아직 도달하지 않았습니다.

📐 Valuation
PER = 현재가 ÷ TTM EPS = $346.96 ÷ $27.90 = 12.4배
PBR = 현재가 ÷ BVPS = $346.96 ÷ $52.37 = 6.6배
과거 대비:
PER 중앙값 16.1배 · 14백분위 · PBR 중앙값 6.7배 · 48백분위
현재 Valuation: 다소 할인
해석: 현재 배수를 그 시점에 공개된 재무정보로 재구성한 역사적 분포와 비교했습니다.
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PER/PBR과 과거 배수 분포를 함께 확인합니다.

📌 다음 확인
• Cloud 성장률과 backlog
• Cloud 영업이익률
• Search monetization
```

## 5. HUT

- Entity: `🏢 Hut 8 Corp.(HUT)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:312`
- Sent at UTC: `2026-08-25 23:40:11.137647`
- Content SHA-256: `9d290c8615b55b987d84acf879634af88cb3aaf998d17034839ed3fa8ffb52bc`

### Exact Text

```text
🏢 Hut 8 Corp.(HUT)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 매우 높음

🎯 핵심
Hut 8은 비트코인 채굴·전력 인프라 자산에서 AI/HPC 데이터센터 인프라 사업으로 확장 중이며, 2026년 8월 기준 약 949MW 계약 IT 용량, 약 266억달러 base-term 계약가치, 연간 NOI 17.5억달러 이상 기대와 investment-grade 상대방 기반의 장기 계약이 핵심 가치 근거다. 장기 기업가치 옵션은 매우 크지만 현재 손익은 여전히 Compute/채굴 비중이 높고, 대형 계약이 실제 준공·가동·NOI로 전환되는 실행 리스크가 크다.

👁 핵심 감시
• 준공 지연·전력 인입 문제
• NOI 하향 조정
• 과도한 모회사 자본투입 또는 희석

💰 가격
현재가: $85.50 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $84.11~$89.67
• 동적 저항: $101.61~$106.89
• 현재가 기준 차트 손익비: 2.67배
보유자:
• 차트 무효화 가격: $79.46
• 동적 지지 유지 여부: $84.11~$89.67
가격 규칙 이력:
• 등록 확인선 $97은 아직 도달하지 않았습니다.

📐 Valuation
PER: N/M
PBR = 현재가 ÷ BVPS = $85.50 ÷ $12.26 = 7.0배
fPER = 현재가 ÷ 시장 예상 EPS = $85.50 ÷ $0.59 = 144.9배
과거 대비:
PER 중앙값 5.6배 · PBR 중앙값 3.6배 · 75백분위
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PBR과 예상 이익 배수를 사용하며, 사용할 수 없는 trailing PER은 제외합니다.

⚠️ 데이터 주의
• 최신 정식 재무 반영이 지연돼 현재 Valuation 신뢰도를 낮춰 봅니다.

📌 다음 확인
• 계약 949MW의 준공·가동 일정과 실제 billing/NOI 발생
• 평균 연간 NOI 17.5억달러 이상 기대치의 실현 여부
• 프로젝트별 CAPEX·project financing·모회사 equity 투입 규모
```

## 6. IBM

- Entity: `🏢 IBM(IBM)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:313`
- Sent at UTC: `2026-08-25 23:40:12.234514`
- Content SHA-256: `23ab6d3aa8f6120633a294c2a55c6165af9a95aed163573a33344ef7412c2db7`

### Exact Text

```text
🏢 IBM(IBM)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 균형

🎯 핵심
Software·Red Hat·AI 관련 성장과 반복매출 확대가 중기 성장을 지지하지만, 회사 전체 매출 성장과 FCF 가속은 아직 충분히 증명되지 않았다. Consulting 회복과 Software 성장률, FCF 증가가 핵심이며 차트상 223~230달러 지지와 250달러 안착, 258~260달러 돌파를 가격 확인 신호로 본다.

📈 사업·실적
2026 회계연도 상반기 누계 Software·Consulting 사업의 PPE 투자 후 잉여현금흐름은 $7.3B입니다. 전년 비교기간보다 늘었고 Software·Consulting 전환과 인수자금 부담을 함께 봅니다.

👁 핵심 감시
• Software 성장 둔화
• Consulting 부진과 FCF 정체
• 인수 관련 무형자산과 조정이익 의존

💰 가격
현재가: $234.19 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $231.55~$235.56
• 동적 저항: $239.37~$244.23
• 현재가 기준 차트 손익비: 0.8배
보유자:
• 차트 무효화 가격: $227.71
• 동적 지지 유지 여부: $231.55~$235.56
가격 규칙 이력:
• 등록 확인선 $250은 아직 도달하지 않았습니다.

📐 Valuation
PER = 현재가 ÷ TTM EPS = $234.19 ÷ $16.56 = 14.1배
PBR = 현재가 ÷ BVPS = $234.19 ÷ $36.14 = 6.5배
fPER: 17.4배
fPBR = 현재가 ÷ 내부 FY1 추정 BVPS = $234.19 ÷ $34.28 = 6.8배
※ 내부 모델 추정치이며 시장 컨센서스가 아닙니다.
과거 대비:
PER 중앙값 15.3배 · 41백분위 · PBR 중앙값 6.5배 · 49백분위
현재 Valuation: 중립 범위
해석: 현재 배수를 그 시점에 공개된 재무정보로 재구성한 역사적 분포와 비교했습니다.

⚠️ 데이터 주의
• 최신 정식 재무 반영이 지연돼 현재 Valuation 신뢰도를 낮춰 봅니다.

📌 다음 확인
• Software 성장률
• Red Hat 성장률
• Consulting backlog와 매출
```

## 7. MU

- Entity: `🏢 Micron Technology(MU)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:314`
- Sent at UTC: `2026-08-25 23:40:13.428105`
- Content SHA-256: `102e3ae1a040b827890c8d97c9cfeb6ddf1cd8829307943d6ea01358d6f1fca6`

### Exact Text

```text
🏢 Micron Technology(MU)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 매우 높음

🎯 핵심
AI 서버·HBM·고부가 DRAM 수요가 Micron의 가격·믹스와 수익성을 구조적으로 끌어올리고 있으며, 장기 고객계약(SCA/RPO)과 대규모 FCF가 과거 메모리 사이클보다 높은 이익 가시성을 제공하는지가 핵심 투자 논리다. 2026-08-12 OHLCV 기준 MU는 월봉·주봉의 장기 상승 레짐이 유지되는 가운데 주봉 MACD와 주요 OSC가 플러스이고, 일봉 MACD histogram도 빠르게 개선되어 SKHY보다 중기 추세 구조가 안정적이다.

📈 사업·실적
2026 회계연도 3분기 누계 메모리 증설의 PPE 투자 후 잉여현금흐름은 $26.1B입니다. 전년 비교기간보다 늘었고 ASP·제품 믹스·재고 사이클과 설비투자 시점을 함께 봅니다.

👁 핵심 감시
• 메모리 ASP 상승률 조기 둔화 또는 가격 하락
• gross margin이 peak 수준에서 예상보다 빠르게 압축
• CAPEX 급증으로 FCF가 크게 감소

💰 가격
현재가: $932.97 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 위험 관리 필요
신규 관찰자:
• 동적 지지: $868.39~$914.93
• 동적 저항: $1,018.09~$1,054.17
• 현재가 기준 차트 손익비: 0.88배
보유자:
• 차트 무효화 가격: $835.70
• 동적 지지 유지 여부: $868.39~$914.93
가격 규칙 이력:
• 등록 확인선 $950은 아직 도달하지 않았습니다.

📐 Valuation
PER = 현재가 ÷ TTM EPS = $932.97 ÷ $48.93 = 19.1배
PBR = 현재가 ÷ BVPS = $932.97 ÷ $89.22 = 10.5배
fPER: 5.9배
fPBR = 현재가 ÷ 내부 FY1 추정 BVPS = $932.97 ÷ $163.09 = 5.7배
※ 내부 모델 추정치이며 시장 컨센서스가 아닙니다.
과거 대비:
PER 중앙값 16.8배 · 66백분위 · PBR 중앙값 2.2배 · 96백분위
현재 Valuation: 부담 구간
해석: 사이클 기업은 낮은 trailing PER를 할인 근거로 쓰지 않고 PBR과 정상화 이익을 우선했습니다.

⚠️ 데이터 주의
• fPER는 산출 기간이 명확하지 않아 참고 수준입니다.

📌 다음 확인
• 분기 매출·gross margin·operating margin과 DRAM/NAND ASP 방향
• HBM4 출하·고객 qualification 및 HBM4E 상용화 진행
• Strategic Customer Agreement·RPO·고객 예치금 규모와 실제 매출 전환
```

## 8. RXRX

- Entity: `🏢 Recursion Pharmaceuticals(RXRX)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:315`
- Sent at UTC: `2026-08-25 23:40:14.526481`
- Content SHA-256: `13f743d483765839a430ec932f26adc4e82ab14ef03fd60a282f63013956aeb2`

### Exact Text

```text
🏢 Recursion Pharmaceuticals(RXRX)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
AI 기반 신약발굴 플랫폼이 실제 파트너 타깃 선택과 임상 후보 진전으로 이어지는지가 핵심이다. 최근 Genentech 공동연구 타깃 선택과 임상 진전은 초기 강화 신호지만, 높은 현금소진과 임상 실패·희석 위험이 크다.

📈 사업·실적
2026 회계연도 상반기 누계 연구개발 단계의 PPE 투자 후 잉여현금흐름은 $-187.35M입니다. 전년 비교기간보다 음수 폭이 줄었고 현금소진 근거로만 쓰며 보유현금 근거 없이 runway를 계산하지 않습니다.

👁 핵심 감시
• 임상 실패 또는 일정 지연
• 현금소진과 희석이 예상 상회
• 초기 파이프라인의 높은 실패확률

💰 가격
현재가: $3.56 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $2.88~$2.96
• 동적 저항: $3.71~$3.91
• 현재가 기준 차트 손익비: 0.19배
보유자:
• 차트 무효화 가격: $2.77
• 동적 지지 유지 여부: $2.88~$2.96
가격 규칙 이력:
• 기존 $3.36 확인선은 이번에 돌파했습니다.

📐 Valuation
PER: N/M
PBR = 현재가 ÷ BVPS = $3.56 ÷ $1.71 = 2.1배
fPER: N/M
과거 대비:
PBR 중앙값 3.3배 · 19백분위
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PBR과 과거 장부가 배수 분포를 함께 확인하며, 이익 기반 배수는 사용하지 않습니다.

📌 다음 확인
• 주요 임상 일정과 데이터
• 파트너 타깃 선택
• milestone·파트너 매출
```

## 9. SKHY

- Entity: `🏢 SK hynix Inc. ADR(SKHY)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:316`
- Sent at UTC: `2026-08-25 23:40:15.568246`
- Content SHA-256: `4fb107f97d198565156b0d15f816829eea75bc4088c14aa7594b04008450874e`

### Exact Text

```text
🏢 SK hynix Inc. ADR(SKHY)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
SK hynix의 기업가치는 HBM4/HBM4E 중심의 AI 메모리 기술·공급 리더십, 장기 고객계약, DRAM/NAND 동반 업황 개선으로 지지된다. 다만 SKHY는 1 ADR=한국 보통주 0.1주 구조에서 미국 내 희소성 프리미엄이 본주 대비 크게 형성될 수 있어, 기초기업 펀더멘털과 ADR 자체의 가격·괴리 리스크를 반드시 분리해 본다.

👁 핵심 감시
• HBM4 출하 또는 고객 인증 지연
• DRAM/NAND 가격 조기 하락
• hyperscaler AI CAPEX 둔화

💰 가격
현재가: $159.53 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 가까운 유효 저항이 없어 현재가 기준 차트 손익비는 계산하지 않습니다.
보유자:
• 유효한 동적 지지와 차트 무효화 가격이 없어 현재 가격 관리 기준은 제공하지 않습니다.
가격 규칙 이력:
• 등록 확인선 $163은 아직 도달하지 않았습니다.

📐 Valuation
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
예탁증권 identity는 확인됐지만 current-security denominator·share·currency basis를 확인하지 못해 배수 해석을 보류합니다.

⚠️ 데이터 주의
• 현재 거래 증권의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류했습니다.

📌 다음 확인
• HBM4/HBM4E 출하량·매출 비중과 주요 고객 채택
• DRAM/NAND ASP 방향과 영업이익률
• 영업현금흐름·FCF·CAPEX 및 순현금 추이
```

## 10. SNDK

- Entity: `🏢 SanDisk(SNDK)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:317`
- Sent at UTC: `2026-08-25 23:40:16.644020`
- Content SHA-256: `47561ee950e0f779fe83583f6f5c8d5a276bebb780bd6a375d5e4113d782e6c8`

### Exact Text

```text
🏢 SanDisk(SNDK)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
AI inference와 데이터센터 SSD/NAND 수요, 장기 고객 계약과 높은 RPO가 강한 매출·마진·FCF를 지지한다. 다만 최근 초고마진의 상당 부분이 NAND 가격 상승에 의존할 가능성이 있어 가격 사이클과 계약의 실제 매출 전환을 확인해야 한다.

📈 사업·실적
2026 회계연도 연간 메모리 증설의 PPE 투자 후 잉여현금흐름은 $11.49B입니다. ASP·제품 믹스·재고 사이클과 설비투자 시점을 함께 봅니다.

👁 핵심 감시
• NAND 가격 반전
• RPO 전환 지연 또는 재고 증가
• 가격 상승기 마진을 영구화할 위험

💰 가격
현재가: $1,480.77 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $950.35~$1,046.03
• 동적 저항: $1,785.67~$1,870.31
• 현재가 기준 차트 손익비: 0.5배
보유자:
• 차트 무효화 가격: $874.30
• 동적 지지 유지 여부: $950.35~$1,046.03
가격 규칙 이력:
• 기존 $1,310 확인선은 이미 돌파한 상태입니다.

📐 Valuation
PBR = 현재가 ÷ BVPS = $1,480.77 ÷ $107.78 = 13.7배
과거 대비:
PER 중앙값 19.1배 · PBR 중앙값 9.8배 · 62백분위
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PBR과 과거 장부가 배수 분포를 함께 확인하며, 이익 기반 배수는 사용하지 않습니다.

📌 다음 확인
• NAND 가격
• 데이터센터 매출
• RPO 매출 전환
```

## 11. TSLA

- Entity: `🏢 Tesla, Inc.(TSLA)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:318`
- Sent at UTC: `2026-08-25 23:40:17.733107`
- Content SHA-256: `021a8e9c8a1187899e814c531594408f62f6b4857938dcc9c8300a99bba36db6`

### Exact Text

```text
🏢 Tesla, Inc.(TSLA)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
Robotaxi/FSD/AI의 고마진 수익화가 장기 기업가치의 핵심이다. 현재는 매출·인도 회복에도 영업이익률 저하로 투자 논리에 초기 균열이 있으며, 향후 자동차·서비스 마진 회복, Robotaxi 경제성이 증명되어야 한다.

📈 사업·실적
2026 회계연도 상반기 누계 자동차 성장투자의 PPE 투자 후 잉여현금흐름은 $352M입니다. 전년 비교기간보다 줄었고 자동차 마진과 성장투자 회수를 함께 봅니다.

⚠️ 기존 경고
• 영업이익률 저하 확인

👁 핵심 감시
• Robotaxi 규제·상용화 지연
• 자동차 마진과 FCF 부진 장기화
• 먼 미래 현금흐름에 대한 과도한 종단가치

💰 가격
현재가: $350.25 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $334.74~$341.26
• 동적 저항: $360.04~$372.58
• 현재가 기준 차트 손익비: 0.44배
보유자:
• 차트 무효화 가격: $327.98
• 동적 지지 유지 여부: $334.74~$341.26
가격 규칙 이력:
• 기존 $342 확인선은 이미 돌파한 상태입니다.

📐 Valuation
PER = 현재가 ÷ TTM EPS = $350.25 ÷ $1.92 = 182.4배
PBR = 현재가 ÷ BVPS = $350.25 ÷ $21.99 = 15.9배
과거 대비:
PER 중앙값 68.5배 · 96백분위 · PBR 중앙값 16.5배 · 47백분위
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PER/PBR과 과거 배수 분포를 함께 확인합니다.

📌 다음 확인
• Robotaxi 유료 운행과 단위경제성
• FSD 구독자와 매출
• 자동차 영업이익률
```

## 12. TSM

- Entity: `🏢 TSMC(TSM)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:319`
- Sent at UTC: `2026-08-25 23:40:18.808236`
- Content SHA-256: `d5bc26224f2943362ef33358932b0c4b151498d2aadba1160e7c67ec4dec8e86`

### Exact Text

```text
🏢 TSMC(TSM)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 매우 높음

🎯 핵심
AI/HPC 수요와 첨단공정 지배력, 높은 가동률과 가격결정력이 높은 gross margin과 현금창출을 지지한다. 핵심 변수는 hyperscaler CAPEX 지속성, 첨단공정 가동률, 해외 팹 비용에 따른 마진 희석이다.

👁 핵심 감시
• hyperscaler CAPEX 둔화
• 해외 팹 비용과 감가상각으로 마진 하락
• 지정학 할인

💰 가격
현재가: $417.41 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $380.77~$390.31
• 동적 저항: $432.30~$439.78
• 현재가 기준 차트 손익비: 0.34배
보유자:
• 차트 무효화 가격: $374.08
• 동적 지지 유지 여부: $380.77~$390.31
가격 규칙 이력:
• 등록 확인선 $432은 아직 도달하지 않았습니다.

📐 Valuation
※ 최근 분기 잠정실적의 매출·영업이익을 반영했습니다.
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
증권 유형과 주당 기준의 일치 여부를 확인하지 못해 배수 해석을 보류합니다.

⚠️ 데이터 주의
• 최신 정식 재무 반영이 지연돼 현재 Valuation 신뢰도를 낮춰 봅니다.
• 최근 공식 잠정실적의 매출·영업이익은 반영했지만 주당 기준을 확인하지 못해 자체 PER 계산은 보류했습니다.

📌 다음 확인
• hyperscaler CAPEX
• 첨단공정 가동률
• wafer ASP
```

## 13. WRD

- Entity: `🏢 WeRide(WRD)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:320`
- Sent at UTC: `2026-08-25 23:40:19.853425`
- Content SHA-256: `a9fea90aa9d339100a406d1a975e7996b5ef62500c19c60816a5ef4e4af29b37`

### Exact Text

```text
🏢 WeRide(WRD)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
Robotaxi 기술과 규제 승인, fleet 확대가 실제 유료 이용률과 매출 성장으로 이어지고 있으나 아직 operating loss가 크다. 핵심은 Robotaxi revenue·fleet utilization·gross margin·operating loss 축소와 현금소진이다.

👁 핵심 감시
• 승인·상용화 지연
• fleet 확대에도 손실과 현금소진 증가
• 초기 매출의 낮은 품질

💰 가격
현재가: $6.08 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $5.91~$6.15
• 동적 저항: $6.38~$6.52
• 현재가 기준 차트 손익비: 0.93배
보유자:
• 차트 무효화 가격: $5.75
• 동적 지지 유지 여부: $5.91~$6.15
가격 규칙 이력:
• 등록 확인선 $6.68은 아직 도달하지 않았습니다.

📐 Valuation
PER: N/M
fPER: N/M
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
증권 유형과 주당 기준의 일치 여부를 확인하지 못해 배수 해석을 보류합니다.

⚠️ 데이터 주의
• 최신 정식 재무 반영이 지연돼 현재 Valuation 신뢰도를 낮춰 봅니다.
• 현재 거래 증권의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류했습니다.

📌 다음 확인
• 유료 서비스 지역
• fleet 규모
• 차량당 이용률
```

## 14. WULF

- Entity: `🏢 TeraWulf Inc.(WULF)`
- Route: `deterministic_fallback`
- Renderer: `ai-assisted-pilot-renderer-v3`
- Canary selected: `false`
- Fallback: `true`
- Validation: `BACKEND_DETERMINISTIC_PAYLOAD_MATCH`
- Delivered: `true`
- Receipt: `notificationdelivery:321`
- Sent at UTC: `2026-08-25 23:40:20.939501`
- Content SHA-256: `3557cca430aa9c2aefb3f3f459013c87a91c45325b103378b1a0d814a70cd74a`

### Exact Text

```text
🏢 TeraWulf Inc.(WULF)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 높아진 상태

시장 기대: 투기적 기대

🎯 핵심
TeraWulf는 비트코인 채굴 사업에서 AI/HPC 데이터센터 임대사업으로 빠르게 전환 중이며, 2026년 2분기 매출의 약 71%가 HPC lease revenue에서 발생하고 102MW가 가동된 상태에서 추가 336MW를 건설 중인 점이 핵심 근거다. Anthropic 관련 약 401MW, 20년, 초기 계약가치 약 190억달러의 장기 계약은 큰 성장 옵션이지만, 현재 Adjusted EBITDA 적자, 대규모 CAPEX, 높은 주식보상과 2026년 신규 주식발행 등으로 주주가치 전환은 아직 증명이 필요하다.

📈 사업·실적
2026 회계연도 상반기 누계 build-out 단계의 PPE 투자 후 잉여현금흐름은 $-1.53B입니다. 전년 비교기간보다 음수 폭이 커졌고 build-out 재투자는 가동·청구 전환과 자금조달을 함께 봅니다.

👁 핵심 감시
• 준공 지연·고객 인도 차질
• Adjusted EBITDA 적자 장기화
• 대규모 추가 증자·주식보상·부채 증가

💰 가격
현재가: $16.32 · 2026-08-25 미국장 종가
현재 구조: 가격 구조상 추가 확인 대기
신규 관찰자:
• 동적 지지: $16.00~$17.09
• 동적 저항: $17.32~$18.12
• 현재가 기준 차트 손익비: 0.93배
보유자:
• 차트 무효화 가격: $15.24
• 동적 지지 유지 여부: $16.00~$17.09
가격 규칙 이력:
• 등록 확인선 $18.40은 아직 도달하지 않았습니다.

📐 Valuation
PER: N/M
PBR = 현재가 ÷ BVPS = $16.32 ÷ $0.30 = 55.3배
과거 대비:
PBR 중앙값 3.2배 · 100백분위
현재 Valuation: 판단 자료 부족
오늘 Valuation 변화: 판단 자료 부족
검증된 현재 PBR과 과거 장부가 배수 분포를 함께 확인하며, 이익 기반 배수는 사용하지 않습니다.

📌 다음 확인
• HPC lease revenue 성장률과 전체 매출 내 비중
• 가동 MW·건설 MW·준공 일정
• Adjusted EBITDA의 흑자 전환 여부
```
