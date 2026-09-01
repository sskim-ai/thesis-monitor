# Track D — Fault Injection + Frozen Replay + Main Merge Guard

Replay archived run-49 packet copy.

Healthy path target:
- 14/14 technical context
- 14/14 candidate generation
- packet-bound accepted decisions
- explicit v2 blocks for accepted-ready subjects

Fault injection:
- ConnectError
- connect/read timeout
- service restart
- one malformed ticker
- stale daily cache
- partial W/M

Run KR regression and current US test sink.

Mandatory controls:
CORZ, CPNG, GOOGL, HUT, TSLA, WULF, MU, 000660, 047810.

No production recipient.
No run-49 replay to production.
Merge only with P0/P1 = 0/0.
Then wait for the next natural live proof.
