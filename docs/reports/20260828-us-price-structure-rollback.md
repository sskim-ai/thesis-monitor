# US Price Structure Rollback

Rollback is independently bounded to the secure operating flag
`US_PRICE_STRUCTURE_V3_ENABLED=false`, followed by the existing service restart and health check.
KR TOP3 and KR Price Structure flags must remain unchanged. No database, assessment, Scheduled
Task, Public Action, schema, or Telegram mutation is part of rollback.

Trigger rollback only for a material natural US Price Structure failure. A pending natural proof
is not a failure and does not trigger rollback.
