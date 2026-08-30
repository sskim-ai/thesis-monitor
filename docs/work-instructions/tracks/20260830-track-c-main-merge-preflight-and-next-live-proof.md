# Track C — Main Merge, Preflight, and Next Natural Live Proof

Before merge:
- full monitored-universe inventory
- fresh non-production preflight
- complete test-sink exact payload proof
- rollback readiness
- P0/P1 = 0/0

Then:
- merge to main
- verify FINAL_MAIN = ORIGIN_MAIN = OPERATING
- arm V2_ACCEPTED production path
- no manual production send on 2026-08-30
- no manual Scheduled Task trigger

Natural targets:
- KR regular close 2026-08-31 KST
- US 2026-08-31 America/New_York close, expected 2026-09-01 KST morning

Review both read-only after normal scheduled execution.
