# Track B — Probability Token Boundary + Negated Trade Semantics

Fix:
- MU: 상승률 vs 승률 substring false positive
- SNDK/TSLA: 즉시 매수가 아닌 false positive

Use token/semantic boundaries, not raw substrings.

Trade semantics:
ACTIONABLE / NEGATED / DESCRIPTIVE / NONE.

Preserve true hard blocks for unsupported:
즉시 매수
반드시 매도
무조건 매수
전량 매도.

