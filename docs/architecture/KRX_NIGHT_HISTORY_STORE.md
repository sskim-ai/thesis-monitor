# KRX Night History Store

Contract: `krx-night-history-store-v1`.

Raw bytes are stored once under query date and raw SHA-256. The receipt records endpoint, service, fetch time, query date, HTTP status, size, row count, field names, and relative raw path. Normalized FINAL bars are keyed by instrument root, exact contract code, reference date, and NIGHT session. A repeated identical fingerprint is idempotent; a different fingerprint at the same identity fails closed without overwrite.

The live provider writes source history incrementally before aggregation. Collector/history failure is isolated as telemetry and never blocks stock V2 generation.
