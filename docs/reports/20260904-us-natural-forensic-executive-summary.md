# US Natural Primary/Backup Forensic Executive Summary

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Answer

Primary did start, claimed `2026-09-04-us-run-55-54cd536c6e4d`, remained actively processing at 08:20, and completed a market-plus-US14 candidate. There was no 08:20 primary-missing checker and no missing flag. The fourth producer run at 08:20 only reused the successful packet and kept delivery held for AI review.

Backup began on its independent 08:30 schedule and reclaimed the same packet at `08:30:39.046046 KST` because the primary's 10-minute lease had expired and no final output existed. Primary and backup overlapped on shared claim ownership. Primary's late finalization was correctly fenced as stale.

Both natural claim-scoped xhigh canaries reproduced the earlier shadow symptom: raw TLS `UnknownIssuer`. The outer Codex automations nevertheless authored candidates. Primary had one 15-part candidate and zero accepted outputs. Backup had one reused 15-part candidate, one permitted correction, and zero accepted outputs after two validator rejections.

The user received exactly `15/15` deterministic fallback messages: market 1 and stocks 14, all first-attempt sends, with no duplicates. The message bodies are captured verbatim in `docs/reports/messages/20260904-us-natural/`.

## Gates

```text
PRIMARY_STATE_AT_0820 = RUNNING_ACTIVE
PRIMARY_MISSING_FLAG_FOUND = NO
BACKUP_TRIGGER_REASON = scheduled backup claim after primary lease expiry
PRIMARY_MODEL_STATE = COMPLETED
PRIMARY_V2_CANARY_MODEL_STATE = FAILED_TLS
BACKUP_MODEL_STATE = COMPLETED
BACKUP_V2_CANARY_MODEL_STATE = FAILED_TLS
NATURAL_US_TLS_STATUS = UNKNOWN_ISSUER_OBSERVED
SHADOW_US_INTERFERENCE = NONE_CONFIRMED
PRIMARY_BACKUP_OVERLAP = OVERLAP_SHARED_STATE
PRIMARY_LATE_RESULT_STATE = SUPERSEDED
FIRST_MATERIAL_FAILURE_CLASS = MODEL_TRANSPORT_FAILURE
AI_SENT = 0
FALLBACK_SENT = 15
DUPLICATE_SENT = 0
```

No replay, model rerun, production mutation, resend, scheduler change, DB mutation, or main merge was performed.
