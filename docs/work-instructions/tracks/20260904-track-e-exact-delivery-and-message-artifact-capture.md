# Track E — Exact Delivery + Messages

실제 전송된 market + US14 메시지 raw text를 저장하고 각 메시지를:
PRIMARY_AI
BACKUP_AI
FALLBACK
UNKNOWN
으로 매핑한다.

Primary가 backup 이후 늦게 완료했다면 late-result state도 추적한다.

No resend.
