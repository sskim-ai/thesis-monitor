# Thesis Monitor 통합 정확도 보완 결과

기준일: 2026-08-11

## 1. 변경 파일

- 재무 수집/정규화: `app/providers/filings.py`, `app/services/financial_snapshot_service.py`, `app/services/financial_validation.py`
- Valuation: `app/services/valuation_snapshot_service.py`
- 일일 평가/가격/경고: `app/services/thesis_evaluation_service.py`, `app/services/daily_monitor_service.py`
- 메시지: `app/services/daily_digest.py`, `app/services/notification_service.py`
- 저장 구조: `app/models/financial.py`, `app/database.py`, `app/schemas/thesis.py`
- 운영 도구: `app/jobs/backfill_financials.py`, `app/jobs/smoke_daily.py`
- Action schema: `openapi.action.json`, `docs/custom_gpt_action_schema*.yaml`
- 회귀 테스트: `tests/test_integrated_accuracy.py`

## 2. DB schema 및 migration

기존 thesis/assessment/event history는 삭제하지 않았다. `financialsnapshot`에 다음 정보를 비파괴 컬럼 추가 방식으로 확장했다.

- fiscal year, period scope, cumulative 여부, normalization method
- standalone/cumulative revenue, operating income, owners-parent net income, EPS
- total/common equity, issued/treasury/outstanding/diluted shares
- financial basis warning, margin quality warning, financial as-of

실제 SQLite migration을 적용했고 기존 이력은 유지됐다.

## 3. 일일 assessment 흐름

모든 활성 종목을 평가한 뒤 DB 저장을 완료하고 renderer와 notification queue를 실행한다. 신규 material event가 없으면 `no_material_change`가 기본이다. 가격 event는 business thesis evidence에서 제외되며, Valuation은 오늘 실제로 충족된 회사 조건과 material macro effect만 사용한다.

## 4. Event dedupe와 relevance

- ticker/date/type/provider/source identifier를 이용한 fingerprint를 assessment에 저장한다.
- 이전 assessment가 사용한 fingerprint와 URL은 다시 delta evidence로 쓰지 않는다.
- 무관한 타사 뉴스와 낮은 관련성 기사는 `non_thesis_noise`로 제외한다.
- background fact와 new confirmed fact를 분리한다.

## 5. Business thesis delta

이전 assessment 이후의 신뢰 가능한 신규 회사 사실만 강화/약화에 사용한다. 가격 지지·돌파, VIX, SOXX 하루 움직임은 사업 투자 논리를 바꾸지 않는다. 큰 상태 전이는 신규 material evidence가 없으면 제한한다.

## 6. Structural risk와 warning lifecycle

- `business_thesis_change`, `structural_risk_level`, `review_required`를 분리한다.
- 경고를 `new_warnings_today`, `open_confirmed_warnings`, `persistent_watch_risks`로 구분한다.
- warning state에 stable id, opened/last-confirmed date, status, resolution condition, source event ids를 저장한다.
- 신규 이벤트가 없어도 기존 open warning은 유지한다.

## 7. 재무 숫자 validation과 기간 정규화

- 지원 단위를 명시적으로 KRW/USD 기준으로 정규화한다.
- 영업이익 절댓값이 매출보다 크거나 margin cross-check가 어긋나면 confirmed fact에서 숫자를 제외한다.
- Q1은 단일분기, Q2는 H1-Q1, Q3는 9M-H1, Q4는 FY-9M 방식으로 정규화한다.
- 이전 누적치가 없으면 임의 단일분기 값을 만들지 않는다.
- OpenDART 표준계정과 전체계정 API를 함께 사용하고 XBRL account id를 한글 계정명보다 우선한다.

## 8. Macro 처리

- persistent market assumption과 today signal을 분리한다.
- VIX는 risk appetite/valuation sentiment 보조 신호이며 매출·EPS에 직접 연결하지 않는다.
- 실질금리는 기본적으로 discount-rate/Valuation 경로로 처리한다.
- 환율은 종목별 exposure condition이 없으면 mixed/unknown으로 둔다.
- stale 금리/달러 데이터는 neutral이 아니라 판단 유보로 출력한다.

## 9. Price state

현재가와 등록 규칙으로 다음 상태를 계산한다.

- `above_confirmation`
- `between_confirmation_and_support`
- `inside_support`
- `below_support`
- `below_warning`
- `below_invalidation`
- `no_price_rule`

장중은 provisional, 종가는 confirmed로 분리한다. 이미 확인 가격을 상회한 경우 미래형 돌파 문구를 쓰지 않는다. 내부 `invalidation_price`의 사용자 표시는 재점검 가격으로 유지한다.

## 10. Valuation snapshot

각 배수에 value, status, source type, method, price/financial as-of, quality, confidence, warnings를 저장한다.

- trailing PER: provider 우선, 없으면 TTM diluted EPS, 다음으로 owners-parent common net income
- trailing PBR: provider 우선, 없으면 owners-parent common equity/current common shares
- forward PER/PBR: consensus provider 우선, 조건을 충족할 때만 FY1 deterministic model
- 내부 forward 값은 `modeled_forward`로 저장하고 사용자에게 `내부 추정 fPER/fPBR`로 표시한다.
- provider 값과 derived 값 차이가 설정 임계치를 넘으면 discrepancy warning을 남긴다.
- 음수 earnings는 PER 숫자 대신 N/M으로 표시한다.

## 11. 업종별 모델

- 보험: normalized ROE와 common equity 중심, P/B-ROE 우선
- 메모리: 8개 분기 normalized/cycle-adjusted margin 사용, 최근 분기 단순 연율화 금지
- SOTP: 삼성전자/POSCO홀딩스에는 일반 FY1 forward 모델 미적용
- 바이오/Robotaxi: 적자 상태에서 PER/fPER를 억지 생성하지 않음
- Tesla/scenario 종목: provider multiple은 참고 자료로만 표시

## 12. Valuation relative position

`valuation_context`는 오늘 변화, `valuation_relative_position`은 현재 배수 위치다. 숫자로 된 historical/peer range가 없으면 `unknown`으로 유지한다. 현재 14종목은 비교 range가 정형 데이터로 저장되어 있지 않아 모두 `unknown`이며, 텍스트 설명만으로 저평가/고평가를 단정하지 않는다.

## 13. Confidence

50% 고정값을 제거했다. 가격/Valuation 품질, stale 여부, unknown 수, 미검증 event 수, 확정 provider 상태를 반영한다. provider 조회가 정상이고 신규 event가 없다는 사실 자체는 confidence를 낮추지 않는다.

## 14. LLM 비호출

Daily digest, daily stock analysis, macro morning, material event alert payload는 모두 `use_llm=false`로 생성된다. 일일 기본 경로는 deterministic rule engine과 renderer만 사용한다.

## 15. KRX 5년 backfill

- 000660: 20/20 저장
- 003690: 22/36 저장, 14건은 usable snapshot 미생성
- 005490: 29/30 저장, provider warning 2건
- 005930: 20/20 저장
- 086280: 23/23 저장

## 16. Regression tests

전체 103개 테스트 통과. 신규 테스트는 누적분기 차감, prior 누락 시 계산 금지, OpenDART Q3/누적 scope, common-share parsing, derived PER/PBR, N/M, FY1 model gate/label, SOTP 제외, price state, confidence, warning metadata를 포함한다.

## 17. 14종목 smoke test

- 실행: 14개
- 성공: 14개
- 실패: 0개
- business thesis: no_material_change 14
- valuation context: neutral 14
- valuation distribution warning: 없음

KRX 5종목은 trailing PER/PBR이 `derived_trailing`으로 산출됐다. 000660/003690/086280은 조건을 통과해 내부 FY1 fPER/fPBR이 생성됐고, SOTP인 005490/005930은 forward model을 생성하지 않았다. 미국 종목은 Finnhub trailing/consensus forward 값을 사용하며 forward PBR은 provider 자료가 없어 unavailable이다.

## 18. 수정 전/후 예시

수정 전 대표 문제:

```text
VIX 소폭 하락 -> valuation expansion
가격 지지 -> business thesis strengthen
신규 회사 근거 없음인데 14종목 중 12종목 valuation expansion
```

수정 후 실제 분포:

```text
투자 논리: 강화 0 / 유지 14 / 약화 0
오늘 Valuation 영향: 확장 0 / 중립 14 / 혼재 0 / 압축 0
가격 상태는 별도 price_state로만 갱신
현재 Valuation 위치는 비교 근거 부족으로 unknown
```

## 19. 운영 검증

- localhost health: ok
- public `/thesis/health`: ok
- Action OpenAPI JSON parse: 성공
- 서버 LaunchAgent: running
- 일일 LaunchAgent: 07:50, 08:05, 08:35 KST
- 서버 로그: 재시작 후 정상 기동

## 20. 남은 provider/data 한계

- 미국 forward PBR consensus는 현재 provider가 제공하지 않아 자료 없음이다.
- KRX 내부 FY1 값은 시장 consensus가 아니며 quality가 낮으면 계산하지 않는다.
- numeric historical/peer multiple range가 아직 없어 Valuation relative position은 대부분 unknown이다.
- 일부 OpenDART 정정보고서/비표준 금융계정은 usable snapshot으로 만들지 못한다.
- Finnhub denominator as-of가 누락되는 경우 quality는 partial이다.
- provider 실패 또는 stale macro series는 결론 강도를 낮추며 neutral로 대체하지 않는다.
