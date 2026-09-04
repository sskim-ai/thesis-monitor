# Track D — Shared US Regression + Exactly Once

Because common daily-review/orchestration code may be changed, verify US too.

If the changed code is shared with US:
run one real production-entrypoint US TEST E2E.

Required:
- AI market = 1
- explicit stock V2 = 14
- compatibility/pilot fallback = 0
- deterministic fallback = 0
- duplicates = 0
- UnknownIssuer = 0
- healthy primary backup reclaim = 0

Also test:
- V2 hard timeout
- authorized interruption
- fallback/compatibility beats late AI
- late V2 cannot duplicate a terminal delivery
