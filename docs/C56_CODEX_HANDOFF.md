# C56 — 종가 숫자 등록과 Source 누락 진단

## 범위와 기준

사용자가 2026-11-25 새 챗 세션에서 승인한 세 범위를 구현했다.

1. `latest_daily_close`·`weekly_close`를 기존 `chart_close_price`에 등록하고 KRW/USD 및 일·주봉 기준일 의미를 유지한다.
2. `business_mandatory_source_incomplete` 발생 시 기존 실패 영수증에 시장·종목·누락 항목·필드 경로를 보존한다.
3. 한국·미국의 실제 Source 조립 경로, 정상 숫자 등록, 다른 미등록 숫자의 차단, 오류 진단 보존을 집중 검증한다.

- 저장소: `sskim-ai/thesis-monitor`
- 기준 커밋: `f36b5530d500b286ba1af1ff6b135ab65d6b0c5a`
- 구현 브랜치: `codex/c56-source-numeric-diagnostics-20261125`
- 반영 대상: 채팅으로 전달하는 최종 C56 40자 커밋 SHA
- 구현 완료와 Mac 운영 반영은 별도 상태다. 이번 작업은 코드 수정·오프라인 검증·push까지다.

## 확인된 원인과 수정

C54는 차트 무효화 fact에 두 종가를 추가했지만, 숫자 등록 규칙에는 해당 필드가 없었다. C55의 기존 registry 코드와 수정 코드를 같은 합성 차트 관측값으로 대조했다.

| 필드 | C55 등록 상태 | C56 등록 상태 |
|---|---|---|
| `chart_invalidation.fields.latest_daily_close` | `registered=false`, `unit=number` | `registered=true`, `chart_close_price`, KRW/USD |
| `chart_invalidation.fields.weekly_close` | `registered=false`, `unit=number` | `registered=true`, `chart_close_price`, KRW/USD |

`numeric_semantic_registry.py`의 기존 필드 규칙에 정확한 두 경로만 추가했다. 새로운 숫자 의미·완화 규칙·종목별 예외는 만들지 않았다. 기존 `evaluation_date`, `weekly_bar_date`, 비교 기준, 무효화 상태, 가격·손익비 계산은 그대로다.

`fresh_financial_stock_owner.py`에서는 기존 `ValueError`를 상속하는 `BusinessMandatorySourceIncomplete`로 실패 문맥을 전달한다. 기존 오류 문자열 접두사와 누락 코드 형식을 유지하고, `source_context`에는 다음만 넣는다.

- `market`, `ticker`
- 중복 제거·정렬한 `mandatory_missing`
- `fact_id`와 `field_path`만 포함하는 `unregistered_fields`

`unified_market_snapshot.py`의 기존 `failure-diagnostic.json` 기록기는 이 예외 타입에만 고정 오류 코드와 문맥을 추가한다. 숫자 값·원본 응답·개인 투자논리·일반 예외 전문은 추가하지 않는다. 기존 정적 오류 목록, 일반 오류의 영수증 형식, 최초 기록과 SHA 보존, STOP 및 예외 재전파 동작을 유지한다.

## 검증 결과

Python 3.12.14 / pytest 8.4.2에서 아래 변경 경계를 실행했다.

| 실행 범위 | 결과 | 실행 시간 |
|---|---|---|
| `tests/test_c56_source_numeric.py` | 4 PASS, 실패·오류·skip 0 | 27.26초 |
| `tests/test_c56_failure_diagnostic.py`와 `tests/test_local_failure_diagnostic.py` | 12 PASS, 실패·오류·skip 0 | 2.63초 |
| 합계 | **16 PASS** | 두 실행 모두 exit 0 |

Source 검증은 KR `005930`과 US `CORZ`의 합성 원본 응답·수신 영수증에서 시작한다. 거래소 달력의 거래일로 일봉을 만들고 주·월봉으로 집계한 뒤, 기존 완료봉 소유자와 `assemble_fresh_stock(reported_comparison_business=True)`를 실제로 거친다. 사전 조립한 stock/catalog나 Source 성공 결과를 대신 주입하지 않는다.

두 시장 모두 차트와 무효화 fact가 실제 생성된 상태에서 정상 Source 조립을 통과했다. 두 종가의 값·통화, 서로 다른 일봉 평가일과 주봉 관측일, 원본 입력, boolean 상태, evidence statement 보존을 확인했다. 실제 fact 생산기에 추가한 미등록 숫자는 두 시장 모두 계속 차단됐고 해당 종목과 정확한 필드 경로가 남았다.

오류 기록 검증은 KR/US 문맥 보존, 원시 값 제외, 최초 영수증·SHA 보존, 같은 접두사를 가진 일반 오류의 비공개 처리, 원래 예외 객체 재전파와 `STOPPED_NO_SEND`, 이미 소진된 실행의 재실행 차단을 확인했다. 새 테스트 2개 파일의 Ruff 검사와 `git diff --check`도 통과했다. 읽기 전용 독립 리뷰에서 수정이 필요한 기능 결함은 발견되지 않았다.

전체 테스트와 C54·C55의 기존 수집·분석·검증은 반복하지 않았다. 테스트 fixture의 메모리 SQLite와 합성 HTTP transport만 사용했으며 **실제 금융 HTTP·실모델·운영 DB 접근·발송·주문·예약 변경은 모두 0회**다.

## C55 실제 실행과의 구분

기존 `TM_PR52_C55_KR1600_20261125_FAILURE_ANALYSIS.zip`의 SHA-256을 함께 받은 SHA 파일과 대조했다.

```text
fc61f028e359a095ea414fc740474e4563067c49d539cbad528fc0c58f599191
```

보고서와 실패 코드가 연결되는 것을 확인했지만, 이 ZIP에는 해당 실행을 다시 조립할 전체 원본이 없다. 당시 최초 실패 영수증은 종목·누락 필드를 기록하지 않았으므로, C56 fixture의 종목을 당시 최초 실패 종목으로 주장하지 않는다. 이번 확인은 코드 결함의 재현과 수정 검증이며, 원래 한국 실행의 Source 재수락이나 실제 9문안 생성 결과가 아니다. 원래 실행 상태는 시장 0/1·종목 0/8·모델 0회로 보존한다.

## Mac 검증·반영 인계

현재 운영 예약이 이 커밋을 사용한다고 보고하지 않는다. 기존 합의된 Mac 검증·반영 단계에서 최종 C56 SHA를 가져와 별도 작업트리에서 확인하고, 기존 실행 코드와 설정의 핀을 함께 맞춘다. 예약이 참조하는 활성 작업트리를 임의 checkout하지 않는다.

반영 검증에는 위 개발 결과를 재사용한다. Mac 환경 확인이 필요한 경우에도 다음 변경 경계만 한 번 사용한다.

```bash
"$C56_PY" -m pytest -q \
  tests/test_c56_source_numeric.py \
  tests/test_c56_failure_diagnostic.py \
  tests/test_local_failure_diagnostic.py
```

한국 평일 16:00과 기존 미국 단발의 시각·대상·호출 상한은 변경하지 않는다. 기존 인계 기준 미국 단발은 **2026-11-26 08:10 KST**, 대상은 미국 2026-11-25 완료장이며, 이번 문서는 새 예약·단발·재수집·실모델 호출을 추가하지 않는다. 원래 실패 실행을 재개하거나 새 tag로 다시 돌리지 않는다.

Mac 반영 결과는 실제 커밋·코드/설정 핀 readback으로 별도 보고한다. 이후 원래 정상 예약 결과를 읽을 때 Source 수락 여부와 새 오류 문맥의 실제 보존 여부를 확인한다. 이번 오프라인 PASS를 실제 문안 생성 성공으로 대체하지 않는다.
