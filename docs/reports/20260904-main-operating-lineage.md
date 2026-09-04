# 2026-09-04 Main and Operating Lineage

The promotion candidate is a descendant of common base `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`, KR repair `90cc52231c7343056c853c355ea90dfea10de25b`, and US repair `deb4dc511aafa6e435b0af00436d690e2e498c0b`.

Final documentation SHA, main SHA, and operating SHA are resolved from Git at closure. Promotion requires final exact-SHA Actions PASS and a clean operating fast-forward. The production API is restarted only if the deployed service imports changed runtime modules; scheduled task timing and ownership remain unchanged.

Natural proof state after promotion:

- KR: `PENDING_NEXT_ORDINARY_SCHEDULED_RUN`
- US: `PENDING_NEXT_ORDINARY_SCHEDULED_RUN`
- controlled TEST proof: PASS for both markets
