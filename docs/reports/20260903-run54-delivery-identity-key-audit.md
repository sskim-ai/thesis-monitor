# Run 54 Delivery Identity Key Audit

The repair separates three identities:

| Identity | Inputs | Purpose |
| --- | --- | --- |
| analysis generation | market, business date, source monitor run | permits analysis reuse without changing delivery ownership |
| content generation | packet, claim, policy | identifies the accepted content generation |
| delivery generation | analysis generation, content generation, channel, recipient class | owns exactly-once delivery |

All IDs are deterministic hashes. The delivery identity no longer consists of packet ID alone.
The `recipient_class` value is `production` or `test`; no recipient value is included. Reuse packet
IDs are recorded as observations and cannot replace the active or terminal owner. A mismatched
analysis generation records an ownership conflict rather than silently taking ownership.

Rejected generations have zero delivery eligibility. A delivery generation is eligible only after
the accepted artifact, selector result, combined runtime-quality gate, and persisted payload agree.
