# Track D — Single Live-Path E2E Rehearsal Contract

Replace misleading "production-equivalent" readiness claims with one real live-path E2E.

Must enter through the real production entrypoint and use:
- production config/path resolution
- selector
- persisted delivery state
- retry/dedupe/fallback
- real delivery adapter

Only redirect recipient to dedicated TEST and use isolated rehearsal namespace through native seams.

Mandatory variants:
1. full AI9 send
2. process-boundary pending recovery
3. backup/dedupe after AI send
4. controlled AI failure -> fallback9

No production recipient.
