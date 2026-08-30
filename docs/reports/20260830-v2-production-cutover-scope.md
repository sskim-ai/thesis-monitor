# V2 Production Cutover Scope

Date KST: `2026-08-30`

- Repository: `sskim-ai/thesis-monitor`
- Actual base: `6db9256b539e437a7067a1822237ef9c504c63fa`
- Work-instruction commit: `0eb8bad`
- Exact source ZIP SHA-256: `c679c7fc0c343040275f9b2ef91155db8e19f8e7d728a612080e2b5fb2bdfe05`
- Track A: `1a6488e` (`decision-aware-change-condition-v1`)
- Track B: `7f32c34` (`v2-accepted-production-runtime-v1`)
- Convergence implementation: `6c429fc2f8afc4316b319494ca098c77594d0d2d`

The cutover changes only stock decision ownership and rendering. It preserves market messages,
Price Structure, valuation, delivery identity, schema 4, Public Action 0.4.5, and all schedules.
Raw V2 candidates and unresolved adjudications are never production-visible. V1 remains an
explicit selector rollback path.

No production Telegram send, Scheduled Task trigger, assessment mutation, DB mutation, or
Production Assist enablement occurred during implementation or preflight.
