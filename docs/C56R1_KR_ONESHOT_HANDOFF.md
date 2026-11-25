# C56R1 — 오늘 한국 단발 실물 E2E

사용자 승인: 2026-11-25 한국 완료장, 시장 1 + 기존 등록 종목 8, LIVE_NO_SEND 캠페인 정확히 한 번. 기존 C56 분석 코드를 유지한다. C56R1은 C56 9479e9be66e05124b206e94a5936e26a1d419303을 부모로 하는 공통 예약 진입점만의 변경이다. 기존 정기와 미국 예약의 C56 핀은 이번 작업에서 변경하지 않는다.

## 준비 및 시험

기존 Mac Python 3.11.15와 새 C56R1 clean worktree를 사용한다. 이미 지원되는 정식 수동 실행이 정확한 C56 및 별도 세대에서 같은 등록/검사/lease 경로를 재사용할 수 있다면 우선 재사용하고 C56R1 시험은 생략 가능하다. 지원되는 경로가 확인되지 않으면 C56R1 지정 SHA 사용. 직접 Owner/원장/동결 계획 재구현, 검사 우회 금지. 변경은 기존 configured one_shot에 KR tag/완료장 검증을 추가한 것이다. 분석, Source, 모델, 재무, 차트, 판단, 렌더러는 그대로다.

챗 환경에서는 전체 저장소 실행 시험을 하지 못했다. Mac에서 새 15개 사례를 한 번 실행한다.

```bash
/Users/sskim/Codex/thesis-monitor/.venv/bin/python -m pytest -q tests/test_c56r1_kr_configured_slot.py --junitxml=<결과 디렉터리>/C56R1_FOCUSED.xml
```

기존 C56 16개 및 전체 시험 반복 금지. 시작/종료 HEAD, clean 상태, 실제 exit code와 XML 기록. 새 시험 실패 시 원인 보존하고 live 시작 금지.

## 단발 설정과 발화

C56 설치 REGISTRATION.json의 기존 한국 정기 config를 읽어 동일 시장 설정을 새 private 0600 config에 복제한다. 원본 설정, C55 실패 디렉터리와 terminal SHA-256 49f146c61241d53fe86838dff0b7b76218bf3b1163dcc6e6a9a979338aa91043 유지. 신규 run_root, code_commit, one_shot만 지정한다. 새 tag 제안 kr-20261125-c56r1a2b, label local.thesis-monitor.kr.full.once.c56r1.20261125. 실제 미소비 확인. 공유 lease는 기존 것 그대로. 오늘 실제 KST 현재 시각을 기준으로 준비 완료 후 약 5분 뒤의 미래 시각을 정한다. 시험에 쓰인 18:30을 실제 시각으로 사용하지 않는다. 오늘 시작 가능한 시간이고 예약+4시간30분이 내일 미국 08:10보다 앞서는 경우에만 등록한다. 다음 날로 임의 변경 금지. 설정 one_shot={tag, scheduled_at: offset 포함 실제 KST 시각, target_session: 2026-11-25}. 기존 로더와 거래소 달력으로 목표일/완료장 확인. 시작 창 10분, campaign deadline 예약+16200초. 시계 위조·기존 tag/소비 기록 삭제 금지.

한도: KR 금융334(kiwoom190/kis85/opendart48/naver_news8/ecos3), 모델27 공유, MARKET/B2 확정 타임아웃 재시도 기존대로, Source600/CLI600/부모630초, campaign 4시간30분, 작업2GiB 및 기존 여유공간 guard, 호출별 정리, NO-SEND. 등록 필수 운영 DB 읽기만 허용, 쓰기 0. 추가 금융 probe, 모델 probe, 인증 재검사 금지(파일 존재/읽기 가능만). US 야간선물 정책을 KR에 복사하지 않는다. 기존 작업과 공유 lease 상태 확인.

새 plist만 등록: 기존 Python -B -m app.jobs.unified_market_snapshot --local-scheduled --configuration <새 config> --market kr --one-shot-tag <tag>. WorkingDirectory는 검증된 worktree. RunAtLoad/KeepAlive false, StartCalendarInterval 실제 KST 월/일/시/분. plutil -lint, config 로더, 달력, launchd readback. kickstart 및 다른 분석 명령 병행 금지. 예정 창 놓침/lease busy/STOP/실패면 추가 실행 금지. 기존 KR16:00 C56, US 11/26 08:10 C56, US 12:45 helper C56 및 US 정기 OFF 유지. 등록과 실행은 구분.

## 실제 결과

같은 세대의 Source/ModelPlan/MARKET/CORE/A/B/B2/VALIDATE/RENDER, 금융 실제 물리 원장, 모델 시도/수락/재시도, 등록 DB 읽기/쓰기, 실제 원문, 9/9 RENDER_VERIFIED_NO_SEND 여부를 확인한다. 실패 시 최초 오류 및 새 source_context를 보존하고 재실행하지 않는다. 실제 종목별 종합/B2/보유 판단, PBR 전달·인용, 현재가/선택 지지/손익비/무효화/WAIT 이유·확인 조건, 세 환율, 호출별 자동 정리/보관량을 표로 제출. 새 모델이나 재렌더로 채우지 않는다. 종료/lease 해제 후 새 단발 label/plist만 정리. 기존 예약 경로/핀, C55 원래 실패 terminal 보존 재확인.

작은 결과 ZIP+SHA256: 등록/시험 XML(실행시)/실제 terminal/실제 원문·비교표/호출 및 저장 요약/실패 상세/기존 예약·원래 실패 보존. 원본 금융 전체, DB, 환경, 인증값, 모델 임시 상태 복사 금지. iCloud 실제 복사본 해시 및 업로드 완료 확인. E2E는 C56 분석 코드 + C56R1 예약 진입점으로 구분 보고. C56R1은 검증 후보이며 영구 별도 시장 포크가 아니다.
