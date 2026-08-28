# US Current-Time Stock Universe

The active DB-backed US/foreign monitored universe contained `13` subjects:

`CORZ CRCL GOOGL HUT IBM MU RXRX SKHY SNDK TSLA TSM WRD WULF`

No ticker allowlist was introduced. Eligibility was contract-derived: `ELIGIBLE_SR_ONLY=12`,
`BLOCKED=1`. WRD was blocked because its daily source ended `2026-08-26` while the declared current
session was `2026-08-27`.
