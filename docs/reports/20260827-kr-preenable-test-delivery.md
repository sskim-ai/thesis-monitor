# KR Pre-Enable Test Delivery

전용 TEST sink가 구성되지 않아 외부 전송과 수신 확인을 수행하지 않았습니다. 아래 문안은 전송 전 production-equivalent 후보입니다.

| Field | Value |
| --- | --- |
| Candidate route before sink gate | AI |
| Test route | NOT_SENT |
| Delivery namespace | TEST_ONLY_NON_PRODUCTION |
| Delivery count | 0 |
| Attempt count | 0 |
| Duplicate | 0 |
| Orphan | 0 |
| Production intent created | 0 |
| Candidate payload SHA-256 | `70b33c34f9cf6f69bb1a92a139c40973abc04e13293e52cec600e5cf2efbe7af` |
| Receipt | NOT_SENT |

`ENABLEMENT_ACTION = DO_NOT_ENABLE`
