# C58 — 원본 기술지표의 예약 분석 연결

기준 커밋: `179ff0f26354893529c5ffd0fbedec7968480bc3` (C57).
작업 브랜치: `codex/c58-native-indicator-integration-20261125`.

## 유지할 합의

OHLCV Analyst / Stock Screener의 원본 지표값·필드명·계산 의미를 그대로 사용한다.
TM은 추가 구조인 ATR, Pivot, S/R, Major Swing, Fibonacci, 박스, 무효화 가격,
구조 손익비를 계산한다. 원본 RSI·MACD·MA·BB·거래량 지표를 TM의 다른 공식으로
대체하지 않는다. 값이 없으면 없는 상태를 전달하며 자체 계산기로 돌아가지 않는다.
공급자 수집 상한은 사용 가능한 지표의 최소 봉 수가 아니다.

완료 조건은 Source 저장에 그치지 않는다. 같은 값·봉 주기·기준일·원본 근거가
예약 경로의 실제 B/B2 요청에 도달하고 기술적 해석이 최종 문안에 반영되어야 한다.
CORE/A의 기업 방향 판단과 B2의 기업가치 판단은 기술적 진입 판단과 분리한다.

## 검토 결과와 수정 경계

| 구간 | C57에서 확인한 문제 | 수정 |
| --- | --- | --- |
| 예약 수집 | 원본 `get_bars()`까지만 호출 | 같은 격리 worker에서 원본 지표 함수를 한 번 사용 |
| 원본 보관 | raw normalization replay가 봉 해시에 의존 | 원본 봉 보존, 작은 지표 파일을 기존 receipt에 연결 |
| Source 조립 | TM feature 계산 및 반복 계산 | 원본 지표 projection, `features=None` |
| 완료 주·월봉 | 진행 중인 주·월봉을 TM이 일봉으로 합성 | 원본 완료봉 지표와 합성 partial 구조 봉을 구분 |
| 차트·구조 | 원본 필드를 제거하고 TM 거래량 비율 재주입 | 원본 chart 필드 복구, 기존 `provider_native=True` 사용 |
| 미국 가격 대체 경로 | `features`와 TM builder를 직접 사용 | native 품질 상태를 유지하고 가격 owner는 그대로 사용 |
| B 입력 | native 공식·주기 묶음이 중간 context에서 사라짐 | 기존 native evidence와 compact bundle을 함께 전달 |
| B2 입력·출력 | 지표 없음, 기업가치만 판단 | 같은 bundle 전달 및 별도 기술 해석 한 항목 |
| 최종 문안 | 가격·구조 판단만 반영 | 기술 해석·근거와 일관된 진입 행동 표시 |
| 지표 inventory | legacy ID/필드명만 인식 | native MA/BB/RSI/MACD/volume 인식 |

검토한 연결은 registered/scheduled entry → native worker → raw replay → canonical
Source → KR/US completed-price 경로 → stock owner → typed evidence → CORE/A/B/B2
요청 → 출력 검증 → 상세 문안이다. 과거 결과 재현용 계산기와 dated native 연구
경로도 호출 관계를 확인했다. 과거 코드의 일괄 삭제나 금융 분석 정책 변경은 필요 없다.

## 설계

### 1. 수집 단계에서 원본 계산기를 한 번 사용

기존 수집 요청·페이지 수·수급 요청·타임아웃·재시도는 그대로 사용한다.
원본 OHLCV owner의 `add_indicators()` / `indicator_dict()`를 호출한다.
전체 수집 history를 원본 서비스와 같은 순서로 정렬·계산한 뒤 최근 30개 지표행만
보관한다. 이미 완성된 지표가 제공된 경로는 해당 값을 그대로 복사한다.
TM 수식 복사, 구간별 EMA 재시작, 새로운 금융 조회는 추가하지 않는다.

`role-###.normalized.json`은 변경하지 않는다. 별도 지표 파일은 다음만 보관한다.

- 기존 role의 `entry_id`와 normalized 원본 해시
- 실제 원본 계산기/serializer 모듈 및 내용 해시, 지표 schema
- 계산에 사용한 행 수와 원본 지표의 날짜별 값
- 사용 가능 여부 및 계산하지 못한 경우의 구체적인 상태

기존 role receipt의 `native_indicators = {artifact, sha256}`으로 연결한다.
원본 봉 replay에서는 지표를 다시 계산하지 않는다. 새 승인·등록·시간 계약은 없다.

`decode_native_indicators(read, receipt, artifact_reader, required=False)`는 기존
원본 해시와 지표 파일의 연결을 확인하고 값의 변환 없이 반환한다.
새 예약은 지표 파일 형식을 요구한다. 파일 안의 null/짧은 history/UNAVAILABLE은
기술정보 부족으로 전달하며 legacy 계산기로 대체하지 않는다.

### 2. 같은 native 자료를 Source와 구조 계산에 연결

`native_indicators`는 D/W/M별 작은 projection mapping으로 전달한다.
raw 봉에 가짜 HTTP capture나 새 출처를 붙이지 않는다.

`build_owned_provider_native_view()`는 기존 완료봉 선택 결과와 이 projection을
결합한다. `ProviderNativeTechnicalView`와 `PacketOwnedTechnicalContext`를 재사용하며
예약 기술 사용 범위는 `MONITORING_TECHNICAL`로 표현한다. 가격의 적격 여부는 기존
가격 owner가 계속 결정한다. 연구용 `DATED_TECHNICAL_ANALYSIS`의 의미는 보존한다.

`materialize_source_components(..., native_indicators=None)`에서 `None`은 과거
저장 결과의 legacy 재현만 의미한다. 새 예약의 mapping은 TM feature builder,
feature dependency 재계산, current-effective feature 재계산을 통과하지 않는다.
`components.native_technical_context`에 결과를 보관하고 stock owner는 이 값과
원본 projection의 일치를 확인한다.

완료된 원본 주·월봉의 날짜를 그대로 유지한다. 일봉으로 만든 partial 주·월봉에
다른 날짜의 지표를 이식하지 않는다. 숫자를 TM feature 정밀도로 반올림하지 않는다.
차트에 기존 RSI/MACD/BB/거래량 필드를 복구하고, 구조 계산에는 기존 native 옵션을
사용해 별도 Bollinger 재계산·legacy confluence 혼합을 피한다.

### 3. B/B2에 실제 전달

B의 기존 `native:` evidence를 그대로 사용한다. 과거 `technical-feature:` 필터를
해제해 TM 자체 지표까지 섞지 않는다.

`canonical_monitoring_input.b_input()`에서 `native_technical_context`를 붙인다.
provider, 지표 schema, 원본 공식 설명, D/W/M별 날짜·값·계산 이력 길이·완료행 수·quality·field→evidence ref를
포함하고 전체 봉은 넣지 않는다. B2의 두 whitelist에도 같은 묶음을 연결한다.
기존 frozen context가 이 입력을 함께 고정하므로 별도 검증 체계를 추가하지 않는다.

B는 지표를 추세·모멘텀·거래량과 지지구간 선택 설명에 사용한다.
B2는 기업가치 출력과 실제 가격/지지구간 관계를 보존하면서 다음 항목을 추가한다.

```text
technical_assessment:
  state: SUPPORTIVE | MIXED | ADVERSE | INSUFFICIENT
  evidence_refs: 실제 전달한 원본 지표 근거
  reason: 짧은 한국어 정성 해석
```

새 native 입력에는 이 출력이 필요하다. 원본 지표가 없는 과거 요청은 기존 형식을
유지한다. 지표가 유리하다고 기업 매력을 올리거나, 지표가 불리하다고 기업 매력을
내리지 않는다. RSI 등의 보편 임계값이나 티커별 예외를 새로 만들지 않는다.

### 4. 문안과 진입 행동

상세 문안에 기술지표 해석과 원본 근거를 한 줄 추가한다. 실제 ADVERSE 해석이
있으면 '신규 매수 검토 가능'과 충돌하지 않도록 기술적 부담 확인 대기를 표시한다.
기존 기업 매력·보유자 판단·가격이 지지구간 안/위/아래라는 사실은 바꾸지 않는다.
MIXED/일부 지표 누락을 일괄 매수 금지로 바꾸지 않는다.

## 구현 순서와 파일 소유 범위

| 단계 | 주요 파일 | 완료 기준 |
| --- | --- | --- |
| 1. 원본 지표 수집 | `unified_stock_source_worker.py`, `unified_stock_acquisition.py` | 원본 함수 1회, raw 불변, 지표 파일과 receipt 연결 |
| 2. Source/구조 전환 | `provider_native_technical.py`, `packet_owned_technical_context_service.py`, `unified_stock_anomaly_scope.py`, `unified_stock_owner.py`, `kiwoom_completed_close_owner.py` | native 값 보존, TM 기본 지표 계산 없음, 추가 구조 유지 |
| 3. 공통 예약 연결 | `canonical_source_replay.py`, `completed_price_state.py` | KR/US 및 미국 대체 가격 경로가 같은 native mapping 사용 |
| 4. 모델과 문안 | canonical B input/domain, B2 input/request/contract, 상세 renderer | B/B2 실제 payload와 문안까지 연결 |
| 5. evidence/inventory 및 독립 검토 | cross-market evidence, direction/timing inventory, 집중 시험 | 공식·범위·값이 일치하며 legacy/가격/기업 판단 경계 유지 |

## 필요한 확인만 수행

원본 엔진 시험은 OHLCV Analyst 커밋 `f19c54b8299031caf473737e044f0a2b77db5671`의
원본 `app/indicators/technical.py`를 그대로 보관한
`tests/fixtures/ohlcv-native-f19c54b.technical.py.txt`를 사용한다.
Git blob `7054107179b78a49165fc019eb14019808ce27c3` 및 SHA-256
`ed793cdeb4b89d6787f95e5ee2ba191ec0f7ffd0d1c680b90451dc10aa838835`로 원본을 대조했다.
이 파일은 시험 데이터이며 운영 코드에서는 import하지 않는다. 운영 worker는 기존
OHLCV 작업트리의 실제 함수를 사용한다. 시험 중 네트워크 다운로드나 새 시장 조회는 없다.

1. full history로 계산한 원본값과 저장된 지표가 동일하고, null과 정밀도를 보존한다.
2. KR/US 실제 Source 조립에서 native 값이 B와 최종 B2 provider payload까지 도달한다.
3. 해당 경로에서 TM feature/local BB 함수를 호출하면 실패하도록 하여 재계산 없음을 확인한다.
4. 완료 W/M와 partial 봉 구분, 원본 누락 시 fallback 없음, CORE/A 분리를 확인한다.
5. 실제 renderer에서 기술 해석과 근거, ADVERSE일 때의 진입 문구 일관성을 확인한다.
6. 변경된 경계의 기존 대표 시험만 실행하고, 실패가 생기면 해당 원인에 한해 재검사한다.

전체 suite·C57 저장량 시험 반복, 신규 실수집·모델 호출은 이 코드 검증에 필요 없다.
Mac 설치는 완성된 변경·집중 시험 결과를 기준으로 별도 인계한다. 이 작업의 검증
결과만으로 실제 시장·모델 E2E 성공이나 운영 반영 완료를 주장하지 않는다.

## 검증 결과

Python 3.12.14 개발 환경에서 C58 관련 고유 **38건의 PASS**를 확인했다.
35건은 새 수집·Source·모델 전달·실제 요청 생성 시험이고, 3건은 변경 경계의 기존
대표 시험이다. 전체 suite는 실행하지 않았다.

| 실행 | 실제 결과 | 처리 |
| --- | --- | --- |
| 최초 집중 실행 | 38건 중 26 PASS / 12 FAIL | 실패 근거 XML 보존 |
| 수정 항목과 새 경계 확인 | 15건 중 14 PASS / 1 FAIL | 실패한 경계 fixture의 실제 거래일 사용으로 수정 |
| 실제 B 요청 생성과 최종 경계 확인 | 3/3 PASS | KR/US before_b→capture→freeze→wire와 partial/future 구분 |
| 별도 C57 원본 비교 | 기존 dated 연구 시험 2건 모두 같은 FAIL | C58 회귀와 구분해 기록 |

최초 실패 12건은 Linux 시험에서 Mac boot identity를 직접 호출한 fixture 2건,
새 빈 근거 배열의 wire item 타입 누락 1건, 새 기술 출력 enum/prose를 생성하지 못한
기존 시험 helper 7건, 수정 전 C57에서도 실패하는 dated 연구 경로 2건이다.
boot 값과 모델 출력은 시험에서만 명시적인 합성 자료로 제공했다. 운영 boot 검사,
원본값 일치 검사, 모델 출력 제한을 약화하지 않았다. 후속 1건은 한국 휴장일을
완료 거래일로 가정한 시험 fixture 오류로, 실제 fixture의 마지막 거래일을 사용했다.

교차 코드 검토에서 다음을 추가 보완했다.

- 완료봉 필터로 사라진 불량 과거 봉이 원본 EMA 계산에 미친 영향을 숨기지 않도록,
  기존 원본 무결성 검사를 완료봉 선택 전으로 옮겼다. 이후 partial/future 봉은
  이전 완료 지표를 보편적으로 차단하지 않는다.
- B/B2에 계산행 수·완료행 수를 전달한다. 별도 최소 이력 조건은 만들지 않았다.
- `RSI14 주봉` 같은 정확한 지표명 숫자가 수량으로 오인되지 않도록 기존 문안
  검사의 지표명 처리 순서를 바로잡았다.
- 미국 가격 재결합에서 native 파일이 사라져도 legacy TM 계산으로 돌아가지 않는다.

통합 시험은 실제 원본 엔진, KR/US Source 조립, canonical B 변환,
`ProductionMonitoringSession.before_b`·`capture`·`freeze_stage`·`verify_model_build`,
최종 B2 request owner와 `production_model_transport.render_prompt`를 사용한다.
시장 봉·금융 응답·상류 경제 판단·모델 응답은 합성 자료다. 외부 모델의 실제 판단
품질이나 운영 session의 실행 권한을 합성 시험으로 입증했다고 주장하지 않는다.

## 완료 상태

관련 경로 감사, 설계, 단계별 구현, 집중 검증과 독립 검토 완료.
Mac 인계는 `docs/C58_CODEX_HANDOFF.md`를 따른다.
Mac 설치와 실제 예약의 최종 문안 생성은 PENDING이다.
