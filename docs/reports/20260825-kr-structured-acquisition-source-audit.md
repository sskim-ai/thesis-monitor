# KR Structured Acquisition Source Audit

The configured official source is KRX Open API. The implementation uses only the four existing
readiness endpoints for KOSPI stocks, KOSDAQ stocks, KOSPI indices, and KOSDAQ indices.

## Exact Target Session

- Session: `2026-08-25`
- Observation: `2026-08-25T12:27:41.246670Z`
- HTTP: `4/4` success
- Rows: `0/0/0/0`
- State: `MARKET_COMPLETED_PROVIDER_PENDING`
- Published index/breadth/flow facts: `0`

The target-session replay therefore contains no KOSPI/KOSDAQ direction, no breadth count, and no
market-wide flow. The publication state itself is useful evidence and is persisted without numeric
defaults.

## Capability Proof

The bounded 8/24 probe verified exact index identities and separate KOSPI/KOSDAQ breadth universes.
`ACC_TRDVOL` and `ACC_TRDVAL` remain official reported activity fields; no close-times-volume
substitution is labeled official. Market-wide foreign/institution/retail flow is not present in the
verified endpoints and remains Unknown.

Provider calls: `8` KRX requests, `8` successes, `0` failures. Credentials were not persisted.

Decision: `KR_STRUCTURED_ACQUISITION = PARTIAL` because capability and fail-closed integration pass,
while the exact target session was not yet published.
