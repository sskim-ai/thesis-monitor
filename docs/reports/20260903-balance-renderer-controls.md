# 2026-09-03 Balance Renderer Controls

## Accepted Renderer

Both accepted renderers read `accepted_directional_balance` from a READY accepted plan and emit:

```text
🧠 AI 분석 판단: HOLD
판단 균형: BUY 5 : SELL 5
판단 확신도: ...
```

Integer values omit `.0`; half-step values retain one decimal place. Render validation requires the exact accepted balance line and rejects candidate-label leakage. Runtime block loading verifies the stored block balance against the accepted plan.

## Focused Validation

- V2 decision, runtime, and onboarding regression files: 71 passed
- Ruff format/check: PASS
- Production renderer BUY/HOLD/SELL controls across US and KR: PASS
- KEEP_V1 candidate BUY to accepted HOLD balance rendering: PASS
- Common transaction disclaimer behavior: unchanged

No Telegram, recipient, delivery-ledger, assessment, warning, or production state mutation occurred in Track A.
