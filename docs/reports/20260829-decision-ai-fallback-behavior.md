# Decision AI Fallback Behavior

- Date: `2026-08-29 KST`
- Contract: `cross-market-ai-decision-engine-v1`
- User-visible production change: `0`

AI/schema/ref/semantic failure produces `decision_omitted`. It does not create BUY, HOLD, or SELL from a score, does not alter the existing production message, and does not mutate assessments. Rejected attempts were retained as archive evidence and never delivered.
