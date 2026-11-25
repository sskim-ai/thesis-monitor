# C58 — 원본 기술지표 연결 인계

## 전달 대상

- 저장소: `sskim-ai/thesis-monitor`
- 브랜치: `codex/c58-native-indicator-integration-20261125`
- 기준: C57 `179ff0f26354893529c5ffd0fbedec7968480bc3`
- 대상 SHA: 전달 결과의 `IMPLEMENTATION_COMMIT.txt`와 최종 보고에 적힌 전체 40자 SHA.
- 설계·수정 범위: `docs/C58_NATIVE_INDICATOR_INTEGRATION.md`.

이번 전달은 코드와 오프라인 검증 결과다. Mac 설치와 실제 예약 실행 결과는 아직 없다.
실행 여부를 확인하려고 금융·모델 호출이나 별도 단발을 시작하지 않는다.

## 변경의 의미

원본 OHLCV worker가 기존 봉 수집 뒤 원본 지표 함수를 한 번 사용한다.
이미 제공된 지표는 그대로 소비하고, 원본 봉은 변경하지 않는다. 작은 지표 파일을
기존 role receipt에 연결하며 replay에서는 다시 계산하지 않는다.

KR/US Source, 미국 가격 보조 경로, 실제 B/B2 요청과 상세 문안이 같은 native 자료를
사용한다. RSI·MACD·MA·BB·거래량 지표의 TM 대체 계산은 새 예약 경로에서 호출하지
않으며 ATR·Pivot·S/R·Fibonacci 등 추가 구조 계산은 유지한다. 기업 방향·보유자 판단과
밸류 판단은 기술적 진입 해석과 분리한다. 새로운 외부 요청이나 모델 호출 단계는 없다.

## Mac에서 필요한 작업

1. 전달한 SHA로 새 clean 작업트리를 만든다. 기존 실행 중 작업트리는 checkout하지 않는다.
2. 기존 Python 3.11.15 환경에서 아래 지정 시험을 한 번 실행한다.
3. 설치 작업을 진행하는 시점에 실행 중인 worker/공유 잠금이 없으면, 기존 한국·미국
   config의 `code_commit`과 plist의 코드 경로·`WorkingDirectory`, 사후 확인 helper의
   코드 참조를 같은 C58 작업트리로 맞춘다. config의 분석 정책 값은 수정할 필요가 없다.
4. 기존 로더와 plist 문법 확인, launchd readback으로 최종 참조를 한 번 대조한다.
   이미 실행되거나 소비된 미국 단발을 다시 등록·실행하지 않는다.

검증 결과는 tests/failures/errors/skipped와 실제 Python 버전으로 보고한다.
실패하면 그 원인을 수정하고 해당 항목만 재검사한다. C56·C56R1·C57 시험 및 전체 suite를
반복할 필요는 없다. 새 환경·인증·시간 계약을 만들지 않는다.

```bash
/Users/sskim/Codex/thesis-monitor/.venv/bin/python -m pytest -q \
  tests/test_c58_native_indicator_acquisition.py \
  tests/test_c58_native_source.py \
  tests/test_c58_native_model_delivery.py \
  tests/test_c58_native_integration.py \
  tests/test_c45_technical_inputs.py::test_completed_frames_and_owned_volume_reach_structure_and_source_facts \
  'tests/test_newbuyer_b2_v2.py::test_supportive_is_fundamentally_attractive_independent_of_timing[UNRESOLVED]' \
  'tests/test_c50_chart_statement.py::test_long_dwm_facts_reach_bound_b_b2_and_full_renderer[daily-us]' \
  --junitxml=C58_MAC_FOCUSED.xml
```

이 시험의 원본 엔진 파일은 저장소에 시험 데이터로 포함되어 있다. 별도 다운로드나
기존 큰 native archive 준비가 필요 없다. 실제 worker는 기존 OHLCV owner의 지표
모듈을 사용하며, 계산기와 serializer의 실제 소스 해시를 지표 파일에 함께 남긴다.

## 기존 예약

아래는 사용자가 전달한 C57 설치 결과에 따른 일정이며, 이 개발 환경에서 Mac을
직접 확인한 결과는 아니다. 적용 시점의 실제 상태를 기준으로 이어간다.

| 작업 | 유지할 일정·상태 |
| --- | --- |
| 한국 정기 | 평일 16:00 KST |
| 미국 단발 | 2026-11-26 08:10 KST, 기존 tag·대상 결과 경로 |
| 미국 사후 확인 | 2026-11-26 12:45 KST, 위 실행 결과 읽기 |
| 미국 정기 | OFF·미등록 |

NO-SEND, 호출·저장 한도, 타임아웃·재시도, 야간선물 정책과 기존 실패·소비 기록을
유지한다. 새 tag나 추가 캠페인은 이 코드 설치에 필요하지 않다.

## 다음 실제 결과에서 볼 내용

기존 정상 예약이 실행되면 같은 결과의 저장 자료만 읽어 다음을 확인한다.

- adjusted D/W/M receipt의 `native_indicators` 파일에 원본 값·null·계산 이력이 있다.
- Source의 `technical_context.features`는 null이고 native context가 연결된다.
- B와 B2 실제 요청에 같은 `native_technical_context`의 값·주기·기준일·근거가 있다.
- B2의 `technical_assessment`와 상세 문안의 기술 해석·진입 행동이 일치한다.
- 실제 원본 부족은 구체적인 부족 상태로 설명된다. 값이 없는데 TM 계산으로 보충하지 않는다.

설치 완료, 실제 Source/B/B2 도달, 최종 문안 생성은 관찰한 단계까지만 보고한다.
이번 합성 시험 통과를 실제 시장·모델 E2E 성공으로 표시하지 않는다.

## 기존 시험의 별도 문제

확장 확인으로 실행한
`tests/test_provider_native_technical.py::test_client_to_typed_prompt_and_original_sr_no_send`
KR/US 두 사례는 `dated_reference_native_period_replay_mismatch`로 실패했다.
수정하지 않은 C57 SHA의 별도 clean 작업트리에서도 두 사례가 동일하게 실패했다.
이 경로는 기존 dated 연구용 OhlcvClient 시험이며, C58 예약 경로의 회귀로 분류하지 않는다.
최초 결과와 C57 재현 XML을 함께 보관했다. 이번 설치 지정 목록에 포함하지 않는다.
