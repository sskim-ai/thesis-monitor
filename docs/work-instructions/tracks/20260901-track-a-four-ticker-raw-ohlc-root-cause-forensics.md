# Track A — Four-Ticker Raw OHLC Root-Cause Forensics

Mandatory subjects:
- CPNG
- HUT
- MU
- SKHY

For each identify:
- exact invalid bar/timeframe/session
- raw provider values
- violated invariant
- raw/normalized fingerprints
- first bad transformation stage
- reproducibility across bounded refetches

Trace:
provider → adapter → mapping → adjustment → timezone/session → aggregation → cache → packet → validator.

Do not repair yet until root cause is evidenced.
