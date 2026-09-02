# Three-P1 Dedicated Test-Sink Proof

The canonical secret audit found exactly one configured dedicated test sink and proved it differs
from the production recipient. Raw recipient values were not logged, committed, reported, or
included in the bundle.

The first delivery sent 20 exact payloads and stopped on Telegram HTTP 429. Identity-aware resume
selected only the remaining two payloads. The reconciled receipt is:

- KR/US/total: `8/14/22`
- Initial/continuation: `20/2`
- Exact payload matches: `22/22`
- Duplicate/orphan: `0/0`
- Production collision: `0`
- Production recipient send: `0`
- Production delivery intent: `0`

This proof does not count as natural live delivery.
