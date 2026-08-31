# 2026-08-31 KR V2 Feature State

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

```text
VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED
V2_PRODUCTION_ENABLED = true
FULL_MONITORED_STOCK_COVERAGE_TARGET = true
V1_VISIBLE_DECISION_ENGINE = false
V1_ROLLBACK_AVAILABLE = true
V2_ACCEPTED_PRODUCTION_ARMED = true
AI_REVIEW_MODE = shadow
PRODUCTION_ASSIST = OFF
KR_MARKET_SECTOR_TOP3_ENABLED = true
KR_PRICE_STRUCTURE_V3_ENABLED = true
```

The feature state was read through the existing Settings model. No environment value was changed and no secret value was copied into this report.

The packet-level readiness result was nevertheless false: active profiles 20 complete / 22 active, with 2 missing. The suppression reason was `shadow_profile_gate_not_ready`. Production packet persistence remained independently eligible, so the normal 17:10 deterministic fallback path stayed available.
