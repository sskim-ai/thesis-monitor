# KR Pre-Enable Data Collection

추가 provider 호출은 `0`입니다. 같은 세션의 production packet과 당시 저장된 42/42 성공 증거를
read-only로 재사용했습니다.

| Family | Result | Evidence |
| --- | --- | --- |
| ka20001 | PASS | KOSPI/KOSDAQ index direction and scoped breadth |
| ka20003 | PASS | six size/style rows and current-session sector rows |
| ka10051 | PASS | six aggregate participant-flow rows, raw `100M_KRW` |
| ka10066 KOSPI | PASS | 14 pages, 1,316 rows, duplicate 0 |
| ka10066 KOSDAQ | PASS | 19 pages, 1,824 rows, duplicate 0 |

`PREENABLE_DATA_COLLECTION = PASS`
