# US Exact-Payload Quality Contract

Contract: `us-morning-exact-payload-quality-v1`

Quality input is the exact Telegram response text. Required section order and bounded malformed or
generic macro semantics are checked programmatically. A stale validator result cannot be paired
with a changed candidate because report generation requires validator SHA and received SHA parity.

`QUALITY_VALIDATOR_INPUT = EXACT_RECEIVED_PAYLOAD`
`QUALITY_REPORT_PAYLOAD_SHA256 = d4c4d2e2399cfe1dd24cf9d598d5cf8a853f8d4a7160adff4625aec77fbbb3d3`
`RECEIVED_PAYLOAD_SHA256 = d4c4d2e2399cfe1dd24cf9d598d5cf8a853f8d4a7160adff4625aec77fbbb3d3`
`QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = 0`
`REPORT_PAYLOAD_QUALITY_PARITY = PASS`
