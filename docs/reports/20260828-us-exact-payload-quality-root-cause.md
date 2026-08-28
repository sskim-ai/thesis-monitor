# US Exact-Payload Quality Root Cause

The prior report asserted that the malformed phrase was absent without evaluating a quality result
derived from the received Telegram response. The receipt itself proved that rendered, outbound,
and received bytes all contained the defect. The new delivery hook validates `result.text`, stores
its payload SHA and rule outcomes, and the report generator refuses to run unless every payload
and validator SHA is identical.

`QUALITY_PAYLOAD_MISMATCH_ROOT_CAUSE = PASS`
`HARDCODED_UNVERIFIED_QUALITY_ASSERTION = 0`
