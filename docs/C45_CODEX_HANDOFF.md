# C45 — 기술 입력·가격 관계·최종 행동 연결 검증

## 목적과 범위

사용자가 합의한 네 가지 연결 수정의 Mac 오프라인 검증이다.

1. 확정 구조 계산에는 기존 완료 상태가 확인된 봉을 사용하고, 이미 계산된 현재 유효 일봉 거래량비율을 구조 엔진에 연결한다.
2. 현재 일봉 기준가격과 지지를 만든 주·월봉의 기간을 구분한다.
3. 신규매수 WAIT의 실제 이유 및 지지 무효화가 최종 행동 문구에 반영되도록 한다.
4. 한국·미국의 수락된 선택 지지 표시를 공통화하고, 미국의 V3 참고 S/R 유무와 분리한다.

기준 커밋은 `5f84a44471fd75485f7ed287029c88e7362cd61c`이다. 검증 대상은 전달 메시지에 명시된 **C45의 전체 40자리 커밋 SHA**다. 브랜치 이름만으로 대상 버전을 추정하지 않는다.

브랜치: `codex/c45-entry-technical-20261123`

## 구현 요약

- `unified_stock_owner.py`: 원본·V3 입력을 보존하면서 legacy 구조용 완료봉 view를 선택한다. 현재 유효한 `TechnicalFeatureFact`의 `volume_ratio_20` 값을 사용하며, 원본 제공자 지표 열을 대체 입력으로 사용하지 않는다. 완료봉 필터로 달라진 실제 소비 구간에도 기존 consumer 판정을 적용한다.
- `entry_price_basis.py`: 현재 일봉가격 확인과 주·월봉 구조 확인을 구분하는 작은 공통 함수다. 새로운 Owner나 인증 단계가 아니다.
- `new_buyer_input_owner.py`: 선택 지지의 평가일은 현재 가격 세션과 연결하고, 주·월봉 라벨일은 보존한다. 날짜를 덮어쓰거나 참고 V3를 ENTRY로 바꾸지 않는다.
- `detailed_stock_message_v2.py`: 같은 가격 기준 함수를 진입 품질·위치·선택 지지 표시에 사용한다. WAIT 이유를 최종 행동에 전달하고, 지지 이탈·무효화는 대기 문구에 가려지지 않도록 한다. 양국의 선택 지지는 같은 함수로 한 번 표시한다.

### 판정 의미

- 과거 주·월봉의 종가가 현재 일봉가격과 달라도, 완료봉이며 현재 세션에 평가된 구조라는 기존 원천 정보가 있으면 위치를 비교할 수 있다.
- 새 완료·평가일 정보가 없는 과거 입력은 원래의 같은 날짜·같은 종가 경로만 유지한다. 오래된 참고봉을 새 진입 근거로 승격하지 않는다.
- 가격 위치를 확인했다고 신규매수를 허용하지 않는다. 기존 사업·가치평가 판단, 현재가 손익비, 무효화 조건을 계속 사용한다.
- 월봉 무효화·손익비 공식을 새로 만들지 않는다. 지지 위치를 설명하는 것과 신규매수 검토 가능 여부는 구분한다.
- 돌파·거래량 확인 정보를 연결하지만, 별도의 돌파형 매수 정책은 추가하지 않는다.

완료봉 선택은 기존 원천 조립 결과의 완료 상태를 따른다. 원시 `PARTIAL`/`UNCONFIRMED` 표기와 거래 달력 사이의 우선순위를 정하는 상류 정책은 이번 변경 범위에 포함하지 않았다.

## 이번 검증의 경계

**오프라인 검증만 수행한다.** 금융 HTTP, 실제 모델 CLI, 운영 DB 읽기·쓰기, 발송·주문, 운영 설치·핀 변경, 예약 변경은 필요하지 않다. 기존 시험의 임시 메모리 SQLite fixture는 운영 DB가 아니다.

PBR 활용 정책, CORE/B의 종합·보유자 판단 범위, 신규 돌파 매수 정책, 재시도·시간 제한·모델 호출 상한, 인증 정책 및 범용 결과 보존·재생 시스템은 이번 변경에 포함하지 않았다.

현재 운영은 기존에 합의한 핀과 예약을 사용한다. 이 커밋의 검증 통과는 운영 전환이나 미국 정기 활성화를 뜻하지 않는다.

## 구현 환경에서의 확인

아래와 동일한 집중 시험을 Python 3.12.14에서 실행해 **53/53 PASS**를 확인했다. 신규 C45 검사 25개와 관련 기존 회귀 검사 28개이며, 실패·오류·skip은 0개였다. 이 결과는 Mac 검증을 대신하지 않는다.

수정한 운영 코드 4개와 신규·확장 fixture의 Ruff 검사 및 `git diff --check`도 통과했다. 기존 C43 시험에는 기대 문구 한 곳만 수정했으며, 그 파일의 기존 스타일 경고는 이번 변경에 포함하지 않았다.

## 실행 순서

1. 기존 개발용 통합 작업트리에서 원격 브랜치를 fetch하고 전달받은 정확한 SHA를 확인한다. 운영 예약이 사용하는 작업트리는 바꾸지 않는다. 개발 작업트리에 미커밋 작업이 있으면 이를 보존하고 별도 작업트리를 사용한다. 기존 Python 환경을 우선 재사용한다.
2. `git rev-parse HEAD`, `git status --short`로 대상과 시작 상태를 기록한다.
3. 아래 집중 시험을 한 번 수행한다. 먼저 전체 pytest를 수집하거나 과거 외부 fixture/인증 환경을 복구하는 작업은 하지 않는다.

```bash
python -m pytest -q \
  tests/test_c45_technical_inputs.py \
  tests/test_c45_entry_basis.py \
  tests/test_c45_entry_presentation.py \
  tests/test_c44_entry_presentation.py \
  tests/test_c44_renderer_replay.py \
  tests/test_c43_offline.py::test_supported_only_with_bound_current_price_scenario \
  tests/test_c43_offline.py::test_resistance_overlap_and_invalidation_win_over_positive_rr \
  tests/test_c43_offline.py::test_no_zone_vs_mismatch_and_changed_context \
  tests/test_c43_offline.py::test_action_axes_and_reason_matrix \
  tests/test_c43_offline.py::test_only_entry_owned_typed_confirmation_or_warning \
  tests/test_newbuyer_b2_shadow.py::test_timing_adapter_uses_exact_owned_price_zone_chain \
  tests/test_unified_stock_owner.py::test_actual_existing_owners_deterministic_and_optional_absence \
  tests/test_completed_bar_b2_parity.py::test_changed_price_input_cannot_reuse_old_model_output \
  --junitxml=../C45_FOCUSED.xml
```

명령의 `python`은 기존 개발 환경의 Python을 사용한다. XML은 작업트리 밖에 기록하며, 이미 같은 이름의 파일이 있으면 새 결과 디렉터리를 사용한다. 새 환경 설치나 전체 의존성 갱신이 필요하면 원인을 먼저 특정한다. 변경되지 않은 시험을 반복 실행해 통과 개수를 늘리지 않는다.

4. 집중 시험이 실패하면 정확한 실패와 관련 코드만 확인한다. 이 검증 작업에서 분석 정책을 바꾸거나 원래 수락 결과를 고쳐 맞추지 않는다. 구현 변경이 필요하면 실패 근거와 최소 수정 제안을 반환한다.
5. `git diff --check`, 최종 HEAD와 작업트리 상태를 확인한다. 이전 C44의 정상 예약·설치 확인을 반복하기 위해 plist나 운영 DB를 다시 조사할 필요는 없다.

## 검증이 증명하는 것

- 원천 조립 함수에서 실제 구조 엔진까지의 완료봉·거래량 연결.
- 주·월 지지와 현재 일봉가격의 관계 및 부적격 입력 거부.
- 지지 이탈·무효화와 사업/가치평가 WAIT 사유의 일관된 표시.
- V3 참고 S/R 없이도 한국·미국 전체 종목 렌더러가 선택 지지를 한 번 표시하는 합성 사례.
- 기존 종합·보유 결론, 원본 B2 요청·결과·수락 정보 및 NO-SEND의 보존.

원천 조립 검사는 기존 합성 fixture를 사용한다. 전체 문안 검사는 **합성 수락 입력을 실제 렌더러로 처리한 결과**다. C42/C36 보존 실물의 전체 문안을 재생한 증거가 아니며, 과거의 0/2를 PASS로 바꾸지 않는다.

입력 연결이 바뀌었으므로, 과거 실물의 B2 수락 해시를 새 입력에 맞게 수정하거나 원래 프로세스의 Owner를 재발급해 재생하지 않는다. 새 입력에 대한 실제 모델 판단은 별도로 합의한 다음 실물 실행에서 확인할 항목이다.

## 최소 반환 결과

- `RESULT.md`: 대상 전체 SHA, Python 버전, 집중 시험의 실제 개수·실패 여부, 변경점 네 가지와 검증 범위.
- `C45_FOCUSED.xml`: 위 한 번의 시험 결과.
- 시작/종료 Git 상태와 `git diff --check` 결과.
- 실물 금융·모델·운영 DB·발송·예약·설치 변경 횟수.

성공 표기는 `C45_MAC_OFFLINE_PASS`로 한다. 합성 결과를 KR 실물 9/9·US 실물 15/15 또는 실제 B2 재수락으로 표시하지 않는다.

결과 전달은 기존 `Codex Results` 방식의 작은 ZIP과 SHA-256이면 충분하다. 소스 저장소·venv·과거 결과 ZIP을 중복 복사하지 않는다. iCloud 완료 여부는 Mac에서 실제 확인한 범위만 보고한다.
